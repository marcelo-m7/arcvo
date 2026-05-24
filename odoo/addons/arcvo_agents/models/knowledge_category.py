from odoo import api, fields, models


class ArcvoKnowledgeCategory(models.Model):
    _name = "arcvo.knowledge.category"
    _description = "Arcvo Knowledge Category"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "complete_name"

    name = fields.Char(required=True, translate=True, index=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=10, required=True)
    active = fields.Boolean(default=True)
    parent_id = fields.Many2one("arcvo.knowledge.category", ondelete="restrict", index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many("arcvo.knowledge.category", "parent_id", string="Children")
    complete_name = fields.Char(compute="_compute_complete_name", store=True)
    article_ids = fields.One2many("arcvo.knowledge.article", "category_id", string="Articles")
    article_count = fields.Integer(compute="_compute_article_count", store=False)

    _sql_constraints = [
        (
            "arcvo_knowledge_category_name_parent_unique",
            "unique(name, parent_id)",
            "Category name must be unique under the same parent.",
        ),
    ]

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "%s / %s" % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_article_count(self):
        for category in self:
            category.article_count = self.env["arcvo.knowledge.article"].search_count(
                [("category_id", "=", category.id)]
            )
