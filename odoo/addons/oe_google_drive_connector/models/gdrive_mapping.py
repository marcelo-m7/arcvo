# -*- coding: utf-8 -*-
import ast
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Models that must never be auto-synced (system / internal plumbing).
EXCLUDED_MODELS = {
    "ir.attachment", "gdrive.connection", "gdrive.folder", "gdrive.mapping",
    "gdrive.log", "mail.message", "ir.cron", "ir.logging",
}


class GDriveMapping(models.Model):
    """Optional rule: 'attachments of records of model X auto-push to Drive'."""
    _name = "gdrive.mapping"
    _description = "Google Drive Auto-Push Rule"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    connection_id = fields.Many2one(
        "gdrive.connection", required=True, ondelete="cascade",
        domain=[("state", "=", "connected")],
    )
    model_id = fields.Many2one(
        "ir.model", string="Odoo Model", required=True, ondelete="cascade",
    )
    model_name = fields.Char(related="model_id.model", store=True, index=True)
    domain = fields.Char(
        default="[]",
        help="Optional filter on the records whose attachments should be pushed.",
    )
    auto_push = fields.Boolean(
        string="Auto Push", default=True,
        help="Include this rule when the scheduled push job runs.",
    )

    @api.constrains("model_id")
    def _check_model(self):
        for rule in self:
            if rule.model_name in EXCLUDED_MODELS:
                raise ValidationError(_(
                    "The model '%s' cannot be used for Drive auto-push."
                ) % rule.model_name)

    @api.constrains("domain")
    def _check_domain(self):
        for rule in self:
            try:
                ast.literal_eval(rule.domain or "[]")
            except (ValueError, SyntaxError):
                raise ValidationError(_("The domain of rule '%s' is not valid.") % rule.name)

    def _eval_domain(self):
        self.ensure_one()
        try:
            return ast.literal_eval(self.domain or "[]")
        except (ValueError, SyntaxError):
            return []

    # -------------------------------------------------------------------- cron
    @api.model
    def _cron_push_attachments(self, limit=200):
        """Scheduled one-way push: Odoo -> Drive for all enabled rules."""
        rules = self.search([("auto_push", "=", True),
                             ("connection_id.state", "=", "connected")])
        Attachment = self.env["ir.attachment"]
        pushed = 0
        for rule in rules:
            model = rule.model_name
            if model not in self.env:
                continue
            records = self.env[model].search(rule._eval_domain())
            if not records:
                continue
            attachments = Attachment.search([
                ("res_model", "=", model),
                ("res_id", "in", records.ids),
                ("gdrive_file_id", "=", False),
                ("gdrive_state", "!=", "error"),
            ], limit=limit - pushed)
            attachments = attachments._gdrive_syncable()
            for attachment in attachments:
                try:
                    attachment._gdrive_push(rule.connection_id)
                    pushed += 1
                    # Commit per file so a later failure does not lose progress.
                    self.env.cr.commit()
                except Exception as exc:  # noqa: BLE001 - log and continue
                    self.env.cr.rollback()
                    attachment.sudo().write({"gdrive_state": "error"})
                    rule.connection_id.env["gdrive.log"]._record(
                        rule.connection_id, "error",
                        _("Auto-push failed for attachment %s: %s") % (attachment.id, exc),
                    )
                    self.env.cr.commit()
                if pushed >= limit:
                    return pushed
        return pushed
