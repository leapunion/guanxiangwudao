"""tests/test_publisher.py — 出版门禁 publisher.py 的测试套件。

合成经文一律使用占位符（〔测试文本甲/乙/丙…〕），禁止出现真实卦辞或爻辞。
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from gxwd.publisher import PublicationError, hash_file, request_publication
from gxwd.workflow import State, transition

# ── 测试常量 ────────────────────────────────────────────────────────────────

HEXAGRAM_ID = 37  # 家人卦（普通卦，无 yong）
APPROVER_ID = "chief-editor"
PRODUCER_ID = "researcher-01"
VERIFIER_ID = "verifier-01"
APPROVED_AT = "2026-01-02T10:00:00+08:00"

# 合成文本占位符，不含真实经文
_TEXT_PLACEHOLDER = "〔测试文本甲〕"


# ── Fixtures ────────────────────────────────────────────────────────────────


def _make_verified_text_entry(
    text_id: str,
    text_type: str,
    hexagram_id: int = HEXAGRAM_ID,
    line_position: int | str | None = None,
    line_name: str | None = None,
    text: str = _TEXT_PLACEHOLDER,
) -> dict:
    return {
        "text_id": text_id,
        "hexagram_id": hexagram_id,
        "text_type": text_type,
        "line_position": line_position,
        "line_name": line_name,
        "original_text": text,
        "source_id": "src-001",
        "edition": "通行本",
        "page": 100,
        "variant_readings": [],
        "verification_status": "verified",
    }


def _build_canonical_texts(hexagram_id: int = HEXAGRAM_ID) -> dict:
    """构造指定卦的完整、已核验经文（不含真实原文）。"""
    entries = []
    # gua_ci
    entries.append(
        _make_verified_text_entry(
            f"H{hexagram_id:02d}-gua_ci", "gua_ci", hexagram_id, None, None
        )
    )
    # tuan
    entries.append(
        _make_verified_text_entry(
            f"H{hexagram_id:02d}-tuan", "tuan", hexagram_id, None, None
        )
    )
    # da_xiang
    entries.append(
        _make_verified_text_entry(
            f"H{hexagram_id:02d}-da_xiang", "da_xiang", hexagram_id, None, None
        )
    )
    # 6 条 yao_ci（占位）
    yao_names = ["初九", "九二", "九三", "六四", "九五", "上九"]
    for pos, name in enumerate(yao_names, start=1):
        entries.append(
            _make_verified_text_entry(
                f"H{hexagram_id:02d}-yao_ci-L{pos}",
                "yao_ci",
                hexagram_id,
                pos,
                name,
            )
        )
    return {"version": "1", "entries": entries}


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_review_file(
    path: Path,
    hexagram_id: int = HEXAGRAM_ID,
    result: str = "pass",
    verifier: str = VERIFIER_ID,
) -> None:
    _write_json(path, {"hexagram_id": hexagram_id, "result": result, "verifier": verifier})


@pytest.fixture()
def pub_env(tmp_path: Path):
    """完整、合规的出版环境 fixture（data_dir、reviews_dir、approvers、catalog）。"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    reviews_dir = tmp_path / "reviews"
    reviews_dir.mkdir()

    # --- 复制主数据（不修改 data/） ---
    repo_root = Path(__file__).resolve().parents[1]
    for fname in ("hexagrams.json", "trigrams.json"):
        shutil.copy(repo_root / "data" / fname, data_dir / fname)

    # --- 经文 ---
    texts_path = data_dir / "canonical-texts.json"
    _write_json(texts_path, _build_canonical_texts())

    # --- 审查报告 ---
    _make_review_file(reviews_dir / "g1-classics.json")
    _make_review_file(reviews_dir / "g2-art.json")
    _make_review_file(reviews_dir / "g3-publication.json")
    _make_review_file(reviews_dir / "interpretation-review.json")

    # --- approvers ---
    approvers_path = data_dir / "approvers.json"
    _write_json(
        approvers_path,
        {
            "approvers": [
                {"id": APPROVER_ID, "name": "总主编", "role": "chief_editor"},
            ]
        },
    )

    # --- catalog（REVIEW_REQUIRED 状态，history actor = PRODUCER_ID）---
    # 不复用 repo 的 asset-catalog.json —— 它可能已被 autopilot 推到 PUBLISHED，
    # fixture 需要从 build_catalog 构造全新的 DRAFT 状态 catalog。
    from gxwd import catalog as catalog_mod
    from gxwd import domain as domain_mod
    catalog_path = data_dir / "asset-catalog.json"
    hexagrams = domain_mod.load_hexagrams(data_dir)
    catalog = catalog_mod.build_catalog(hexagrams)
    # 把第 37 卦推进到 REVIEW_REQUIRED
    for i, rec in enumerate(catalog["records"]):
        if rec["hexagram_id"] == HEXAGRAM_ID:
            path_states = [
                "RESEARCHED", "TEXT_VERIFIED", "ART_DRAFT",
                "ART_APPROVED", "LAYOUT_READY", "REVIEW_REQUIRED",
            ]
            for s in path_states:
                rec = transition(rec, State(s), actor=PRODUCER_ID)
            catalog["records"][i] = rec
            break
    _write_json(catalog_path, catalog)

    return {
        "data_dir": data_dir,
        "reviews_dir": reviews_dir,
        "approvers_path": approvers_path,
        "texts_path": texts_path,
        "catalog_path": catalog_path,
    }


def _call(pub_env: dict, **overrides) -> dict:
    kwargs = {
        "hexagram_id": HEXAGRAM_ID,
        "approved_by": APPROVER_ID,
        "approved_at": APPROVED_AT,
        "data_dir": pub_env["data_dir"],
        "reviews_dir": pub_env["reviews_dir"],
        "approvers_path": pub_env["approvers_path"],
    }
    kwargs.update(overrides)
    return request_publication(**kwargs)  # type: ignore[arg-type]


# ── hash_file 测试 ──────────────────────────────────────────────────────────


def test_hash_file_returns_sha256_hex(tmp_path):
    # Arrange
    f = tmp_path / "x.txt"
    f.write_bytes(b"hello")
    expected = hashlib.sha256(b"hello").hexdigest()

    # Act
    result = hash_file(f)

    # Assert
    assert result == expected
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_hash_file_different_content_different_hash(tmp_path):
    # Arrange
    f1, f2 = tmp_path / "a.txt", tmp_path / "b.txt"
    f1.write_bytes(b"aaa")
    f2.write_bytes(b"bbb")

    # Assert
    assert hash_file(f1) != hash_file(f2)


# ── 正例：合规路径全部通过 ──────────────────────────────────────────────────


def test_request_publication_success(pub_env):
    """完整合规环境下 request_publication 应成功并返回 PUBLISHED 状态。"""
    # Act
    record = _call(pub_env)

    # Assert
    assert record["state"] == "PUBLISHED"
    approval = record["approval"]
    assert approval["approved_by"] == APPROVER_ID
    assert approval["gates"] == {"G1": "passed", "G2": "passed", "G3": "passed"}
    assert approval["interpretation_review"] == "passed"
    assert "review_hashes" in approval
    assert "canonical_text_version" in approval
    assert len(approval["canonical_text_version"]) == 64


def test_request_publication_release_version_is_v1_first_time(pub_env):
    """首次出版 release_version 应为 'v1'。"""
    record = _call(pub_env)

    assert record.get("release_version") == "v1"
    assert record["approval"]["release_version"] == "v1"


def test_request_publication_review_hashes_correct(pub_env):
    """review_hashes 应与实际文件哈希一致。"""
    record = _call(pub_env)
    rh = record["approval"]["review_hashes"]

    assert rh["g1"] == hash_file(pub_env["reviews_dir"] / "g1-classics.json")
    assert rh["g2"] == hash_file(pub_env["reviews_dir"] / "g2-art.json")
    assert rh["g3"] == hash_file(pub_env["reviews_dir"] / "g3-publication.json")
    assert rh["interpretation"] == hash_file(
        pub_env["reviews_dir"] / "interpretation-review.json"
    )


# ── 反例：approved_by 不在名单 ──────────────────────────────────────────────


def test_approved_by_not_in_list_raises(pub_env):
    """approved_by 不在 approvers.json 时应抛 PublicationError。"""
    with pytest.raises(PublicationError, match="approved_by"):
        _call(pub_env, approved_by="unknown-person")


def test_approved_by_in_list_passes(pub_env):
    """approved_by 在名单中时正常通过（对偶正例）。"""
    record = _call(pub_env, approved_by=APPROVER_ID)

    assert record["state"] == "PUBLISHED"


# ── 反例：approved_by == verifier / producer ────────────────────────────────


def test_approved_by_equals_verifier_raises(pub_env):
    """approved_by 与审查报告 verifier 相同时应抛 PublicationError。"""
    # 把审批人加入 approvers，并让 verifier 也是该人
    approvers_data = json.loads(pub_env["approvers_path"].read_text("utf-8"))
    approvers_data["approvers"].append(
        {"id": VERIFIER_ID, "name": "兼任主编", "role": "verifier"}
    )
    _write_json(pub_env["approvers_path"], approvers_data)

    with pytest.raises(PublicationError, match="生产者"):
        _call(pub_env, approved_by=VERIFIER_ID)


def test_approved_by_not_equals_verifier_passes(pub_env):
    """approved_by 与 verifier 不同时正常通过（对偶正例）。"""
    record = _call(pub_env)

    assert record["approval"]["approved_by"] == APPROVER_ID
    assert record["state"] == "PUBLISHED"


def test_approved_by_equals_producer_raises(pub_env):
    """approved_by 与 catalog history actor（生产者）相同时应抛 PublicationError。"""
    # 把 PRODUCER_ID 加入 approvers
    approvers_data = json.loads(pub_env["approvers_path"].read_text("utf-8"))
    approvers_data["approvers"].append(
        {"id": PRODUCER_ID, "name": "研究员兼任", "role": "researcher"}
    )
    _write_json(pub_env["approvers_path"], approvers_data)

    with pytest.raises(PublicationError, match="生产者"):
        _call(pub_env, approved_by=PRODUCER_ID)


# ── 反例：经文仍 pending ──────────────────────────────────────────────────────


def test_pending_text_raises(pub_env):
    """有任一条 verification_status != 'verified' 时应抛 PublicationError。"""
    texts = _build_canonical_texts()
    # 把第一条改为 pending
    texts["entries"][0]["verification_status"] = "pending"
    texts["entries"][0]["original_text"] = None
    texts["entries"][0]["source_id"] = "SOURCE_PENDING"
    texts["entries"][0]["edition"] = None
    texts["entries"][0]["page"] = None
    _write_json(pub_env["texts_path"], texts)

    with pytest.raises(PublicationError, match="未核验"):
        _call(pub_env)


def test_all_texts_verified_passes(pub_env):
    """所有经文已核验时通过（对偶正例）。"""
    record = _call(pub_env)

    assert record["state"] == "PUBLISHED"


# ── 反例：审查报告缺失 ──────────────────────────────────────────────────────


@pytest.mark.parametrize("missing_file", [
    "g1-classics.json",
    "g2-art.json",
    "g3-publication.json",
    "interpretation-review.json",
])
def test_missing_review_file_raises(pub_env, missing_file):
    """任一审查报告文件缺失时应抛 PublicationError。"""
    (pub_env["reviews_dir"] / missing_file).unlink()

    with pytest.raises(PublicationError):
        _call(pub_env)


def test_all_review_files_present_passes(pub_env):
    """所有审查报告文件存在时通过（对偶正例）。"""
    record = _call(pub_env)

    assert record["state"] == "PUBLISHED"


# ── 反例：审查报告 result != pass ───────────────────────────────────────────


@pytest.mark.parametrize("fail_file,label", [
    ("g1-classics.json", "g1"),
    ("g2-art.json", "g2"),
    ("g3-publication.json", "g3"),
    ("interpretation-review.json", "interpretation-review"),
])
def test_review_result_not_pass_raises(pub_env, fail_file, label):
    """审查报告 result='fail' 时应抛 PublicationError。"""
    path = pub_env["reviews_dir"] / fail_file
    data = json.loads(path.read_text("utf-8"))
    data["result"] = "fail"
    _write_json(path, data)

    with pytest.raises(PublicationError, match="result"):
        _call(pub_env)


def test_all_reviews_pass_succeeds(pub_env):
    """所有审查报告 result='pass' 时通过（对偶正例）。"""
    record = _call(pub_env)

    assert record["approval"]["interpretation_review"] == "passed"


# ── 反例：validate_all 失败 ──────────────────────────────────────────────────


def test_validate_all_failure_raises(pub_env, tmp_path):
    """hexagrams.json 损坏时 validate_all 失败应抛 PublicationError。"""
    # 写一个只有 1 条（非 64 条）记录的 hexagrams.json
    bad_hexagrams = [
        {
            "hexagram_id": 1,
            "name": "乾",
            "full_name": "乾为天",
            "slug": "01-qian",
            "symbol": chr(0x4DC0),
            "lower_trigram": {"name": "乾", "binary": "111"},
            "upper_trigram": {"name": "乾", "binary": "111"},
            "binary_bottom_to_top": "111111",
            "lines_top_to_bottom": ["yang", "yang", "yang", "yang", "yang", "yang"],
            "text_verification": "pending",
            "artwork_status": "not_checked",
        }
    ]
    _write_json(pub_env["data_dir"] / "hexagrams.json", bad_hexagrams)

    with pytest.raises(PublicationError, match="validate_all"):
        _call(pub_env)


def test_valid_hexagrams_passes_validation(pub_env):
    """正常 hexagrams.json 通过 validate_all（对偶正例）。"""
    record = _call(pub_env)

    assert record["state"] == "PUBLISHED"


# ── 反例：canonical-texts.json 缺失 ─────────────────────────────────────────


def test_missing_canonical_texts_raises(pub_env):
    """canonical-texts.json 不存在时应抛 PublicationError。"""
    pub_env["texts_path"].unlink()

    with pytest.raises(PublicationError, match="canonical-texts.json"):
        _call(pub_env)


def test_canonical_texts_present_passes(pub_env):
    """canonical-texts.json 存在时通过（对偶正例）。"""
    record = _call(pub_env)

    assert record["state"] == "PUBLISHED"


# ── 反例：缺少必要经文类型 ──────────────────────────────────────────────────


def test_missing_gua_ci_raises(pub_env):
    """缺少 gua_ci 类型时应抛 PublicationError。"""
    texts = _build_canonical_texts()
    texts["entries"] = [e for e in texts["entries"] if e["text_type"] != "gua_ci"]
    _write_json(pub_env["texts_path"], texts)

    with pytest.raises(PublicationError, match="gua_ci"):
        _call(pub_env)


def test_insufficient_yao_ci_count_raises(pub_env):
    """yao_ci 条数不足 6 条时应抛 PublicationError。"""
    texts = _build_canonical_texts()
    # 只保留 5 条 yao_ci
    yao = [e for e in texts["entries"] if e["text_type"] == "yao_ci"][:5]
    others = [e for e in texts["entries"] if e["text_type"] != "yao_ci"]
    texts["entries"] = others + yao
    _write_json(pub_env["texts_path"], texts)

    with pytest.raises(PublicationError, match="yao_ci"):
        _call(pub_env)


# ── 乾坤额外 yong 测试 ──────────────────────────────────────────────────────


def test_qian_requires_yong(tmp_path):
    """第 1 卦（乾）缺少 yong 时应抛 PublicationError。"""
    qian_id = 1
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    repo_root = Path(__file__).resolve().parents[1]
    for fname in ("hexagrams.json", "trigrams.json"):
        shutil.copy(repo_root / "data" / fname, data_dir / fname)

    # 构造乾卦经文，但不含 yong
    entries = []
    entries.append(
        _make_verified_text_entry(f"H{qian_id:02d}-gua_ci", "gua_ci", qian_id, None, None)
    )
    entries.append(
        _make_verified_text_entry(f"H{qian_id:02d}-tuan", "tuan", qian_id, None, None)
    )
    entries.append(
        _make_verified_text_entry(f"H{qian_id:02d}-da_xiang", "da_xiang", qian_id, None, None)
    )
    yao_names = ["初九", "九二", "九三", "九四", "九五", "上九"]
    for pos, name in enumerate(yao_names, start=1):
        entries.append(
            _make_verified_text_entry(
                f"H{qian_id:02d}-yao_ci-L{pos}", "yao_ci", qian_id, pos, name
            )
        )
    # 故意省略 yong
    _write_json(data_dir / "canonical-texts.json", {"version": "1", "entries": entries})

    reviews_dir = tmp_path / "reviews"
    reviews_dir.mkdir()
    _make_review_file(reviews_dir / "g1-classics.json", qian_id)
    _make_review_file(reviews_dir / "g2-art.json", qian_id)
    _make_review_file(reviews_dir / "g3-publication.json", qian_id)
    _make_review_file(reviews_dir / "interpretation-review.json", qian_id)

    approvers_path = data_dir / "approvers.json"
    _write_json(approvers_path, {"approvers": [{"id": APPROVER_ID, "name": "总编", "role": "chief"}]})

    # 构造 catalog（从头 build，不复用 repo data/——它可能已被 autopilot 推到 PUBLISHED）
    from gxwd import catalog as catalog_mod
    from gxwd import domain as domain_mod
    hexagrams = domain_mod.load_hexagrams(data_dir)
    full_catalog = catalog_mod.build_catalog(hexagrams)
    for i, rec in enumerate(full_catalog["records"]):
        if rec["hexagram_id"] == qian_id:
            for s in ["RESEARCHED", "TEXT_VERIFIED", "ART_DRAFT", "ART_APPROVED", "LAYOUT_READY", "REVIEW_REQUIRED"]:
                rec = transition(rec, State(s), actor=PRODUCER_ID)
            full_catalog["records"][i] = rec
            break
    _write_json(data_dir / "asset-catalog.json", full_catalog)

    with pytest.raises(PublicationError, match="yong"):
        request_publication(
            qian_id,
            approved_by=APPROVER_ID,
            approved_at=APPROVED_AT,
            data_dir=data_dir,
            reviews_dir=reviews_dir,
            approvers_path=approvers_path,
        )
