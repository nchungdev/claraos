---
name: code-review
description: Rà soát mã nguồn toàn diện: kiến trúc, bảo mật, hiệu năng, concurrent edge-cases, coding conventions và test coverage
---

# Code Review Skill cho ClaraOS

Bộ quy chuẩn và công cụ rà soát mã nguồn tự động dành riêng cho dự án **ClaraOS** (FastAPI backend, Tauri/Rust wrapper, Docker Compose orchestration, Vanilla JS/Tailwind WebUI).

---

## 🎯 1. Nguyên Tắc Cốt Lõi (Core Principles)

1. **Không khen ngợi chung chung**: Nhận xét phải chỉ rõ file, dòng code và đưa ra code mẫu thay thế.
2. **5 Chiều Đánh Giá Bắt Buộc**:
   * **Kiến trúc & Ranh giới (Scope & Architecture)**: Diff chỉ tập trung đúng mục tiêu được giao, không phá vỡ mô hình DDD hoặc BaseModule của ClaraOS.
   * **Bảo mật (Security & Sanitization)**: Chống XSS (trong WebUI innerHTML), cấm lộ token/secrets (TorBox, TMDb, API keys), xác thực tham số truyền vào Docker engine, chống Path Traversal.
   * **Hiệu năng & Rò rỉ tài nguyên (Performance & Resource Leaks)**: Tránh blocking I/O trong hàm `async def`, tái sử dụng HTTP connection pool, hủy bỏ timers và event listeners đúng cách.
   * **Concurrency & Biên dữ liệu (Edge Cases & Concurrency)**: Xử lý container chưa cài đặt, container đang restart, timeout khi kéo Docker image hoặc mạng ngắt kết nối.
   * **Test & Verification**: Mã nguồn phải biên dịch thành công (`py_compile`, `cargo check`), không lạm dụng mock rỗng.

---

## 📏 2. Quy Chuẩn Độ Dài File, Hàm & Dòng (Length & Complexity Limits)

Nhằm ngăn chặn hiện tượng **"God Object" / "Monster File"** (file ôm đồm quá nhiều trách nhiệm, khó đọc, dễ gây merge conflicts):

| Tiêu chí | 🟢 Lý tưởng | 🟡 Ngưỡng xem xét tách (Warning) | 🔴 Ngưỡng vi phạm (Blocker / Refactor) |
|---|---|---|---|
| **Độ dài File (.py, .rs, .js)** | **< 300 dòng** | **300 – 500 dòng** | **> 500 dòng** *(Bắt buộc phải tách module/helper)* |
| **Độ dài Hàm / Method** | **< 30 dòng** | **30 – 50 dòng** | **> 50 dòng** *(Vi phạm Single Responsibility)* |
| **Độ dài 1 dòng code** | **88 – 100 ký tự** | **100 – 120 ký tự** | **> 120 ký tự** *(Khó đọc trên màn hình chia đôi)* |

*(Ngoại lệ: File dữ liệu seed/template tĩnh như `resources/app-catalog/apps.yaml` hoặc file sinh tự động).*

---

## 📐 3. Các Coding Convention Chuẩn Quốc Tế Áp Dụng

### A. Python / FastAPI (`claraos/`):
* **PEP 8 (Style Guide)**:
  - Tên hàm, biến, module: `snake_case` (ví dụ: `get_full_catalog`, `docker_manager`).
  - Tên class: `PascalCase` (ví dụ: `DockerManager`, `OrganizerModule`).
  - Hằng số: `UPPER_SNAKE_CASE` (ví dụ: `DOCKER_SOCKET`, `CATEGORY_MAP`).
  - Thụt dòng chuẩn 4 spaces, không dùng tab.
* **PEP 484 & PEP 526 (Type Hints)**:
  - Bắt buộc khai báo kiểu dữ liệu cho tham số và kiểu trả về ở mọi hàm public:
    ```python
    async def start_container(self, container_id: str) -> bool:
    ```
* **Async IO Discipline**:
  - Tuyệt đối không gọi blocking I/O (`time.sleep`, `requests`, `os.walk`, `shutil.move`) trong `async def` — bắt buộc bọc qua `await asyncio.to_thread(...)`.
* **Exception Handling**:
  - Không nuốt ngoại lệ âm thầm (`except: pass`). Mọi endpoint phải trả về `HTTPException` với status code chuẩn (`400`, `404`, `409`, `500`).

### B. Rust / Tauri (`src-tauri/`):
* **Rust Style Guide (RFC 2436)** & **Clippy**:
  - Tránh lạm dụng `.unwrap()` hoặc `.expect()` trên runtime; ưu tiên toán tử `?` và trả về `Result<T, E>`.
  - Các hàm IPC `#[tauri::command]` phải xác thực tham số đầu vào trước khi gọi command hệ điều hành.

### C. Web Frontend (`claraos/web/static/`):
* **Modern JavaScript Standard**:
  - Dùng `const` / `let`, tuyệt đối không dùng `var`.
  - Tên hàm và biến: `camelCase`.
  - Tránh XSS: Khi chèn dữ liệu động người dùng vào `innerHTML`, cần escape HTML hoặc dùng `textContent`.
* **UI/UX & Button Balance (Phương án B - Compact)**:
  - Các nút hành động không kéo dãn nhân tạo (`w-auto`, không dùng `flex-1` trừ khi chia đôi 50/50).
  - Độ rộng nút co giãn tự nhiên theo nội dung chữ, tránh nút dài 70% lệch với nút 30%.

### D. RESTful API Design (RFC 9110):
* URL endpoint dùng danh từ số nhiều: `/api/modules/apps`, `/api/modules/organizer/files`.
* Phân định rõ method: `GET` (đọc dữ liệu), `POST` (tạo mới hoặc thực hiện action), `DELETE` (xóa tài nguyên).

### E. Git Conventions:
* **Conventional Commits 1.0.0**: `feat(...)`, `fix(...)`, `refactor(...)`, `docs(...)`, `chore(...)`.

---

## 🏷️ 4. Phân Loại Mức Độ Nghiêm Trọng (Severity Classification)

* 🔴 **`[Blocker]`**: Lỗ hổng bảo mật (Path Traversal, XSS, lộ secrets), blocking event loop trong asyncio, file logic vượt quá 500 dòng mà không có kế hoạch tách, lỗi cú pháp. **Bắt buộc phải kèm code sửa chữa mẫu**.
* 🟡 **`[Warning]`**: Bẫy hiệu năng ($O(n^2)$, thiếu connection pooling), file 300-500 dòng, hàm > 50 dòng, thiếu type hints, ngoại lệ lỏng lẻo.
* 🟢 **`[Nit]`**: Dòng code dài > 100 ký tự, tối ưu đặt tên biến, gợi ý refactor nhẹ.

---

## ⚡ 5. Lệnh Kiểm Tra Nhanh

Sử dụng script tích hợp để tự động rà soát file, cú pháp và quy chuẩn độ dài:

```bash
# Rà soát toàn diện codebase ClaraOS:
python3 .agents/skills/code-review/scripts/runner.py

# Rà soát chỉ các thay đổi so với nhánh master:
python3 .agents/skills/code-review/scripts/runner.py --target master
```
