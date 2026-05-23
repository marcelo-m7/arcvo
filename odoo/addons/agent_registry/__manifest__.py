{
    "name": "Agent Registry",
    "summary": "Autonomous Agent Management & Task Coordination System",
    "description": """
        Central registry for autonomous agents operating in Arcvo.
        
        Features:
        - Agent profiles and capabilities management
        - Task assignment routing
        - Audit trail and compliance logging
        - Agent health monitoring (heartbeats)
        - Task workload management
        
        This addon is the core of the autonomous organization,
        enabling agents to discover tasks, claim work, and
        report progress in a traceable way.
    """,
    "author": "Monynha Softwares",
    "website": "https://monynha.com",
    "category": "Technical",
    "version": "0.1",
    "depends": [
        "base",
        "project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/agent_capability_views.xml",
        "views/agent_views.xml",
        "views/agent_assignment_views.xml",
        "views/agent_audit_log_views.xml",
        "data/agent_capabilities_demo.xml",
    ],
    "demo": [
        "data/agent_demo.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
