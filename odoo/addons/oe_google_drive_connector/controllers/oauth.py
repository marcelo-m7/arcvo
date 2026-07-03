# -*- coding: utf-8 -*-
import logging

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class GDriveOAuthController(http.Controller):
    """Receives Google's redirect after the user grants (or denies) consent."""

    @http.route("/gdrive/oauth/callback", type="http", auth="user", website=False,
                csrf=False, save_session=False)
    def gdrive_oauth_callback(self, **params):
        state = params.get("state")
        code = params.get("code")
        error = params.get("error")

        connection = request.env["gdrive.connection"].sudo().search(
            [("oauth_state", "=", state)], limit=1) if state else None

        if not connection:
            return self._render_message(
                _("Connection not found"),
                _("The Google authorization could not be matched to a connection. "
                  "Please start again from the connection form."),
                ok=False)

        if error:
            connection._set_error(_("Authorization was denied: %s") % error)
            return self._redirect_to(connection)

        if not code:
            connection._set_error(_("No authorization code was returned by Google."))
            return self._redirect_to(connection)

        try:
            connection._complete_oauth(code)
        except Exception as exc:  # never surface a raw 500 to the user
            _logger.exception("Google Drive OAuth callback failed")
            connection._set_error(_("Connection failed: %s") % exc)
        return self._redirect_to(connection)

    # ------------------------------------------------------------------ helpers
    def _redirect_to(self, connection):
        # Legacy hash URL works across Odoo 17, 18 and 19 (17 has no /odoo/... route).
        url = "/web#id=%s&model=gdrive.connection&view_type=form" % connection.id
        return request.redirect(url)

    def _render_message(self, title, body, ok=True):
        return request.make_response(
            "<html><head><meta charset='utf-8'><title>%s</title></head>"
            "<body style='font-family:sans-serif;padding:40px'>"
            "<h2>%s</h2><p>%s</p></body></html>" % (title, title, body)
        )
