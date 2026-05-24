from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    arcvo_agent_id = fields.Many2one("arcvo.agent", string="Arcvo Agent")
    arcvo_requires_agent = fields.Boolean(string="Requires Arcvo Agent")
    arcvo_assignment_ids = fields.One2many(
        "arcvo.agent.assignment",
        "task_id",
        string="Arcvo Assignment History",
    )
    arcvo_helpdesk_ticket_ids = fields.One2many(
        "arcvo.helpdesk.ticket",
        "task_id",
        string="Arcvo Helpdesk Tickets",
    )
    arcvo_knowledge_article_ids = fields.One2many(
        "arcvo.knowledge.article",
        "task_id",
        string="Arcvo Knowledge Articles",
    )
