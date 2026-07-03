from odoo import fields, models


class McpAgent(models.Model):
    """Model to store MCP Agent configurations."""

    _name = "mcp.agent"
    _description = "MCP Agent"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="Permissions will be evaluated based on this user's ACLs in addition to MCP-specific permissions.",
    )
    api_key_id = fields.Many2one(
        "res.users.apikeys",
        string="API Key",
        domain="[('user_id', '=', user_id)]",
        ondelete="set null",
        tracking=True,
        help="The Odoo API Key used by this agent.",
    )
    notes = fields.Text(help="Internal notes about this agent.")

    def action_view_permissions(self):
        """Open view of all enabled models."""
        self.ensure_one()
        return {
            "name": "MCP Permissions",
            "type": "ir.actions.act_window",
            "res_model": "mcp.enabled.model",
            "view_mode": "list,kanban,form",
            "context": {"search_default_active": 1},
        }
