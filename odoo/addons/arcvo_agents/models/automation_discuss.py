"""
Smart Discuss Action Audit - Tracks agent responses and button interactions.
"""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ArcvoAutomationDiscussAction(models.Model):
    """Audit trail for smart Discuss agent responses and user interactions."""

    _name = "arcvo.automation.discuss.action"
    _description = "Agent Discuss Action Audit"
    _order = "create_date DESC"

    # Core relationships
    agent_id = fields.Many2one(
        "hr.employee",
        required=True,
        ondelete="cascade",
        string="Agent",
        help="Agent that generated the response",
    )
    mention_message_id = fields.Many2one(
        "mail.message",
        required=True,
        ondelete="cascade",
        string="Mention Message",
        help="Original @mention message",
    )
    response_message_id = fields.Many2one(
        "mail.message",
        ondelete="set null",
        string="Response Message",
        help="Discuss response posted by agent",
    )

    # Response metadata
    action_type = fields.Selection(
        [
            ("info", "Information"),
            ("question", "Question"),
            ("task", "Task"),
            ("escalation", "Escalation"),
        ],
        required=True,
        default="info",
        string="Action Type",
        help="Type of action generated",
    )
    confidence = fields.Float(
        string="Confidence",
        help="Model confidence in response (0.0-1.0)",
    )
    response_text = fields.Text(
        string="Response Text",
        help="Full text of the agent's response",
    )
    needs_human_review = fields.Boolean(
        string="Needs Review",
        default=False,
        help="Whether this response should be reviewed by a human",
    )
    suggested_next_step = fields.Text(
        string="Suggested Next Step",
        help="What the agent recommends should happen next",
    )

    # Button tracking
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("paused", "Paused"),
            ("rejected", "Rejected"),
            ("escalated", "Escalated"),
        ],
        default="pending",
        string="Status",
        help="Current status of the action (based on user button clicks)",
    )
    button_clicks = fields.Integer(
        default=0,
        string="Button Clicks",
        help="How many button interactions this action has received",
    )
    button_click_ids = fields.One2many(
        "arcvo.automation.discuss.button.click",
        "action_id",
        string="Button Clicks",
        help="Detail of each button interaction",
    )

    # Audit
    created_by = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        readonly=True,
        string="Created By",
    )
    create_date = fields.Datetime(readonly=True, string="Created")

    # Computed fields
    response_delay_seconds = fields.Float(
        compute="_compute_response_delay",
        store=False,
        string="Response Delay (s)",
    )

    @api.depends("mention_message_id", "create_date")
    def _compute_response_delay(self):
        """Calculate time between mention and agent response."""
        for record in self:
            if record.mention_message_id and record.create_date:
                mention_time = record.mention_message_id.create_date
                response_time = record.create_date
                delay = (response_time - mention_time).total_seconds()
                record.response_delay_seconds = delay
            else:
                record.response_delay_seconds = 0

    def action_accept(self):
        """User clicked Accept button."""
        for record in self:
            record.status = "accepted"
            record.button_clicks += 1
            record._log_button_click("accept")
            _logger.info(
                f"User accepted discuss action {record.id} from agent {record.agent_id.name}"
            )

    def action_pause(self):
        """User clicked Pause button."""
        for record in self:
            record.status = "paused"
            record.button_clicks += 1
            record._log_button_click("pause")
            _logger.info(
                f"User paused discuss action {record.id} from agent {record.agent_id.name}"
            )

    def action_retry(self):
        """User clicked Retry button - regenerate response."""
        for record in self:
            record.button_clicks += 1
            record._log_button_click("retry")
            _logger.info(
                f"User requested retry for discuss action {record.id} from agent {record.agent_id.name}"
            )

            # Trigger re-generation (placeholder)
            # TODO: Call discuss_response_engine again

    def _log_button_click(self, button_type):
        """Create button click record."""
        self.ensure_one()
        self.env["arcvo.automation.discuss.button.click"].create(
            {
                "action_id": self.id,
                "button_type": button_type,
                "clicked_by": self.env.user.id,
            }
        )


class ArcvoAutomationDiscussButtonClick(models.Model):
    """Audit detail for each button click on Discuss responses."""

    _name = "arcvo.automation.discuss.button.click"
    _description = "Discuss Button Click Audit"
    _order = "create_date DESC"

    # Core relationship
    action_id = fields.Many2one(
        "arcvo.automation.discuss.action",
        required=True,
        ondelete="cascade",
        string="Action",
        help="Parent action that was clicked",
    )

    # Click data
    button_type = fields.Selection(
        [
            ("accept", "Accept ✓"),
            ("pause", "Pause ⏸"),
            ("retry", "Retry 🔄"),
        ],
        required=True,
        string="Button Type",
    )
    clicked_by = fields.Many2one(
        "res.users",
        required=True,
        readonly=True,
        string="Clicked By",
    )
    create_date = fields.Datetime(readonly=True, string="Clicked At")
    notes = fields.Text(
        string="Notes",
        help="Optional user notes when clicking button",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Log button click creation."""
        records = super().create(vals_list)
        for record in records:
            _logger.debug(
                f"Button click {record.button_type} by {record.clicked_by.name} "
                f"on action {record.action_id.id}"
            )
        return records
