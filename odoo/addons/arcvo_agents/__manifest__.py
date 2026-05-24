{
    "name": "Arcvo Agents",
    "summary": "Agent registry and task assignment layer for Arcvo Odoo projects",
    "description": """
Arcvo Agents

Provides the canonical Odoo-side registry for Arcvo agents, capabilities,
task assignments, and audit logs. Models use the arcvo.* namespace to avoid
collisions with experimental agent addons.
    """,
    "author": "Monynha Softwares",
    "website": "https://marcelo-m7.com",
    "category": "Project",
    "version": "19.0.1.0.0",
    "depends": ["base", "mail", "project"],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/agent_views.xml",
        "views/capability_views.xml",
        "views/assignment_views.xml",
        "views/audit_log_views.xml",
        "views/helpdesk_stage_views.xml",
        "views/helpdesk_ticket_views.xml",
        "views/knowledge_category_views.xml",
        "views/knowledge_article_views.xml",
        "views/project_task_views.xml",
        "data/helpdesk_stage_data.xml",
        "data/ir_cron_data.xml",
        "data/arcvo_agent_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
