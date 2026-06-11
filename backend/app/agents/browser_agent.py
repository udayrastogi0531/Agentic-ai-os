"""
Uday AI — Browser Agent (Playwright / Computer Use)

Automates web browsing, extracting content, filling forms, clicking elements,
and downloading files. Uses Playwright with a fallback HTTP scraper.
"""

from __future__ import annotations

import re
import logging
from bs4 import BeautifulSoup  # Wait, bs4 is not in requirements.txt, we will use Python's built-in html.parser
import urllib.parse
from html.parser import HTMLParser
from io import StringIO

import httpx
from langchain_core.messages import AIMessage
from app.agents.state import AgentState

logger = logging.getLogger(__name__)


# ── Simple HTML Stripper (built-in fallback) ──────────────────────────

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_html_tags(html: str) -> str:
    """Extract clean raw text from HTML string."""
    s = HTMLTextExtractor()
    s.feed(html)
    text = s.get_data()
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── Playwright Browser Automation Core ────────────────────────────────

async def playwright_browser_action(
    action: str,
    url: str | None = None,
    selector: str | None = None,
    value: str | None = None
) -> dict:
    """Perform a real browser action using Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.warning("[Browser Agent] Playwright library not installed. Falling back to HTTP.")
        return {"success": False, "error": "Playwright is not installed."}

    try:
        async with async_playwright() as p:
            # Start headless browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"[Browser Agent] Playwright page opened for action '{action}'")

            if action == "open" or action == "extract" or action == "summarize":
                if not url:
                    return {"success": False, "error": "URL is missing."}
                await page.goto(url, wait_until="networkidle", timeout=10000)
                content = await page.content()
                title = await page.title()
                await browser.close()
                return {"success": True, "title": title, "content": content}

            elif action == "click":
                if not url or not selector:
                    return {"success": False, "error": "URL or Selector is missing."}
                await page.goto(url, wait_until="networkidle", timeout=10000)
                await page.click(selector, timeout=5000)
                await page.wait_for_timeout(2000) # Wait for page changes
                content = await page.content()
                title = await page.title()
                await browser.close()
                return {"success": True, "title": title, "content": content}

            elif action == "fill":
                if not url or not selector or not value:
                    return {"success": False, "error": "URL, Selector, or Value is missing."}
                await page.goto(url, wait_until="networkidle", timeout=10000)
                await page.fill(selector, value, timeout=5000)
                await page.wait_for_timeout(2000)
                content = await page.content()
                title = await page.title()
                await browser.close()
                return {"success": True, "title": title, "content": content}
                
            elif action == "download":
                if not url:
                    return {"success": False, "error": "URL is missing."}
                # Setup download listener
                await page.goto(url, wait_until="networkidle", timeout=10000)
                async with page.expect_download() as download_info:
                    await page.goto(url) # or trigger download click
                download = await download_info.value
                path = f"./workspace/{download.suggested_filename}"
                await download.save_as(path)
                await browser.close()
                return {"success": True, "download_path": path}

            await browser.close()
            return {"success": False, "error": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"[Browser Agent] Playwright failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


# ── HTTP Scraper Fallback ─────────────────────────────────────────────

async def http_scraper_action(url: str) -> dict:
    """Fetch page raw HTML using HTTP request and clean it."""
    logger.info(f"[Browser Agent] HTTP Scraper fallback triggered for {url}")
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                return {
                    "success": True,
                    "title": "HTTP Page Scraped",
                    "content": res.text
                }
            return {"success": False, "error": f"HTTP status code {res.status_code}"}
    except Exception as e:
        logger.error(f"[Browser Agent] HTTP Scraper failed: {e}")
        return {"success": False, "error": str(e)}


# ── Main Agent Runner ──────────────────────────────────────────────────

async def run_browser_agent(state: AgentState) -> dict:
    """Run the browser agent."""
    messages = state.get("messages", [])
    argument = messages[-1].content if messages else ""

    logger.info(f"Browser agent input: {argument[:80]}")

    # Parse command intent
    # Formats: 
    # - open https://example.com
    # - click #button-id on https://example.com
    # - fill #input-id value on https://example.com
    # - extract https://example.com
    # - download https://example.com/file.pdf
    
    action = "extract"
    url = None
    selector = None
    value = None

    arg_lower = argument.lower()
    
    # Simple regex parsing for commands
    if arg_lower.startswith("open "):
        action = "open"
        url = argument[5:].strip()
    elif arg_lower.startswith("extract "):
        action = "extract"
        url = argument[8:].strip()
    elif arg_lower.startswith("summarize "):
        action = "summarize"
        url = argument[10:].strip()
    elif arg_lower.startswith("download "):
        action = "download"
        url = argument[9:].strip()
    elif "click " in arg_lower:
        action = "click"
        match = re.search(r"click\s+(.+?)\s+on\s+(https?://\S+)", argument, re.IGNORECASE)
        if match:
            selector = match.group(1).strip()
            url = match.group(2).strip()
    elif "fill " in arg_lower:
        action = "fill"
        match = re.search(r"fill\s+(.+?)\s+with\s+(.+?)\s+on\s+(https?://\S+)", argument, re.IGNORECASE)
        if match:
            selector = match.group(1).strip()
            value = match.group(2).strip()
            url = match.group(3).strip()

    # Fallback to standard URL extraction if not matching formats
    if not url:
        urls = re.findall(r'https?://\S+', argument)
        if urls:
            url = urls[0]
        else:
            # If no URL is provided, treat the query as a search engine query
            encoded_query = urllib.parse.quote_plus(argument)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            action = "extract"

    logger.info(f"[Browser Agent] Selected action: {action} on {url}")

    # Run Playwright
    playwright_res = await playwright_browser_action(action, url, selector, value)
    
    # Fallback to HTTP if Playwright is unavailable or fails
    if not playwright_res["success"]:
        if action in ("open", "extract", "summarize") and url:
            scrape_res = await http_scraper_action(url)
        else:
            scrape_res = playwright_res # Return the Playwright error
    else:
        scrape_res = playwright_res

    # Build response
    if scrape_res["success"]:
        if "download_path" in scrape_res:
            response_text = f"📥 **Download Completed**\n\nThe file was saved successfully to: `{scrape_res['download_path']}`"
        else:
            raw_html = scrape_res.get("content", "")
            title = scrape_res.get("title", "Webpage")
            
            # Clean HTML to text
            clean_text = strip_html_tags(raw_html)
            
            # Substring preview to avoid blowing up context window
            preview_text = clean_text[:4000]
            
            if action == "summarize":
                from app.llm.provider import get_llm
                from langchain_core.messages import SystemMessage, HumanMessage
                
                llm = get_llm(temperature=0.3)
                summary_prompt = "You are a summarizing assistant. Summarize the following webpage content concisely."
                summary_res = await llm.ainvoke([
                    SystemMessage(content=summary_prompt),
                    HumanMessage(content=f"Title: {title}\nContent:\n{preview_text}")
                ])
                response_text = f"🌐 **Webpage Summary: {title}**\n\n{summary_res.content}"
            else:
                response_text = f"🌐 **Scraped Webpage: {title}**\n\n{preview_text}..."
    else:
        response_text = f"❌ **Browser Action Failed**\n\nError: {scrape_res.get('error', 'Unknown error')}"

    return {
        "agent_results": {
            **state.get("agent_results", {}),
            "browser_agent": {"response": response_text, "action": action, "url": url},
        },
        "final_response": response_text,
        "messages": [AIMessage(content=response_text)],
    }
