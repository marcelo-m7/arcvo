"""
Automation Webhooks - Event-driven triggers for agent execution.

Allows registration of event triggers (task creation, state change) that
automatically dispatch agent work without waiting for cron.
"""
import logging
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ArcvoAutomationWebhook(models.Model):
    """Event trigger configuration for automatic agent execution."""

    _name = "arcvo.automation.webhook"
    _description = "Automation Webhook"
    _order = "sequence, name"

    name = fields.Char(
        string="Webhook Name",
        required=True,
        help="Descriptive name for this automation rule",
    )
    sequence = fields.Integer(default=10, help="Execution order")
    trigger = fields.Selection(
        [
            ("task.created", "Task Created"),
            ("task.state_change", "Task State Changed"),
            ("task.write", "Task Updated"),
        ],
        required=True,
        string="Trigger Event",
        help="Which event should fire this webhook",
    )
    domain = fields.Json(
        string="Domain Filter",
        default="[]",
        help="""Domain filter (JSON format). Example:
        [["project_id", "=", 5], ["arcvo_requires_agent", "=", true]]
        Empty = applies to all tasks matching trigger.""",
    )
    action = fields.Selection(
        [
            ("run_agent", "Run Assigned Agent"),
            ("assign_and_run", "Auto-Assign & Run"),
            ("notify", "Notify Only"),
        ],
        default="run_agent",
        required=True,
        string="Action",
        help="What to do when webhook fires",
    )
    active = fields.Boolean(default=True, help="Enable/disable this webhook")
    notes = fields.Text(help="Internal notes about this automation")

    # Statistics
    execution_count = fields.Integer(
        default=0,
        readonly=True,
        help="Number of times this webhook has executed",
    )
    last_execution = fields.Datetime(
        readonly=True,
        help="Timestamp of last execution",
    )
    last_error = fields.Text(
        readonly=True,
        help="Most recent error message if execution failed",
    )

    def _dispatch(self, task, action: str):
        """
        Dispatch webhooks for a given task and action.
        
        Called by signal handlers in agent_orchestration.py when tasks are created/updated.
        
        Args:
            task: project.task record
            action (str): "created", "state_change", "write"
        """
        # Map action string to trigger field value
        trigger_map = {
            "created": "task.created",
            "state_change": "task.state_change",
            "write": "task.write",
        }
        trigger = trigger_map.get(action)
        if not trigger:
            _logger.warning(f"Unknown webhook action: {action}")
            return

        # Find matching webhooks
        webhooks = self.search([("active", "=", True), ("trigger", "=", trigger)])
        executed = 0

        for webhook in webhooks:
            # Check domain filter
            try:
                domain = webhook.domain or []
                if domain and not self.env["project.task"].search(
                    [["id", "=", task.id]] + domain, limit=1
                ):
                    # Task doesn't match domain filter
                    webhook._log_execution(task, "skipped", "Domain filter did not match")
                    continue
            except Exception as e:
                _logger.error(f"Webhook {webhook.name} domain error: {e}")
                webhook._log_execution(task, "error", f"Domain filter error: {e}")
                continue

            # Execute action
            try:
                if webhook.action == "run_agent":
                    webhook._execute_run_agent(task)
                    result = "success"
                    message = "Agent execution triggered"
                elif webhook.action == "assign_and_run":
                    webhook._execute_assign_and_run(task)
                    result = "success"
                    message = "Auto-assigned and triggered"
                elif webhook.action == "notify":
                    webhook._execute_notify(task)
                    result = "success"
                    message = "Notification sent"
                else:
                    result = "error"
                    message = f"Unknown action: {webhook.action}"

                webhook._log_execution(task, result, message)
                executed += 1

            except Exception as e:
                _logger.exception(f"Webhook {webhook.name} execution failed: {e}")
                webhook._log_execution(task, "error", str(e))

        if executed > 0:
            _logger.info(
                f"Webhooks: dispatched {executed} actions for task {task.id} ({action})"
            )

    def _execute_run_agent(self, task):
        """Execute assigned agent immediately if task has agent assigned."""
        self.ensure_one()
        
        if not task.arcvo_agent_id:
            raise ValidationError(
                f"Cannot run agent: task {task.name} has no agent assigned"
            )

        agent = task.arcvo_agent_id
        if not agent.is_agent:
            raise ValidationError(f"Employee {agent.name} is not configured as an agent")

        # Run agent immediately (not waiting for cron)
        _logger.info(f"Webhook executing agent {agent.name} for task {task.name}")
        agent._execute_agent_cycle()

    def _execute_assign_and_run(self, task):
        """Auto-assign task to agent (via matcher) and run immediately."""
        self.ensure_one()

        if task.arcvo_agent_id:
            # Already assigned, just run
            self._execute_run_agent(task)
            return

        # Use matcher from Fase 2 to auto-assign
        try:
            assigned = task._auto_assign_task()
            if assigned:
                # Task was assigned, run it
                self._execute_run_agent(task)
            else:
                _logger.warning(
                    f"Webhook assign_and_run: task {task.name} could not be auto-assigned"
                )
        except Exception as e:
            _logger.exception(f"Webhook assign_and_run failed: {e}")
            raise ValidationError(f"Auto-assignment failed: {e}")

    def _execute_notify(self, task):
        """Send notification (stub for future use)."""
        self.ensure_one()
        _logger.info(f"Webhook notify: task {task.name}")

    def _log_execution(self, task, result: str, message: str):
        """Create audit log entry for this webhook execution."""
        self.ensure_one()
        
        try:
            self.env["arcvo.automation.log"].sudo().create(
                {
                    "webhook_id": self.id,
                    "task_id": task.id,
                    "action": self.action,
                    "result": result,
                    "message": message,
                }
            )
        except Exception as e:
            _logger.error(f"Failed to create webhook log: {e}")

        # Update webhook stats
        self.write(
            {
                "execution_count": self.execution_count + 1,
                "last_execution": fields.Datetime.now(),
                "last_error": message if result == "error" else self.last_error,
            }
        )


class ArcvoAutomationLog(models.Model):
    """Audit log for all webhook executions."""

    _name = "arcvo.automation.log"
    _description = "Automation Webhook Log"
    _order = "create_date DESC"

    webhook_id = fields.Many2one(
        "arcvo.automation.webhook",
        string="Webhook",
        ondelete="cascade",
        help="Which webhook triggered this log entry",
    )
    task_id = fields.Many2one(
        "project.task",
        string="Task",
        ondelete="cascade",
        help="Task that triggered the webhook",
    )
    agent_id = fields.Many2one(
        "hr.employee",
        string="Agent",
        ondelete="set null",
        help="Agent that was executed (if applicable)",
    )
    action = fields.Char(
        string="Action",
        help="Action that was attempted (run_agent, assign_and_run, notify)",
    )
    result = fields.Selection(
        [
            ("success", "Success"),
            ("error", "Error"),
            ("skipped", "Skipped"),
        ],
        default="success",
        string="Result",
    )
    message = fields.Text(
        string="Message",
        help="Details about execution (error message if failed)",
    )
    create_date = fields.Datetime(readonly=True, string="Timestamp")

    def _get_stats(self, days=7):
        """Get webhook execution statistics for past N days."""
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)
        logs = self.search([("create_date", ">=", cutoff)])

        stats = {
            "total": len(logs),
            "success": len(logs.filtered(lambda x: x.result == "success")),
            "error": len(logs.filtered(lambda x: x.result == "error")),
            "skipped": len(logs.filtered(lambda x: x.result == "skipped")),
        }
        return stats
