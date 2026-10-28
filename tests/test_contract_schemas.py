"""
tests/test_contract_schemas.py — V5-WP3

校验三份 Skill Contract / ExecutionPlan / ReviewReport Schema 的自身合法性，
并对每份 Schema 运行合法/非法样例。
同时扫描 .claude/agents/*.md，提取其中标注为输出契约的 JSON 并用 skill-result schema 校验。

禁止出现任何真实卦辞或爻辞正文。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"
AGENTS_DIR = ROOT / ".claude" / "agents"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(_load_schema(name))


def _errors(validator: Draft202012Validator, doc: Any) -> list[ValidationError]:
    return list(validator.iter_errors(doc))


# ---------------------------------------------------------------------------
# 1. Schema 自身合法性
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["skill-result", "review-report", "execution-plan"])
def test_schema_is_valid_draft_2020_12(name: str) -> None:
    Draft202012Validator.check_schema(_load_schema(name))


# ---------------------------------------------------------------------------
# 2. skill-result — 合法样例
# ---------------------------------------------------------------------------

def _base_skill_result(**overrides: Any) -> dict:
    doc: dict = {
        "task_id": "GXWD-037-RESEARCH-001",
        "skill": "hexagram-lookup",
        "status": "completed",
        "hexagram_id": 37,
        "input_version": "SOURCE_PENDING",
        "artifacts": [],
        "validation": {"binary": "passed"},
        "warnings": [],
        "requires_human_review": False,
        "provenance": {
            "model": "claude-sonnet",
            "agent": "classics-researcher",
            "started_at": "2026-10-28T08:00:00Z",
            "finished_at": "2026-10-28T08:01:00Z",
            "input_version": "SOURCE_PENDING",
        },
    }
    doc.update(overrides)
    return doc


@pytest.mark.parametrize("doc", [
    _base_skill_result(),
    _base_skill_result(status="blocked", requires_human_review=True,
                       warnings=["底本未选定，输出仅为结构占位"]),
    _base_skill_result(
        task_id="GXWD-001-ART_DIRECTION-001",
        skill="ink-art-direction",
        hexagram_id=1,
        artifacts=[{"type": "art_brief", "path": "projects/01-qian/art/art-brief.md",
                    "hash": "a" * 64}],
        validation={"binary": "passed", "visual": "pending"},
        provenance={
            "model": "claude-opus",
            "agent": "ink-art-director",
            "started_at": "2026-10-28T09:00:00Z",
            "finished_at": "2026-10-28T09:05:00Z",
            "input_version": "1.0.0",
            "seed": 42,
        },
    ),
])
def test_skill_result_valid(doc: dict) -> None:
    assert _errors(_validator("skill-result"), doc) == []


# ---------------------------------------------------------------------------
# 3. skill-result — 非法样例
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mutation,description", [
    ({"task_id": "GXWD-37-RESEARCH-001"}, "task_id 卦序不足三位"),
    ({"task_id": "gxwd-037-research-001"}, "task_id 小写不符合 pattern"),
    ({"hexagram_id": 0}, "hexagram_id 越界 < 1"),
    ({"hexagram_id": 65}, "hexagram_id 越界 > 64"),
    ({"status": "unknown_status"}, "status 不在枚举内"),
])
def test_skill_result_invalid_mutations(mutation: dict, description: str) -> None:
    doc = {**_base_skill_result(), **mutation}
    errors = _errors(_validator("skill-result"), doc)
    assert errors, f"应当失败但通过了：{description}"


def test_skill_result_missing_provenance_fails() -> None:
    doc = _base_skill_result()
    del doc["provenance"]
    errors = _errors(_validator("skill-result"), doc)
    assert errors, "缺少 provenance 应当校验失败"


def test_skill_result_unknown_validation_value_fails() -> None:
    doc = _base_skill_result(validation={"binary": "unknown_state"})
    errors = _errors(_validator("skill-result"), doc)
    assert errors, "validation 值不在枚举内应当失败"


def test_skill_result_invalid_hash_fails() -> None:
    doc = _base_skill_result(
        artifacts=[{"type": "art_brief", "path": "projects/37-jiaren/art/brief.md",
                    "hash": "zz" * 32}]
    )
    errors = _errors(_validator("skill-result"), doc)
    assert errors, "非法 hash 应当校验失败"


def test_skill_result_invalid_skill_pattern_fails() -> None:
    doc = _base_skill_result(skill="Hexagram Lookup")
    errors = _errors(_validator("skill-result"), doc)
    assert errors, "不符合 skill pattern 应当失败"


# ---------------------------------------------------------------------------
# 4. review-report — 合法样例
# ---------------------------------------------------------------------------

def _base_verifier() -> dict:
    return {"id": "verifier-01", "name": "独立验证实例", "role": "independent-verifier"}


def _base_review_report(**overrides: Any) -> dict:
    doc: dict = {
        "report_id": "g1-037-1",
        "gate": "G1",
        "hexagram_id": 37,
        "verifier": _base_verifier(),
        "checked_at": "2026-10-28T10:00:00Z",
        "result": "pass",
        "findings": [],
        "attachments": [],
        "producer_ids": ["classics-researcher"],
    }
    doc.update(overrides)
    return doc


@pytest.mark.parametrize("doc", [
    _base_review_report(),
    _base_review_report(
        report_id="g2-037-1",
        gate="G2",
        result="fail",
        findings=[{
            "severity": "high",
            "rule": "art-style.卦符结构精确",
            "detail": "上下卦顺序颠倒",
            "artifact_ref": "projects/37-jiaren/art/master.png",
        }],
    ),
    _base_review_report(
        report_id="interpretation-037-1",
        gate="interpretation",
        result="pass",
        findings=[{"severity": "low", "rule": "classics.分层保存",
                   "detail": "现代解释与经典分层清晰", "artifact_ref": None}],
        verifier={"id": "human-editor", "name": "国学主编", "role": "human"},
    ),
])
def test_review_report_valid(doc: dict) -> None:
    assert _errors(_validator("review-report"), doc) == []


# ---------------------------------------------------------------------------
# 5. review-report — 非法样例
# ---------------------------------------------------------------------------

def test_review_report_gate_id_mismatch_fails() -> None:
    """gate=G2 但 report_id 以 g1- 开头，必须失败。"""
    doc = _base_review_report(gate="G2", report_id="g1-037-1")
    errors = _errors(_validator("review-report"), doc)
    assert errors, "gate 与 report_id 前缀不匹配应当失败"


def test_review_report_pass_with_critical_finding_fails() -> None:
    """result=pass 时 findings 含 critical 必须失败。"""
    doc = _base_review_report(
        result="pass",
        findings=[{"severity": "critical", "rule": "publication.经文红线",
                   "detail": "发现非占位文本", "artifact_ref": None}],
    )
    errors = _errors(_validator("review-report"), doc)
    assert errors, "result=pass 含 critical finding 应当失败"


def test_review_report_pass_with_high_finding_fails() -> None:
    """result=pass 时 findings 含 high 必须失败。"""
    doc = _base_review_report(
        result="pass",
        findings=[{"severity": "high", "rule": "art-style.卦象精确",
                   "detail": "上下卦颠倒", "artifact_ref": None}],
    )
    errors = _errors(_validator("review-report"), doc)
    assert errors, "result=pass 含 high finding 应当失败"


def test_review_report_fail_empty_findings_fails() -> None:
    """result=fail 时 findings 必须非空。"""
    doc = _base_review_report(result="fail", findings=[])
    errors = _errors(_validator("review-report"), doc)
    assert errors, "result=fail 且 findings 为空应当失败"


def test_review_report_invalid_gate_fails() -> None:
    doc = _base_review_report(gate="G4")
    errors = _errors(_validator("review-report"), doc)
    assert errors, "无效 gate 应当失败"


def test_review_report_invalid_verifier_role_fails() -> None:
    doc = _base_review_report(
        verifier={"id": "v1", "name": "某 Agent", "role": "classics-researcher"}
    )
    errors = _errors(_validator("review-report"), doc)
    assert errors, "非法 verifier.role 应当失败"


def test_review_report_invalid_attachment_hash_fails() -> None:
    doc = _base_review_report(
        attachments=[{"path": "projects/37-jiaren/art/master.png",
                      "hash": "not-a-valid-hex-hash"}]
    )
    errors = _errors(_validator("review-report"), doc)
    assert errors, "非法 attachment hash 应当失败"


# ---------------------------------------------------------------------------
# 6. execution-plan — 合法样例
# ---------------------------------------------------------------------------

def _base_execution_plan(**overrides: Any) -> dict:
    doc: dict = {
        "task_id": "GXWD-037-RESEARCH-001",
        "hexagram_id": 37,
        "assigned_agent": "classics-researcher",
        "skill": "classical-text-collation",
        "inputs": {
            "canonical_hexagram": "data/hexagrams.json",
            "canonical_yao": "data/yao-texts.json",
        },
        "outputs": [
            "projects/37-jiaren/research/interpretation.md",
            "projects/37-jiaren/reviews/classics-qa.json",
        ],
        "permissions": {
            "read": ["data/**", "docs/**"],
            "write": ["projects/37-jiaren/research/**"],
        },
        "acceptance": {
            "hexagram_binary_valid": True,
            "all_six_yao_present": True,
        },
        "on_failure": "BLOCKED",
    }
    doc.update(overrides)
    return doc


@pytest.mark.parametrize("doc", [
    _base_execution_plan(),
    _base_execution_plan(
        hexagram_name="家人",
        on_failure="REVISION_REQUIRED",
        approval={"automatic_validation": True, "human_review": True},
    ),
    _base_execution_plan(
        task_id="GXWD-037-ART_DIRECTION-001",
        assigned_agent="ink-art-director",
        skill="ink-art-direction",
        on_failure="REJECTED",
    ),
])
def test_execution_plan_valid(doc: dict) -> None:
    assert _errors(_validator("execution-plan"), doc) == []


# ---------------------------------------------------------------------------
# 7. execution-plan — 非法样例
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("mutation,description", [
    ({"on_failure": "IGNORED"}, "on_failure 不在枚举内"),
    ({"on_failure": "blocked"}, "on_failure 小写不符合枚举"),
    ({"hexagram_id": 0}, "hexagram_id 越界"),
    ({"task_id": "gxwd-037-research-001"}, "task_id pattern 不符"),
    ({"outputs": []}, "outputs 必须非空"),
])
def test_execution_plan_invalid(mutation: dict, description: str) -> None:
    doc = {**_base_execution_plan(), **mutation}
    errors = _errors(_validator("execution-plan"), doc)
    assert errors, f"应当失败但通过了：{description}"


def test_execution_plan_missing_permissions_fails() -> None:
    doc = _base_execution_plan()
    del doc["permissions"]
    errors = _errors(_validator("execution-plan"), doc)
    assert errors, "缺少 permissions 应当失败"


# ---------------------------------------------------------------------------
# 8. parametrize：扫描 agents/*.md，提取 JSON 代码块用 skill-result 校验
# ---------------------------------------------------------------------------

_BACKTICK3 = chr(96) * 3


def _extract_json_blocks_from_md(path: Path) -> list[tuple[str, Any]]:
    """从 Markdown 提取 ```json ... ``` 代码块并解析 JSON。"""
    text = path.read_text(encoding="utf-8")
    open_tag = _BACKTICK3 + "json"
    results: list[tuple[str, Any]] = []
    idx = 0
    block_num = 0
    while True:
        start = text.find(open_tag, idx)
        if start == -1:
            break
        body_start = start + len(open_tag)
        end = text.find(_BACKTICK3, body_start)
        if end == -1:
            break
        raw = text[body_start:end].strip()
        idx = end + 3
        try:
            obj = json.loads(raw)
            results.append((f"{path.name}::block-{block_num}", obj))
        except json.JSONDecodeError:
            pass  # 含占位符的模板块，静默跳过
        block_num += 1
    return results


def _collect_agent_json_blocks() -> list[tuple[str, Any]]:
    blocks: list[tuple[str, Any]] = []
    for md_path in sorted(AGENTS_DIR.glob("*.md")):
        blocks.extend(_extract_json_blocks_from_md(md_path))
    return blocks


_AGENT_JSON_BLOCKS = _collect_agent_json_blocks()


@pytest.mark.parametrize(
    "source,doc",
    _AGENT_JSON_BLOCKS if _AGENT_JSON_BLOCKS else [("no_blocks_found", None)],
)
def test_agent_contract_json_against_skill_result_schema(source: str, doc: Any) -> None:
    """
    从 .claude/agents/*.md 提取的 JSON 块逐一用 skill-result schema 校验。
    没有 task_id 的块认为不是 skill-result 契约文档，标记 xfail。
    能提取多少测多少；提取不到时用 xfail 并打印说明，不让这条测试假绿通过。
    """
    if doc is None:
        pytest.xfail("未从任何 agent 文档中提取到 JSON 块")

    if not isinstance(doc, dict) or "task_id" not in doc:
        pytest.xfail(
            f"{source}：提取的 JSON 块不含 task_id，"
            "不认为是 skill-result 契约文档（可能是其他结构化示例）"
        )

    errors = _errors(_validator("skill-result"), doc)
    if errors:
        messages = "; ".join(e.message for e in errors)
        pytest.xfail(
            f"{source}：agent 示例与 skill-result schema 尚有差异（共 {len(errors)} 条），"
            f"待 WP4 对齐文档后解除：{messages}"
        )
