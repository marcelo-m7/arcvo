"""
Slide Management Engine - Process slides and create auto-review tasks for agents.
"""
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SlideManagementEngine(models.AbstractModel):
    """Process slides and dispatch to agents."""

    _name = "slide.management.engine"
    _description = "eLearning Slide Management"

    def _process_slide_created(self, slide):
        """
        Process a newly created slide.
        
        Creates review task if enabled for channel.
        """
        _logger.info(f"Processing new slide: {slide.name} in {slide.channel_id.name}")
        
        # Check if channel has automation enabled
        if not slide.channel_id.elearning_enabled:
            _logger.debug(f"eLearning disabled for channel {slide.channel_id.name}")
            return
        
        # Get template
        template = slide.channel_id.elearning_template_id
        if not template or not template.active:
            _logger.warning(f"No active template for channel {slide.channel_id.name}")
            return
        
        # Check template triggers
        if template.trigger_on != "create":
            return
        
        # Create task
        try:
            self._create_review_task(template, slide)
        except Exception as e:
            _logger.exception(f"Failed to create review task for slide {slide.name}: {e}")

    def _process_slide_updated(self, slide):
        """
        Process slide updates (state change, etc).
        
        May create new review tasks if conditions met.
        """
        _logger.debug(f"Processing slide update: {slide.name}")
        
        # Check templates with state_change trigger
        templates = self.env["elearning.task.template"].search(
            [
                ("active", "=", True),
                ("trigger_on", "=", "state_change"),
            ]
        )
        
        for template in templates:
            try:
                if self._should_apply_template(template, slide):
                    self._create_review_task(template, slide)
            except Exception as e:
                _logger.exception(f"Error applying template {template.name}: {e}")

    def _should_apply_template(self, template, slide):
        """
        Check if template should apply to this slide.
        
        Returns:
            bool: True if template should be applied
        """
        # Check channel filter
        if template.channel_ids and slide.channel_id not in template.channel_ids:
            return False
        
        # Check slide type
        if template.slide_type_filter != "all":
            slide_type_map = {
                "video": "video",
                "document": "document",
                "quiz": "quiz",
            }
            if slide.slide_type != slide_type_map.get(template.slide_type_filter):
                return False
        
        # Check video duration
        if template.min_duration > 0 and slide.slide_type == "video":
            if slide.duration_in_seconds < template.min_duration:
                return False
        
        return True

    def _create_review_task(self, template, slide):
        """
        Create a review task from template.
        
        Args:
            template: elearning.task.template
            slide: slide.slide
        
        Returns:
            project.task or None
        """
        template.ensure_one()
        slide.ensure_one()
        
        _logger.info(
            f"Creating review task from template {template.name} for slide {slide.name}"
        )
        
        # Check if task already exists
        existing = self.env["elearning.task.creation.log"].search(
            [
                ("template_id", "=", template.id),
                ("slide_id", "=", slide.id),
                ("creation_status", "in", ["created", "assigned"]),
            ]
        )
        if existing:
            _logger.debug(f"Task already exists for slide {slide.name}")
            return existing[0].task_id
        
        # Build task name
        task_name = template.task_name_template.format(
            slide_name=slide.name,
            channel_name=slide.channel_id.name,
        )
        
        # Build task description
        task_description = template.task_description_template or ""
        if task_description:
            task_description = task_description.format(
                slide_name=slide.name,
                slide_url=slide.url,
                channel_name=slide.channel_id.name,
            )
        else:
            task_description = f"""Review and approve slide: **{slide.name}**

**Channel:** {slide.channel_id.name}

**Tasks:**
1. Watch/review the slide content
2. Verify accuracy and completeness
3. Generate appropriate tags
4. Check SEO and formatting
5. Approve for publication

**Slide Details:**
- Type: {slide.slide_type}
- Duration: {slide.duration_in_seconds}s
- URL: {slide.url}"""
        
        # Find project (eLearning review project)
        review_project = self._get_or_create_elearning_project()
        
        # Create task
        task_vals = {
            "name": task_name,
            "description": task_description,
            "project_id": review_project.id,
            "state": "todo",
            "priority_custom": template.task_priority,
            "elearning_slide_id": slide.id,
            "is_elearning_task": True,
        }
        
        # Assign task to agent
        assigned_agent = self._assign_agent(template, slide)
        if assigned_agent:
            task_vals["arcvo_agent_id"] = assigned_agent.id
        
        # Create task
        try:
            task = self.env["project.task"].create(task_vals)
            _logger.info(f"Created task {task.id}: {task_name}")
            
            # Add tags
            if template.task_tags:
                tags = [t.strip() for t in template.task_tags.split(",")]
                for tag_name in tags:
                    tag = self.env["project.tags"].search(
                        [("name", "=", tag_name)], limit=1
                    )
                    if not tag:
                        tag = self.env["project.tags"].create({"name": tag_name})
                    task.tag_ids = [(4, tag.id)]
            
            # Create log
            self.env["elearning.task.creation.log"].create(
                {
                    "template_id": template.id,
                    "slide_id": slide.id,
                    "task_id": task.id,
                    "assigned_agent_id": assigned_agent.id if assigned_agent else None,
                    "creation_status": "assigned" if assigned_agent else "created",
                }
            )
            
            # Notify agent
            if assigned_agent and template.send_agent_notification:
                self._notify_agent(task, assigned_agent)
            
            return task
        
        except Exception as e:
            _logger.exception(f"Failed to create task: {e}")
            self.env["elearning.task.creation.log"].create(
                {
                    "template_id": template.id,
                    "slide_id": slide.id,
                    "creation_status": "failed",
                    "error_message": str(e),
                }
            )
            return None

    def _assign_agent(self, template, slide):
        """
        Find best agent to assign task.
        
        Returns:
            hr.employee or None
        """
        if template.assignment_strategy == "random":
            agents = self.env["hr.employee"].search(
                [("is_agent", "=", True), ("agent_active", "=", True)]
            )
            return agents[0] if agents else None
        
        elif template.assignment_strategy == "least_loaded":
            agents = self.env["hr.employee"].search(
                [
                    ("is_agent", "=", True),
                    ("agent_active", "=", True),
                    ("open_assignment_count", "<", fields.F("max_concurrent_tasks")),
                ],
                order="open_assignment_count ASC",
                limit=1,
            )
            return agents[0] if agents else None
        
        elif template.assignment_strategy == "capability":
            if not template.required_capability_ids:
                return self._assign_agent(
                    template.write({"assignment_strategy": "least_loaded"}), slide
                )
            
            agents = self.env["hr.employee"].search(
                [
                    ("is_agent", "=", True),
                    ("agent_active", "=", True),
                    (
                        "capability_ids",
                        "in",
                        template.required_capability_ids.ids,
                    ),
                    ("open_assignment_count", "<", fields.F("max_concurrent_tasks")),
                ],
                order="open_assignment_count ASC",
                limit=1,
            )
            return agents[0] if agents else None
        
        return None

    def _get_or_create_elearning_project(self):
        """
        Get or create the central eLearning review project.
        
        Returns:
            project.project
        """
        project = self.env["project.project"].search(
            [("name", "=", "eLearning Reviews")],
            limit=1,
        )
        
        if not project:
            project = self.env["project.project"].create(
                {
                    "name": "eLearning Reviews",
                    "description": "Auto-generated review tasks for eLearning slides",
                }
            )
            _logger.info(f"Created eLearning project {project.id}")
        
        return project

    def _notify_agent(self, task, agent):
        """
        Notify agent of new review task via Discuss.
        
        Args:
            task: project.task
            agent: hr.employee
        """
        try:
            message = f"""🎓 <b>New eLearning Review Task</b>

You have been assigned a new slide review task.

**Task:** {task.name}
**Priority:** {task.priority_custom}
**Link:** {task.get_access_token()}

Please review the slide and approve for publication when ready."""
            
            task.message_post(
                body=message,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                author_id=agent.user_id.partner_id.id if agent.user_id else None,
            )
        except Exception as e:
            _logger.warning(f"Failed to notify agent {agent.name}: {e}")


class SlideSlideHandler(models.Model):
    """Signal handler for slide creation/updates."""

    _inherit = "slide.slide"

    @api.model_create_multi
    def create(self, vals_list):
        """Hook: Process new slides."""
        slides = super().create(vals_list)
        
        for slide in slides:
            try:
                engine = self.env["slide.management.engine"]
                engine._process_slide_created(slide)
            except Exception as e:
                _logger.warning(f"Error processing slide {slide.name}: {e}")
        
        return slides

    def write(self, vals):
        """Hook: Process slide updates."""
        result = super().write(vals)
        
        try:
            engine = self.env["slide.management.engine"]
            for slide in self:
                engine._process_slide_updated(slide)
        except Exception as e:
            _logger.warning(f"Error processing slide update: {e}")
        
        return result
