"""
Smart Discuss Response Engine - Handles agent responses to @mentions with context collection.
"""
import json
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .ollama_client import OllamaClient

_logger = logging.getLogger(__name__)


class DiscussResponseEngine(models.AbstractModel):
    """Engine to generate intelligent Discuss responses."""

    _name = "discuss.response.engine"
    _description = "Generates LLM-powered responses for Discuss messages"

    def collect_thread_context(self, message, lookback_hours=24):
        """
        Collect context from the message thread.

        Args:
            message: mail.message record
            lookback_hours: How many hours back to look for context

        Returns:
            dict: Context data {thread_id, recent_messages, participant_count, ...}
        """
        context = {
            "thread_id": message.res_id,
            "thread_model": message.model,
            "thread_name": message.record_name or "Unknown",
            "recent_messages": [],
            "participant_count": 0,
            "thread_start": None,
            "mention_context": None,
        }

        # Get all messages in thread (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
        thread_messages = self.env["mail.message"].search(
            [
                ("model", "=", message.model),
                ("res_id", "=", message.res_id),
                ("create_date", ">=", cutoff_time.isoformat()),
                ("message_type", "=", "comment"),
            ],
            order="create_date ASC",
            limit=20,  # Max last 20 messages
        )

        # Build message history
        for msg in thread_messages:
            author_name = msg.author_id.name if msg.author_id else "System"
            context["recent_messages"].append(
                {
                    "author": author_name,
                    "body": msg.body[:500],  # Truncate for token limit
                    "created": msg.create_date.isoformat(),
                }
            )

        # Get unique participants
        participants = thread_messages.mapped("author_id.name")
        context["participant_count"] = len(set(participants))

        # Thread start date
        if thread_messages:
            context["thread_start"] = thread_messages[0].create_date.isoformat()

        # Mention context (from the message itself)
        if message.body:
            # Extract mention info
            context["mention_context"] = {
                "mentioned_by": message.author_id.name if message.author_id else "Unknown",
                "mention_body": message.body[:500],
            }

        return context

    def build_response_prompt(self, agent, message, context):
        """
        Build LLM prompt for generating a Discuss response.

        Args:
            agent: hr.employee (agent)
            message: mail.message (the @mention)
            context: dict from collect_thread_context()

        Returns:
            str: Prompt for LLM
        """
        system_prompt = agent.ollama_system_prompt or self._default_discuss_system_prompt(
            agent
        )

        # Build context summary
        context_summary = self._build_context_summary(context)

        prompt = f"""{system_prompt}

---
CURRENT DISCUSS CONTEXT:
{context_summary}

---
THREAD INFORMATION:
- Thread: {context['thread_name']}
- Model: {context['thread_model']}
- Participants: {context['participant_count']}
- Start: {context['thread_start']}

---
RECENT MESSAGES:
"""
        for msg in context["recent_messages"][-5:]:  # Last 5 messages for context
            prompt += (
                f"- [{msg['author']} @ {msg['created']}]: {msg['body']}\n"
            )

        if context["mention_context"]:
            prompt += f"""
---
YOU WERE MENTIONED BY: {context['mention_context']['mentioned_by']}
MENTION MESSAGE: {context['mention_context']['mention_body']}

---
TASK:
Analyze the thread and provide a helpful response. Respond ONLY with valid JSON:
{{
    "response": "Your response text here (clear, concise, actionable)",
    "action_type": "info|question|task|escalation",
    "confidence": 0.0-1.0,
    "needs_human_review": true|false,
    "suggested_next_step": "Optional suggestion for follow-up"
}}

Keep response concise (<300 chars). Current time: {datetime.now().isoformat()}
"""

        return prompt

    def _default_discuss_system_prompt(self, agent):
        """Default system prompt for Discuss responses."""
        return f"""You are {agent.name}, an intelligent agent in the Odoo team.
Your role is to:
1. Analyze team discussions and provide helpful insights
2. Answer questions based on available context
3. Flag issues that need human attention
4. Suggest actionable next steps

Be concise, professional, and data-driven. When unsure, ask clarifying questions."""

    def _build_context_summary(self, context):
        """Build human-readable context summary."""
        summary = f"Thread: {context['thread_name']}\n"
        summary += f"Participants: {context['participant_count']}\n"

        if context["recent_messages"]:
            summary += f"Last message: {context['recent_messages'][-1]['author']}\n"

        return summary

    def generate_response(self, agent, message, context):
        """
        Generate an LLM response for a Discuss message.

        Args:
            agent: hr.employee (agent)
            message: mail.message (the @mention)
            context: dict from collect_thread_context()

        Returns:
            dict: Generated response {response_text, action_type, confidence, needs_review, next_step}
            or None if failed
        """
        try:
            prompt = self.build_response_prompt(agent, message, context)

            # Call Ollama
            client = OllamaClient()
            response_text = client.generate(
                model=agent.ollama_model or "gemma3:4b",
                prompt=prompt,
                temperature=0.7,
            )

            # Parse JSON response
            try:
                # Try to extract JSON from response (may have extra text)
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    _logger.warning(f"Invalid JSON in response: {response_text[:200]}")
                    result = {
                        "response": response_text[:300],
                        "action_type": "info",
                        "confidence": 0.5,
                        "needs_human_review": True,
                    }
            except json.JSONDecodeError as e:
                _logger.exception(f"JSON parse error: {e}")
                result = {
                    "response": response_text[:300],
                    "action_type": "info",
                    "confidence": 0.3,
                    "needs_human_review": True,
                }

            return result

        except Exception as e:
            _logger.exception(f"Failed to generate response: {e}")
            return None

    def post_discuss_response(self, agent, message, response_data):
        """
        Post agent response to Discuss.

        Args:
            agent: hr.employee (agent)
            message: mail.message (the @mention)
            response_data: dict from generate_response()

        Returns:
            mail.message: Posted response message or None
        """
        if not response_data:
            return None

        try:
            # Get the thread model instance
            thread_model = self.env[message.model]
            thread_record = thread_model.browse(message.res_id)

            # Post response
            response_message = thread_record.message_post(
                body=response_data.get("response", ""),
                message_type="comment",
                author_id=agent.user_id.partner_id.id if agent.user_id else None,
                subtype_xmlid="mail.mt_comment",
            )

            return response_message

        except Exception as e:
            _logger.exception(f"Failed to post response: {e}")
            return None

    def create_discuss_action_record(self, agent, message, response_data, response_msg):
        """
        Create audit trail in arcvo.automation.discuss.action.

        Args:
            agent: hr.employee (agent)
            message: mail.message (the @mention)
            response_data: dict from generate_response()
            response_msg: mail.message (posted response) or None
        """
        try:
            self.env["arcvo.automation.discuss.action"].create(
                {
                    "agent_id": agent.id,
                    "mention_message_id": message.id,
                    "response_message_id": response_msg.id if response_msg else None,
                    "action_type": response_data.get("action_type", "info"),
                    "confidence": response_data.get("confidence", 0.0),
                    "needs_human_review": response_data.get("needs_human_review", False),
                    "suggested_next_step": response_data.get(
                        "suggested_next_step", ""
                    ),
                    "button_clicks": 0,
                    "status": "pending",
                    "response_text": response_data.get("response", ""),
                }
            )

        except Exception as e:
            _logger.exception(f"Failed to create action record: {e}")
