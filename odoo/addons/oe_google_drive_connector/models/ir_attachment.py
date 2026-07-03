# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..services import drive_api

# Web-asset mimetypes that should never be treated as user documents.
SKIP_MIMETYPES = ("text/css", "text/scss", "text/javascript", "application/javascript")


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    gdrive_connection_id = fields.Many2one(
        "gdrive.connection", string="Drive Connection", copy=False, index=True,
    )
    gdrive_file_id = fields.Char(string="Drive File ID", copy=False, index=True)
    gdrive_url = fields.Char(string="Drive Link", copy=False)
    gdrive_state = fields.Selection(
        [("local", "Local Only"), ("linked", "On Drive"), ("error", "Error")],
        default="local", copy=False, index=True,
    )
    gdrive_offloaded = fields.Boolean(
        string="Offloaded to Drive", copy=False,
        help="The binary lives only on Google Drive; Odoo keeps a link.",
    )

    # ------------------------------------------------------------------ helpers
    def _gdrive_syncable(self):
        """Filter out attachments that should not be pushed to Drive."""
        result = self.browse()
        for att in self:
            if att.gdrive_file_id:
                continue
            if not att.res_model or att.res_model.startswith("gdrive."):
                continue
            if att.res_field:  # binary field storage, not a user document
                continue
            if (att.mimetype or "") in SKIP_MIMETYPES:
                continue
            result |= att
        return result

    def _gdrive_default_connection(self):
        param = self.env["ir.config_parameter"].sudo().get_param(
            "oe_google_drive_connector.default_connection_id")
        if param:
            conn = self.env["gdrive.connection"].browse(int(param)).exists()
            if conn and conn.state == "connected":
                return conn
        return self.env["gdrive.connection"].search(
            [("state", "=", "connected")], limit=1)

    def _gdrive_should_offload(self):
        return self.env["ir.config_parameter"].sudo().get_param(
            "oe_google_drive_connector.offload", "False") == "True"

    # ------------------------------------------------------------------- push
    def _gdrive_push(self, connection):
        """Upload one attachment's content to the record's Drive folder."""
        self.ensure_one()
        record = self.env[self.res_model].browse(self.res_id)
        if not record.exists():
            raise UserError(_("The record linked to this attachment no longer exists."))

        folder = connection._folder_for_record(record)
        session = connection._session()
        content = self.raw or b""
        uploaded = session.upload(
            folder.drive_folder_id, self.name, self.mimetype, content)

        vals = {
            "gdrive_connection_id": connection.id,
            "gdrive_file_id": uploaded.get("id"),
            "gdrive_url": uploaded.get("webViewLink"),
            "gdrive_state": "linked",
        }
        if self._gdrive_should_offload():
            # Convert to a pure link and release the stored binary.
            vals.update({
                "type": "url",
                "url": uploaded.get("webViewLink"),
                "raw": False,
                "gdrive_offloaded": True,
            })
        self.write(vals)
        self.env["gdrive.log"]._record(
            connection, "info", _("Pushed '%s' to Drive.") % self.name)
        return True

    def action_gdrive_push(self):
        """User action: push the selected attachments using the default connection."""
        if not drive_api.libraries_available():
            raise UserError(_(drive_api.missing_library_message()))
        connection = self._gdrive_default_connection()
        if not connection:
            raise UserError(_(
                "No connected Google Drive connection found. Configure one under "
                "Google Drive > Connections."))
        targets = self._gdrive_syncable()
        if not targets:
            raise UserError(_("None of the selected attachments can be pushed to Drive."))
        try:
            for att in targets:
                att._gdrive_push(connection)
        except drive_api.DriveError as exc:
            # Surface Google-side failures as a clean dialog, not a server error.
            raise UserError(str(exc))
        return self._gdrive_notify(
            _("%s attachment(s) uploaded to Google Drive.") % len(targets))

    def action_gdrive_fetch_back(self):
        """Restore an offloaded attachment's binary from Drive into Odoo."""
        count = 0
        try:
            for att in self:
                if not att.gdrive_file_id or not att.gdrive_connection_id:
                    continue
                session = att.gdrive_connection_id._session()
                content = session.download(att.gdrive_file_id)
                att.write({
                    "type": "binary",
                    "raw": content,
                    "url": False,
                    "gdrive_offloaded": False,
                })
                count += 1
        except drive_api.DriveError as exc:
            raise UserError(str(exc))
        return self._gdrive_notify(_("%s file(s) fetched back from Drive.") % count)

    def _gdrive_notify(self, message, ntype="success"):
        """Show a toast and softly refresh the view so badges/buttons update.

        Returned to form/kanban object buttons. The chatter JS calls these
        methods over RPC and shows its own toast, ignoring this action.
        """
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Google Drive"),
                "message": message,
                "type": ntype,
                "sticky": False,
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def action_gdrive_open(self):
        self.ensure_one()
        if not self.gdrive_url:
            raise UserError(_("This attachment is not linked to Google Drive."))
        return {"type": "ir.actions.act_url", "url": self.gdrive_url, "target": "new"}

    # ------------------------------------------------------------------- unlink
    def unlink(self):
        """Best-effort cleanup of the matching Drive file before deletion."""
        to_clean = [
            (att.gdrive_connection_id.id, att.gdrive_file_id)
            for att in self
            if att.gdrive_file_id and att.gdrive_connection_id
        ]
        res = super().unlink()
        Connection = self.env["gdrive.connection"]
        for conn_id, file_id in to_clean:
            connection = Connection.browse(conn_id).exists()
            if not connection:
                continue
            try:
                connection._session().delete(file_id)
            except Exception as exc:  # noqa: BLE001 - deletion is best effort
                self.env["gdrive.log"]._record(
                    connection, "warning",
                    _("Could not delete Drive file %s: %s") % (file_id, exc))
        return res
