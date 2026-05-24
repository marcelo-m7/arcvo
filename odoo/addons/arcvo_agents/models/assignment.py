from odoo import fields, models


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
