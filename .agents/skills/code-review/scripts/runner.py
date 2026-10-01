import os
import re
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout + res.stderr
    except Exception as e:
        return 1, str(e)


def check_git_diff() -> list[dict]:
    issues = []
    code, diff_text = run_cmd(["git", "diff", "HEAD"])
    if not diff_text.strip():
        code, diff_text = run_cmd(["git", "diff"])

    if not diff_text.strip():
        return issues

    current_file = ""
    line_num = 0

    secret_regex = re.compile(
        r"(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]",
        re.IGNORECASE,
    )
    broad_except_regex = re.compile(r"except(\s+Exception)?\s*:\s*pass")
    python_func_no_type_regex = re.compile(r"^def\s+[a-z0-9_]+\([^)]*\)\s*:")

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            line_num = 0
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            if m:
                line_num = int(m.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            raw_line = line[1:]
            content = raw_line.strip()

            # 1. Secret check
            if secret_regex.search(content) and not ("example" in current_file.lower() or "template" in current_file.lower()):
                issues.append({
                    "severity": "BLOCKER",
                    "file": current_file,
                    "line": line_num,
                    "message": "Phát hiện potential secret / API token cứng trong mã nguồn.",
                })

            # 2. Broad except pass check (PEP 8 Exception handling)
            if current_file.endswith(".py") and not current_file.endswith("runner.py") and broad_except_regex.search(content):
                issues.append({
                    "severity": "WARNING",
                    "file": current_file,
                    "line": line_num,
                    "message": "Vi phạm PEP 8: Nuốt ngoại lệ âm thầm 'except: pass'. Phải log hoặc xử lý cụ thể.",
                })

            # 3. Rust unwrap risk check (Rust RFC 2436)
            if current_file.endswith(".rs") and ".unwrap()" in content and not current_file.endswith("test.rs"):
                issues.append({
                    "severity": "WARNING",
                    "file": current_file,
                    "line": line_num,
                    "message": "Vi phạm Rust Safety: Dùng .unwrap() có thể gây panic. Ưu tiên dùng '?' hoặc match.",
                })

            # 4. Line length check (> 120 chars for code files)
            code_exts = {".py", ".rs", ".js", ".ts", ".css"}
            if len(raw_line) > 120 and Path(current_file).suffix in code_exts:
                issues.append({
                    "severity": "NIT",
                    "file": current_file,
                    "line": line_num,
                    "message": f"Dòng code dài {len(raw_line)} ký tự (vượt ngưỡng khuyến nghị 100-120).",
                })

            # 5. Type hint recommendation (PEP 484)
            if current_file.endswith(".py") and python_func_no_type_regex.search(content) and not content.startswith("def test_"):
                issues.append({
                    "severity": "NIT",
                    "file": current_file,
                    "line": line_num,
                    "message": "Khuyến nghị PEP 484: Hàm thiếu return type annotation (-> Type).",
                })

            line_num += 1
        elif not line.startswith("-"):
            line_num += 1

    return issues


def check_python_syntax() -> list[dict]:
    issues = []
    py_files = list(Path("claraos").glob("**/*.py"))
    for py in py_files:
        code, out = run_cmd([sys.executable, "-m", "py_compile", str(py)])
        if code != 0:
            issues.append({
                "severity": "BLOCKER",
                "file": str(py),
                "line": 0,
                "message": f"Lỗi cú pháp Python: {out.strip()}",
            })
    return issues


def check_file_length_limits() -> list[dict]:
    issues = []
    # Scan source code files (.py, .js, .rs, .html)
    extensions = {".py", ".rs", ".js", ".html"}
    ignored_patterns = {"resources", "node_modules", "target", ".git", ".venv", "apps.yaml"}

    for root, dirs, files in os.walk("."):
        # Skip ignored dirs
        dirs[:] = [d for d in dirs if d not in ignored_patterns and not d.startswith(".")]

        for f in files:
            path = Path(root) / f
            if path.suffix in extensions and not any(ign in str(path) for ign in ignored_patterns):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                        lines = len(fh.readlines())
                    
                    if lines > 500:
                        issues.append({
                            "severity": "WARNING",
                            "file": str(path),
                            "line": lines,
                            "message": f"File dài {lines} dòng (vượt ngưỡng 500 dòng). Cần xem xét tách module.",
                        })
                    elif lines > 300:
                        issues.append({
                            "severity": "NIT",
                            "file": str(path),
                            "line": lines,
                            "message": f"File dài {lines} dòng (vượt ngưỡng khuyến nghị 300 dòng).",
                        })
                except Exception:
                    continue
    return issues


def main():
    print("🔍 Đang rà soát mã nguồn & Coding Conventions ClaraOS...")
    all_issues = []

    # 1. Check Python syntax
    syntax_issues = check_python_syntax()
    all_issues.extend(syntax_issues)

    # 2. Check git diff patterns & conventions
    diff_issues = check_git_diff()
    all_issues.extend(diff_issues)

    # 3. Check file length limits
    length_issues = check_file_length_limits()
    all_issues.extend(length_issues)

    if not all_issues:
        print("✅ Hoàn thành rà soát: Không phát hiện lỗi cấu trúc, cú pháp hay rò rỉ bảo mật.")
        return 0

    print(f"\n📊 Báo cáo kết quả rà soát ({len(all_issues)} mục cần lưu ý):")
    blockers = 0
    warnings = 0
    nits = 0

    for issue in all_issues:
        sev = issue["severity"]
        if sev == "BLOCKER":
            prefix = "🔴 [BLOCKER]"
            blockers += 1
        elif sev == "WARNING":
            prefix = "🟡 [WARNING]"
            warnings += 1
        else:
            prefix = "🟢 [NIT]"
            nits += 1

        loc = f"{issue['file']}:{issue['line']}" if issue["line"] else issue["file"]
        print(f"  {prefix} ({loc}) - {issue['message']}")

    print(f"\nTổng kết: {blockers} Blocker | {warnings} Warning | {nits} Nit")
    if blockers > 0:
        print(f"❌ Có {blockers} vấn đề Blocker cần khắc phục trước khi commit!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
