from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        session_info = super().session_info()
        if session_info.get("uid") and session_info.get("is_internal_user"):
            session_info["custom_backend_layout"] = (
                self.env["res.config.settings"].sudo().get_custom_backend_layout_config()
            )
        return session_info
