"""
Nidhi — Security Confirmation Gates

Intercepts sensitive write/delete operations (files, tasks, notes)
and requires human-in-the-loop approval.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

def requires_confirmation(tool: str, argument: str) -> bool:
    """
    Check if the given tool execution step requires human confirmation.
    
    Triggers on:
    - Files: write, delete, modify, remove
    - Tasks: create, add, update, delete, remove, edit, complete
    - Notes: create, add, save, delete, remove, edit, update
    """
    tool = tool.lower()
    arg = argument.lower()
    
    # Files: write, delete, modify, remove
    if tool == "files":
        if any(w in arg for w in ["write", "delete", "create", "update", "modify", "remove", "save"]):
            return True
            
    # Tasks: create, add, update, delete, remove, edit, complete
    elif tool == "tasks":
        if any(w in arg for w in ["create", "add", "update", "delete", "remove", "edit", "complete", "finish"]):
            return True
            
    # Notes: create, add, save, delete, remove, edit, update
    elif tool == "notes":
        if any(w in arg for w in ["create", "add", "save", "delete", "remove", "edit", "update"]):
            return True
            
    # Browser: click, fill, submit, download, post, login
    elif tool == "browser":
        if any(w in arg for w in ["click", "fill", "submit", "download", "post", "login", "buy", "pay"]):
            return True
            
    # Computer: opening apps, running files/folders, sending messages
    elif tool == "computer":
        if any(w in arg for w in ["open", "start", "run", "message", "send", "delete", "write"]):
            return True
            
    # WhatsApp: sending messages
    elif tool == "whatsapp":
        if any(w in arg for w in ["send", "message", "write", "post"]):
            return True
            
    return False

