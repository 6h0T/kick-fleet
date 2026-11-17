from playwright.async_api import Page

from agent import kick


async def run_steps(page: Page, steps: list[dict], channel: str | None = None) -> list[dict]:
    log: list[dict] = []
    for step in steps:
        action = step.get("action")
        if action == "goto":
            await page.goto(step["url"], wait_until="domcontentloaded")
        elif action == "goto_channel":
            await kick.goto_channel(page, step.get("channel") or channel or "")
        elif action == "wait":
            await page.wait_for_selector(step["selector"], timeout=step.get("timeout_ms", 15000))
        elif action == "wait_chat":
            await kick.wait_chat(page, step.get("timeout_ms", 20000))
        elif action == "click":
            await page.click(step["selector"])
        elif action == "type":
            await page.fill(step["selector"], step.get("text", ""))
        elif action == "press":
            await page.keyboard.press(step["key"])
        elif action == "send_chat":
            await kick.send_chat(page, step.get("text", ""))
        elif action == "listen":
            await page.wait_for_timeout(int(step.get("duration_ms", 5000)))
        elif action == "wait_ms":
            await page.wait_for_timeout(int(step.get("ms", 1000)))
        else:
            raise ValueError(f"unknown script action: {action}")
        log.append({"action": action, "ok": True})
    return log
