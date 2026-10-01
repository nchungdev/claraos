#!/usr/bin/env python3
"""Automated code review, conventions & pre-commit auditor for ClaraOS."""

import argparse
import ast
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


def _check_added_line(
    raw_line: str,
    file_path: str,
    line_num: int,
    issues: list[dict],
    secret_re: re.Pattern,
    except_re: re.Pattern,
) -> None:
    content = raw_line.strip()
    # 1. Secret pattern check
    if secret_re.search(content) and not any(k in file_path.lower() for k in ("example", "template")):
        issues.append({
            "severity": "BLOCKER",
            "file": file_path,
            "line": line_num,
            "message": "Phát hiện potential secret / API token cứng trong mã nguồn.",
        })

    # 2. Broad except pass check (PEP 8)
    if file_path.endswith(".py") and not file_path.endswith("runner.py") and except_re.search(content):
        issues.append({
            "severity": "WARNING",
            "file": file_path,
            "line": line_num,
            "message": "Vi phạm PEP 8: Nuốt ngoại lệ âm thầm 'except: pass'. Phải log hoặc xử lý.",
        })

    # 3. Rust unwrap risk check (Rust RFC 2436)
    if file_path.endswith(".rs") and ".unwrap()" in content and not file_path.endswith("test.rs"):
        issues.append({
            "severity": "WARNING",
            "file": file_path,
            "line": line_num,
            "message": "Vi phạm Rust Safety: Dùng .unwrap() có thể gây panic. Dùng '?' hoặc match.",
        })

    # 4. Line length check (> 120 chars for code files)
    code_exts = {".py", ".rs", ".js", ".ts", ".css"}
    if len(raw_line) > 120 and Path(file_path).suffix in code_exts:
        issues.append({
            "severity": "NIT",
            "file": file_path,
            "line": line_num,
            "message": f"Dòng code dài {len(raw_line)} ký tự (vượt ngưỡng khuyến nghị 100-120).",
        })


def check_git_diff(target: str | None = None) -> tuple[list[dict], set[str]]:
    issues: list[dict] = []
    changed_files: set[str] = set()

    if target:
        code, diff_text = run_cmd(["git", "diff", f"{target}...HEAD"])
        if code != 0 or not diff_text.strip():
            code, diff_text = run_cmd(["git", "diff", target])
    else:
        code, diff_text = run_cmd(["git", "diff", "HEAD"])
        if not diff_text.strip():
            code, diff_text = run_cmd(["git", "diff"])

    if not diff_text.strip():
        return issues, changed_files

    current_file = ""
    line_num = 0
    secret_re = re.compile(
        r"(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]",
        re.IGNORECASE,
    )
    except_re = re.compile(r"except(\s+Exception)?\s*:\s*pass")

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            line_num = 0
            changed_files.add(current_file)
            continue
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            if m:
                line_num = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            _check_added_line(line[1:], current_file, line_num, issues, secret_re, except_re)
            line_num += 1
        elif not line.startswith("-"):
            line_num += 1

    return issues, changed_files


def check_python_syntax(files: list[Path] | None = None) -> list[dict]:
    issues: list[dict] = []
    py_files = files if files is not None else list(Path("claraos").glob("**/*.py"))
    for py in py_files:
        if not py.exists():
            continue
        code, out = run_cmd([sys.executable, "-m", "py_compile", str(py)])
        if code != 0:
            issues.append({
                "severity": "BLOCKER",
                "file": str(py),
                "line": 0,
                "message": f"Lỗi cú pháp Python: {out.strip()}",
            })
    return issues


def check_python_ast(py_files: list[Path]) -> list[dict]:
    issues: list[dict] = []
    for py in py_files:
        if not py.exists() or not py.name.endswith(".py"):
            continue
        try:
            with open(py, "r", encoding="utf-8") as f:
                code_text = f.read()
            tree = ast.parse(code_text, filename=str(py))
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                end_lineno = getattr(node, "end_lineno", node.lineno)
                func_length = end_lineno - node.lineno + 1
                if func_length > 50:
                    issues.append({
                        "severity": "WARNING",
                        "file": str(py),
                        "line": node.lineno,
                        "message": f"Hàm '{node.name}' dài {func_length} dòng (vượt ngưỡng 50).",
                    })

                if not node.name.startswith("_") and not node.name.startswith("test_") and node.returns is None:
                    issues.append({
                        "severity": "NIT",
                        "file": str(py),
                        "line": node.lineno,
                        "message": f"Khuyến nghị PEP 484: Hàm public '{node.name}' thiếu return type.",
                    })
    return issues


def check_file_length_limits(files_to_check: list[Path] | None = None) -> list[dict]:
    issues: list[dict] = []
    extensions = {".py", ".rs", ".js", ".html"}
    ignored = {"resources", "node_modules", "target", ".git", ".venv", "apps.yaml"}

    if files_to_check is not None:
        file_list = [f for f in files_to_check if f.suffix in extensions and not any(k in str(f) for k in ignored)]
    else:
        file_list = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in ignored and not d.startswith(".")]
            for f in files:
                p = Path(root) / f
                if p.suffix in extensions and not any(k in str(p) for k in ignored):
                    file_list.append(p)

    for path in file_list:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                lines = len(fh.readlines())

            if lines > 500:
                is_pure_logic = path.suffix in {".py", ".rs", ".js"}
                sev = "BLOCKER" if is_pure_logic else "WARNING"
                issues.append({
                    "severity": sev,
                    "file": str(path),
                    "line": lines,
                    "message": f"File dài {lines} dòng (vượt ngưỡng 500 dòng). Cần tách nhỏ.",
                })
            elif lines > 300:
                issues.append({
                    "severity": "WARNING",
                    "file": str(path),
                    "line": lines,
                    "message": f"File dài {lines} dòng (vượt ngưỡng khuyến nghị 300 dòng).",
                })
        except Exception:
            continue

    return issues


def _render_summary(all_issues: list[dict]) -> int:
    print(f"\n📊 Báo cáo kết quả rà soát ({len(all_issues)} mục):")
    blockers, warnings, nits = 0, 0, 0
    prefix_map = {"BLOCKER": "🔴 [BLOCKER]", "WARNING": "🟡 [WARNING]", "NIT": "🟢 [NIT]"}

    for issue in all_issues:
        sev = issue["severity"]
        prefix = prefix_map.get(sev, "ℹ️ [INFO]")
        if sev == "BLOCKER":
            blockers += 1
        elif sev == "WARNING":
            warnings += 1
        else:
            nits += 1

        loc = f"{issue['file']}:{issue['line']}" if issue["line"] else issue["file"]
        print(f"  {prefix} ({loc}) - {issue['message']}")

    print(f"\nTổng kết: {blockers} Blocker | {warnings} Warning | {nits} Nit")
    if blockers > 0:
        print(f"❌ Có {blockers} vấn đề Blocker cần khắc phục trước khi commit!")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Code review & conventions auditor for ClaraOS.")
    parser.add_argument("--target", default=None, help="Git target ref (e.g. master, HEAD^).")
    parser.add_argument("--scan-all", action="store_true", help="Scan full project AST instead of diff.")
    args = parser.parse_args()

    target_desc = f"so với '{args.target}'" if args.target else "các thay đổi chưa commit"
    print(f"🔍 Đang rà soát mã nguồn & Coding Conventions ClaraOS ({target_desc})...")
    all_issues: list[dict] = []

    diff_issues, changed_files = check_git_diff(args.target)
    all_issues.extend(diff_issues)

    if args.target and not args.scan_all and changed_files:
        changed_py = [Path(f) for f in changed_files if f.endswith(".py")]
        changed_paths = [Path(f) for f in changed_files]
        all_issues.extend(check_python_syntax(changed_py))
        all_issues.extend(check_python_ast(changed_py))
        all_issues.extend(check_file_length_limits(changed_paths))
    else:
        all_issues.extend(check_python_syntax())
        all_issues.extend(check_python_ast(list(Path("claraos").glob("**/*.py"))))
        all_issues.extend(check_file_length_limits())

    return _render_summary(all_issues)


if __name__ == "__main__":
    sys.exit(main())
