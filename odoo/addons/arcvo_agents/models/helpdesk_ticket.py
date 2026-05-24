from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ArcvoHelpdeskTicket(models.Model):
    _name = "arcvo.helpdesk.ticket"
    _description = "Arcvo Helpdesk Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, create_date desc, id desc"

    name = fields.Char(required=True, tracking=True)
    ticket_ref = fields.Char(readonly=True, copy=False, index=True)
    description = fields.Html()
    stage_id = fields.Many2one(
        "arcvo.helpdesk.stage",
        required=True,
        ondelete="restrict",
        default=lambda self: self._default_stage_id(),
        tracking=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("blocked", "Blocked"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        related="stage_id.code",
        store=True,
        readonly=True,
    )
    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        default="1",
        required=True,
        tracking=True,
        index=True,
    )
    requester_partner_id = fields.Many2one(
        "res.partner",
        string="Requester",
        default=lambda self: self.env.user.partner_id.id,
        tracking=True,
    )
    assignee_agent_id = fields.Many2one(
        "arcvo.agent",
        string="Assigned Agent",
        ondelete="set null",
        tracking=True,
        index=True,
    )
    task_id = fields.Many2one("project.task", string="Project Task", ondelete="set null", tracking=True)
    assignment_id = fields.Many2one(
        "arcvo.agent.assignment",
        string="Agent Assignment",
        ondelete="set null",
        tracking=True,
    )
    knowledge_article_ids = fields.Many2many(
        "arcvo.knowledge.article",
        "arcvo_knowledge_article_ticket_rel",
        "ticket_id",
        "article_id",
        string="Knowledge Articles",
    )
    comment_ids = fields.One2many("arcvo.helpdesk.comment", "ticket_id", string="Comments")

    opened_at = fields.Datetime(default=fields.Datetime.now, readonly=True, required=True)
    first_response_at = fields.Datetime(readonly=True, tracking=True)
    resolved_at = fields.Datetime(readonly=True, tracking=True)
    closed_at = fields.Datetime(readonly=True, tracking=True)
    sla_deadline = fields.Datetime(tracking=True)
    sla_breached = fields.Boolean(compute="_compute_sla_breached", store=False)
    response_time_hours = fields.Float(compute="_compute_time_metrics", store=False)
    resolution_time_hours = fields.Float(compute="_compute_time_metrics", store=False)

    _sql_constraints = [
        ("arcvo_helpdesk_ticket_ref_unique", "unique(ticket_ref)", "Ticket reference must be unique."),
    ]

    @api.depends("sla_deadline", "state")
    def _compute_sla_breached(self):
        now = fields.Datetime.now()
        for ticket in self:
            ticket.sla_breached = bool(
                ticket.sla_deadline
                and ticket.state not in {"resolved", "closed"}
                and ticket.sla_deadline < now
            )

    @api.depends("opened_at", "first_response_at", "resolved_at")
    def _compute_time_metrics(self):
        for ticket in self:
            ticket.response_time_hours = ticket._hours_between(ticket.opened_at, ticket.first_response_at)
            ticket.resolution_time_hours = ticket._hours_between(ticket.opened_at, ticket.resolved_at)

    @api.constrains("task_id", "assignment_id")
    def _check_assignment_task_consistency(self):
        for ticket in self:
            if (
                ticket.assignment_id
                and ticket.task_id
                and ticket.assignment_id.task_id.id != ticket.task_id.id
            ):
                raise ValidationError(_("Assignment must belong to the selected task."))

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()
        for vals in vals_list:
            if not vals.get("ticket_ref"):
                vals["ticket_ref"] = self.env["ir.sequence"].next_by_code("arcvo.helpdesk.ticket")
            if not vals.get("sla_deadline"):
                priority = vals.get("priority") or "1"
                vals["sla_deadline"] = now + timedelta(hours=self._sla_hours(priority))
        tickets = super().create(vals_list)
        for ticket in tickets:
            ticket.message_post(body=_("Ticket created in Arcvo Helpdesk."))
            ticket._add_comment(_("Ticket created."), comment_type="system")
        return tickets

    def write(self, vals):
        previous_state = {ticket.id: ticket.state for ticket in self}
        stage = False
        if vals.get("stage_id"):
            stage = self.env["arcvo.helpdesk.stage"].browse(vals["stage_id"])

        result = super().write(vals)
        now = fields.Datetime.now()
        for ticket in self:
            current_state = stage.code if stage else ticket.state
            prior_state = previous_state.get(ticket.id)
            update_vals = {}
            if current_state == "resolved" and not ticket.resolved_at:
                update_vals["resolved_at"] = now
            if current_state == "closed" and not ticket.closed_at:
                update_vals["closed_at"] = now
            if current_state == "in_progress" and not ticket.first_response_at:
                update_vals["first_response_at"] = now
            if update_vals:
                super(ArcvoHelpdeskTicket, ticket).write(update_vals)
            if prior_state and prior_state != current_state:
                ticket._add_comment(
                    _("Stage changed from %(old)s to %(new)s.", old=prior_state, new=current_state),
                    comment_type="system",
                )
        return result

    def action_set_in_progress(self):
        stage = self._stage_by_code("in_progress")
        self.write({"stage_id": stage.id})
        self._mark_first_response_if_missing()

    def action_set_blocked(self):
        stage = self._stage_by_code("blocked")
        self.write({"stage_id": stage.id})

    def action_set_resolved(self):
        stage = self._stage_by_code("resolved")
        self.write({"stage_id": stage.id})

    def action_set_closed(self):
        stage = self._stage_by_code("closed")
        self.write({"stage_id": stage.id})

    def action_reopen(self):
        stage = self._stage_by_code("in_progress")
        self.write({"stage_id": stage.id, "closed_at": False})

    def action_record_first_response(self):
        self._mark_first_response_if_missing()

    def action_assign_agent(self, note=None):
        for ticket in self:
            if not ticket.assignee_agent_id:
                raise ValidationError(_("Select an Arcvo agent before assigning the ticket."))
            if ticket.task_id:
                assignment_model = self.env["arcvo.agent.assignment"]
                existing = assignment_model.search(
                    [
                        ("agent_id", "=", ticket.assignee_agent_id.id),
                        ("task_id", "=", ticket.task_id.id),
                        ("status", "in", ["assigned", "in_progress", "blocked"]),
                    ],
                    limit=1,
                )
                if existing:
                    ticket.assignment_id = existing.id
                else:
                    ticket.assignment_id = assignment_model.create(
                        {
                            "agent_id": ticket.assignee_agent_id.id,
                            "task_id": ticket.task_id.id,
                            "status": "assigned",
                            "notes": note or _("Linked from helpdesk ticket %(ref)s", ref=ticket.ticket_ref),
                        }
                    ).id
            ticket._add_comment(
                _("Agent %(agent)s assigned to ticket.", agent=ticket.assignee_agent_id.name),
                comment_type="system",
            )
            ticket.message_post(body=_("Ticket assigned to Arcvo agent %(agent)s.", agent=ticket.assignee_agent_id.name))

    def action_sync_from_assignment(self, status, summary=""):
        status_map = {
            "assigned": "new",
            "in_progress": "in_progress",
            "blocked": "blocked",
            "completed": "resolved",
            "failed": "blocked",
        }
        target_state = status_map.get(status)
        if not target_state:
            return
        stage = self._stage_by_code(target_state)
        for ticket in self:
            ticket.write({"stage_id": stage.id})
            note = summary or _("Assignment status updated to %(status)s.", status=status)
            ticket._add_comment(note, comment_type="system")
            ticket.message_post(body=note)

    @api.model
    def _cron_check_sla(self):
        now = fields.Datetime.now()
        tickets = self.search(
            [
                ("sla_deadline", "!=", False),
                ("sla_deadline", "<", now),
                ("stage_id.code", "not in", ["resolved", "closed"]),
            ]
        )
        for ticket in tickets:
            ticket._add_comment(_("SLA deadline breached."), comment_type="system")
            ticket.message_post(body=_("SLA deadline has been breached for this ticket."))
            ticket._schedule_sla_activity()

    @api.model
    def _default_stage_id(self):
        stage = self._stage_by_code("new", raise_if_missing=False)
        return stage.id if stage else False

    @api.model
    def _stage_by_code(self, code, raise_if_missing=True):
        stage = self.env["arcvo.helpdesk.stage"].search([("code", "=", code)], limit=1)
        if not stage and raise_if_missing:
            raise ValidationError(_("Missing helpdesk stage for state '%s'.") % code)
        return stage

    @api.model
    def _sla_hours(self, priority):
        return {"0": 72, "1": 48, "2": 24, "3": 8}.get(priority, 48)

    def _mark_first_response_if_missing(self):
        now = fields.Datetime.now()
        for ticket in self.filtered(lambda rec: not rec.first_response_at):
            ticket.write({"first_response_at": now})

    def _schedule_sla_activity(self):
        todo_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if not todo_type:
            return
        for ticket in self:
            user_id = ticket.create_uid.id
            if ticket.assignee_agent_id and ticket.assignee_agent_id.write_uid:
                user_id = ticket.assignee_agent_id.write_uid.id
            self.env["mail.activity"].create(
                {
                    "res_model_id": self.env["ir.model"]._get_id("arcvo.helpdesk.ticket"),
                    "res_id": ticket.id,
                    "activity_type_id": todo_type.id,
                    "user_id": user_id,
                    "summary": _("SLA breached"),
                    "note": _("Ticket %(ref)s exceeded its SLA deadline.", ref=ticket.ticket_ref),
                    "date_deadline": fields.Date.today(),
                }
            )

    @api.model
    def _hours_between(self, start, end):
        if not start or not end:
            return 0.0
        delta = end - start
        return round(delta.total_seconds() / 3600.0, 2)

    def _add_comment(self, body, comment_type="note"):
        for ticket in self:
            self.env["arcvo.helpdesk.comment"].create(
                {
                    "ticket_id": ticket.id,
                    "body": body,
                    "comment_type": comment_type,
                }
            )
