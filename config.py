"""
Cấu hình cho LinkedIn Job Crawler
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── LinkedIn Experience Level Filters ────────────────────────────────────────
# LinkedIn dùng f_E parameter để filter theo cấp độ
EXPERIENCE_LEVELS = {
    "internship": {
        "label": "Thực tập (Internship)",
        "f_E": "1",
        "keywords": ["intern", "internship", "software engineer intern"],
    },
    "entry": {
        "label": "Junior / Entry Level",
        "f_E": "2",
        "keywords": ["junior software engineer", "software engineer I", "entry level"],
    },
    "associate": {
        "label": "Associate / Mid",
        "f_E": "3",
        "keywords": ["software engineer II", "associate software engineer"],
    },
    "mid_senior": {
        "label": "Mid-Senior Level",
        "f_E": "4",
        "keywords": ["senior software engineer", "software engineer III"],
    },
    "director": {
        "label": "Director / Staff / Principal",
        "f_E": "5",
        "keywords": ["staff software engineer", "principal engineer", "director of engineering"],
    },
    "executive": {
        "label": "Executive / VP / CTO",
        "f_E": "6",
        "keywords": ["VP engineering", "CTO", "chief technology officer"],
    },
}

# ─── Search Configuration ──────────────────────────────────────────────────────
BASE_SEARCH_KEYWORD = "software engineer"
BASE_LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs/search/"

# Vị trí địa lý (để trống = toàn cầu, hoặc thêm: "Vietnam", "Ho Chi Minh City", etc.)
LOCATION = ""

# ─── Crawler Settings ──────────────────────────────────────────────────────────
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
BROWSER_PROFILE_DIR = os.getenv("BROWSER_PROFILE_DIR", "./browser_profile")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
MAX_JOBS_PER_LEVEL = int(os.getenv("MAX_JOBS_PER_LEVEL", "50"))
DELAY_BETWEEN_REQUESTS = float(os.getenv("DELAY_BETWEEN_REQUESTS", "3"))

# ─── LinkedIn Selectors ────────────────────────────────────────────────────────
SELECTORS = {
    "job_cards": "li.scaffold-layout__list-item",
    "job_title": "a.job-card-list__title",
    "company_name": "span.job-card-container__primary-description",
    "location": "li.job-card-container__metadata-item",
    "job_link": "a.job-card-list__title",
    # Detail page selectors
    "detail_title": "h1.job-details-jobs-unified-top-card__job-title",
    "detail_company": "a.job-details-jobs-unified-top-card__company-name",
    "detail_location": "span.tvm__text",
    "detail_description": "div.jobs-description-content__text",
    "detail_seniority": "span.job-details-jobs-unified-top-card__job-insight-view-model-secondary",
}

def build_search_url(level_key: str, start: int = 0) -> str:
    """Tạo URL search LinkedIn cho cấp độ cụ thể."""
    level = EXPERIENCE_LEVELS[level_key]
    params = {
        "keywords": BASE_SEARCH_KEYWORD,
        "f_E": level["f_E"],
        "start": str(start),
        "sortBy": "DD",  # Date Descending - mới nhất trước
    }
    if LOCATION:
        params["location"] = LOCATION

    query_string = "&".join(f"{k}={v.replace(' ', '%20')}" for k, v in params.items())
    return f"{BASE_LINKEDIN_SEARCH_URL}?{query_string}"
