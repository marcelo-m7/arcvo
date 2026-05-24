from odoo import fields, models
from odoo.exceptions import ValidationError


class ArcvoAgentAssignment(models.Model):
    _name = "arcvo.agent.assignment"
    _description = "Arcvo Agent Assignment"
    _order = "assigned_at desc, id desc"

    agent_id = fields.Many2one("arcvo.agent", required=True, ondelete="cascade")
    task_id = fields.Many2one("project.task", required=True, ondelete="cascade")
    status = fields.Selection(
        [
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("blocked", "Blocked"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="assigned",
        required=True,
    )
    assigned_at = fields.Datetime(default=fields.Datetime.now, required=True)
    started_at = fields.Datetime()
    completed_at = fields.Datetime()
    progress = fields.Integer(default=0)
    result = fields.Text()
    error_message = fields.Text()
    notes = fields.Text()

    _sql_constraints = [
        (
            "arcvo_assignment_agent_task_unique",
            "unique(agent_id, task_id)",
            "This agent is already assigned to this task.",
        ),
    ]

    def action_start(self):
        self.write({"status": "in_progress", "started_at": fields.Datetime.now()})

    def action_complete(self):
        self.write({"status": "completed", "progress": 100, "completed_at": fields.Datetime.now()})
        for assignment in self:
            assignment.agent_id.record_execution(True)

    def action_fail(self):
        self.write({"status": "failed", "completed_at": fields.Datetime.now()})
        for assignment in self:
            assignment.agent_id.record_execution(False)

    def action_apply_progress(
        self,
        status="in_progress",
        progress=0,
        result="",
        error_message="",
        payload=None,
    ):
        allowed = {"assigned", "in_progress", "blocked", "completed", "failed", "cancelled"}
        if status not in allowed:
            raise ValidationError(f"Invalid assignment status: {status}")

        progress_value = max(0, min(100, int(progress or 0)))
        now = fields.Datetime.now()

        for assignment in self:
            previous_status = assignment.status
            vals = {
                "status": status,
                "progress": 100 if status == "completed" else progress_value,
                "result": result or assignment.result,
                "error_message": error_message or assignment.error_message,
            }
            if status == "in_progress" and not assignment.started_at:
                vals["started_at"] = now
            if status in {"completed", "failed", "blocked", "cancelled"}:
                vals["completed_at"] = now

            assignment.write(vals)

            if status == "completed" and previous_status != "completed":
                assignment.agent_id.record_execution(True)
            if status == "failed" and previous_status != "failed":
                assignment.agent_id.record_execution(False)

            if status == "completed":
                action = "completed"
            elif status == "failed":
                action = "failed"
            elif status == "blocked":
                action = "blocked"
            else:
                action = "progress"

            assignment.env["arcvo.agent.audit.log"].sudo().create(
                {
                    "agent_id": assignment.agent_id.id,
                    "task_id": assignment.task_id.id,
                    "assignment_id": assignment.id,
                    "action": action,
                    "message": result or error_message or "Assignment updated.",
                    "payload": payload if isinstance(payload, dict) else None,
                }
            )
