"""
Automation Matcher - Auto-assign tasks to agents based on capabilities.

Allows configuring matching rules to automatically assign tasks to the best available
agent based on skills, tags, and other criteria. Prevents over-assignment by respecting
max_concurrent_tasks limits.
"""
import logging
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ArcvoAutomationMatcher(models.Model):
    """Rules for matching tasks to agents based on capabilities."""

    _name = "arcvo.automation.matcher"
    _description = "Automation Matcher"
    _order = "sequence, name"

    name = fields.Char(
        string="Matcher Name",
        required=True,
        help="Descriptive name for this matching rule",
    )
    sequence = fields.Integer(default=10, help="Evaluation order (lower first)")
    
    # Matching criteria
    match_type = fields.Selection(
        [
            ("tag", "Task Tags Match Capabilities"),
            ("keyword", "Task Name/Description Contains"),
            ("project", "Specific Project"),
            ("custom", "Custom Domain Filter"),
        ],
        required=True,
        default="tag",
        string="Match Type",
        help="How to identify matching tasks",
    )
    
    # Tag-based matching
    task_tag_ids = fields.Many2many(
        "project.tags",
        "arcvo_matcher_tag_rel",
        "matcher_id",
        "tag_id",
        string="Task Tags",
        help="Tasks with any of these tags will match (OR logic)",
    )
    
    # Keyword-based matching
    keyword = fields.Char(
        string="Keyword",
        help="Match if keyword appears in task name or description",
    )
    
    # Project-based matching
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        help="Only match tasks in this project",
    )
    
    # Custom domain
    domain = fields.Json(
        string="Domain Filter",
        default="[]",
        help="Custom Odoo domain to match tasks",
    )

    # Agent selection strategy
    assignment_strategy = fields.Selection(
        [
            ("first_available", "First Available"),
            ("least_loaded", "Least Loaded"),
            ("preferred", "Preferred Agent"),
            ("round_robin", "Round Robin"),
        ],
        default="first_available",
        required=True,
        string="Assignment Strategy",
        help="How to choose which agent gets the task",
    )
    
    # Preferred agent (for "preferred" strategy)
    preferred_agent_id = fields.Many2one(
        "hr.employee",
        string="Preferred Agent",
        domain=[("is_agent", "=", True)],
        help="Agent to prefer when using 'Preferred Agent' strategy",
    )
    
    # Fallback strategy if preferred not available
    fallback_strategy = fields.Selection(
        [
            ("none", "Do Nothing"),
            ("least_loaded", "Least Loaded"),
            ("first_available", "First Available"),
            ("escalate", "Escalate to Human"),
        ],
        default="least_loaded",
        string="Fallback Strategy",
        help="What to do if preferred agent unavailable",
    )

    # Capability matching
    require_all_capabilities = fields.Boolean(
        default=False,
        help="If true, agent must have ALL task capabilities. If false, agent needs ANY.",
    )
    
    # Exclusions
    excluded_agent_ids = fields.Many2many(
        "hr.employee",
        "arcvo_matcher_excluded_agent_rel",
        "matcher_id",
        "agent_id",
        string="Excluded Agents",
        help="Never assign to these agents",
    )

    active = fields.Boolean(default=True, help="Enable/disable this matcher")
    notes = fields.Text(help="Internal notes")

    # Statistics
    assignment_count = fields.Integer(
        default=0,
        readonly=True,
        help="Number of successful assignments",
    )
    last_assignment = fields.Datetime(
        readonly=True,
        help="Timestamp of last assignment",
    )
    last_error = fields.Text(
        readonly=True,
        help="Most recent error if assignment failed",
    )

    @api.constrains("match_type")
    def _check_match_type_config(self):
        """Validate that required fields are filled based on match_type."""
        for record in self:
            if record.match_type == "tag" and not record.task_tag_ids:
                raise ValidationError("Tag-based matcher requires at least one tag")
            elif record.match_type == "keyword" and not record.keyword:
                raise ValidationError("Keyword-based matcher requires a keyword")
            elif record.match_type == "project" and not record.project_id:
                raise ValidationError("Project-based matcher requires a project")
            elif record.match_type == "custom" and not record.domain:
                raise ValidationError("Custom matcher requires a domain filter")

    def _match_task(self, task) -> bool:
        """
        Check if this matcher applies to the given task.
        
        Args:
            task: project.task record
            
        Returns:
            bool: True if task matches this rule
        """
        self.ensure_one()

        if not self.active:
            return False

        if self.match_type == "tag":
            # Check if task has any of the matcher tags
            task_tag_ids = task.tag_ids.ids if task.tag_ids else []
            matcher_tag_ids = self.task_tag_ids.ids
            return bool(set(task_tag_ids) & set(matcher_tag_ids))

        elif self.match_type == "keyword":
            # Check if keyword appears in task name or description
            name = (task.name or "").lower()
            desc = (task.description or "").lower()
            keyword = (self.keyword or "").lower()
            return keyword in name or keyword in desc

        elif self.match_type == "project":
            # Check if task belongs to specified project
            return task.project_id.id == self.project_id.id

        elif self.match_type == "custom":
            # Evaluate custom domain
            try:
                matching_tasks = self.env["project.task"].search(
                    [["id", "=", task.id]] + self.domain,
                    limit=1,
                )
                return bool(matching_tasks)
            except Exception as e:
                _logger.error(f"Error evaluating custom domain for matcher {self.name}: {e}")
                return False

        return False

    def _find_best_agent(self, task):
        """
        Find the best available agent for this task using assignment strategy.
        
        Args:
            task: project.task record
            
        Returns:
            hr.employee or None: Best matching agent, or None if no agent available
        """
        self.ensure_one()

        # Get all active agents
        all_agents = self.env["hr.employee"].search(
            [
                ("is_agent", "=", True),
                ("agent_active", "=", True),
                ("id", "not in", self.excluded_agent_ids.ids),
            ]
        )

        if not all_agents:
            _logger.warning(f"Matcher {self.name}: no active agents found")
            return None

        # Filter by capability if task defines them
        if task.arcvo_task_capability_ids:
            capability_ids = task.arcvo_task_capability_ids.ids
            
            if self.require_all_capabilities:
                # Agent must have ALL capabilities
                matching_agents = all_agents.filtered(
                    lambda a: all(
                        cap_id in a.capability_ids.ids
                        for cap_id in capability_ids
                    )
                )
            else:
                # Agent must have ANY capability
                matching_agents = all_agents.filtered(
                    lambda a: any(
                        cap_id in a.capability_ids.ids
                        for cap_id in capability_ids
                    )
                )
        else:
            matching_agents = all_agents

        if not matching_agents:
            _logger.warning(
                f"Matcher {self.name}: no agents with matching capabilities for task {task.name}"
            )
            return None

        # Filter by availability (not overloaded)
        available_agents = self._filter_available_agents(matching_agents)

        if not available_agents:
            _logger.warning(
                f"Matcher {self.name}: no available agents (all overloaded)"
            )
            return None

        # Apply assignment strategy
        if self.assignment_strategy == "first_available":
            return available_agents[0]

        elif self.assignment_strategy == "least_loaded":
            # Sort by current assignment count
            return min(
                available_agents,
                key=lambda a: a.open_assignment_count,
            )

        elif self.assignment_strategy == "preferred":
            if self.preferred_agent_id in available_agents:
                return self.preferred_agent_id
            else:
                # Preferred not available, apply fallback
                return self._apply_fallback_strategy(available_agents)

        elif self.assignment_strategy == "round_robin":
            # Simple round-robin: track index in company settings or use ID
            # For now, use creation date as pseudo-round-robin (cyclic by date)
            if available_agents:
                # Sort by assignment count to distribute fairly
                sorted_agents = sorted(
                    available_agents,
                    key=lambda a: (a.open_assignment_count, a.id)
                )
                return sorted_agents[0]  # Pick least loaded among circle

        return available_agents[0] if available_agents else None

    def _filter_available_agents(self, agents):
        """Filter agents that are not overloaded (< max_concurrent_tasks)."""
        return agents.filtered(
            lambda a: a.open_assignment_count < a.max_concurrent_tasks
        )

    def _apply_fallback_strategy(self, available_agents):
        """Apply fallback strategy if preferred agent not available."""
        if self.fallback_strategy == "none":
            return None
        elif self.fallback_strategy == "least_loaded":
            return min(
                available_agents,
                key=lambda a: a.open_assignment_count,
            ) if available_agents else None
        elif self.fallback_strategy == "first_available":
            return available_agents[0] if available_agents else None
        elif self.fallback_strategy == "escalate":
            # TODO: Escalate to human (manager) - handled in Phase 4
            return None
        return None

    def _log_assignment(self, task, agent, success: bool, message: str):
        """Create audit log entry for this matcher assignment attempt."""
        self.ensure_one()
        
        try:
            self.env["arcvo.automation.log"].sudo().create(
                {
                    "matcher_id": self.id,
                    "task_id": task.id,
                    "agent_id": agent.id if agent else None,
                    "action": "assign",
                    "result": "success" if success else "error",
                    "message": message,
                }
            )
        except Exception as e:
            _logger.error(f"Failed to create matcher log: {e}")

        # Update matcher stats
        if success:
            self.write(
                {
                    "assignment_count": self.assignment_count + 1,
                    "last_assignment": fields.Datetime.now(),
                }
            )
        else:
            self.last_error = message

    def apply_matcher(self, task):
        """
        Try to match and assign this task to an agent.
        
        Called by webhook dispatcher or manually.
        
        Args:
            task: project.task record
            
        Returns:
            bool: True if assignment successful
        """
        self.ensure_one()

        # Check if task matches this rule
        if not self._match_task(task):
            return False

        # Task is already assigned
        if task.arcvo_agent_id:
            _logger.info(f"Matcher {self.name}: task {task.name} already has agent")
            return False

        # Find best agent
        agent = self._find_best_agent(task)
        if not agent:
            self._log_assignment(task, None, False, "No matching agent available")
            return False

        # Assign task to agent
        try:
            task.write({"arcvo_agent_id": agent.id, "arcvo_requires_agent": True})
            self._log_assignment(
                task, agent, True, f"Auto-assigned to {agent.name}"
            )
            _logger.info(f"Matcher {self.name}: assigned task {task.name} to {agent.name}")
            return True
        except Exception as e:
            self._log_assignment(task, agent, False, f"Assignment failed: {e}")
            _logger.exception(f"Matcher {self.name} assignment failed: {e}")
            return False


class ProjectTaskCapability(models.Model):
    """Link required capabilities to project tasks."""

    _name = "project.task.capability"
    _description = "Task Capability Requirement"

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        required=True,
        ondelete="cascade",
    )
    capability_id = fields.Many2one(
        "arcvo.agent.capability",
        string="Required Capability",
        required=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        (
            "project_task_capability_unique",
            "unique(task_id, capability_id)",
            "Capability already assigned to this task",
        ),
    ]


class ProjectTaskExtension(models.Model):
    """Extend project.task with capability requirements."""

    _inherit = "project.task"

    arcvo_task_capability_ids = fields.One2many(
        "project.task.capability",
        "task_id",
        string="Required Capabilities",
        help="Capabilities required for this task (for auto-assignment)",
    )
