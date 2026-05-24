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
