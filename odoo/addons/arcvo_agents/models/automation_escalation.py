"""
Smart Escalation Engine - Detect stuck assignments and escalate to available agents or humans.
"""
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ArcvoAutomationEscalation(models.Model):
    """Rules and audit trail for smart escalation."""

    _name = "arcvo.automation.escalation"
    _description = "Escalation Rules and Audit"
    _order = "sequence ASC"

    # Core
    name = fields.Char(required=True, string="Name", help="Escalation rule name")
    sequence = fields.Integer(default=10, help="Execution order")
    active = fields.Boolean(default=True, string="Active")

    # Trigger conditions
    blocked_threshold_hours = fields.Integer(
        default=4,
        help="Escalate if assignment stuck for N hours",
    )
    max_retries = fields.Integer(
        default=3,
        help="Escalate if assignment failed this many times",
    )
    min_priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        default="1",
        help="Only escalate tasks with this priority or higher",
    )

    # Escalation target
    escalation_type = fields.Selection(
        [
            ("find_agent", "Find Alternative Agent"),
            ("escalate_human", "Escalate to Human"),
            ("both", "Try Agent First, Escalate if Fails"),
        ],
        default="both",
        help="How to handle escalation",
    )

    # Agent selection criteria
    prefer_capability_match = fields.Boolean(
        default=True,
        help="Prefer agents with similar capabilities",
    )
    require_availability = fields.Boolean(
        default=True,
        help="Only escalate to available agents",
    )
    max_attempts_per_agent = fields.Integer(
        default=3,
        help="Max times to try the same task on an agent",
    )

    # Escalation target (if type=escalate_human or both)
    escalate_to_user_id = fields.Many2one(
        "res.users",
        string="Escalate To User",
        help="User to notify for escalation (if human)",
    )
    escalation_group_id = fields.Many2one(
        "res.groups",
        string="Escalation Group",
        help="Group to notify (fallback)",
    )

    # Notify via Discuss
    send_discuss_message = fields.Boolean(
        default=True,
        help="Post escalation notice to Discuss thread",
    )

    # Audit counts
    escalation_count = fields.Integer(
        compute="_compute_escalation_count",
        store=False,
        help="Total times this rule triggered",
    )

    @api.depends("name")
    def _compute_escalation_count(self):
        """Count escalations for this rule."""
        for record in self:
            count = self.env["arcvo.automation.escalation.log"].search_count(
                [("escalation_id", "=", record.id)]
            )
            record.escalation_count = count


class ArcvoAutomationEscalationLog(models.Model):
    """Audit trail for escalation events."""

    _name = "arcvo.automation.escalation.log"
    _description = "Escalation Audit Log"
    _order = "create_date DESC"

    # Core
    escalation_id = fields.Many2one(
        "arcvo.automation.escalation",
        required=True,
        ondelete="cascade",
        string="Escalation Rule",
    )
    assignment_id = fields.Many2one(
        "arcvo.agent.assignment",
        required=True,
        ondelete="cascade",
        string="Assignment",
    )
    task_id = fields.Many2one(
        "project.task",
        related="assignment_id.task_id",
        readonly=True,
        string="Task",
    )

    # Original agent
    original_agent_id = fields.Many2one(
        "hr.employee",
        related="assignment_id.agent_id",
        readonly=True,
        string="Original Agent",
    )

    # Escalation action
    escalation_action = fields.Selection(
        [
            ("found_agent", "Found Alternative Agent"),
            ("escalated_human", "Escalated to Human"),
            ("reassigned", "Reassigned to Same Agent"),
            ("no_action", "No Action Taken"),
        ],
        required=True,
        string="Action Taken",
    )

    # New assignment (if escalation_action=found_agent)
    new_agent_id = fields.Many2one(
        "hr.employee",
        string="New Agent",
        help="Agent this was reassigned to",
    )

    # Escalation to human
    escalated_to_user_id = fields.Many2one(
        "res.users",
        string="Escalated To User",
        help="Human user this was escalated to",
    )

    # Context
    reason = fields.Char(
        string="Reason",
        help="Why escalation was triggered",
    )
    blocked_hours = fields.Float(
        string="Blocked Hours",
        help="How long assignment was stuck",
    )
    attempt_count = fields.Integer(
        default=1,
        help="How many times this agent attempted the task",
    )

    # Discussion message
    discuss_message_id = fields.Many2one(
        "mail.message",
        string="Discuss Message",
        help="Escalation notice posted to Discuss",
    )

    # Status
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
        string="Status",
    )

    created_by = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        readonly=True,
        string="Created By",
    )
    create_date = fields.Datetime(readonly=True, string="Created")


class ArcvoEscalationEngine(models.AbstractModel):
    """Engine to detect and handle escalations."""

    _name = "escalation.engine"
    _description = "Intelligent escalation handler"

    def _cron_check_escalations(self):
        """
        Check for stuck assignments and escalate.
        
        Called from _cron_run_active_agents (every 5 minutes).
        Detects assignments that are:
        - Blocked for > threshold hours
        - Failed multiple times
        - Priority >= min_priority
        """
        _logger.info("Running escalation check")

        escalation_rules = self.env["arcvo.automation.escalation"].search(
            [("active", "=", True)], order="sequence ASC"
        )

        if not escalation_rules:
            _logger.debug("No active escalation rules")
            return

        # Find stuck assignments
        stuck_assignments = self._find_stuck_assignments()
        _logger.debug(f"Found {len(stuck_assignments)} stuck assignments")

        # Apply rules
        for rule in escalation_rules:
            for assignment in stuck_assignments:
                try:
                    self._apply_escalation_rule(rule, assignment)
                except Exception as e:
                    _logger.exception(f"Error applying escalation rule {rule.name}: {e}")

    def _find_stuck_assignments(self):
        """
        Find assignments that are blocked/stuck.
        
        Returns:
            assignment recordset: Assignments meeting escalation criteria
        """
        assignment_model = self.env["arcvo.agent.assignment"]

        # Look for assignments in stuck states
        stuck = assignment_model.search(
            [
                ("status", "in", ["assigned", "in_progress", "blocked"]),
                ("create_date", "<", (datetime.now() - timedelta(hours=4)).isoformat()),
            ]
        )

        return stuck

    def _apply_escalation_rule(self, rule, assignment):
        """
        Apply escalation rule to assignment.
        
        Args:
            rule: arcvo.automation.escalation record
            assignment: arcvo.agent.assignment record
        """
        rule.ensure_one()

        # Check if assignment matches rule criteria
        task = assignment.task_id
        if task.priority:
            priority = int(task.priority)
        else:
            priority = 0

        if priority < int(rule.min_priority):
            return  # Skip low-priority tasks

        # Calculate how long stuck
        blocked_hours = (datetime.now() - assignment.create_date).total_seconds() / 3600

        if blocked_hours < rule.blocked_threshold_hours:
            return  # Not stuck long enough yet

        _logger.warning(
            f"Assignment {assignment.id} (task {task.name}, agent {assignment.agent_id.name}) "
            f"stuck for {blocked_hours:.1f} hours, escalating"
        )

        # Determine escalation action
        if rule.escalation_type == "find_agent":
            self._escalate_find_agent(rule, assignment, blocked_hours)
        elif rule.escalation_type == "escalate_human":
            self._escalate_human(rule, assignment, blocked_hours)
        elif rule.escalation_type == "both":
            # Try to find agent first
            if not self._escalate_find_agent(rule, assignment, blocked_hours):
                # If no agent available, escalate to human
                self._escalate_human(rule, assignment, blocked_hours)

    def _escalate_find_agent(self, rule, assignment, blocked_hours):
        """
        Try to find alternative agent for stuck assignment.
        
        Returns:
            bool: True if successfully reassigned
        """
        task = assignment.task_id
        current_agent = assignment.agent_id

        # Find candidates
        candidates = self._find_alternative_agents(
            rule, task, current_agent
        )

        if not candidates:
            _logger.warning(f"No alternative agents found for escalation")
            return False

        # Pick best candidate
        best_agent = candidates[0]
        _logger.info(f"Reassigning task {task.name} to agent {best_agent.name}")

        # Create new assignment
        try:
            self.env["arcvo.agent.assignment"].create(
                {
                    "task_id": task.id,
                    "agent_id": best_agent.id,
                    "status": "assigned",
                }
            )

            # Log escalation
            self.env["arcvo.automation.escalation.log"].create(
                {
                    "escalation_id": rule.id,
                    "assignment_id": assignment.id,
                    "escalation_action": "found_agent",
                    "new_agent_id": best_agent.id,
                    "reason": f"Blocked for {blocked_hours:.1f} hours",
                    "blocked_hours": blocked_hours,
                }
            )

            # Post notice to Discuss (if enabled)
            if rule.send_discuss_message:
                self._post_escalation_notice(
                    task, current_agent, best_agent, "reassigned"
                )

            return True

        except Exception as e:
            _logger.exception(f"Failed to create new assignment: {e}")
            return False

    def _escalate_human(self, rule, assignment, blocked_hours):
        """
        Escalate stuck assignment to human.
        """
        task = assignment.task_id
        current_agent = assignment.agent_id

        # Determine who to escalate to
        escalate_to = rule.escalate_to_user_id
        if not escalate_to and rule.escalation_group_id:
            # Use first user in group
            users = self.env["res.users"].search(
                [("groups_id", "=", rule.escalation_group_id.id)],
                limit=1,
            )
            escalate_to = users[0] if users else None

        _logger.info(
            f"Escalating task {task.name} to human: "
            f"{escalate_to.name if escalate_to else 'no user specified'}"
        )

        # Create escalation log
        self.env["arcvo.automation.escalation.log"].create(
            {
                "escalation_id": rule.id,
                "assignment_id": assignment.id,
                "escalation_action": "escalated_human",
                "escalated_to_user_id": escalate_to.id if escalate_to else None,
                "reason": f"No agents available (blocked {blocked_hours:.1f}h)",
                "blocked_hours": blocked_hours,
            }
        )

        # Post notice to Discuss
        if rule.send_discuss_message:
            self._post_escalation_notice(
                task, current_agent, escalate_to, "escalated_human"
            )

    def _find_alternative_agents(self, rule, task, current_agent):
        """
        Find alternative agents for reassignment.
        
        Returns:
            list: Agents sorted by priority (best first)
        """
        candidates = []

        # Get all active agents
        agents = self.env["hr.employee"].search(
            [("is_agent", "=", True), ("agent_active", "=", True)]
        )

        # Filter
        for agent in agents:
            if agent.id == current_agent.id:
                continue  # Skip current agent

            # Check availability
            if rule.require_availability:
                if (
                    agent.open_assignment_count
                    >= agent.max_concurrent_tasks
                ):
                    continue  # Agent overloaded

            # Check capability match (if enabled)
            if rule.prefer_capability_match:
                task_capabilities = task.arcvo_task_capability_ids.mapped(
                    "capability_id"
                )
                agent_capabilities = agent.capability_ids

                # If task has capabilities, agent must have at least one match
                if task_capabilities:
                    if not agent_capabilities & task_capabilities:
                        continue  # No capability match

            candidates.append(agent)

        # Sort by availability (least loaded first)
        candidates.sort(
            key=lambda a: a.open_assignment_count
        )

        return candidates

    def _post_escalation_notice(self, task, from_agent, to_agent_or_user, action_type):
        """
        Post escalation notice to Discuss thread.
        
        Args:
            task: project.task
            from_agent: hr.employee (original agent)
            to_agent_or_user: hr.employee or res.users (new recipient)
            action_type: "reassigned" or "escalated_human"
        """
        try:
            if action_type == "reassigned":
                body = f"""🔄 <b>Task Escalation</b>
                
This task has been reassigned to a more available agent.

<b>Original Agent:</b> {from_agent.name}
<b>New Agent:</b> {to_agent_or_user.name}
<b>Task:</b> {task.name}

The new agent will take over immediately."""
            else:  # escalated_human
                to_name = (
                    to_agent_or_user.name
                    if to_agent_or_user
                    else "Escalation Queue"
                )
                body = f"""🚨 <b>Task Escalated</b>
                
This task could not be handled by agents and requires human attention.

<b>Agent:</b> {from_agent.name}
<b>Escalated To:</b> {to_name}
<b>Task:</b> {task.name}

Please review and take action."""

            # Post to task thread
            task.message_post(
                body=body,
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )

        except Exception as e:
            _logger.exception(f"Failed to post escalation notice: {e}")
