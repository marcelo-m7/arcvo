"""
eLearning Task Templates - Create automatic review/publish tasks for slides.
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ElearningTaskTemplate(models.Model):
    """Templates for creating tasks when slides are created/updated."""

    _name = "elearning.task.template"
    _description = "eLearning Task Template"
    _order = "sequence ASC"

    # Core
    name = fields.Char(required=True, string="Name", help="Template name")
    sequence = fields.Integer(default=10, help="Execution order")
    active = fields.Boolean(default=True, string="Active")

    # Trigger conditions
    trigger_on = fields.Selection(
        [
            ("create", "Slide Created"),
            ("state_change", "State Change"),
            ("tag_change", "Tag Updated"),
        ],
        required=True,
        default="create",
        help="When to trigger task creation",
    )

    # Filter
    channel_ids = fields.Many2many(
        "slide.channel",
        "elearning_template_channel_rel",
        "template_id",
        "channel_id",
        string="Channels",
        help="Only apply to these channels (empty = all)",
    )
    slide_type_filter = fields.Selection(
        [("all", "All"), ("video", "Video"), ("document", "Document"), ("quiz", "Quiz")],
        default="all",
        help="Filter by slide type",
    )
    min_duration = fields.Integer(
        default=0,
        help="Min video duration (seconds) to trigger",
    )

    # Task configuration
    task_name_template = fields.Char(
        required=True,
        default="Review: {slide_name}",
        help="Task name template (use {slide_name}, {channel_name})",
    )
    task_priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        default="1",
        help="Priority for created tasks",
    )

    # Agent assignment
    assignment_strategy = fields.Selection(
        [
            ("tag", "By Tag"),
            ("keyword", "By Keyword"),
            ("capability", "By Capability"),
            ("random", "Random Agent"),
            ("least_loaded", "Least Loaded"),
        ],
        default="capability",
        help="How to assign task to agent",
    )
    required_capability_ids = fields.Many2many(
        "arcvo.agent.capability",
        "elearning_template_capability_rel",
        "template_id",
        "capability_id",
        string="Required Capabilities",
        help="Agent must have these capabilities",
    )

    # Task details
    task_description_template = fields.Text(
        help="Task description template (Markdown supported)",
    )
    task_tags = fields.Char(
        help="Comma-separated tags to add to task",
    )

    # Automation options
    auto_publish_on_completion = fields.Boolean(
        default=True,
        help="Auto-publish slide when task is completed",
    )
    require_agent_approval = fields.Boolean(
        default=False,
        help="Require agent to manually approve before publishing",
    )
    send_agent_notification = fields.Boolean(
        default=True,
        help="Notify assigned agent via Discuss",
    )

    # Audit
    task_count = fields.Integer(
        compute="_compute_task_count",
        store=False,
        help="Total tasks created from this template",
    )

    @api.depends("name")
    def _compute_task_count(self):
        """Count tasks created from this template."""
        for record in self:
            count = self.env["elearning.task.creation.log"].search_count(
                [("template_id", "=", record.id)]
            )
            record.task_count = count


class ElearningTaskCreationLog(models.Model):
    """Audit trail for tasks created from templates."""

    _name = "elearning.task.creation.log"
    _description = "eLearning Task Creation Log"
    _order = "create_date DESC"

    template_id = fields.Many2one(
        "elearning.task.template",
        required=True,
        ondelete="cascade",
        string="Template",
    )
    slide_id = fields.Many2one(
        "slide.slide",
        required=True,
        ondelete="cascade",
        string="Slide",
    )
    task_id = fields.Many2one(
        "project.task",
        ondelete="set null",
        string="Created Task",
    )
    assigned_agent_id = fields.Many2one(
        "hr.employee",
        ondelete="set null",
        string="Assigned Agent",
    )

    creation_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("created", "Created"),
            ("assigned", "Assigned"),
            ("failed", "Failed"),
        ],
        default="pending",
        string="Status",
    )
    error_message = fields.Text(
        string="Error Message",
        help="If creation failed, why",
    )

    created_by = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        readonly=True,
        string="Created By",
    )
    create_date = fields.Datetime(readonly=True, string="Created")


class SlideChannelElearning(models.Model):
    """Extend slide.channel with agent/automation fields."""

    _inherit = "slide.channel"

    # Agent configuration
    elearning_enabled = fields.Boolean(
        default=False,
        string="Enable Agent Automation",
        help="Auto-create review tasks for new slides",
    )
    elearning_template_id = fields.Many2one(
        "elearning.task.template",
        string="Default Task Template",
        help="Template to use for auto-created tasks",
    )
    elearning_auto_publish = fields.Boolean(
        default=False,
        string="Auto-Publish on Completion",
        help="Automatically publish slides when agent completes review",
    )

    # Stats
    slides_pending_review = fields.Integer(
        compute="_compute_pending_review",
        store=False,
        help="Slides waiting for agent review",
    )
    slides_published_by_agents = fields.Integer(
        compute="_compute_published_by_agents",
        store=False,
        help="Total slides published by agents",
    )

    @api.depends("slide_ids.state")
    def _compute_pending_review(self):
        """Count slides in draft waiting for agent."""
        for record in self:
            count = self.env["slide.slide"].search_count(
                [("channel_id", "=", record.id), ("state", "=", "draft")]
            )
            record.slides_pending_review = count

    @api.depends("slide_ids.publish_date")
    def _compute_published_by_agents(self):
        """Count slides published via agent automation."""
        for record in self:
            # Find slides with arcvo tasks that are completed
            count = self.env["slide.slide"].search_count(
                [
                    ("channel_id", "=", record.id),
                    ("state", "=", "published"),
                ]
            )
            record.slides_published_by_agents = count


class SlideSlideElearning(models.Model):
    """Extend slide.slide with agent/task tracking."""

    _inherit = "slide.slide"

    # Agent task tracking
    elearning_task_ids = fields.One2many(
        "project.task",
        "elearning_slide_id",
        string="Review Tasks",
        help="Tasks created for reviewing/publishing this slide",
    )
    elearning_task_status = fields.Selection(
        [
            ("none", "No Task"),
            ("pending", "Pending Review"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        compute="_compute_task_status",
        store=False,
        help="Status of associated review task",
    )

    # Agent-generated metadata
    agent_generated_tags = fields.Char(
        string="Agent Generated Tags",
        help="Tags created/suggested by agent",
    )
    agent_analysis = fields.Text(
        string="Agent Analysis",
        help="Agent's analysis/summary of slide content",
    )
    agent_recommendations = fields.Text(
        string="Agent Recommendations",
        help="Suggestions from agent (improvements, etc)",
    )
    published_by_agent = fields.Boolean(
        default=False,
        string="Published by Agent",
        help="Whether this was published automatically by agent",
    )
    agent_review_date = fields.Datetime(
        string="Agent Review Date",
        help="When agent completed review",
    )

    @api.depends("elearning_task_ids.state")
    def _compute_task_status(self):
        """Get status of most recent review task."""
        for record in self:
            if not record.elearning_task_ids:
                record.elearning_task_status = "none"
            else:
                latest_task = record.elearning_task_ids.sorted(
                    key=lambda t: t.create_date, reverse=True
                )[0]
                if latest_task.state == "done":
                    record.elearning_task_status = "completed"
                elif latest_task.state == "cancelled":
                    record.elearning_task_status = "failed"
                elif latest_task.state in ["todo", "in_progress"]:
                    record.elearning_task_status = "in_progress"
                else:
                    record.elearning_task_status = "pending"


class ProjectTaskElearning(models.Model):
    """Extend project.task to link back to slides."""

    _inherit = "project.task"

    # eLearning relationship
    elearning_slide_id = fields.Many2one(
        "slide.slide",
        ondelete="set null",
        string="Related Slide",
        help="Slide this task is reviewing",
    )
    elearning_channel_id = fields.Many2one(
        related="elearning_slide_id.channel_id",
        readonly=True,
        string="Channel",
    )
    is_elearning_task = fields.Boolean(
        default=False,
        string="Is eLearning Task",
        help="Whether this is an auto-created slide review task",
    )

    # eLearning task workflow
    agent_approval_pending = fields.Boolean(
        default=False,
        string="Awaiting Agent Approval",
        help="Task completed but awaiting agent approval to publish",
    )

    def action_mark_elearning_complete(self):
        """Mark eLearning task complete and trigger publish."""
        for record in self:
            if not record.is_elearning_task:
                continue

            record.state = "done"

            # Auto-publish if enabled
            if record.elearning_channel_id.elearning_auto_publish:
                if record.elearning_slide_id:
                    record.elearning_slide_id.state = "published"
                    record.elearning_slide_id.published_by_agent = True
                    record.elearning_slide_id.agent_review_date = fields.Datetime.now()
