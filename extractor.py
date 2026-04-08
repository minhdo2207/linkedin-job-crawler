"""
Trích xuất thông tin job từ HTML của LinkedIn
"""
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from rich.console import Console

from config import BROWSER_PROFILE_DIR, DELAY_BETWEEN_REQUESTS

console = Console()


@dataclass
class JobListing:
    """Model cho một job listing."""
    title: str = ""
    company: str = ""
    location: str = ""
    level: str = ""          # Cấp độ: internship, entry, mid_senior, etc.
    level_label: str = ""    # Label hiển thị: "Junior / Entry Level"
    job_url: str = ""
    posted_date: str = ""
    job_type: str = ""       # Full-time, Part-time, Contract
    workplace_type: str = "" # On-site, Remote, Hybrid
    description: str = ""
    applicants: str = ""
    seniority_level: str = ""
    employment_type: str = ""
    industries: str = ""
    skills: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# CSS-based extraction schema cho LinkedIn job cards
JOB_CARD_SCHEMA = {
    "name": "LinkedIn Job Cards",
    "baseSelector": "li.scaffold-layout__list-item",
    "fields": [
        {
            "name": "title",
            "selector": "a.job-card-list__title--link",
            "type": "text",
        },
        {
            "name": "company",
            "selector": "div.artdeco-entity-lockup__subtitle span",
            "type": "text",
        },
        {
            "name": "location",
            "selector": "ul.job-card-container__metadata-wrapper li",
            "type": "text",
        },
        {
            "name": "job_url",
            "selector": "a.job-card-list__title--link",
            "type": "attribute",
            "attribute": "href",
        },
        {
            "name": "posted_date",
            "selector": "time",
            "type": "attribute",
            "attribute": "datetime",
        },
    ],
}

# Schema cho job detail page
JOB_DETAIL_SCHEMA = {
    "name": "LinkedIn Job Detail",
    "baseSelector": "body",
    "fields": [
        {
            "name": "title",
            "selector": "h1.job-details-jobs-unified-top-card__job-title",
            "type": "text",
        },
        {
            "name": "company",
            "selector": "div.job-details-jobs-unified-top-card__company-name a",
            "type": "text",
        },
        {
            "name": "location",
            "selector": "div.job-details-jobs-unified-top-card__primary-description-container span.tvm__text",
            "type": "text",
        },
        {
            "name": "applicants",
            "selector": "span.tvm__text--positive",
            "type": "text",
        },
        {
            "name": "description",
            "selector": "div.jobs-description-content__text",
            "type": "text",
        },
        {
            "name": "seniority_level",
            "selector": "li.description__job-criteria-item:nth-child(1) span.description__job-criteria-text",
            "type": "text",
        },
        {
            "name": "employment_type",
            "selector": "li.description__job-criteria-item:nth-child(2) span.description__job-criteria-text",
            "type": "text",
        },
        {
            "name": "job_function",
            "selector": "li.description__job-criteria-item:nth-child(3) span.description__job-criteria-text",
            "type": "text",
        },
        {
            "name": "industries",
            "selector": "li.description__job-criteria-item:nth-child(4) span.description__job-criteria-text",
            "type": "text",
        },
    ],
}


def parse_job_cards(extracted_data: list[dict], level_key: str, level_label: str) -> list[JobListing]:
    """Chuyển dữ liệu thô từ crawler thành danh sách JobListing."""
    jobs = []
    for item in extracted_data:
        if not item.get("title"):
            continue

        job_url = item.get("job_url", "")
        # Làm sạch URL LinkedIn (bỏ query params thừa)
        if job_url and "?" in job_url:
            job_url = job_url.split("?")[0]
        if job_url and not job_url.startswith("http"):
            job_url = f"https://www.linkedin.com{job_url}"

        job = JobListing(
            title=item.get("title", "").strip(),
            company=item.get("company", "").strip(),
            location=item.get("location", "").strip(),
            level=level_key,
            level_label=level_label,
            job_url=job_url,
            posted_date=item.get("posted_date", ""),
        )
        jobs.append(job)

    return jobs


def enrich_job_from_detail(job: JobListing, detail_data: dict) -> JobListing:
    """Bổ sung thông tin chi tiết vào job từ trang detail."""
    if not detail_data:
        return job

    if detail_data.get("description"):
        job.description = detail_data["description"].strip()[:3000]  # Giới hạn 3000 ký tự

    if detail_data.get("seniority_level"):
        job.seniority_level = detail_data["seniority_level"].strip()

    if detail_data.get("employment_type"):
        job.employment_type = detail_data["employment_type"].strip()

    if detail_data.get("industries"):
        job.industries = detail_data["industries"].strip()

    if detail_data.get("applicants"):
        job.applicants = detail_data["applicants"].strip()

    # Trích xuất workplace type từ location string
    location = detail_data.get("location", "") or job.location
    if "remote" in location.lower():
        job.workplace_type = "Remote"
    elif "hybrid" in location.lower():
        job.workplace_type = "Hybrid"
    else:
        job.workplace_type = "On-site"

    return job
