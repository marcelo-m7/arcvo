from odoo import fields, models


class ArcvoHelpdeskStage(models.Model):
    _name = "arcvo.helpdesk.stage"
    _description = "Arcvo Helpdesk Stage"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("blocked", "Blocked"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        required=True,
        default="new",
        index=True,
    )
    sequence = fields.Integer(default=10, required=True)
    fold = fields.Boolean(default=False)
    is_closed = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)

    _sql_constraints = [
        ("arcvo_helpdesk_stage_name_unique", "unique(name)", "Stage name must be unique."),
        ("arcvo_helpdesk_stage_code_sequence_unique", "unique(code, sequence)", "Stage ordering conflict."),
    ]
