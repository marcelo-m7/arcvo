from odoo import fields, models


class ArcvoAgentCapability(models.Model):
    _name = "arcvo.agent.capability"
    _description = "Arcvo Agent Capability"
    _order = "category, name"

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    category = fields.Selection(
        [
            ("strategy", "Strategy"),
            ("operations", "Operations"),
            ("odoo", "Odoo"),
            ("backend", "Backend"),
            ("hermes", "Hermes Operations"),
            ("frontend", "Hermes Operations (Legacy)"),
            ("data", "Data"),
            ("qa", "Quality"),
            ("docs", "Documentation"),
        ],
        default="operations",
        required=True,
    )
    active = fields.Boolean(default=True)
    agent_ids = fields.Many2many(
        "arcvo.agent",
        "arcvo_agent_capability_rel",
        "capability_id",
        "agent_id",
        string="Agents",
    )

    _sql_constraints = [
        ("arcvo_capability_name_unique", "unique(name)", "Capability name must be unique."),
    ]
