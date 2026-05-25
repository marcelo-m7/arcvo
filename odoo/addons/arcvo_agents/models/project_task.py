from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    arcvo_agent_id = fields.Many2one(
        "hr.employee",
        string="Arcvo Agent",
        domain=[("is_agent", "=", True)],
    )
    arcvo_requires_agent = fields.Boolean(string="Requires Arcvo Agent")
    arcvo_assignment_ids = fields.One2many(
        "arcvo.agent.assignment",
        "task_id",
        string="Arcvo Assignment History",
    )
