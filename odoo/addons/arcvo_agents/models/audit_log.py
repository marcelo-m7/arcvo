from odoo import fields, models


class ArcvoAgentAuditLog(models.Model):
    _name = "arcvo.agent.audit.log"
    _description = "Arcvo Agent Audit Log"
    _order = "created_at desc, id desc"

    agent_id = fields.Many2one("arcvo.agent", ondelete="set null")
    task_id = fields.Many2one("project.task", ondelete="set null")
    assignment_id = fields.Many2one("arcvo.agent.assignment", ondelete="set null")
    action = fields.Selection(
        [
            ("heartbeat", "Heartbeat"),
            ("message", "Message"),
            ("assigned", "Assigned"),
            ("progress", "Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("blocked", "Blocked"),
            ("system", "System"),
        ],
        default="system",
        required=True,
    )
    message = fields.Text()
    payload = fields.Json()
    created_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
