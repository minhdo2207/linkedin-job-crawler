# Yêu cầu hệ thống

## Phần mềm (Software)

| Thành phần | Yêu cầu tối thiểu | Đã test |
|---|---|---|
| **Python** | 3.10+ | 3.13.12 ✅ |
| **crawl4ai** | ≥ 0.4.0 | 0.8.6 ✅ |
| **Playwright** | (tự động cài) | 1.58.0 ✅ |
| **pandas** | ≥ 2.0.0 | 3.0.2 ✅ |
| **chardet** | ≥ 5.0.0 | 5.2.0 ✅ |

> ⚠️ **Python 3.9 mặc định của macOS không dùng được** — phải dùng Python 3.10+.  
> Khuyến nghị dùng [miniconda](https://docs.conda.io/en/latest/miniconda.html) hoặc [pyenv](https://github.com/pyenv/pyenv) để quản lý version.

---

## Phần cứng (Hardware)

| Thành phần | Tối thiểu | Khuyến nghị |
|---|---|---|
| **RAM** | 4 GB | 8 GB+ |
| **CPU** | 2 cores | 4 cores+ |
| **Disk trống** | 1 GB | 2 GB+ |

### Chi tiết dung lượng disk

| Thư mục | Dung lượng | Mô tả |
|---|---|---|
| `ms-playwright/` | ~520 MB | Chromium browser (tự động tải khi `crawl4ai-setup`) |
| `browser_profile/` | ~182 MB | LinkedIn session & cookies (sau khi login) |
| `output/` | vài MB | CSV/JSON kết quả crawl |

> Chromium headless tiêu thụ **~500MB–1GB RAM** khi đang chạy.

---

## Hệ điều hành

| OS | Hỗ trợ |
|---|---|
| macOS (Intel & Apple Silicon) | ✅ |
| Linux (Ubuntu, Debian, v.v.) | ✅ |
| Windows 10/11 | ✅ |

---

## Kết luận

Máy **Apple M1 Pro / 16GB RAM / 278GB disk trống** hiện tại chạy project **hoàn toàn bình thường**, dư tài nguyên so với yêu cầu tối thiểu.

Cấu hình thấp nhất có thể chạy được:
- Laptop phổ thông 4GB RAM, 2-core CPU, ~1GB disk trống
- Python 3.10+ (không dùng được Python mặc định của macOS)
