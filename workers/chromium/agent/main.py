import asyncio
import json
from typing import Any

import redis.asyncio as redis

from agent.browser import BrowserRuntime
from agent.client import Controller
from agent.health import metrics
from agent.kick import attach_chat_listener, current_channel
from agent.settings import settings
from agent.tasks import execute


async def heartbeat_loop(runtime: BrowserRuntime, ctl: Controller) -> None:
    while True:
        try:
            m = metrics()
            snap = None
            try:
                snap = await runtime.screenshot_b64()
            except Exception:
                snap = None
            await ctl.heartbeat(
                {
                    "id": settings.worker_id,
                    "name": settings.worker_name,
                    "status": "busy" if runtime.busy else "idle",
                    "cpu_percent": m["cpu_percent"],
                    "ram_mb": m["ram_mb"],
                    "ram_limit_mb": m["ram_limit_mb"],
                    "novnc_url": settings.novnc_public_url,
                    "vnc_port": 5900,
                    "labels": {"engine": "chromium", "isolation": "container"},
                    "snapshot_jpeg_b64": snap,
                }
            )
        except Exception as exc:
            print(f"heartbeat failed: {exc}", flush=True)
        await asyncio.sleep(4)


async def on_chat(ctl: Controller, page: Any, text: str) -> None:
    await ctl.ingest_chat(
        {
            "worker_id": settings.worker_id,
            "channel": current_channel(page),
            "direction": "in",
            "body": text,
        }
    )


async def run_claimed(runtime: BrowserRuntime, ctl: Controller, claimed: dict[str, Any]) -> None:
    task = claimed.get("task")
    if not task:
        return
    task_id = task["id"]
    runtime.busy = True
    try:
        await ctl.log("info", f"running {task['type']}", {"task_id": task_id})
        body = await execute(runtime, ctl, claimed)
        await ctl.report(task_id, body)
        if runtime.page:
            await attach_chat_listener(runtime.page, lambda text: asyncio.create_task(on_chat(ctl, runtime.page, text)))
        await ctl.log("info", f"finished {task['type']}", {"task_id": task_id})
    except Exception as exc:
        await ctl.report(task_id, {"status": "error", "error": str(exc), "account_status": "error", "health_delta": -10})
        await ctl.log("error", str(exc), {"task_id": task_id})
    finally:
        runtime.busy = False


async def worker_loop(runtime: BrowserRuntime, ctl: Controller) -> None:
    r = redis.from_url(settings.redis_url, decode_responses=False)
    key = f"fleet.tasks:{settings.worker_id}"
    while True:
        item = await r.brpop(key, timeout=5)
        task_id = None
        if item:
            _, raw = item
            payload = json.loads(raw)
            task_id = payload.get("task_id")
        claimed = await ctl.claim(task_id)
        if claimed.get("task"):
            await run_claimed(runtime, ctl, claimed)
        else:
            # poll fallback if redis missed
            await asyncio.sleep(0.2)


async def main() -> None:
    ctl = Controller()
    runtime = BrowserRuntime()
    await ctl.log("info", "worker starting")
    await runtime.start()
    await ctl.log("info", "chromium session live")
    try:
        await asyncio.gather(heartbeat_loop(runtime, ctl), worker_loop(runtime, ctl))
    finally:
        await runtime.stop()
        await ctl.close()


if __name__ == "__main__":
    asyncio.run(main())
