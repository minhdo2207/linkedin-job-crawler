"""
LinkedIn Job Crawler - Core Module
Crawl danh sách job theo từng cấp độ từ LinkedIn
"""
import asyncio
import json
from pathlib import Path
from typing import Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from config import (
    BROWSER_PROFILE_DIR,
    DELAY_BETWEEN_REQUESTS,
    EXPERIENCE_LEVELS,
    MAX_JOBS_PER_LEVEL,
    build_search_url,
)
from extractor import (
    JOB_CARD_SCHEMA,
    JOB_DETAIL_SCHEMA,
    JobListing,
    enrich_job_from_detail,
    parse_job_cards,
)

console = Console()

# JS để scroll và load thêm job cards
SCROLL_AND_LOAD_JS = """
async function scrollAndLoad() {
    const container = document.querySelector('.scaffold-layout__list');
    if (!container) return;

    let lastHeight = 0;
    let attempts = 0;
    const maxAttempts = 5;

    while (attempts < maxAttempts) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 2000));

        const newHeight = document.body.scrollHeight;
        if (newHeight === lastHeight) {
            attempts++;
        } else {
            attempts = 0;
            lastHeight = newHeight;
        }
    }
}
await scrollAndLoad();
"""

# JS để đóng popup nếu có
CLOSE_POPUP_JS = """
const closeBtn = document.querySelector('button[aria-label="Dismiss"]') ||
                 document.querySelector('.msg-overlay-bubble-header__control--close-btn') ||
                 document.querySelector('[data-test-modal-close-btn]');
if (closeBtn) closeBtn.click();
"""


class LinkedInJobCrawler:
    """Crawler chính để lấy job từ LinkedIn."""

    def __init__(self, levels: Optional[list[str]] = None, headless: bool = True):
        """
        Args:
            levels: Danh sách cấp độ cần crawl. None = tất cả cấp độ.
            headless: Chạy browser ở chế độ headless (không hiện UI).
        """
        self.levels = levels or list(EXPERIENCE_LEVELS.keys())
        self.headless = headless
        self.profile_path = Path(BROWSER_PROFILE_DIR).resolve()
        self.all_jobs: dict[str, list[JobListing]] = {}

    def _get_browser_config(self) -> BrowserConfig:
        return BrowserConfig(
            headless=self.headless,
            user_data_dir=str(self.profile_path),
            use_persistent_context=True,
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

    async def _crawl_job_list_page(
        self,
        crawler: AsyncWebCrawler,
        level_key: str,
        start: int = 0,
    ) -> list[dict]:
        """Crawl một trang danh sách job."""
        url = build_search_url(level_key, start)
        level_info = EXPERIENCE_LEVELS[level_key]

        extraction_strategy = JsonCssExtractionStrategy(JOB_CARD_SCHEMA, verbose=False)

        run_config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            js_code=[CLOSE_POPUP_JS, SCROLL_AND_LOAD_JS],
            wait_for="css:li.scaffold-layout__list-item",
            page_timeout=30000,
            cache_mode=CacheMode.BYPASS,  # Luôn lấy data mới
            delay_before_return_html=3.0,
        )

        try:
            result = await crawler.arun(url=url, config=run_config)

            if not result.success:
                console.print(f"[red]  ✗ Lỗi crawl trang {start}: {result.error_message}[/red]")
                return []

            if result.extracted_content:
                data = json.loads(result.extracted_content)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]

        except Exception as e:
            console.print(f"[red]  ✗ Exception khi crawl trang {start}: {e}[/red]")

        return []

    async def _crawl_job_detail(
        self,
        crawler: AsyncWebCrawler,
        job_url: str,
    ) -> dict:
        """Crawl trang chi tiết của một job."""
        if not job_url:
            return {}

        extraction_strategy = JsonCssExtractionStrategy(JOB_DETAIL_SCHEMA, verbose=False)

        run_config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            wait_for="css:h1.job-details-jobs-unified-top-card__job-title",
            page_timeout=20000,
            cache_mode=CacheMode.BYPASS,
            delay_before_return_html=2.0,
        )

        try:
            result = await crawler.arun(url=job_url, config=run_config)

            if result.success and result.extracted_content:
                data = json.loads(result.extracted_content)
                if isinstance(data, list) and data:
                    return data[0]
                elif isinstance(data, dict):
                    return data

        except Exception as e:
            console.print(f"[dim red]  Lỗi detail {job_url[:60]}...: {e}[/dim red]")

        return {}

    async def crawl_level(
        self,
        crawler: AsyncWebCrawler,
        level_key: str,
        fetch_details: bool = True,
    ) -> list[JobListing]:
        """Crawl tất cả job cho một cấp độ."""
        level_info = EXPERIENCE_LEVELS[level_key]
        jobs: list[JobListing] = []
        page_size = 25  # LinkedIn hiển thị 25 jobs/trang

        console.print(f"\n[bold cyan]📋 Crawling: {level_info['label']}[/bold cyan]")
        console.print(f"   Target: {MAX_JOBS_PER_LEVEL} jobs")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            list_task = progress.add_task(
                f"[cyan]Lấy danh sách jobs...", total=MAX_JOBS_PER_LEVEL
            )

            # Crawl các trang danh sách
            start = 0
            while len(jobs) < MAX_JOBS_PER_LEVEL:
                raw_items = await self._crawl_job_list_page(crawler, level_key, start)

                if not raw_items:
                    console.print(f"[yellow]  ⚠ Không còn job ở trang {start}[/yellow]")
                    break

                new_jobs = parse_job_cards(raw_items, level_key, level_info["label"])

                # Lọc bỏ job trùng URL
                existing_urls = {j.job_url for j in jobs}
                new_jobs = [j for j in new_jobs if j.job_url not in existing_urls]

                jobs.extend(new_jobs[:MAX_JOBS_PER_LEVEL - len(jobs)])
                progress.update(list_task, completed=len(jobs))

                console.print(f"  [dim]Trang {start//page_size + 1}: +{len(new_jobs)} jobs (tổng: {len(jobs)})[/dim]")

                if len(raw_items) < page_size:
                    break  # Không còn trang tiếp theo

                start += page_size
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

            # Fetch detail cho từng job
            if fetch_details and jobs:
                detail_task = progress.add_task(
                    f"[green]Lấy chi tiết...", total=len(jobs)
                )

                for i, job in enumerate(jobs):
                    if job.job_url:
                        detail = await self._crawl_job_detail(crawler, job.job_url)
                        jobs[i] = enrich_job_from_detail(job, detail)

                    progress.update(detail_task, completed=i + 1)
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS * 0.7)

        console.print(f"  [green]✅ Hoàn thành: {len(jobs)} jobs[/green]")
        return jobs

    async def run(self, fetch_details: bool = True) -> dict[str, list[JobListing]]:
        """
        Chạy crawler cho tất cả cấp độ đã cấu hình.

        Args:
            fetch_details: Có lấy thêm thông tin chi tiết từng job không.

        Returns:
            Dict mapping level_key -> danh sách JobListing
        """
        console.print("[bold green]🚀 Bắt đầu crawl LinkedIn Jobs[/bold green]")
        console.print(f"Cấp độ sẽ crawl: {', '.join(self.levels)}")
        console.print(f"Tối đa {MAX_JOBS_PER_LEVEL} jobs/cấp độ\n")

        # Kiểm tra browser profile
        if not self.profile_path.exists():
            console.print("[red]❌ Chưa có browser profile. Vui lòng chạy auth.py trước.[/red]")
            console.print("[yellow]   python auth.py[/yellow]")
            return {}

        browser_config = self._get_browser_config()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            for level_key in self.levels:
                if level_key not in EXPERIENCE_LEVELS:
                    console.print(f"[yellow]⚠ Bỏ qua cấp độ không hợp lệ: {level_key}[/yellow]")
                    continue

                try:
                    jobs = await self.crawl_level(crawler, level_key, fetch_details)
                    self.all_jobs[level_key] = jobs
                except Exception as e:
                    console.print(f"[red]❌ Lỗi crawl {level_key}: {e}[/red]")
                    self.all_jobs[level_key] = []

                # Delay giữa các cấp độ
                if level_key != self.levels[-1]:
                    console.print(f"[dim]⏳ Nghỉ {DELAY_BETWEEN_REQUESTS * 2}s trước cấp độ tiếp theo...[/dim]")
                    await asyncio.sleep(DELAY_BETWEEN_REQUESTS * 2)

        return self.all_jobs
