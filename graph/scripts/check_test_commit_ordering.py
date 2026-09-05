#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试先行取证（工作包 B 放行条件之一，评审 §三：先写测试再改实现）。

检查三件事并落盘证据：
  1. 顺序：test_lifecycle_boundary.py 的首个提交早于 lifecycle_fields.py /
     lifecycle_adjudicator.py 的首个提交；
  2. 当时失败：在测试文件的提交点上开临时 worktree 跑测试，必须失败
     （实现不存在的提交上测试通过 = 测试是事后补的摆设）；
  3. 未被削弱：测试文件当前内容与提交点内容哈希一致。若确需扩展测试，
     用 --regenerate 重新取证（可见、可审计的动作）。

证据落盘：reports/lifecycle_B/test_first_evidence.json

用法：
    python graph/scripts/check_test_commit_ordering.py
    python graph/scripts/check_test_commit_ordering.py --regenerate
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_FILE = "graph/tests/test_lifecycle_boundary.py"
IMPL_FILES = (
    "graph/scripts/lifecycle_fields.py",
    "graph/scripts/lifecycle_adjudicator.py",
)
EVIDENCE_PATH = PROJECT_ROOT / "reports" / "lifecycle_B" / "test_first_evidence.json"


def git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {result.stderr.strip()}")
    return result.stdout.strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def first_commit_touching(path: str) -> str | None:
    shas = git(["log", "--follow", "--diff-filter=A", "--format=%H", "--", path]).splitlines()
    return shas[0] if shas else None


def file_content_at(commit: str, path: str) -> str:
    return git(["show", f"{commit}:{path}"])


def run_tests_at(commit: str) -> tuple[bool, str]:
    """在临时 worktree 中检出 commit 并运行 lifecycle 边界测试。返回 (通过?, 输出尾部)。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        worktree = Path(temp_dir) / "wt"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), commit],
            cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "graph.tests.test_lifecycle_boundary"],
                cwd=worktree, capture_output=True, text=True, encoding="utf-8", check=False,
            )
            output = (result.stdout or "") + (result.stderr or "")
            return result.returncode == 0, output[-1500:]
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--regenerate", action="store_true",
        help="测试文件经可见扩展后重新取证（证据仍要求：原提交点上失败 + 顺序正确）",
    )
    args = parser.parse_args()

    findings: list[str] = []
    ok = True

    test_commit = first_commit_touching(TEST_FILE)
    if test_commit is None:
        print(f"CHECK FAILED: {TEST_FILE} 尚未提交")
        return 1

    impl_commits: dict[str, str | None] = {}
    for impl in IMPL_FILES:
        impl_commits[impl] = first_commit_touching(impl)

    for impl, impl_commit in impl_commits.items():
        if impl_commit is None:
            findings.append(f"{impl} 尚未提交（测试先于实现，顺序检查放行）")
            continue
        is_ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", test_commit, impl_commit],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
        ).returncode == 0
        if is_ancestor and test_commit != impl_commit:
            findings.append(f"顺序 OK：测试提交 {test_commit[:10]} 早于 {impl} 提交 {impl_commit[:10]}")
        else:
            findings.append(f"顺序违规：{impl} 未晚于测试提交（{test_commit[:10]} vs {impl_commit[:10]}）")
            ok = False

    if ok and not args.regenerate and EVIDENCE_PATH.exists():
        evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        if evidence.get("test_commit") == test_commit:
            current_sha = sha256_text(file_content_at("HEAD", TEST_FILE))
            if current_sha == evidence.get("test_file_sha256_at_commit"):
                print("test-first 证据有效（已取证过，测试文件未变更）")
                return 0
            print("测试文件在取证后被修改——需 --regenerate 重新取证")
            ok = False

    # 当时失败：测试提交点上跑测试必须不通过
    passed_at_commit, output_tail = run_tests_at(test_commit)
    if passed_at_commit:
        findings.append("当时失败违规：测试在其提交点上竟然通过（事后摆设测试）")
        ok = False
    else:
        findings.append("当时失败 OK：测试在其提交点上失败（真实先于实现）")

    evidence = {
        "kind": "test_first_evidence.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_commit": test_commit,
        "impl_commits": impl_commits,
        "test_file_sha256_at_commit": sha256_text(file_content_at(test_commit, TEST_FILE)),
        "test_file_sha256_at_head": sha256_text(file_content_at("HEAD", TEST_FILE)),
        "failed_at_test_commit": not passed_at_commit,
        "unittest_output_tail_at_test_commit": output_tail,
        "findings": findings,
    }
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for finding in findings:
        print(f"  - {finding}")
    print(f"evidence -> {EVIDENCE_PATH}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
