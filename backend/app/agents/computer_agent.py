"""
Uday AI — Computer Use & Desktop Automation Agent

Handles opening applications, opening files/folders, and browser-based WhatsApp automation.
"""

from __future__ import annotations

import os
import subprocess
import logging
from typing import Literal
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)


class ComputerAction(BaseModel):
    action_type: Literal["open_app", "open_folder", "whatsapp_message", "unknown"] = Field(
        description="The classification of the computer/desktop action request."
    )
    target: str = Field(
        description="The app name (e.g., 'vscode', 'chrome'), absolute path to folder, or contact name for WhatsApp"
    )
    message: str = Field(
        description="The text message content to send (only for whatsapp_message action_type)",
        default=""
    )


COMPUTER_SYSTEM_PROMPT = """You are the **Computer Use Agent** for Uday AI, a personal AI Operating System.
Your job is to analyze the user's desktop/browser action command and classify it into a structured format.

Actions available:
1. `open_app` - Opens desktop programs like VS Code ('vscode', 'vs code', 'code'), Chrome ('chrome'), etc.
2. `open_folder` - Opens a directory/folder or file path in the file explorer.
3. `whatsapp_message` - Launches WhatsApp Web to send a message to a contact.
4. `unknown` - Used when the instruction is not clear.

Map the instruction to the correct action type, target, and message parameters.
"""


async def run_computer_agent(state: AgentState) -> dict:
    """Run the computer/OS automation agent."""
    messages = state.get("messages", [])
    argument = messages[-1].content if messages else ""

    logger.info(f"[Computer Agent] Input: {argument[:80]}")

    llm = get_llm(temperature=0.1)

    try:
        structured_llm = llm.with_structured_output(ComputerAction)
        action_res = await structured_llm.ainvoke([
            SystemMessage(content=COMPUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"Instruction: {argument}")
        ])
        action_type = action_res.action_type
        target = action_res.target
        message = action_res.message
    except Exception as e:
        logger.error(f"[Computer Agent] Failed to parse structured output: {e}")
        # Basic fallback parsing
        action_type = "unknown"
        target = ""
        message = ""
        arg_lower = argument.lower()
        if "message" in arg_lower or "whatsapp" in arg_lower:
            action_type = "whatsapp_message"
            import re
            match = re.search(r"message\s+(\w+)\s+(.+)", argument, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                message = match.group(2).strip()
        elif "open" in arg_lower:
            if "folder" in arg_lower or "directory" in arg_lower or "\\" in argument or "/" in argument:
                action_type = "open_folder"
                target = argument.replace("open folder", "").replace("open", "").strip()
            else:
                action_type = "open_app"
                target = argument.replace("open", "").strip()

    result_text = ""

    if action_type == "open_app":
        app_name = target.lower().strip()
        
        # 1. Shell character filter to prevent injection
        import re
        if re.search(r"[&\|;\$><`!\r\n]", target):
            logger.warning(f"[Computer Agent] Blocked command execution with shell characters: {target}")
            result_text = "❌ **Command Execution Blocked**\n\nSecurity filter blocked command execution due to presence of dangerous shell characters."
            return {
                "agent_results": {
                    **state.get("agent_results", {}),
                    "computer_agent": {"response": result_text, "action": action_type, "target": target},
                },
                "final_response": result_text,
                "messages": [AIMessage(content=result_text)],
            }
            
        try:
            if any(w in app_name for w in ["vscode", "vs code", "code"]):
                subprocess.Popen(["code"])
                result_text = "💻 **VS Code Opened**\n\nI have successfully launched VS Code for you."
            elif "chrome" in app_name:
                if os.name == "nt":
                    subprocess.Popen(["cmd.exe", "/c", "start chrome"])
                else:
                    subprocess.Popen(["google-chrome"])
                result_text = "💻 **Google Chrome Opened**\n\nI have successfully launched Google Chrome."
            else:
                import shlex
                cmd_args = shlex.split(target)
                if cmd_args:
                    subprocess.Popen(cmd_args)
                    result_text = f"💻 **Command Executed**\n\nI have launched the application or run command: `{target}`"
                else:
                    result_text = "❌ **Command Execution Failed**\n\nEmpty command targeted."
        except Exception as err:
            logger.error(f"[Computer Agent] Open app failed: {err}")
            result_text = f"❌ **Failed to Open App**\n\nError attempting to open `{target}`: {err}"

    elif action_type == "open_folder":
        folder_path = os.path.expandvars(target)
        try:
            abs_path = os.path.abspath(folder_path)
            
            # Check for path traversal elements
            if ".." in folder_path or not os.path.exists(abs_path):
                raise ValueError("Path traversal attempt or invalid directory path detected.")
                
            # Block access to system-critical directories
            if os.name == "nt":
                forbidden_dirs = [
                    os.environ.get("SystemRoot", "C:\\Windows").lower(),
                    "c:\\windows",
                    "c:\\program files",
                    "c:\\program files (x86)",
                    "c:\\users\\all users",
                    "c:\\programdata"
                ]
                abs_path_lower = abs_path.lower()
                if any(abs_path_lower.startswith(fd) for fd in forbidden_dirs):
                    raise PermissionError("Access to system-critical directories or system files is restricted.")
            else:
                forbidden_dirs = ["/etc", "/bin", "/sbin", "/usr", "/var", "/lib", "/sys", "/proc", "/root"]
                abs_path_lower = abs_path.lower()
                if any(abs_path_lower.startswith(fd) for fd in forbidden_dirs):
                    raise PermissionError("Access to system-critical directories or system files is restricted.")

            if os.name == "nt":
                os.startfile(abs_path)
            else:
                subprocess.Popen(["xdg-open", abs_path])
            result_text = f"📂 **Folder/File Opened**\n\nI have opened the folder or file at: `{abs_path}`"
        except Exception as err:
            logger.error(f"[Computer Agent] Open folder failed: {err}")
            result_text = f"❌ **Failed to Open Folder**\n\nError attempting to open folder: {err}"

    elif action_type == "whatsapp_message":
        # Check safety/approval status before execution
        if not state.get("approved"):
            # Intercepted! Returns approval required
            return {
                "approval_required": True,
                "final_response": f"I need your approval to send a WhatsApp message to {target}.",
                "messages": [AIMessage(content=f"[Approval Required] Send WhatsApp message to {target}: {message}")]
            }

        # Approved! Run browser-based WhatsApp automation using Playwright
        try:
            result_text = await run_whatsapp_automation(target, message)
        except Exception as play_err:
            logger.error(f"[Computer Agent] Playwright WhatsApp automation failed: {play_err}")
            result_text = f"❌ **WhatsApp Automation Failed**\n\nError running Playwright: {play_err}"

    else:
        result_text = f"💻 **Computer Use Action Unknown**\n\nI couldn't classify or execute the computer command: `{argument}`."

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "computer_agent": {"response": result_text, "action": action_type, "target": target},
        },
        "final_response": result_text,
        "messages": [AIMessage(content=result_text)],
    }


async def run_whatsapp_automation(contact_name: str, message: str) -> str:
    """Automates WhatsApp Web using Playwright."""
    from playwright.async_api import async_playwright
    from pathlib import Path

    # Persistent context directory to save login QR code session
    context_dir = Path("./data/playwright_whatsapp")
    context_dir.mkdir(parents=True, exist_ok=True)

    browser = None
    try:
        async with async_playwright() as p:
            # Launch persistent context browser (use remote browserless CDP if configured)
            from app.config import get_settings
            settings = get_settings()

            if settings.browserless_url:
                logger.info(f"[Computer Agent] Connecting to browserless instance at {settings.browserless_url}...")
                browser = await p.chromium.connect_over_cdp(settings.browserless_url)
                context = browser.contexts[0] if browser.contexts else await browser.new_context(viewport={"width": 1280, "height": 800})
                page = await context.new_page()
            else:
                browser = await p.chromium.launch_persistent_context(
                    user_data_dir=str(context_dir),
                    headless=True,
                    viewport={"width": 1280, "height": 800}
                )
                page = browser.pages[0] if browser.pages else await browser.new_page()
            logger.info("[Computer Agent] Navigating to WhatsApp Web...")
            await page.goto("https://web.whatsapp.com/", wait_until="networkidle", timeout=30000)

            # Wait to check if logged in (div[data-tab="3"] is chat search or canvas QR is visible)
            try:
                # Check for QR canvas
                qr_canvas = await page.query_selector("canvas")
                if qr_canvas:
                    # Save screenshot of QR code for the user to scan
                    screenshot_path = Path("./data/uploads/whatsapp_login.png")
                    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(screenshot_path))
                    return (
                        "⚠️ **WhatsApp Scan Required**\n\n"
                        "You are not logged in to WhatsApp Web.\n"
                        "Please scan the QR code to log in. I have saved a screenshot of the QR code to: "
                        "`data/uploads/whatsapp_login.png`."
                    )
            except Exception as check_err:
                logger.debug(f"Checked QR Canvas with exception (probably logged in): {check_err}")

            # Search for contact
            search_selectors = [
                'div[contenteditable="true"][data-tab="3"]',
                'div[data-tab="3"]',
                'input[placeholder="Search or start new chat"]'
            ]

            search_box = None
            for sel in search_selectors:
                try:
                    search_box = await page.wait_for_selector(sel, timeout=10000)
                    if search_box:
                        break
                except Exception:
                    continue

            if not search_box:
                # Save debug screenshot
                err_screenshot = Path("./data/uploads/whatsapp_error.png")
                await page.screenshot(path=str(err_screenshot))
                return "❌ **WhatsApp Timeout**\n\nCould not locate the search box. Screenshot saved to `data/uploads/whatsapp_error.png`."

            # Search and Select contact
            await search_box.click()
            await search_box.fill("")
            await search_box.type(contact_name)
            await page.wait_for_timeout(2000)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)

            # Locate message box
            message_selectors = [
                'div[contenteditable="true"][data-tab="10"]',
                'div[data-tab="10"]',
                'footer div[contenteditable="true"]'
            ]

            message_box = None
            for sel in message_selectors:
                try:
                    message_box = await page.wait_for_selector(sel, timeout=5000)
                    if message_box:
                        break
                except Exception:
                    continue

            if not message_box:
                return f"❌ **Contact Not Found**\n\nCould not focus chat for contact: `{contact_name}`."

            # Send message
            await message_box.click()
            await message_box.type(message)
            await page.wait_for_timeout(1000)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2000)  # Wait for send completion

            return f"✅ **WhatsApp Message Sent!**\n\nMessage successfully sent to `{contact_name}`: \"{message}\"."
    finally:
        if browser:
            await browser.close()
