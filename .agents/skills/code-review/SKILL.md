---
name: code-review
description: Rà soát mã nguồn toàn diện: kiến trúc, bảo mật, hiệu năng, concurrent edge-cases và test coverage
---

# Code Review Skill cho ClaraOS

Bộ quy chuẩn và công cụ rà soát mã nguồn tự động dành riêng cho dự án **ClaraOS** (FastAPI backend, Tauri/Rust wrapper, Docker Compose orchestration, Vanilla JS/Tailwind WebUI).

---

## 🎯 1. Nguyên Tắc Cốt Lõi (Core Principles)

1. **Không khen ngợi chung chung**: Nhận xét phải cụ thể vào từng dòng code, file và giải pháp thay thế.
2. **5 Chiều Đánh Giá Bắt Buộc**:
   * **Kiến trúc & Ranh giới (Scope & Architecture)**: Diff chỉ tập trung đúng mục tiêu được giao, không phá vỡ mô hình DDD hoặc ModuleBase của ClaraOS.
   * **Bảo mật (Security & Sanitization)**: Chống XSS (trong WebUI innerHTML), cấm lộ token/secrets (TorBox, TMDb, API keys), xác thực tham số truyền vào Docker engine.
   * **Hiệu năng & Rò rỉ tài nguyên (Performance & Resource Leaks)**: Tránh blocking I/O trong hàm `async def`, quản lý vòng đời HTTP client/session, hủy bỏ timers và event listeners đúng cách.
   * **Concurrency & Biên dữ liệu (Edge Cases & Concurrency)**: Xử lý container chưa cài đặt, container đang restart, timeout khi kéo Docker image hoặc mạng ngắt kết nối.
   * **Test & Verification**: Mã nguồn phải biên dịch thành công (`py_compile`, `cargo check`), không lạm dụng mock rỗng.

---

## 🏷️ 2. Phân Loại Kết Quả Review (Severity Classification)

* 🔴 **`[Blocker]`**: Lỗi nghiêm trọng, lỗ hổng bảo mật, nguy cơ crash hệ thống, rò rỉ secret, hoặc phá vỡ tính năng cốt lõi. **Bắt buộc phải kèm code sửa chữa mẫu**.
* 🟡 **`[Warning]`**: Bẫy hiệu năng ($O(n^2)$, blocking asyncio), thiếu kiểm tra biên, xử lý ngoại lệ lỏng lẻo (`except: pass`), thiếu type hint.
* 🟢 **`[Nit]`**: Tối ưu đặt tên biến, định dạng code, gợi ý refactor nhẹ mà không ảnh hưởng logic.

---

## 🔍 3. Checklist Chuyên Sâu Cho ClaraOS

### A. Python / FastAPI (`claraos/`):
- [ ] Không gọi hàm đồng bộ gây nghẽn (blocking I/O như `requests`, `time.sleep`, `subprocess.run` dài) trực tiếp trong hàm `async def` — phải bọc qua `asyncio.to_thread()`.
- [ ] Mọi endpoint phải xử lý mã lỗi HTTP chuẩn (`400`, `404`, `409`, `500`) thông qua `HTTPException`.
- [ ] Không nuốt ngoại lệ âm thầm (`except Exception: pass`). Phải log lỗi qua `logger.error(...)` hoặc re-raise.
- [ ] Giữ tính toàn vẹn của mô hình `BaseModule` khi đăng ký route.

### B. Rust / Tauri (`src-tauri/`):
- [ ] Tránh dùng `.unwrap()` hoặc `.expect()` trên các nhánh có thể trả về lỗi từ runtime; ưu tiên dùng toán tử `?` và trả về `Result`.
- [ ] Các lệnh IPC (`#[tauri::command]`) phải xác thực tham số đầu vào trước khi thực thi lệnh hệ thống.

### C. Web Frontend (`claraos/web/static/`):
- [ ] Tránh XSS: Khi chèn dữ liệu động người dùng vào `innerHTML`, cần escape HTML hoặc dùng `textContent` / `innerText`.
- [ ] Tối ưu hóa UI: Các button hành động không bị rớt dòng trên màn hình nhỏ (mobile responsive).
- [ ] Ứng dụng chưa cài đặt không hiển thị đường dẫn URL khả dụng hoặc gây nhầm lẫn là đang chạy.

---

## ⚡ 4. Lệnh Kiểm Tra Nhanh

Sử dụng script tích hợp để tự động quét diff git hiện tại:

```bash
# Kiểm tra tự động các thay đổi chưa commit:
python3 .agents/skills/code-review/scripts/runner.py

# Kiểm tra so với branch master:
python3 .agents/skills/code-review/scripts/runner.py --target master
```
