import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ArcvoKnowledgeArticle(models.Model):
    _name = "arcvo.knowledge.article"
    _description = "Arcvo Knowledge Article"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "write_date desc, id desc"

    name = fields.Char(required=True, tracking=True)
    article_ref = fields.Char(readonly=True, copy=False, index=True)
    slug = fields.Char(readonly=True, index=True)
    summary = fields.Text(tracking=True)
    content_html = fields.Html(string="Content", sanitize=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("review", "In Review"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    category_id = fields.Many2one("arcvo.knowledge.category", ondelete="set null", index=True)
    owner_agent_id = fields.Many2one("arcvo.agent", ondelete="set null", tracking=True)
    task_id = fields.Many2one("project.task", ondelete="set null", tracking=True)
    related_ticket_ids = fields.Many2many(
        "arcvo.helpdesk.ticket",
        "arcvo_knowledge_article_ticket_rel",
        "article_id",
        "ticket_id",
        string="Related Tickets",
    )
    tags = fields.Char()
    version = fields.Integer(default=1, readonly=True)
    published_at = fields.Datetime(readonly=True)
    last_reviewed_at = fields.Datetime(readonly=True)
    is_published = fields.Boolean(compute="_compute_is_published", store=True)

    _sql_constraints = [
        ("arcvo_knowledge_article_ref_unique", "unique(article_ref)", "Article reference must be unique."),
        ("arcvo_knowledge_article_slug_unique", "unique(slug)", "Article slug must be unique."),
    ]

    @api.depends("state")
    def _compute_is_published(self):
        for article in self:
            article.is_published = article.state == "published"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("article_ref"):
                vals["article_ref"] = self.env["ir.sequence"].next_by_code("arcvo.knowledge.article")
            title = vals.get("name") or ""
            vals["slug"] = self._slugify(title)
        articles = super().create(vals_list)
        for article in articles:
            article.message_post(body=_("Article created in Arcvo Knowledge."))
        return articles

    def write(self, vals):
        update_vals = dict(vals)
        if "name" in update_vals and update_vals["name"]:
            update_vals["slug"] = self._slugify(update_vals["name"])
        if "content_html" in update_vals or "summary" in update_vals:
            update_vals["version"] = max(self.mapped("version") or [1]) + 1
        return super().write(update_vals)

    def action_submit_review(self):
        self.write({"state": "review", "last_reviewed_at": fields.Datetime.now()})
        self.message_post(body=_("Article moved to review."))

    def action_publish(self):
        for article in self:
            if not article.content_html:
                raise ValidationError(_("Add content before publishing an article."))
        self.write({"state": "published", "published_at": fields.Datetime.now()})
        self.message_post(body=_("Article published."))

    def action_archive(self):
        self.write({"state": "archived"})
        self.message_post(body=_("Article archived."))

    def action_reset_draft(self):
        self.write({"state": "draft"})
        self.message_post(body=_("Article moved back to draft."))

    @api.model
    def _slugify(self, title):
        base = (title or "").strip().lower()
        base = re.sub(r"[^a-z0-9\s-]", "", base)
        base = re.sub(r"[\s-]+", "-", base).strip("-")
        if not base:
            base = "article"

        slug = base
        seq = 1
        while self.search_count([("slug", "=", slug)]):
            seq += 1
            slug = f"{base}-{seq}"
        return slug
