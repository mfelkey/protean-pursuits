"""
core/__init__.py

Protean Pursuits shared core utilities.

Usage in any team running under PP:
    from core.notifications import notify_human
    from core.hitl import request_human_approval
    from core.context import create_project_context, save_context, log_event
    from core.git_helper import git_push, git_push_submodule, submodule_update_all
"""

from core.notifications import send_sms, send_email, notify_human
from core.hitl import request_human_approval
from core.context import (
    create_project_context, save_context, log_event,
    add_artifact, add_blocker, load_context, get_latest_context
)
from core.git_helper import git_push, git_push_submodule, submodule_update_all

__all__ = [
    "send_sms", "send_email", "notify_human",
    "request_human_approval",
    "create_project_context", "save_context", "log_event",
    "add_artifact", "add_blocker", "load_context", "get_latest_context",
    "git_push", "git_push_submodule", "submodule_update_all",
]
