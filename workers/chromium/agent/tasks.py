from typing import Any

from agent import kick
from agent.browser import BrowserRuntime
from agent.client import Controller
from agent.scripts import run_steps
from agent.settings import settings


async def execute(runtime: BrowserRuntime, ctl: Controller, claimed: dict[str, Any]) -> dict[str, Any]:
    task = claimed["task"]
    creds = claimed.get("credentials") or {}
    storage = claimed.get("storage_state")
    payload = task.get("payload") or {}
    ttype = task["type"]
    page = await runtime.ensure()
    if storage and ttype == "login":
        page = await runtime.start(storage)

    result: dict[str, Any] = {}
    account_status = None

    if ttype == "start_browser":
        page = await runtime.start(storage)
        result = {"url": page.url}
    elif ttype == "stop_browser":
        await runtime.stop()
        result = {"stopped": True}
    elif ttype == "login":
        page = await runtime.ensure()
        await kick.login(page, creds.get("username") or "", creds.get("password") or "")
        if payload.get("channel"):
            await kick.goto_channel(page, payload["channel"])
        account_status = "session_live"
        result = {"url": page.url}
    elif ttype == "open_channel":
        await kick.goto_channel(page, payload["channel"])
        await kick.wait_chat(page)
        result = {"url": page.url}
    elif ttype == "send_message":
        if payload.get("channel") and page.url.rstrip("/") != kick.channel_url(payload["channel"]).rstrip("/"):
            await kick.goto_channel(page, payload["channel"])
            await kick.wait_chat(page)
        await kick.send_chat(page, payload["text"])
        await ctl.ingest_chat(
            {
                "account_id": task.get("account_id"),
                "worker_id": settings.worker_id,
                "channel": payload.get("channel", ""),
                "direction": "out",
                "body": payload.get("text", ""),
            }
        )
        result = {"sent": True}
    elif ttype == "run_script":
        result = {"steps": await run_steps(page, payload.get("steps") or [], payload.get("channel"))}
    elif ttype == "inspect":
        snap = await runtime.accessibility_snapshot()
        result = {"url": page.url, "title": await page.title(), "accessibility": snap}
    elif ttype == "screenshot":
        snap = await runtime.screenshot_b64()
        result = {"snapshot_b64": snap}
    elif ttype == "restart":
        await runtime.stop()
        page = await runtime.start(storage)
        result = {"restarted": True}
    else:
        raise ValueError(f"unknown task type {ttype}")

    state = await runtime.storage_state()
    return {
        "status": "done",
        "result": result,
        "storage_state": state,
        "account_status": account_status,
        "health_delta": 1 if ttype != "stop_browser" else 0,
    }
