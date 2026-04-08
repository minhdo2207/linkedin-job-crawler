"""
LinkedIn Software Engineer Job Crawler
Crawl jobs theo cấp độ từ LinkedIn

Usage:
    # Crawl tất cả cấp độ
    python main.py

    # Crawl cấp độ cụ thể
    python main.py --levels entry mid_senior

    # Chỉ lấy danh sách, không lấy chi tiết (nhanh hơn)
    python main.py --no-details

    # Đăng nhập trước khi crawl
    python main.py --login

    # Đăng nhập thủ công (nếu bị CAPTCHA)
    python main.py --manual-login
"""
import argparse
import asyncio
import sys

from rich.console import Console
from rich.panel import Panel

from auth import is_logged_in, auto_login, manual_login
from config import EXPERIENCE_LEVELS
from crawler import LinkedInJobCrawler
from storage import print_sample_jobs, print_summary, save_jobs

console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Crawl LinkedIn Software Engineer Jobs theo cấp độ"
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        choices=list(EXPERIENCE_LEVELS.keys()),
        default=None,
        help="Cấp độ cần crawl (mặc định: tất cả)",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        default=False,
        help="Không crawl trang chi tiết job (nhanh hơn nhưng ít thông tin hơn)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Chạy browser ở chế độ headless (mặc định: True)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        default=False,
        help="Hiện browser khi crawl",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        default=False,
        help="Đăng nhập tự động trước khi crawl",
    )
    parser.add_argument(
        "--manual-login",
        action="store_true",
        default=False,
        help="Mở browser để đăng nhập thủ công",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        default=False,
        help="In mẫu jobs sau khi crawl",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    console.print(Panel.fit(
        "[bold cyan]🔍 LinkedIn Software Engineer Job Crawler[/bold cyan]\n"
        "[dim]Crawl jobs theo cấp độ: Intern → Junior → Mid → Senior → Director[/dim]",
        border_style="cyan",
    ))

    # ── Xử lý authentication ───────────────────────────────────────────────────
    if args.manual_login:
        await manual_login()
        console.print("[green]✅ Đã lưu session. Chạy lại không có --manual-login để crawl.[/green]")
        return

    if args.login:
        success = await auto_login()
        if not success:
            console.print("[red]❌ Đăng nhập thất bại. Thử --manual-login để đăng nhập thủ công.[/red]")
            sys.exit(1)

    if not is_logged_in():
        console.print("[yellow]⚠ Chưa phát hiện browser profile (session LinkedIn).[/yellow]")
        console.print("[yellow]  Chạy: python main.py --manual-login[/yellow]")
        console.print("[yellow]  Hoặc: python main.py --login (nếu đã cấu hình .env)[/yellow]")
        console.print()

        # Hỏi user có muốn tiếp tục không
        confirm = input("Tiếp tục crawl mà không có session? (có thể bị redirect login) [y/N]: ")
        if confirm.lower() != "y":
            sys.exit(0)

    # ── Cấu hình crawler ───────────────────────────────────────────────────────
    levels = args.levels or list(EXPERIENCE_LEVELS.keys())
    headless = not args.no_headless
    fetch_details = not args.no_details

    console.print(f"\n[bold]Cấu hình:[/bold]")
    console.print(f"  Cấp độ: {', '.join(levels)}")
    console.print(f"  Lấy chi tiết: {'Có' if fetch_details else 'Không'}")
    console.print(f"  Chế độ browser: {'Headless' if headless else 'Hiển thị'}")
    console.print()

    # ── Chạy crawler ───────────────────────────────────────────────────────────
    crawler = LinkedInJobCrawler(levels=levels, headless=headless)

    try:
        all_jobs = await crawler.run(fetch_details=fetch_details)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Dừng crawler theo yêu cầu...[/yellow]")
        all_jobs = crawler.all_jobs  # Lưu những gì đã crawl được

    if not all_jobs:
        console.print("[red]❌ Không crawl được job nào.[/red]")
        sys.exit(1)

    # ── Lưu kết quả ───────────────────────────────────────────────────────────
    console.print("\n[bold]💾 Lưu kết quả...[/bold]")
    saved_files = save_jobs(all_jobs)

    # ── Hiển thị tóm tắt ───────────────────────────────────────────────────────
    print_summary(all_jobs)

    if args.sample:
        print_sample_jobs(all_jobs, n=3)

    console.print("\n[bold green]🎉 Hoàn thành![/bold green]")
    console.print(f"Files đã lưu tại: [cyan]{saved_files.get('combined_csv', 'N/A')}[/cyan]")


if __name__ == "__main__":
    asyncio.run(main())
