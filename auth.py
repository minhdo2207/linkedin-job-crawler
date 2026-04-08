"""
LinkedIn Authentication Module
Xử lý login và lưu session vào browser profile
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright
from rich.console import Console

from config import BROWSER_PROFILE_DIR, LINKEDIN_EMAIL, LINKEDIN_PASSWORD

console = Console()

WAIT_SECONDS = 120  # Thời gian chờ user login


async def manual_login(wait: int = WAIT_SECONDS):
    """
    Dùng Playwright trực tiếp để mở browser và giữ cho đến khi login xong.
    Browser profile được lưu để dùng lại cho crawler.
    """
    profile_path = Path(BROWSER_PROFILE_DIR).resolve()
    profile_path.mkdir(parents=True, exist_ok=True)

    console.print("[cyan]🌐 Mở browser để đăng nhập LinkedIn...[/cyan]")
    console.print(f"[yellow]⏳ Bạn có {wait} giây để đăng nhập.[/yellow]")
    console.print("[dim]  Browser sẽ tự đóng sau khi login xong hoặc hết giờ.[/dim]\n")

    async with async_playwright() as p:
        # Dùng persistent context = lưu cookies/session tự động
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")

        # Đếm ngược và kiểm tra login thành công
        for elapsed in range(0, wait, 5):
            await asyncio.sleep(5)
            remaining = wait - elapsed - 5

            try:
                current_url = page.url
                # Nếu đã redirect về feed = login thành công
                if "feed" in current_url or "mynetwork" in current_url or "jobs" in current_url:
                    console.print("[green]✅ Phát hiện đăng nhập thành công![/green]")
                    await asyncio.sleep(2)  # Đợi cookies được lưu
                    break

                if remaining > 0:
                    console.print(f"[dim]  Đang chờ... còn {remaining}s[/dim]", end="\r")
            except Exception:
                break

        await context.close()

    console.print(f"\n[green]✅ Session đã lưu tại: {profile_path}[/green]")
    console.print("[cyan]Bây giờ chạy: python main.py[/cyan]")


async def auto_login() -> bool:
    """Login tự động bằng email/password từ .env."""
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        console.print("[red]❌ Chưa cấu hình LINKEDIN_EMAIL / LINKEDIN_PASSWORD trong .env[/red]")
        return False

    profile_path = Path(BROWSER_PROFILE_DIR).resolve()
    profile_path.mkdir(parents=True, exist_ok=True)

    console.print("[cyan]🔐 Tự động đăng nhập LinkedIn...[/cyan]")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        await page.wait_for_load_state("networkidle")

        # Điền form
        await page.fill("#username", LINKEDIN_EMAIL)
        await asyncio.sleep(0.5)
        await page.fill("#password", LINKEDIN_PASSWORD)
        await asyncio.sleep(0.5)
        await page.click('button[type="submit"]')

        # Chờ redirect
        try:
            await page.wait_for_url("**/feed/**", timeout=15000)
            console.print("[green]✅ Đăng nhập thành công![/green]")
            await asyncio.sleep(2)
            await context.close()
            return True
        except Exception:
            console.print("[yellow]⚠ Có thể bị CAPTCHA hoặc xác minh 2 bước.[/yellow]")
            console.print(f"[yellow]  Chờ thêm {WAIT_SECONDS}s để xử lý thủ công...[/yellow]")

            # Cho thêm thời gian xử lý thủ công
            for _ in range(WAIT_SECONDS // 5):
                await asyncio.sleep(5)
                if "feed" in page.url:
                    console.print("[green]✅ Đăng nhập thành công![/green]")
                    await asyncio.sleep(2)
                    await context.close()
                    return True

            await context.close()
            return False


def is_logged_in() -> bool:
    """Kiểm tra đã có browser profile chưa."""
    profile_path = Path(BROWSER_PROFILE_DIR)
    return profile_path.exists() and any(profile_path.iterdir())


if __name__ == "__main__":
    asyncio.run(manual_login())
