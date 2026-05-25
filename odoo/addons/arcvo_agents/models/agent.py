from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html_escape


class ArcvoAgent(models.Model):
    _name = "arcvo.agent"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Arcvo Agent"
    _order = "role, name"

    name = fields.Char(required=True, index=True, tracking=True)
    role = fields.Selection(
        [
            ("ceo", "CEO"),
            ("coo", "Operations"),
            ("cto", "Technology"),
            ("pm", "Project Manager"),
            ("odoo", "Odoo Specialist"),
            ("backend", "Backend"),
            ("hermes", "Hermes Operations"),
            ("frontend", "Hermes Operations (Legacy)"),
            ("data", "Data"),
            ("qa", "Quality"),
            ("docs", "Documentation"),
        ],
        default="odoo",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        [
            ("idle", "Idle"),
            ("busy", "Busy"),
            ("blocked", "Blocked"),
            ("offline", "Offline"),
            ("disabled", "Disabled"),
        ],
        default="idle",
        required=True,
        tracking=True,
    )
    description = fields.Text()
    user_id = fields.Many2one("res.users", string="Odoo User")
    partner_id = fields.Many2one("res.partner", string="Discuss Partner")
    discuss_channel_id = fields.Many2one(
        "discuss.channel",
        string="Discuss Channel",
        readonly=True,
        copy=False,
    )
    capability_ids = fields.Many2many(
        "arcvo.agent.capability",
        "arcvo_agent_arcvo_capability_rel",
        "arcvo_agent_id",
        "capability_id",
        string="Capabilities",
    )
    max_concurrent_tasks = fields.Integer(default=3, required=True)
    active = fields.Boolean(default=True)
    last_heartbeat = fields.Datetime(readonly=True)
    assignment_ids = fields.One2many("arcvo.agent.assignment", "agent_id", string="Assignments")
    open_assignment_count = fields.Integer(compute="_compute_assignment_counts")
    completed_assignment_count = fields.Integer(compute="_compute_assignment_counts")
    total_executions = fields.Integer(default=0, readonly=True)
    successful_executions = fields.Integer(default=0, readonly=True)
    success_rate = fields.Float(compute="_compute_success_rate", store=True)
    is_available = fields.Boolean(compute="_compute_is_available")

    _sql_constraints = [
        ("arcvo_agent_name_unique", "unique(name)", "Agent name must be unique."),
        (
            "arcvo_agent_max_tasks_positive",
            "check(max_concurrent_tasks > 0)",
            "Max concurrent tasks must be greater than zero.",
        ),
    ]

    @api.depends("assignment_ids.status")
    def _compute_assignment_counts(self):
        for agent in self:
            open_assignments = agent.assignment_ids.filtered(
                lambda assignment: assignment.status in {"assigned", "in_progress", "blocked"}
            )
            completed_assignments = agent.assignment_ids.filtered(
                lambda assignment: assignment.status == "completed"
            )
            agent.open_assignment_count = len(open_assignments)
            agent.completed_assignment_count = len(completed_assignments)

    @api.depends("total_executions", "successful_executions")
    def _compute_success_rate(self):
        for agent in self:
            agent.success_rate = (
                (agent.successful_executions / agent.total_executions) * 100
                if agent.total_executions
                else 0.0
            )

    @api.depends("active", "state", "open_assignment_count", "max_concurrent_tasks")
    def _compute_is_available(self):
        for agent in self:
            agent.is_available = (
                agent.active
                and agent.state in {"idle", "busy"}
                and agent.open_assignment_count < agent.max_concurrent_tasks
            )

    @api.constrains("max_concurrent_tasks")
    def _check_max_concurrent_tasks(self):
        for agent in self:
            if agent.max_concurrent_tasks <= 0:
                raise ValidationError("Max concurrent tasks must be greater than zero.")

    def action_heartbeat(self, state=None, message=None):
        vals = {"last_heartbeat": fields.Datetime.now()}
        if state in {"idle", "busy", "blocked", "offline", "disabled"}:
            vals["state"] = state
        self.write(vals)
        for agent in self:
            if message:
                agent._post_agent_chatter(message)
                agent.action_post_discuss_message(body=message)
            self.env["arcvo.agent.audit.log"].sudo().create(
                {
                    "agent_id": agent.id,
                    "action": "heartbeat",
                    "message": message or "Heartbeat recorded.",
                }
            )

    def record_execution(self, success):
        for agent in self:
            vals = {"total_executions": agent.total_executions + 1}
            if success:
                vals["successful_executions"] = agent.successful_executions + 1
            agent.write(vals)

    def action_ensure_discuss_channel(self):
        for agent in self:
            agent._ensure_discuss_channel()
        return True

    def action_open_discuss_channel(self):
        self.ensure_one()
        channel = self._ensure_discuss_channel()
        return {
            "type": "ir.actions.act_window",
            "name": channel.display_name,
            "res_model": "discuss.channel",
            "res_id": channel.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_post_discuss_message(self, body=None, task_id=None, assignment_id=None):
        safe_body = body or _("Arcvo agent message.")
        for agent in self:
            channel = agent._ensure_discuss_channel()
            channel.message_post(
                body=agent._format_message_body(safe_body, task_id=task_id, assignment_id=assignment_id),
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
            agent._post_agent_chatter(safe_body, task_id=task_id, assignment_id=assignment_id)
            agent.env["arcvo.agent.audit.log"].sudo().create(
                {
                    "agent_id": agent.id,
                    "task_id": task_id or False,
                    "assignment_id": assignment_id or False,
                    "action": "message",
                    "message": safe_body,
                    "payload": {"target": "discuss"},
                }
            )
        return True

    def _ensure_discuss_channel(self):
        self.ensure_one()
        if self.discuss_channel_id:
            return self.discuss_channel_id

        channel_model = self.env["discuss.channel"].sudo()
        channel = channel_model.create(
            {
                "name": f"Arcvo Agent: {self.name}",
                "channel_type": "channel",
            }
        )
        self.sudo().write({"discuss_channel_id": channel.id})
        self._post_agent_chatter(_("Discuss channel created for this Arcvo agent."))
        return channel

    def _post_agent_chatter(self, body, task_id=None, assignment_id=None):
        self.ensure_one()
        self.message_post(
            body=self._format_message_body(body, task_id=task_id, assignment_id=assignment_id),
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )

    @staticmethod
    def _format_message_body(body, task_id=None, assignment_id=None):
        details = []
        if task_id:
            details.append(f"Task #{int(task_id)}")
        if assignment_id:
            details.append(f"Assignment #{int(assignment_id)}")
        suffix = f"<br/><small>{html_escape(' | '.join(details))}</small>" if details else ""
        return f"{html_escape(body)}{suffix}"
