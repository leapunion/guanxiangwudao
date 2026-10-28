import json
import shutil
from pathlib import Path

import pytest

from gxwd.cli import main

REPO_DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.mark.parametrize(
    "argv",
    [
        ["research", "37"],
        ["art", "brief", "37"],
        ["art", "create", "37"],
        ["verify", "37"],
        ["publish", "card", "37"],
        ["publish", "book"],
        ["review", "queue"],
    ],
)
def test_stub_commands_return_2(argv, capsys):
    code = main(argv)

    captured = capsys.readouterr()
    assert code == 2
    assert "not implemented in V0.1" in captured.err
    assert captured.out == ""


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    for name in ("hexagrams.json", "trigrams.json"):
        assert (REPO_DATA / name).exists(), f"data/{name} 缺失"
        shutil.copy(REPO_DATA / name, tmp_path / name)
    monkeypatch.setenv("GXWD_DATA_DIR", str(tmp_path))
    return tmp_path


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_init_creates_files_and_refuses_overwrite(data_dir, capsys):
    assert main(["init"]) == 0
    catalog = json.loads((data_dir / "asset-catalog.json").read_text(encoding="utf-8"))
    yao = json.loads((data_dir / "yao-texts.json").read_text(encoding="utf-8"))
    assert len(catalog["records"]) == 64
    assert yao["version"] == "1" and len(yao["hexagrams"]) == 64

    (data_dir / "asset-catalog.json").write_text("{}", encoding="utf-8")
    assert main(["init"]) == 1
    assert (data_dir / "asset-catalog.json").read_text(encoding="utf-8") == "{}"
    assert main(["init", "--force"]) == 0
    assert len(json.loads((data_dir / "asset-catalog.json").read_text())["records"]) == 64


def test_status_prints_counts(data_dir, capsys):
    main(["init"])
    capsys.readouterr()

    code = main(["status"])

    out = capsys.readouterr().out
    assert code == 0
    assert "DRAFT: 64" in out
    assert "已发布 0/64" in out


def test_hexagram_show_prints_details(data_dir, capsys):
    code = main(["hexagram", "show", "37"])

    out = capsys.readouterr().out
    assert code == 0
    assert "家人" in out and "风火家人" in out and "101011" in out
    assert "⚊" in out and "⚋" in out


def test_hexagram_show_unknown_id_returns_1(data_dir, capsys):
    code = main(["hexagram", "show", "999"])

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err != ""


def test_validate_binary_all_passes(data_dir, capsys):
    code = main(["validate", "binary", "--all"])

    assert code == 0
    assert "64/64 通过" in capsys.readouterr().out


def test_render_svg_all_writes_64_files(data_dir, tmp_path, capsys):
    out_dir = tmp_path / "svg"

    code = main(["render", "svg", "--all", "--out", str(out_dir)])

    assert code == 0
    assert len(list(out_dir.glob("*.svg"))) == 64


def test_render_svg_single(data_dir, tmp_path):
    out_dir = tmp_path / "svg"

    code = main(["render", "svg", "37", "--out", str(out_dir)])

    assert code == 0
    assert [p.name for p in out_dir.glob("*.svg")] == ["37-jiaren.svg"]


def test_status_rejects_published_without_approval(data_dir, capsys):
    main(["init"])
    path = data_dir / "asset-catalog.json"
    catalog = _read(path)
    catalog["records"][0]["state"] = "PUBLISHED"
    _write(path, catalog)
    capsys.readouterr()

    code = main(["status"])

    captured = capsys.readouterr()
    assert code == 1
    assert "已发布" not in captured.out
    assert "published_approval" in captured.err


def test_init_force_refuses_non_draft_record(data_dir, capsys):
    main(["init"])
    path = data_dir / "asset-catalog.json"
    catalog = _read(path)
    catalog["records"][0]["state"] = "RESEARCHED"
    _write(path, catalog)
    before = path.read_text(encoding="utf-8")

    code = main(["init", "--force"])

    assert code == 1
    assert path.read_text(encoding="utf-8") == before
    assert "拒绝 --force" in capsys.readouterr().err


def test_init_force_refuses_filled_original_text(data_dir):
    main(["init"])
    yao_path = data_dir / "yao-texts.json"
    yao = _read(yao_path)
    yao["hexagrams"][0]["extra_lines"][0]["original_text"] = "见群龙无首"
    _write(yao_path, yao)
    before = yao_path.read_text(encoding="utf-8")

    code = main(["init", "--force"])

    assert code == 1
    assert yao_path.read_text(encoding="utf-8") == before


def test_init_force_allows_pristine_state(data_dir):
    main(["init"])

    code = main(["init", "--force"])

    assert code == 0
