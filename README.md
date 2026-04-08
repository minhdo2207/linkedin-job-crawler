# LinkedIn Software Engineer Job Crawler

Tự động crawl job **Software Engineer** theo từng cấp độ từ LinkedIn, sử dụng [crawl4ai](https://github.com/unclecode/crawl4ai) + Playwright. Kết quả xuất ra CSV và JSON.

## Tính năng

- Crawl **6 cấp độ**: Internship → Junior → Associate → Mid-Senior → Director/Staff → Executive/VP
- Lưu kết quả ra **CSV và JSON** (từng cấp độ riêng + file tổng hợp)
- Hỗ trợ **persistent session** — đăng nhập một lần, crawl nhiều lần
- Tự động detect login thành công, đếm ngược thời gian
- Hiển thị bảng tóm tắt đẹp với Rich

## Cài đặt

```bash
# 1. Clone repo
git clone <repo-url>
cd linkedin-job-crawler

# 2. Tạo và kích hoạt virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Cài Playwright browsers (bắt buộc)
crawl4ai-setup

# 5. Cấu hình
cp .env.example .env
# Chỉnh sửa .env nếu cần (có thể bỏ qua, login thủ công)
```

## Cách chạy

### Bước 1 — Đăng nhập LinkedIn (chỉ cần làm một lần)

```bash
python auth.py
```

Browser Chromium sẽ tự mở. **Đăng nhập LinkedIn** trong vòng 120 giây. Script tự detect và lưu session.

> **Lưu ý:** Session được lưu tại `./browser_profile/` — không commit thư mục này lên git (đã có trong .gitignore).

### Bước 2 — Crawl jobs

```bash
# Crawl tất cả 6 cấp độ (kèm chi tiết job)
python main.py

# Crawl tất cả + in mẫu kết quả
python main.py --sample

# Chỉ crawl một số cấp độ cụ thể
python main.py --levels entry mid_senior

# Crawl nhanh (chỉ lấy danh sách, không vào từng trang job)
python main.py --no-details

# Hiện browser trong lúc crawl (để debug)
python main.py --no-headless

# Đăng nhập tự động (cần điền .env) rồi crawl
python main.py --login
```

### Tất cả options

| Option | Mô tả |
|--------|-------|
| `--levels` | Chọn cấp độ: `internship entry associate mid_senior director executive` |
| `--no-details` | Bỏ qua crawl trang chi tiết (nhanh hơn ~3x) |
| `--no-headless` | Hiện browser khi crawl |
| `--login` | Auto-login từ `.env` trước khi crawl |
| `--manual-login` | Mở browser để login thủ công |
| `--sample` | In mẫu 3 jobs đầu mỗi cấp độ sau khi crawl |

## Cấp độ hỗ trợ

| Key | Tên | LinkedIn Filter |
|-----|-----|----------------|
| `internship` | Thực tập (Internship) | f_E=1 |
| `entry` | Junior / Entry Level | f_E=2 |
| `associate` | Associate / Mid | f_E=3 |
| `mid_senior` | Mid-Senior Level | f_E=4 |
| `director` | Director / Staff / Principal | f_E=5 |
| `executive` | Executive / VP / CTO | f_E=6 |

## Output

Files lưu tại `./output/` với timestamp:

```
output/
├── jobs_internship_20260408_123456.csv
├── jobs_entry_20260408_123456.csv
├── jobs_associate_20260408_123456.csv
├── jobs_mid_senior_20260408_123456.csv
├── jobs_director_20260408_123456.csv
├── jobs_executive_20260408_123456.csv
├── jobs_all_levels_20260408_123456.csv   ← Tổng hợp
└── jobs_all_levels_20260408_123456.json
```

### Các trường dữ liệu

| Trường | Mô tả |
|--------|-------|
| `title` | Tên vị trí công việc |
| `company` | Tên công ty |
| `location` | Địa điểm |
| `level` | Key cấp độ (vd: `mid_senior`) |
| `level_label` | Tên cấp độ hiển thị |
| `job_url` | Link trực tiếp đến job |
| `posted_date` | Ngày đăng |
| `workplace_type` | Remote / Hybrid / On-site |
| `employment_type` | Full-time / Part-time / Contract |
| `seniority_level` | Seniority từ LinkedIn |
| `description` | Mô tả công việc (tối đa 3000 ký tự) |
| `industries` | Ngành nghề |
| `applicants` | Số người đã ứng tuyển |

## Cấu trúc project

```
linkedin-job-crawler/
├── main.py          # Entry point, CLI interface
├── crawler.py       # Core crawler (crawl4ai + Playwright)
├── extractor.py     # Data models, CSS selectors, parsing
├── storage.py       # Lưu CSV/JSON, hiển thị bảng tóm tắt
├── auth.py          # LinkedIn login & session management
├── config.py        # Cấp độ, URL builder, cấu hình chung
├── requirements.txt
├── .env.example
└── output/          # Kết quả crawl (tự tạo, không commit)
```

## Cấu hình nâng cao (`.env`)

```env
# Đăng nhập tự động
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Tối đa bao nhiêu jobs mỗi cấp độ (mặc định: 50)
MAX_JOBS_PER_LEVEL=50

# Delay giữa các request tính bằng giây (mặc định: 3)
DELAY_BETWEEN_REQUESTS=3

# Lọc theo vị trí địa lý (để trống = toàn cầu)
# LOCATION=Vietnam
```

## Lưu ý

- **Session**: Sau khi `python auth.py`, session lưu tại `./browser_profile/` — không cần login lại
- **Rate limiting**: Crawler tự delay giữa các request để tránh bị block
- **Selector thay đổi**: LinkedIn thường xuyên cập nhật HTML — nếu bị lỗi selector, chỉnh trong `config.py → SELECTORS`
- **CAPTCHA**: Nếu bị CAPTCHA, dùng `--no-headless` để tự xử lý trong browser

## Yêu cầu

- Python 3.10+
- crawl4ai >= 0.4.0
- Tài khoản LinkedIn
