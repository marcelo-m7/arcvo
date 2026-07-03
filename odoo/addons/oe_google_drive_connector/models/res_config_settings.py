# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    gdrive_default_connection_id = fields.Many2one(
        "gdrive.connection", string="Default Drive Connection",
        config_parameter="oe_google_drive_connector.default_connection_id",
        domain=[("state", "=", "connected")],
    )
    gdrive_offload = fields.Boolean(
        string="Offload Binaries to Drive",
        config_parameter="oe_google_drive_connector.offload",
        help="When pushing, convert attachments to Drive links and free Odoo "
             "storage. When off, a copy stays in Odoo.",
    )
    gdrive_log_retention_days = fields.Integer(
        string="Log Retention (days)", default=30,
        config_parameter="oe_google_drive_connector.log_retention_days",
    )
