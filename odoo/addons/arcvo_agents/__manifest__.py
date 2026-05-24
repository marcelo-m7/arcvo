{
    "name": "Arcvo Agents",
    "summary": "Odoo SSOT for Arcvo agents, task delegation, Discuss, and audit",
    "description": """
Arcvo Agents

Provides the canonical Odoo-side registry for Arcvo agents, capabilities,
task assignments, Discuss channels, and audit logs. Project tasks remain the
source of operational work and every agent action is traceable in Odoo.
    """,
    "author": "Monynha Softwares",
    "website": "https://marcelo-m7.com",
    "category": "Project",
    "version": "19.0.2.0.0",
    "depends": ["base", "mail", "project"],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "views/agent_views.xml",
        "views/capability_views.xml",
        "views/assignment_views.xml",
        "views/audit_log_views.xml",
        "views/project_task_views.xml",
        "data/arcvo_agent_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
