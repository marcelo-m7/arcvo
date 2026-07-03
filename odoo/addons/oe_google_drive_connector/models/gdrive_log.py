# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GDriveLog(models.Model):
    _name = "gdrive.log"
    _description = "Google Drive Activity Log"
    _order = "create_date desc, id desc"
    _rec_name = "message"

    connection_id = fields.Many2one("gdrive.connection", ondelete="cascade", index=True)
    level = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("error", "Error")],
        default="info", index=True,
    )
    message = fields.Text()

    @api.model
    def _record(self, connection, level, message):
        """Lightweight, always-sudo logger used across the module."""
        return self.sudo().create({
            "connection_id": connection.id if connection else False,
            "level": level,
            "message": message,
        })

    @api.model
    def _cron_trim(self):
        """Drop logs older than the configured retention window."""
        days = int(self.env["ir.config_parameter"].sudo().get_param(
            "oe_google_drive_connector.log_retention_days", 30))
        if days <= 0:
            return
        limit = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        self.sudo().search([("create_date", "<", limit)]).unlink()
