# -*- coding: utf-8 -*-
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..services import drive_api


class GDriveConnection(models.Model):
    _name = "gdrive.connection"
    _description = "Google Drive Connection"
    _order = "sequence, id"

    name = fields.Char(required=True, help="Label shown to users, e.g. 'Company Drive'.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    auth_method = fields.Selection(
        [("oauth", "OAuth (user consent)"),
         ("service_account", "Service Account")],
        string="Authentication", default="oauth", required=True,
    )

    # -- OAuth credentials (secrets are manager-only at field level) ----------
    client_id = fields.Char(string="OAuth Client ID")
    client_secret = fields.Char(
        string="OAuth Client Secret",
        groups="oe_google_drive_connector.group_gdrive_manager",
    )
    redirect_uri = fields.Char(
        string="Authorized Redirect URI", compute="_compute_redirect_uri",
        help="Register this exact URL in the Google Cloud console under your "
             "OAuth client's authorized redirect URIs.",
    )
    refresh_token = fields.Char(
        groups="oe_google_drive_connector.group_gdrive_manager",
    )
    access_token = fields.Char(
        groups="oe_google_drive_connector.group_gdrive_manager",
    )
    token_expiry = fields.Datetime(
        groups="oe_google_drive_connector.group_gdrive_manager",
    )
    oauth_state = fields.Char(
        copy=False, groups="oe_google_drive_connector.group_gdrive_manager",
    )

    # -- Service account credentials ------------------------------------------
    service_account_key = fields.Text(
        string="Service Account Key (JSON)",
        groups="oe_google_drive_connector.group_gdrive_manager",
        help="Paste the full JSON key file of the service account.",
    )
    impersonate_email = fields.Char(
        string="Impersonate User",
        help="Optional. For Workspace domain-wide delegation, the user whose "
             "Drive the service account should act on behalf of.",
    )

    # -- Target location ------------------------------------------------------
    root_folder_name = fields.Char(default="Odoo", required=True)
    root_folder_id = fields.Char(string="Root Folder ID", readonly=True, copy=False)
    root_folder_url = fields.Char(string="Root Folder Link", readonly=True, copy=False)
    use_shared_drive = fields.Boolean(string="Use a Shared Drive")
    shared_drive_id = fields.Char(string="Shared Drive ID")
    shared_drive_name = fields.Char(string="Shared Drive Name")

    # -- State ----------------------------------------------------------------
    state = fields.Selection(
        [("draft", "Not Connected"), ("connected", "Connected"), ("error", "Error")],
        default="draft", readonly=True, copy=False,
    )
    status_message = fields.Text(readonly=True, copy=False)
    last_connected = fields.Datetime(readonly=True, copy=False)
    folder_count = fields.Integer(compute="_compute_folder_count")

    _sql_constraints = [
        ("name_unique", "unique(name, company_id)",
         "A connection with this name already exists."),
    ]

    # ------------------------------------------------------------------ compute
    @api.depends_context("uid")
    def _compute_redirect_uri(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for conn in self:
            conn.redirect_uri = "%s/gdrive/oauth/callback" % (base or "")

    def _compute_folder_count(self):
        data = self.env["gdrive.folder"]._read_group(
            [("connection_id", "in", self.ids)], ["connection_id"], ["__count"]
        )
        counts = {conn.id: count for conn, count in data}
        for conn in self:
            conn.folder_count = counts.get(conn.id, 0)

    # ------------------------------------------------------------------- helpers
    def _session(self):
        """Return a DriveSession built with this connection's credentials."""
        self.ensure_one()
        if not drive_api.libraries_available():
            raise UserError(_(drive_api.missing_library_message()))
        # sudo so non-manager users can run pushes without reading the secrets.
        return drive_api.DriveSession(self.sudo())

    def _set_error(self, message):
        self.sudo().write({"state": "error", "status_message": message})
        self.env["gdrive.log"]._record(self, "error", message)

    def _ensure_root_folder(self, session=None):
        """Create (once) and return the Drive id of this connection's root folder."""
        self.ensure_one()
        session = session or self._session()
        folder = session.ensure_root(self.root_folder_name)
        self.sudo().write({
            "root_folder_id": folder.get("id"),
            "root_folder_url": folder.get("webViewLink"),
        })
        return folder.get("id")

    def _folder_for_record(self, record):
        """Return the gdrive.folder pointer for ``record``, creating it on demand."""
        self.ensure_one()
        return self.env["gdrive.folder"]._get_or_create(self, record)

    # -------------------------------------------------------------------- actions
    def action_connect(self):
        self.ensure_one()
        if self.auth_method == "service_account":
            return self.action_test_connection()
        if not self.client_id or not self.client_secret:
            raise UserError(_("Please fill in the OAuth Client ID and Secret first."))
        state = uuid.uuid4().hex
        self.sudo().write({"oauth_state": state})
        try:
            url = drive_api.build_consent_url(
                self.client_id, self.sudo().client_secret, self.redirect_uri, state
            )
        except drive_api.DriveError as exc:
            raise UserError(str(exc))
        return {"type": "ir.actions.act_url", "url": url, "target": "self"}

    def _complete_oauth(self, code):
        """Called by the OAuth callback controller after user consent."""
        self.ensure_one()
        try:
            tokens = drive_api.exchange_consent_code(
                self.client_id, self.sudo().client_secret, self.redirect_uri, code
            )
        except drive_api.DriveError as exc:
            self._set_error(str(exc))
            return False
        if not tokens.get("refresh_token"):
            # Google only returns a refresh token on first consent; force re-consent.
            self._set_error(_(
                "Google did not return a refresh token. Remove this app from your "
                "Google account permissions and connect again."
            ))
            return False
        self.sudo().write({
            "refresh_token": tokens["refresh_token"],
            "access_token": tokens.get("access_token"),
            "token_expiry": tokens.get("token_expiry"),
            "oauth_state": False,
        })
        return self.action_test_connection()

    def action_test_connection(self):
        self.ensure_one()
        try:
            session = self._session()
            info = session.about()
            self._ensure_root_folder(session=session)
        except (drive_api.DriveError, UserError) as exc:
            self._set_error(str(exc))
            return self._reload_action()
        user = (info or {}).get("user", {})
        self.sudo().write({
            "state": "connected",
            "status_message": _("Connected as %s.") % (
                user.get("emailAddress") or user.get("displayName") or _("Drive user")
            ),
            "last_connected": fields.Datetime.now(),
        })
        self.env["gdrive.log"]._record(self, "info", _("Connection verified."))
        return self._reload_action()

    def action_reset(self):
        self.ensure_one()
        self.sudo().write({
            "state": "draft", "status_message": False,
            "refresh_token": False, "access_token": False, "token_expiry": False,
            "root_folder_id": False, "root_folder_url": False,
        })
        return self._reload_action()

    def action_open_root_folder(self):
        self.ensure_one()
        if not self.root_folder_url:
            raise UserError(_("This connection has no root folder yet."))
        return {"type": "ir.actions.act_url", "url": self.root_folder_url, "target": "new"}

    def action_view_folders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Drive Folders"),
            "res_model": "gdrive.folder",
            "view_mode": "list,form",
            "domain": [("connection_id", "=", self.id)],
            "context": {"default_connection_id": self.id},
        }

    def _reload_action(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }
