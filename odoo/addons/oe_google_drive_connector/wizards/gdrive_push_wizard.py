# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GDrivePushWizard(models.TransientModel):
    _name = "gdrive.push.wizard"
    _description = "Push Attachments to Google Drive"

    connection_id = fields.Many2one(
        "gdrive.connection", string="Connection", required=True,
        domain=[("state", "=", "connected")],
        default=lambda self: self.env["ir.attachment"]._gdrive_default_connection(),
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    syncable_count = fields.Integer(compute="_compute_counts")
    total_count = fields.Integer(compute="_compute_counts")

    @api.depends("attachment_ids")
    def _compute_counts(self):
        for wiz in self:
            wiz.total_count = len(wiz.attachment_ids)
            wiz.syncable_count = len(wiz.attachment_ids._gdrive_syncable())

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids") or []
        if self.env.context.get("active_model") == "ir.attachment" and active_ids:
            res["attachment_ids"] = [(6, 0, active_ids)]
        return res

    def action_push(self):
        self.ensure_one()
        targets = self.attachment_ids._gdrive_syncable()
        if not targets:
            raise UserError(_("None of the selected attachments can be pushed."))
        for att in targets:
            att._gdrive_push(self.connection_id)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Google Drive"),
                "message": _("%s attachment(s) pushed.") % len(targets),
                "type": "success",
                "sticky": False,
            },
        }
