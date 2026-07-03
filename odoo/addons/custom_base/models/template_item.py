from odoo import fields, models


class CustomTemplateItem(models.Model):
    _name = "custom.template.item"
    _description = "Template Item"

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
