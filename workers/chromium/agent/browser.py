from pathlib import Path

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from agent.settings import settings


class BrowserRuntime:
    def __init__(self) -> None:
        self._pw: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.busy = False

    async def start(self, storage_state: dict | None = None) -> Page:
        await self.stop()
        self._pw = await async_playwright().start()
        Path(settings.profile_dir).mkdir(parents=True, exist_ok=True)
        args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-position=0,0",
            f"--window-size={settings.screen_width},{settings.screen_height}",
            "--disable-blink-features=AutomationControlled",
        ]
        ext = settings.claude_extension_dir.strip()
        if ext and Path(ext).exists():
            args += [f"--load-extension={ext}", f"--disable-extensions-except={ext}"]
        launch = dict(
            user_data_dir=settings.profile_dir,
            headless=not settings.headed,
            args=args,
            viewport={"width": settings.screen_width, "height": settings.screen_height},
            ignore_default_args=["--enable-automation"],
        )
        if storage_state:
            # persistent context cannot take storage_state at launch; apply cookies after
            self.context = await self._pw.chromium.launch_persistent_context(**launch)
            await self.context.add_cookies(storage_state.get("cookies") or [])
        else:
            self.context = await self._pw.chromium.launch_persistent_context(**launch)
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        return self.page

    async def ensure(self) -> Page:
        if self.page and not self.page.is_closed():
            return self.page
        return await self.start()

    async def storage_state(self) -> dict | None:
        if not self.context:
            return None
        return await self.context.storage_state()

    async def screenshot_b64(self) -> str | None:
        if not self.page or self.page.is_closed():
            return None
        raw = await self.page.screenshot(type="jpeg", quality=42, full_page=False)
        import base64

        return base64.b64encode(raw).decode()

    async def accessibility_snapshot(self) -> dict | None:
        if not self.page:
            return None
        return await self.page.accessibility.snapshot()

    async def stop(self) -> None:
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
        if self._pw:
            try:
                await self._pw.stop()
            except Exception:
                pass
        self.context = None
        self.page = None
        self._pw = None
