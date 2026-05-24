from odoo import fields, models


class ArcvoHelpdeskComment(models.Model):
    _name = "arcvo.helpdesk.comment"
    _description = "Arcvo Helpdesk Comment"
    _order = "created_at desc, id desc"

    ticket_id = fields.Many2one("arcvo.helpdesk.ticket", required=True, ondelete="cascade", index=True)
    author_id = fields.Many2one("res.users", default=lambda self: self.env.user.id, readonly=True)
    comment_type = fields.Selection(
        [
            ("note", "Note"),
            ("public", "Public Reply"),
            ("internal", "Internal"),
            ("system", "System"),
        ],
        default="note",
        required=True,
        index=True,
    )
    body = fields.Text(required=True)
    created_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
