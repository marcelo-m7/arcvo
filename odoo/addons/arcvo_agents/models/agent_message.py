"""
Agent Message Model - Structured audit logs for agent executions.
Records each agent action, decision, and result in Odoo database.
"""
from odoo import fields, models


class ArcvoAgentMessage(models.Model):
    """
    Audit log for agent decisions and actions.
    
    Each message represents one LLM decision or action taken by an agent.
    Stores prompt, raw response, parsed decision, and outcome for traceability.
    """

    _name = "arcvo.agent.message"
    _description = "Agent Message Log"
    _order = "create_date DESC"

    # Relationships
    agent_id = fields.Many2one(
        "hr.employee",
        string="Agent",
        required=True,
        help="Employee acting as agent",
    )
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        help="Project context for this message",
    )
    task_id = fields.Many2one(
        "project.task",
        string="Task",
        help="Task that triggered this agent message",
    )
    discuss_message_id = fields.Many2one(
        "mail.message",
        string="Posted Message",
        help="Discuss message created for this agent response",
    )

    # Message content
    prompt = fields.Text(
        string="Prompt",
        required=True,
        help="Input prompt sent to LLM",
    )
    raw_response = fields.Text(
        string="Raw Response",
        required=True,
        help="Raw text response from LLM",
    )
    decision = fields.Json(
        string="Parsed Decision",
        help="""JSON decision parsed from response.
        Typically: {
            "summary": str,
            "status": str,
            "progress": int,
            "command": str
        }""",
    )

    # Metadata
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("success", "Success"),
            ("error", "Error"),
            ("timeout", "Timeout"),
        ],
        default="pending",
        string="Status",
        help="Execution status of this message",
    )
    error_message = fields.Text(
        string="Error Message",
        help="If status=error, details about what went wrong",
    )

    # Timestamps
    executed_at = fields.Datetime(
        string="Executed At",
        help="When LLM generation was executed",
    )
    completed_at = fields.Datetime(
        string="Completed At",
        help="When action completed or error occurred",
    )

    # Statistics
    llm_duration_seconds = fields.Float(
        string="LLM Duration (s)",
        help="Time taken by LLM to generate response",
    )
    prompt_tokens = fields.Integer(
        string="Prompt Tokens",
        help="Tokens in prompt (estimate)",
    )
    response_tokens = fields.Integer(
        string="Response Tokens",
        help="Tokens in response (estimate)",
    )

    def _log_message(
        self,
        agent,
        prompt: str,
        raw_response: str,
        decision=None,
        status: str = "success",
        error_message: str = "",
        project_id=None,
        task_id=None,
        discuss_message_id=None,
        llm_duration_seconds: float = 0.0,
    ) -> "ArcvoAgentMessage":
        """
        Create a new agent message log entry.
        
        Args:
            agent: hr.employee record (the agent)
            prompt (str): Prompt sent to LLM
            raw_response (str): Raw response from LLM
            decision (dict, optional): Parsed decision
            status (str): "success", "error", "timeout", etc
            error_message (str): Error details if status=error
            project_id: project.project record (optional context)
            task_id: project.task record (optional context)
            discuss_message_id: mail.message if posted to Discuss
            llm_duration_seconds (float): How long LLM took
            
        Returns:
            ArcvoAgentMessage: Created message record
        """
        return self.create(
            {
                "agent_id": agent.id,
                "prompt": prompt,
                "raw_response": raw_response,
                "decision": decision,
                "status": status,
                "error_message": error_message,
                "project_id": project_id,
                "task_id": task_id,
                "discuss_message_id": discuss_message_id,
                "llm_duration_seconds": llm_duration_seconds,
                "executed_at": fields.Datetime.now(),
            }
        )
