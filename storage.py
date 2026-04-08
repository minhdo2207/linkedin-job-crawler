"""
Lưu trữ dữ liệu job ra file CSV và JSON
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from rich.console import Console
from rich.table import Table

from config import EXPERIENCE_LEVELS, OUTPUT_DIR
from extractor import JobListing

console = Console()


def save_jobs(
    all_jobs: dict[str, list[JobListing]],
    output_dir: Optional[str] = None,
) -> dict[str, str]:
    """
    Lưu tất cả job ra file CSV và JSON.

    Returns:
        Dict mapping filename -> filepath
    """
    out_dir = Path(output_dir or OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_files = {}

    # ── 1. Lưu từng cấp độ riêng ──────────────────────────────────────────────
    for level_key, jobs in all_jobs.items():
        if not jobs:
            continue

        level_label = EXPERIENCE_LEVELS[level_key]["label"]
        safe_label = level_key.replace("/", "_")

        # CSV
        csv_path = out_dir / f"jobs_{safe_label}_{timestamp}.csv"
        df = pd.DataFrame([j.to_dict() for j in jobs])
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        saved_files[f"{level_key}_csv"] = str(csv_path)

        # JSON
        json_path = out_dir / f"jobs_{safe_label}_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([j.to_dict() for j in jobs], f, ensure_ascii=False, indent=2)
        saved_files[f"{level_key}_json"] = str(json_path)

        console.print(f"  [green]✅ {level_label}[/green]: {len(jobs)} jobs → {csv_path.name}")

    # ── 2. Lưu tổng hợp tất cả cấp độ ────────────────────────────────────────
    all_jobs_flat = []
    for level_key, jobs in all_jobs.items():
        all_jobs_flat.extend([j.to_dict() for j in jobs])

    if all_jobs_flat:
        # Combined CSV
        combined_csv = out_dir / f"jobs_all_levels_{timestamp}.csv"
        df_all = pd.DataFrame(all_jobs_flat)
        df_all.to_csv(combined_csv, index=False, encoding="utf-8-sig")
        saved_files["combined_csv"] = str(combined_csv)

        # Combined JSON
        combined_json = out_dir / f"jobs_all_levels_{timestamp}.json"
        with open(combined_json, "w", encoding="utf-8") as f:
            json.dump(all_jobs_flat, f, ensure_ascii=False, indent=2)
        saved_files["combined_json"] = str(combined_json)

        console.print(f"\n  [bold green]📦 Tổng hợp[/bold green]: {len(all_jobs_flat)} jobs → {combined_csv.name}")

    return saved_files


def print_summary(all_jobs: dict[str, list[JobListing]]) -> None:
    """In bảng tóm tắt kết quả crawl."""
    table = Table(
        title="📊 Kết Quả Crawl LinkedIn Jobs",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Cấp Độ", style="cyan", no_wrap=True)
    table.add_column("Số Jobs", justify="right", style="green")
    table.add_column("Remote", justify="right")
    table.add_column("Hybrid", justify="right")
    table.add_column("On-site", justify="right")
    table.add_column("Top Company", style="dim")

    total = 0
    for level_key, jobs in all_jobs.items():
        if not jobs:
            continue

        level_label = EXPERIENCE_LEVELS[level_key]["label"]
        count = len(jobs)
        total += count

        remote = sum(1 for j in jobs if j.workplace_type == "Remote")
        hybrid = sum(1 for j in jobs if j.workplace_type == "Hybrid")
        onsite = sum(1 for j in jobs if j.workplace_type == "On-site")

        # Top company (xuất hiện nhiều nhất)
        companies = [j.company for j in jobs if j.company]
        top_company = max(set(companies), key=companies.count) if companies else "-"

        table.add_row(
            level_label,
            str(count),
            str(remote),
            str(hybrid),
            str(onsite),
            top_company[:30],
        )

    table.add_section()
    table.add_row("[bold]TỔNG[/bold]", f"[bold]{total}[/bold]", "", "", "", "")

    console.print("\n")
    console.print(table)


def print_sample_jobs(all_jobs: dict[str, list[JobListing]], n: int = 3) -> None:
    """In mẫu n job đầu tiên của mỗi cấp độ."""
    for level_key, jobs in all_jobs.items():
        if not jobs:
            continue

        level_label = EXPERIENCE_LEVELS[level_key]["label"]
        console.print(f"\n[bold yellow]── {level_label} (mẫu {min(n, len(jobs))} jobs) ──[/bold yellow]")

        for job in jobs[:n]:
            console.print(f"  [cyan]{job.title}[/cyan] @ [green]{job.company}[/green]")
            console.print(f"  📍 {job.location} | 🏠 {job.workplace_type or 'N/A'} | 💼 {job.employment_type or 'N/A'}")
            if job.job_url:
                console.print(f"  🔗 {job.job_url}")
            console.print()
