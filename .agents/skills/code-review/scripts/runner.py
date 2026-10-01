#!/usr/bin/env python3
"""Automated code review & pre-commit auditor for ClaraOS."""

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
    # Check unstaged + staged diff
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

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            line_num = 0
            continue
        if line.startswith("@@"):
            # @@ -1,5 +1,6 @@
            m = re.search(r"\+(\d+)", line)
            if m:
                line_num = int(m.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:].strip()
            # 1. Secret check
            if secret_regex.search(content) and not ("example" in current_file.lower() or "template" in current_file.lower()):
                issues.append({
                    "severity": "BLOCKER",
                    "file": current_file,
                    "line": line_num,
                    "message": "Phát hiện potential secret / API token cứng trong mã nguồn.",
                })

            # 2. Broad except pass check (Python)
            if current_file.endswith(".py") and broad_except_regex.search(content):
                issues.append({
                    "severity": "WARNING",
                    "file": current_file,
                    "line": line_num,
                    "message": "Phát hiện 'except: pass' nuốt ngoại lệ âm thầm. Cần log lỗi hoặc xử lý cụ thể.",
                })

            # 3. Rust unwrap risk check
            if current_file.endswith(".rs") and ".unwrap()" in content and not current_file.endswith("test.rs"):
                issues.append({
                    "severity": "WARNING",
                    "file": current_file,
                    "line": line_num,
                    "message": "Sử dụng .unwrap() có thể gây panic runtime trong Rust. Ưu tiên dùng '?' hoặc match.",
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


def main():
    print("🔍 Đang rà soát mã nguồn ClaraOS...")
    all_issues = []

    # 1. Check Python syntax
    syntax_issues = check_python_syntax()
    all_issues.extend(syntax_issues)

    # 2. Check git diff patterns
    diff_issues = check_git_diff()
    all_issues.extend(diff_issues)

    if not all_issues:
        print("✅ Hoàn thành rà soát: Không phát hiện lỗi cấu trúc, cú pháp hay rò rỉ bảo mật.")
        return 0

    print(f"\n🚨 Phát hiện {len(all_issues)} vấn đề cần lưu ý:")
    blockers = 0
    for issue in all_issues:
        sev = issue["severity"]
        prefix = "🔴 [BLOCKER]" if sev == "BLOCKER" else "🟡 [WARNING]"
        if sev == "BLOCKER":
            blockers += 1
        loc = f"{issue['file']}:{issue['line']}" if issue["line"] else issue["file"]
        print(f"  {prefix} ({loc}) - {issue['message']}")

    if blockers > 0:
        print(f"\n❌ Có {blockers} vấn đề Blocker cần khắc phục trước khi commit!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
