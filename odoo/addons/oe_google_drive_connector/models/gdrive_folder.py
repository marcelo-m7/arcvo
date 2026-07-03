# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class GDriveFolder(models.Model):
    """Flat pointer linking one Odoo record to its Drive folder.

    Deliberately not a recursive tree: the layout is always
    Root / <Model label> / <Record name>, computed on demand.
    """
    _name = "gdrive.folder"
    _description = "Google Drive Record Folder"
    _order = "id desc"

    connection_id = fields.Many2one(
        "gdrive.connection", required=True, ondelete="cascade", index=True,
    )
    res_model = fields.Char(string="Model", required=True, index=True)
    res_id = fields.Integer(string="Record ID", required=True, index=True)
    model_label = fields.Char(string="Model Folder")
    name = fields.Char(string="Folder Name", required=True)
    drive_folder_id = fields.Char(string="Drive Folder ID", index=True)
    drive_url = fields.Char(string="Drive Link")
    record_name = fields.Char(compute="_compute_record_name")

    _sql_constraints = [
        ("record_unique", "unique(connection_id, res_model, res_id)",
         "A Drive folder already exists for this record and connection."),
    ]

    def _compute_record_name(self):
        for folder in self:
            label = folder.name
            record = folder._record()
            if record and record.exists():
                label = record.display_name
            folder.record_name = label

    def _record(self):
        self.ensure_one()
        if self.res_model and self.res_id and self.res_model in self.env:
            return self.env[self.res_model].browse(self.res_id)
        return self.env["gdrive.connection"].browse()  # empty recordset placeholder

    # ------------------------------------------------------------------ creation
    @api.model
    def _get_or_create(self, connection, record):
        """Return the Drive-backed folder pointer for ``record``.

        Builds the Root / Model / Record hierarchy in Drive if needed and
        returns this model's record with a usable ``drive_folder_id``.
        """
        pointer = self.search([
            ("connection_id", "=", connection.id),
            ("res_model", "=", record._name),
            ("res_id", "=", record.id),
        ], limit=1)
        if pointer and pointer.drive_folder_id:
            return pointer

        session = connection._session()
        root_id = connection.root_folder_id or connection._ensure_root_folder(session)

        model_label = self.env["ir.model"]._get(record._name).name or record._name
        model_folder = session.ensure_folder(model_label, root_id)
        record_label = record.display_name or _("Record %s") % record.id
        record_folder = session.ensure_folder(record_label, model_folder.get("id"))

        vals = {
            "connection_id": connection.id,
            "res_model": record._name,
            "res_id": record.id,
            "model_label": model_label,
            "name": record_label,
            "drive_folder_id": record_folder.get("id"),
            "drive_url": record_folder.get("webViewLink"),
        }
        if pointer:
            pointer.write(vals)
            return pointer
        return self.create(vals)

    def action_open_drive(self):
        self.ensure_one()
        if not self.drive_url:
            return False
        return {"type": "ir.actions.act_url", "url": self.drive_url, "target": "new"}
