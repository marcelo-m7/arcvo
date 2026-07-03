from odoo import fields, models, _
from odoo.exceptions import UserError


class McpModelBatchWizard(models.TransientModel):
    """Wizard for batch operation on MCP Enabled Models."""

    _name = "mcp.model.batch.wizard"
    _description = "MCP Model Batch Operation"

    mcp_model_ids = fields.Many2many(
        "mcp.enabled.model", string="MCP Models", required=True
    )
    change_read = fields.Boolean("Change Read Permission")
    allow_read = fields.Boolean("Allow Read", default=True)

    change_create = fields.Boolean("Change Create Permission")
    allow_create = fields.Boolean("Allow Create")

    change_write = fields.Boolean("Change Update Permission")
    allow_write = fields.Boolean("Allow Update")

    change_unlink = fields.Boolean("Change Delete Permission")
    allow_unlink = fields.Boolean("Allow Delete")

    change_active = fields.Boolean("Change Active Status")
    active = fields.Boolean("Active", default=True)

    def action_apply(self):
        self.ensure_one()
        if self.change_unlink and self.allow_unlink:
            # We don't have a context check here for simplicity in Odoo 19,
            # but usually we could add a confirmation boolean field in the wizard.
            pass

        vals = {}
        if self.change_read:
            vals["allow_read"] = self.allow_read
        if self.change_create:
            vals["allow_create"] = self.allow_create
        if self.change_write:
            vals["allow_write"] = self.allow_write
        if self.change_unlink:
            vals["allow_unlink"] = self.allow_unlink
        if self.change_active:
            vals["active"] = self.active

        if vals:
            self.mcp_model_ids.write(vals)

        return {"type": "ir.actions.act_window_close"}
