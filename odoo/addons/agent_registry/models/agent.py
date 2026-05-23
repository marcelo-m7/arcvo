from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AgentCapability(models.Model):
    """Skills and capabilities that agents can have."""

    _name = "agent.capability"
    _description = "Agent Capability / Skill"
    _order = "name"

    name = fields.Char(
        string="Capability Name",
        required=True,
        help="e.g., 'backend_dev', 'frontend_dev', 'devops', 'qa', 'project_management'",
    )
    description = fields.Text(string="Description")
    category = fields.Selection(
        [
            ("development", "Development"),
            ("infrastructure", "Infrastructure"),
            ("management", "Management"),
            ("qa", "QA/Testing"),
            ("documentation", "Documentation"),
        ],
        default="development",
        string="Category",
    )
    agents_count = fields.Integer(
        compute="_compute_agents_count",
        string="Agent Count",
        help="Number of agents with this capability",
    )

    _sql_constraints = [
        ("name_unique", "unique(name)", "Capability name must be unique"),
    ]

    def _compute_agents_count(self):
        for record in self:
            record.agents_count = len(record.agent_ids)

    @property
    def agent_ids(self):
        """Get agents with this capability."""
        return self.env["agent.agent"].search([("capabilities_ids", "=", self.id)])


class AgentAgent(models.Model):
    """Autonomous agent profiles."""

    _name = "agent.agent"
    _description = "Autonomous Agent"
    _order = "name"

    name = fields.Char(string="Agent Name", required=True)
    agent_type = fields.Selection(
        [
            ("orchestrator", "Orchestrator (CEO, PM)"),
            ("executor", "Executor (Developer, DevOps)"),
            ("reviewer", "Reviewer (QA, Code Review)"),
            ("support", "Support (Documentation, Monitoring)"),
        ],
        default="executor",
        required=True,
        string="Agent Type",
    )
    status = fields.Selection(
        [
            ("available", "Available"),
            ("busy", "Busy"),
            ("offline", "Offline"),
            ("error", "Error"),
            ("suspended", "Suspended"),
        ],
        default="available",
        string="Status",
        help="Current availability status of the agent",
    )
    description = fields.Text(string="Description")

    # Capabilities
    capabilities_ids = fields.Many2many(
        "agent.capability",
        string="Capabilities",
        help="Skills this agent has",
    )

    # API Access
    api_key = fields.Char(
        string="API Key",
        copy=False,
        readonly=True,
        help="Private key for MCP/API calls (auto-generated)",
    )
    api_key_generated = fields.Datetime(
        string="API Key Generated",
        readonly=True,
    )

    # Health
    last_heartbeat = fields.Datetime(
        string="Last Heartbeat",
        readonly=True,
        help="Last time agent checked in (keep-alive)",
    )
    current_workload = fields.Integer(
        string="Current Workload",
        default=0,
        readonly=True,
        help="Number of tasks currently assigned",
    )
    max_concurrent_tasks = fields.Integer(
        string="Max Concurrent Tasks",
        default=3,
        help="Maximum number of tasks this agent can handle simultaneously",
    )

    # Timestamps
    created_at = fields.Datetime(
        string="Created At",
        default=fields.Datetime.now,
        readonly=True,
    )
    updated_at = fields.Datetime(
        string="Updated At",
        default=fields.Datetime.now,
        readonly=True,
    )

    # Relationships
    assignment_ids = fields.One2many(
        "agent.assignment",
        "agent_id",
        string="Task Assignments",
    )
    audit_log_ids = fields.One2many(
        "agent.audit_log",
        "agent_id",
        string="Audit Logs",
    )

    # Status signals
    is_available = fields.Boolean(
        compute="_compute_is_available",
        string="Is Available",
        help="Can receive new tasks",
    )

    _sql_constraints = [
        ("name_unique", "unique(name)", "Agent name must be unique"),
    ]

    @api.depends("status", "current_workload", "max_concurrent_tasks")
    def _compute_is_available(self):
        """Agent is available if online, not in error, and has capacity."""
        for record in self:
            record.is_available = (
                record.status == "available"
                and record.current_workload < record.max_concurrent_tasks
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Generate API keys for new agents."""
        import secrets
        from datetime import datetime

        for vals in vals_list:
            if not vals.get("api_key"):
                vals["api_key"] = secrets.token_urlsafe(32)
                vals["api_key_generated"] = datetime.now()
        return super().create(vals_list)

    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.update({"last_heartbeat": fields.Datetime.now()})

    def update_workload(self, delta: int):
        """Increment/decrement current workload."""
        for record in self:
            record.current_workload = max(0, record.current_workload + delta)

    def set_status(self, new_status: str):
        """Update agent status."""
        if new_status not in dict(self._fields["status"].selection):
            raise ValidationError(f"Invalid status: {new_status}")
        self.update({"status": new_status})

    def get_pending_tasks(self, limit: int = 10):
        """Get unassigned/pending tasks suitable for this agent."""
        return self.env["project.task"].search(
            [
                ("state", "in", ["todo", "in_progress"]),
                ("assigned_agent_id", "=", False),
                # Task capabilities must be subset of agent capabilities
            ],
            limit=limit,
        )


class AgentAssignment(models.Model):
    """Agent-to-Task assignments tracking."""

    _name = "agent.assignment"
    _description = "Agent Task Assignment"
    _order = "assigned_at desc"

    agent_id = fields.Many2one(
        "agent.agent",
        required=True,
        string="Agent",
        ondelete="cascade",
    )
    task_id = fields.Many2one(
        "project.task",
        required=True,
        string="Task",
        ondelete="cascade",
    )
    status = fields.Selection(
        [
            ("assigned", "Assigned"),
            ("claimed", "Claimed"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("rejected", "Rejected"),
        ],
        default="assigned",
        string="Status",
    )

    # Timestamps
    assigned_at = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    started_at = fields.Datetime(string="Started At", readonly=True)
    completed_at = fields.Datetime(string="Completed At", readonly=True)

    # Progress
    progress_percentage = fields.Integer(
        default=0,
        string="Progress %",
    )
    estimated_hours = fields.Float(string="Estimated Hours")
    actual_hours = fields.Float(string="Actual Hours", readonly=True)
    notes = fields.Text(string="Notes")

    _sql_constraints = [
        (
            "agent_task_unique",
            "unique(agent_id, task_id)",
            "Each task can only be assigned to one agent at a time",
        ),
    ]


class AgentAuditLog(models.Model):
    """Immutable audit trail of all agent actions."""

    _name = "agent.audit_log"
    _description = "Agent Audit Log"
    _order = "timestamp desc"

    agent_id = fields.Many2one(
        "agent.agent",
        required=True,
        string="Agent",
        ondelete="cascade",
    )
    task_id = fields.Many2one(
        "project.task",
        string="Task",
        ondelete="set null",
    )
    action_type = fields.Selection(
        [
            ("registered", "Agent Registered"),
            ("heartbeat", "Heartbeat"),
            ("claimed", "Task Claimed"),
            ("progress", "Progress Reported"),
            ("completed", "Task Completed"),
            ("failed", "Task Failed"),
            ("error", "Error"),
            ("status_change", "Status Changed"),
        ],
        required=True,
        string="Action Type",
    )
    action_details = fields.Json(
        string="Action Details",
        help="JSON payload of action parameters/results",
    )
    status_code = fields.Integer(
        string="Status Code",
        help="HTTP/RPC response code (200, 400, 500, etc.)",
    )
    error_msg = fields.Text(string="Error Message")
    timestamp = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        required=True,
    )

    _index_list = [
        ("agent_id", "task_id", "timestamp"),
        ("agent_id", "timestamp"),
        ("task_id", "timestamp"),
    ]

    def create(self, vals):
        """Log all field changes automatically."""
        # Automatically set timestamp if not provided
        if "timestamp" not in vals:
            vals["timestamp"] = fields.Datetime.now()
        return super().create(vals)

    @api.model
    def log_action(self, agent_id, action_type, task_id=None, **kwargs):
        """Helper to log agent actions."""
        return self.create(
            {
                "agent_id": agent_id,
                "task_id": task_id,
                "action_type": action_type,
                "action_details": kwargs,
            }
        )
