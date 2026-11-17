import re
from typing import Callable
from urllib.parse import urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from agent.settings import settings

CHAT_INPUT = [
    'textarea[placeholder*="Send a message" i]',
    'textarea[placeholder*="Chat" i]',
    '[data-testid="chat-input"]',
    '[contenteditable="true"][role="textbox"]',
    "textarea",
]
LOGIN_USER = [
    'input[name="email"]',
    'input[name="username"]',
    'input[type="email"]',
    'input[placeholder*="email" i]',
    'input[placeholder*="username" i]',
]
LOGIN_PASS = ['input[type="password"]', 'input[name="password"]']


async def first_visible(page: Page, selectors: list[str], timeout: int = 8000):
    last = None
    for sel in selectors:
        loc = page.locator(sel).first
        try:
            await loc.wait_for(state="visible", timeout=timeout)
            return loc
        except PlaywrightTimeout as exc:
            last = exc
    if last:
        raise last
    raise RuntimeError("no selector matched")


def channel_url(channel: str) -> str:
    channel = channel.strip().lstrip("/")
    if channel.startswith("http"):
        return channel
    return f"{settings.kick_base_url.rstrip('/')}/{channel}"


def current_channel(page: Page) -> str:
    """Channel slug from the page URL, or '' when not on a channel page."""
    try:
        path = urlparse(page.url).path.strip("/")
        return path.split("/")[0] if path else ""
    except Exception:
        return ""


async def goto_channel(page: Page, channel: str) -> None:
    await page.goto(channel_url(channel), wait_until="domcontentloaded")
    await page.wait_for_timeout(1500)


async def wait_chat(page: Page, timeout_ms: int = 20000) -> None:
    await first_visible(page, CHAT_INPUT, timeout=timeout_ms)


async def send_chat(page: Page, text: str) -> None:
    box = await first_visible(page, CHAT_INPUT, timeout=12000)
    await box.click()
    await box.fill("")
    await box.type(text, delay=15)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(400)


async def login(page: Page, username: str, password: str) -> None:
    await page.goto(settings.kick_base_url, wait_until="domcontentloaded")
    for label in ["Log In", "Login", "Sign in"]:
        btn = page.get_by_role("button", name=re.compile(label, re.I))
        if await btn.count():
            await btn.first.click()
            break
    user = await first_visible(page, LOGIN_USER, timeout=12000)
    await user.fill(username)
    pwd = await first_visible(page, LOGIN_PASS, timeout=8000)
    await pwd.fill(password)
    submit = page.get_by_role("button", name=re.compile("log in|login|sign in", re.I))
    if await submit.count():
        await submit.first.click()
    else:
        await pwd.press("Enter")
    await page.wait_for_timeout(4000)


async def attach_chat_listener(page: Page, on_message: Callable) -> None:
    try:
        await page.expose_function("__kickFleetOnChat", on_message)
    except Exception:
        pass  # already registered on this page; re-inject the observer below
    await page.evaluate(
        """() => {
          if (window.__kickFleetObserver) return;
          const take = () => {
            const nodes = document.querySelectorAll('[class*="chat"] [class*="message"], [data-chat-entry], .chat-entry');
            return nodes;
          };
          const seen = new Set();
          const emit = () => {
            take().forEach((el) => {
              const text = (el.innerText || '').trim();
              if (!text || seen.has(text)) return;
              seen.add(text);
              window.__kickFleetOnChat(text);
            });
          };
          window.__kickFleetObserver = new MutationObserver(emit);
          window.__kickFleetObserver.observe(document.body, { childList: true, subtree: true });
        }"""
    )
