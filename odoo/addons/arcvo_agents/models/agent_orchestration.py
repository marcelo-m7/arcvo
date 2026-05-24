"""
Agent Orchestration - Handles agent execution via Ollama, cron scheduling, and Discuss integration.
"""
import logging
import time
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError

from .ollama_client import OllamaClient

_logger = logging.getLogger(__name__)


class HrEmployeeAgent(models.Model):
    """Extend hr.employee to support agent capabilities."""

    _inherit = "hr.employee"

    is_agent = fields.Boolean(
        string="Is Agent",
        default=False,
        help="Whether this employee acts as an autonomous agent",
    )
    agent_status = fields.Selection(
        [
            ("idle", "Idle"),
            ("running", "Running"),
            ("paused", "Paused"),
            ("error", "Error"),
        ],
        default="idle",
        string="Agent Status",
        help="Current operational status of the agent",
    )
    agent_last_execution = fields.Datetime(
        string="Last Execution",
        help="When agent last ran or attempted to run",
    )
    agent_last_error = fields.Text(
        string="Last Error",
        help="Most recent error message if status=error",
    )
    
    # LLM Configuration
    ollama_model = fields.Char(
        string="Ollama Model",
        default="gemma3:4b",
        help="LLM model name to use for this agent",
    )
    ollama_system_prompt = fields.Text(
        string="System Prompt",
        help="System-level instructions for this agent's behavior",
    )
    agent_active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether cron should execute this agent",
    )

    # Related logs
    agent_message_ids = fields.One2many(
        "arcvo.agent.message",
        "agent_id",
        string="Agent Messages",
        help="Execution logs and decisions for this agent",
    )

    # Agent capabilities (for Fase 2 matching)
    capability_ids = fields.Many2many(
        "arcvo.agent.capability",
        "arcvo_agent_capability_rel",
        "agent_id",
        "capability_id",
        string="Capabilities",
        help="Skills this agent has (for task matching)",
    )
    max_concurrent_tasks = fields.Integer(
        default=3,
        help="Maximum number of concurrent task assignments",
    )
    open_assignment_count = fields.Integer(
        compute="_compute_open_assignments",
        store=False,
        help="Current number of open assignments",
    )

    def action_test_agent(self):
        """Manual action: Test agent immediately (outside cron)."""
        self.ensure_one()
        if not self.is_agent:
            raise UserError("This employee is not configured as an agent")
        
        try:
            self.agent_status = "running"
            self.env.cr.commit()
            
            # Run a simple test
            test_prompt = f"Hello, I am {self.name}. Respond briefly with your understanding of your role as an agent."
            response = self._run_ollama_generation(test_prompt)
            
            self.agent_status = "idle"
            self.agent_last_execution = fields.Datetime.now()
            
            # Post to Discuss
            self._post_to_discuss(
                f"🤖 Agent Test - {self.name}",
                f"System prompt test successful.\n\n**Input:** {test_prompt}\n\n**Response:**\n{response}",
            )
            
            self.env.cr.commit()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Agent Test Successful",
                    "message": f"{self.name} responded successfully.",
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            _logger.exception(f"Agent test failed for {self.name}: {e}")
            self.agent_status = "error"
            self.agent_last_error = str(e)
            self.env.cr.commit()
            raise UserError(f"Agent test failed: {e}")

    def action_pause_agent(self):
        """Manual action: Pause agent (stop cron execution)."""
        self.ensure_one()
        self.agent_active = False
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Agent Paused",
                "message": f"{self.name} will not run in scheduled cron jobs.",
                "type": "success",
            },
        }

    def action_resume_agent(self):
        """Manual action: Resume agent (allow cron execution)."""
        self.ensure_one()
        self.agent_active = True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Agent Resumed",
                "message": f"{self.name} is now active for scheduled execution.",
                "type": "success",
            },
        }

    def _run_ollama_generation(self, prompt: str) -> str:
        """
        Call Ollama API to generate response.
        
        Args:
            prompt (str): Input prompt for the agent
            
        Returns:
            str: Generated response from LLM
            
        Raises:
            UserError: If Ollama call fails
        """
        config = self.env["ir.config_parameter"].sudo()
        
        ollama_uri = config.get_param("arcvo.ollama_uri") or "https://api.ollama.monynha.me"
        ollama_timeout = int(config.get_param("arcvo.ollama_timeout_seconds") or "90")
        ollama_password = config.get_param("arcvo.ollama_password") or ""
        
        client = OllamaClient(
            base_url=ollama_uri,
            model=self.ollama_model,
            timeout=ollama_timeout,
            auth_password=ollama_password if ollama_password else None,
        )
        
        # Check health first
        if not client.health():
            raise UserError(f"Ollama at {ollama_uri} is not responding")
        
        # Generate
        start_time = time.time()
        try:
            response = client.generate(prompt)
            duration = time.time() - start_time
            
            _logger.info(
                f"Agent {self.name} generated response in {duration:.2f}s, "
                f"response length: {len(response)}"
            )
            
            return response
        except Exception as e:
            _logger.error(f"Agent {self.name} Ollama call failed: {e}")
            raise

    def _post_to_discuss(self, subject: str, body: str):
        """
        Post a message to this employee's Discuss channel (chatter).
        
        Args:
            subject (str): Message subject
            body (str): Message body (supports HTML/markup)
        """
        # Post to employee's partner record (which has chatter)
        if self.user_id and self.user_id.partner_id:
            self.user_id.partner_id.message_post(
                subject=subject,
                body=body,
                message_type="comment",
            )
            _logger.info(f"Posted to Discuss: {subject}")
        else:
            _logger.warning(
                f"Cannot post to Discuss for {self.name} (no user/partner)"
            )

    @api.model
    def _cron_run_active_agents(self):
        """
        Cron job: Run all active agents.
        Called periodically to execute agents that are marked active and is_agent=True.
        """
        _logger.info("Starting cron_run_active_agents")
        
        # Find all active agents
        active_agents = self.search([
            ("is_agent", "=", True),
            ("agent_active", "=", True),
            ("user_id", "!=", False),  # Must have a user
        ])
        
        _logger.info(f"Found {len(active_agents)} active agents to run")
        
        for agent in active_agents:
            try:
                agent._execute_agent_cycle()
            except Exception as e:
                _logger.exception(f"Agent cycle failed for {agent.name}: {e}")
                agent.agent_status = "error"
                agent.agent_last_error = str(e)
        
        self.env.cr.commit()
        
        # Check for stuck assignments and escalate (Fase 4)
        try:
            escalation_engine = self.env["escalation.engine"]
            escalation_engine._cron_check_escalations()
        except Exception as e:
            _logger.warning(f"Escalation check failed: {e}")
        
        _logger.info("Cron_run_active_agents completed")

    def _execute_agent_cycle(self):
        """
        Execute one agent cycle:
        1. Construct prompt based on current context
        2. Call Ollama
        3. Parse response
        4. Update status / take action
        5. Log to arcvo.agent.message
        6. Post to Discuss
        """
        self.ensure_one()
        _logger.info(f"Executing agent cycle for {self.name}")
        
        try:
            self.agent_status = "running"
            
            # Build prompt
            prompt = self._build_agent_prompt()
            
            # Call Ollama
            start_time = time.time()
            raw_response = self._run_ollama_generation(prompt)
            duration = time.time() - start_time
            
            # Parse decision (try to extract JSON)
            ollama_client = OllamaClient(base_url="https://api.ollama.monynha.me")
            decision = ollama_client.extract_json_from_text(raw_response)
            
            # Log to arcvo.agent.message
            message_log = self.env["arcvo.agent.message"]._log_message(
                agent=self,
                prompt=prompt,
                raw_response=raw_response,
                decision=decision,
                status="success",
                llm_duration_seconds=duration,
            )
            
            # Post to Discuss
            summary = decision.get("summary", raw_response[:200]) if decision else raw_response[:200]
            self._post_to_discuss(
                f"🤖 Agent Execution - {self.name}",
                f"**Decision:** {summary}\n\n**Full Response:**\n{raw_response}",
            )
            
            # Update status
            self.agent_status = "idle"
            self.agent_last_execution = fields.Datetime.now()
            
            _logger.info(f"Agent cycle completed for {self.name}")
            
        except Exception as e:
            _logger.exception(f"Error in agent cycle for {self.name}: {e}")
            self.agent_status = "error"
            self.agent_last_error = str(e)
            self.agent_last_execution = fields.Datetime.now()
            
            # Still log the error to arcvo.agent.message
            try:
                self.env["arcvo.agent.message"]._log_message(
                    agent=self,
                    prompt="",
                    raw_response="",
                    status="error",
                    error_message=str(e),
                )
            except Exception as log_error:
                _logger.exception(f"Failed to log error for {self.name}: {log_error}")

    def _build_agent_prompt(self) -> str:
        """
        Build the LLM prompt for this agent.
        Can be overridden per agent type or context.
        
        Returns:
            str: Prompt to send to Ollama
        """
        # Simple default: use system prompt if configured
        if self.ollama_system_prompt:
            return self.ollama_system_prompt
        
        # Generic agent prompt
        return f"""You are {self.name}, an autonomous agent in Odoo.
Your task is to analyze the current state and respond with a JSON decision.

Respond ONLY with valid JSON in this format (no markdown, no extra text):
{{
    "summary": "Brief summary of your decision",
    "status": "success or pending",
    "progress": 0-100,
    "command": "Optional action to take"
}}

Current time: {datetime.now().isoformat()}
"""

    @api.depends("is_agent")
    def _compute_open_assignments(self):
        """Compute number of open assignments for this agent."""
        for employee in self:
            if employee.is_agent:
                open_assignments = self.env["arcvo.agent.assignment"].search_count(
                    [
                        ("agent_id", "=", employee.id),
                        ("status", "in", ["assigned", "in_progress", "blocked"]),
                    ]
                )
                employee.open_assignment_count = open_assignments
            else:
                employee.open_assignment_count = 0


class ProjectTaskWebhook(models.Model):
    """Extend project.task to support webhook dispatching on creation/update."""

    _inherit = "project.task"

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to dispatch webhooks when tasks are created."""
        records = super().create(vals_list)
        
        # Dispatch webhooks for task.created trigger
        try:
            webhook_model = self.env.get("arcvo.automation.webhook")
            if webhook_model:
                for record in records:
                    webhook_model._dispatch(record, "created")
        except Exception as e:
            _logger.warning(f"Error dispatching webhooks on task creation: {e}")
        
        return records

    def write(self, vals):
        """Override write to dispatch webhooks when tasks are updated."""
        result = super().write(vals)
        
        # Dispatch webhooks for task.write trigger
        try:
            webhook_model = self.env.get("arcvo.automation.webhook")
            if webhook_model:
                for record in self:
                    webhook_model._dispatch(record, "write")
                    
                    # Also dispatch task.state_change if state field was updated
                    if "state" in vals:
                        webhook_model._dispatch(record, "state_change")
        except Exception as e:
            _logger.warning(f"Error dispatching webhooks on task update: {e}")
        
        return result

    def _auto_assign_task(self):
        """
        Try to auto-assign this task to an agent using matchers (Fase 2).
        
        Dispatches all active matchers in sequence (priority order) until
        one successfully assigns the task.
        
        Returns:
            bool: True if task was successfully assigned
        """
        self.ensure_one()

        # If already assigned, skip
        if self.arcvo_agent_id:
            _logger.info(f"Task {self.name} already assigned to {self.arcvo_agent_id.name}")
            return True

        # Get all active matchers
        matcher_model = self.env.get("arcvo.automation.matcher")
        if not matcher_model:
            _logger.warning("Matcher model not found (Fase 2 not installed)")
            return False

        matchers = matcher_model.search(
            [("active", "=", True)],
            order="sequence ASC",
        )

        if not matchers:
            _logger.warning(f"No active matchers found for task {self.name}")
            return False

        # Try each matcher in order
        for matcher in matchers:
            try:
                if matcher.apply_matcher(self):
                    _logger.info(
                        f"Task {self.name} auto-assigned to {self.arcvo_agent_id.name} "
                        f"by matcher {matcher.name}"
                    )
                    return True
            except Exception as e:
                _logger.exception(f"Error applying matcher {matcher.name}: {e}")
                continue

        # No matcher succeeded
        _logger.warning(f"No matcher could assign task {self.name}")
        return False


class MailMessageDiscussHandler(models.Model):
    """Handle Discuss messages and dispatch to agents on @mention."""

    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to detect @mentions and dispatch to agents."""
        messages = super().create(vals_list)
        
        # Process messages for Discuss agent responses
        for message in messages:
            try:
                if message.message_type != "comment":
                    continue  # Only process comments
                
                # Check if message mentions any agents
                self._dispatch_to_mentioned_agents(message)
                
            except Exception as e:
                _logger.warning(f"Error processing Discuss message {message.id}: {e}")
        
        return messages

    def _dispatch_to_mentioned_agents(self, message):
        """
        Check if message mentions agents and dispatch Smart Discuss responses.
        
        Looks for @agent-name patterns in message body and triggers
        discuss_response_engine for matching agents.
        """
        if not message.body:
            return
        
        # Find all @mention patterns (simple regex: @word or @"word word")
        import re
        mention_pattern = r'@([a-zA-Z0-9._-]+(?:\s+[a-zA-Z0-9._-]+)*)'
        mentions = re.findall(mention_pattern, message.body)
        
        if not mentions:
            return
        
        _logger.debug(f"Found mentions in message {message.id}: {mentions}")
        
        # Search for matching agents
        for mention in mentions:
            agent = self.env["hr.employee"].search(
                [
                    ("is_agent", "=", True),
                    ("agent_active", "=", True),
                    ("|", ("name", "ilike", mention), ("user_id.login", "ilike", mention)),
                ],
                limit=1,
            )
            
            if agent:
                _logger.info(f"Agent {agent.name} mentioned in message {message.id}")
                
                # Dispatch to agent
                try:
                    self._handle_agent_mention(agent, message)
                except Exception as e:
                    _logger.exception(f"Error dispatching agent mention: {e}")

    def _handle_agent_mention(self, agent, message):
        """
        Generate Smart Discuss response for mentioned agent.
        
        Args:
            agent: hr.employee (agent)
            message: mail.message (the mention)
        """
        # Get response engine
        engine = self.env["discuss.response.engine"]
        
        # Collect context
        context = engine.collect_thread_context(message)
        _logger.debug(f"Collected context for agent {agent.name}: {len(context['recent_messages'])} messages")
        
        # Generate response
        response_data = engine.generate_response(agent, message, context)
        if not response_data:
            _logger.warning(f"Failed to generate response for agent {agent.name}")
            return
        
        _logger.info(f"Generated response for agent {agent.name}: {response_data.get('action_type', 'unknown')}")
        
        # Post to Discuss
        response_msg = engine.post_discuss_response(agent, message, response_data)
        if response_msg:
            _logger.info(f"Posted response message {response_msg.id}")
        
        # Create audit trail
        engine.create_discuss_action_record(agent, message, response_data, response_msg)