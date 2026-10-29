"""gxwd 命令行入口。其他模块在子命令内延迟导入。"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STUB_EXIT = 2
STUB_MESSAGE = "not implemented in V0.1"
# (命令路径, 帮助)
STUB_COMMANDS = (
    (("research",), "研究（占位）"),
    (("art", "brief"), "艺术 Brief（占位）"),
    (("art", "create"), "作画（占位）"),
    (("verify",), "核验（占位）"),
    (("review", "queue"), "审校队列（占位）"),
)
CANONICAL_TEXTS_FILE = "canonical-texts.json"


def _data_dir() -> Path:
    env = os.environ.get("GXWD_DATA_DIR")
    return Path(env) if env else REPO_ROOT / "data"


def _err(message: str) -> None:
    print(message, file=sys.stderr)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _yao_has_text(yao_data: dict) -> bool:
    for hexagram in yao_data.get("hexagrams", []):
        entries = [*hexagram.get("lines", []), *hexagram.get("extra_lines", [])]
        if any(e.get("original_text") is not None for e in entries):
            return True
    return False


def _force_blockers(catalog_path: Path, yao_path: Path) -> list[str]:
    """--force 时返回拒绝覆盖的原因；空列表表示允许。"""
    reasons: list[str] = []
    try:
        if catalog_path.exists():
            records = json.loads(catalog_path.read_text(encoding="utf-8")).get("records", [])
            if any(r.get("state") != "DRAFT" or r.get("history") for r in records):
                reasons.append(f"登记册含非初始记录（非 DRAFT 或有 history）: {catalog_path}")
        if yao_path.exists():
            if _yao_has_text(json.loads(yao_path.read_text(encoding="utf-8"))):
                reasons.append(f"yao-texts 含已录入的 original_text: {yao_path}")
    except (ValueError, AttributeError) as exc:
        reasons.append(f"现有文件无法解析，拒绝覆盖: {exc}")
    return reasons


def _cmd_init(args: argparse.Namespace) -> int:
    from gxwd import domain, yao
    from gxwd.catalog import build_catalog, save_catalog

    data_dir = _data_dir()
    catalog_path = data_dir / "asset-catalog.json"
    yao_path = data_dir / "yao-texts.json"
    existing = [p for p in (catalog_path, yao_path) if p.exists()]
    if existing and not args.force:
        for p in existing:
            _err(f"已存在，未覆盖（使用 --force）: {p}")
        return 1
    blockers = _force_blockers(catalog_path, yao_path) if existing else []
    if blockers:
        for reason in blockers:
            _err(f"拒绝 --force: {reason}")
        return 1
    hexagrams = domain.load_hexagrams(data_dir)
    save_catalog(build_catalog(hexagrams), catalog_path)
    _write_json(
        yao_path, {"version": "1", "hexagrams": yao.build_yao_records(hexagrams)}
    )
    print(f"已生成: {catalog_path}\n已生成: {yao_path}")
    return 0


def _cmd_status(_: argparse.Namespace) -> int:
    from gxwd.catalog import load_catalog, summarize, validate_catalog

    path = _data_dir() / "asset-catalog.json"
    if not path.exists():
        _err(f"登记册不存在，请先运行 gxwd init: {path}")
        return 1
    catalog = load_catalog(path)
    errors = validate_catalog(catalog)
    if errors:
        for e in errors:
            _err(f"卦 {e['hexagram_id']} [{e['rule']}] {e['detail']}")
        return 1
    counts = summarize(catalog)
    for state, count in counts.items():
        print(f"{state}: {count}")
    print(f"已发布 {counts['PUBLISHED']}/64")
    return 0


def _cmd_hexagram_show(args: argparse.Namespace) -> int:
    from gxwd import domain

    try:
        hexagram = domain.get_hexagram(args.id, _data_dir())
    except KeyError:
        _err(f"卦不存在: {args.id}")
        return 1
    lower, upper = hexagram["lower_trigram"], hexagram["upper_trigram"]
    print(f"卦序: {hexagram['hexagram_id']}")
    print(f"卦名: {hexagram['name']}")
    print(f"全名: {hexagram['full_name']}")
    print(f"卦符: {hexagram['symbol']}")
    print(f"上卦: {upper['name']} ({upper['binary']})")
    print(f"下卦: {lower['name']} ({lower['binary']})")
    print(f"编码: {hexagram['binary_bottom_to_top']}")
    marks = {"yang": "⚊", "yin": "⚋"}
    for line in hexagram["lines_top_to_bottom"]:
        print(marks[line])
    return 0


def _validate_single_hexagram(hexagram: dict, trigrams: list[dict]) -> dict:
    """只做单卦结构校验：trigram_table + 当前卦的 _check_hexagram。"""
    from gxwd import validator

    errors = validator._check_trigram_table(trigrams)  # noqa: SLF001 — intentional reuse
    table = validator._trigram_map(trigrams)
    errors += validator._check_hexagram(hexagram, table)
    return {"valid": not errors, "checked": 1, "errors": errors}


def _cmd_validate_binary(args: argparse.Namespace) -> int:
    from gxwd import domain, validator

    if args.all == (args.id is not None):
        _err("请指定 <id> 或 --all（二选一）")
        return 1
    data_dir = _data_dir()
    trigrams = domain.load_trigrams(data_dir)
    if args.id is not None:
        try:
            hexagram = domain.get_hexagram(args.id, data_dir)
        except KeyError:
            _err(f"卦不存在: {args.id}")
            return 1
        result = _validate_single_hexagram(hexagram, trigrams)
    else:
        result = validator.validate_all(domain.load_hexagrams(data_dir), trigrams)
    if args.json:
        payload = {
            "gate": "G1",
            "hexagram_id": args.id,
            "result": "pass" if result["valid"] else "fail",
            **result,
        }
        if args.out:
            _write_json(Path(args.out), payload)
            print(f"已写入: {args.out}")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    if result["valid"]:
        label = f"卦 {args.id}" if args.id is not None else f"{result['checked']}/64"
        print(f"{label} 通过")
        return 0
    for error in result["errors"]:
        _err(f"卦 {error['hexagram_id']} [{error['rule']}] {error['detail']}")
    return 1


def _cmd_render_svg(args: argparse.Namespace) -> int:
    from gxwd import domain, renderer

    if args.all == (args.id is not None):
        _err("请指定 <id> 或 --all（二选一）")
        return 1
    data_dir = _data_dir()
    out_dir = Path(args.out) if args.out else REPO_ROOT / "assets" / "hexagram-svg"
    try:
        targets = (
            domain.load_hexagrams(data_dir)
            if args.all
            else [domain.get_hexagram(args.id, data_dir)]
        )
    except KeyError:
        _err(f"卦不存在: {args.id}")
        return 1
    for hexagram in targets:
        print(renderer.render_hexagram_file(hexagram, out_dir))
    return 0


def _cmd_texts_import(args: argparse.Namespace) -> int:
    from gxwd import domain, texts

    data_dir = _data_dir()
    sources_path = data_dir / "sources.json"
    out_path = data_dir / CANONICAL_TEXTS_FILE
    try:
        sources_doc = json.loads(sources_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _err(f"底本登记册不存在: {sources_path}")
        return 1
    if sources_doc.get("status") != "selected":
        _err(f"底本尚未选定（status={sources_doc.get('status')!r}）；无法录入经文")
        return 1
    try:
        domain.get_hexagram(args.hexagram_id, data_dir)
    except KeyError:
        _err(f"卦不存在: {args.hexagram_id}")
        return 1
    try:
        new_entries = texts.import_canonical_from_csv(
            Path(args.csv), sources_doc.get("sources", []), args.hexagram_id
        )
    except (texts.CanonicalTextError, FileNotFoundError) as exc:
        _err(f"导入失败: {exc}")
        return 1
    existing = texts.load_canonical_texts(data_dir)
    kept = [e for e in existing if e.get("hexagram_id") != args.hexagram_id]
    merged = kept + new_entries
    _write_json(out_path, {"version": "1", "entries": merged})
    print(f"已写入 {len(new_entries)} 条到: {out_path}")
    return 0


def _cmd_texts_validate(_: argparse.Namespace) -> int:
    from gxwd import domain, texts

    data_dir = _data_dir()
    entries = texts.load_canonical_texts(data_dir)
    if not entries:
        print(f"经文为空（{data_dir / CANONICAL_TEXTS_FILE} 不存在或无条目）")
        return 0
    errors = texts.validate_canonical_texts(entries, domain.load_hexagrams(data_dir))
    if not errors:
        print(f"{len(entries)} 条经文通过")
        return 0
    for error in errors:
        _err(f"{error.get('text_id', '?')} [{error['rule']}] {error['detail']}")
    return 1


def _cmd_web_build(args: argparse.Namespace) -> int:
    from gxwd import web

    out = Path(args.out) if args.out else None
    repo = Path(args.repo_root) if args.repo_root else None
    path = web.build(repo_root=repo, out_path=out)
    size_kb = path.stat().st_size / 1024
    print(f"已写入: {path} ({size_kb:.1f} KB)")
    return 0


def _cmd_publish_request(args: argparse.Namespace) -> int:
    from gxwd import domain, publisher

    try:
        domain.get_hexagram(args.id, _data_dir())
    except KeyError:
        _err(f"卦不存在: {args.id}")
        return 1
    reviews_dir = Path(args.reviews_dir) if args.reviews_dir else None
    try:
        record = publisher.request_publication(
            args.id,
            approved_by=args.approved_by,
            approved_at=args.approved_at,
            data_dir=_data_dir(),
            reviews_dir=reviews_dir,
        )
    except publisher.PublicationError as exc:
        _err(f"出版拒绝: {exc}")
        return 1
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def _cmd_stub(_: argparse.Namespace) -> int:
    _err(STUB_MESSAGE)
    return STUB_EXIT


def _add_stubs(sub: argparse._SubParsersAction) -> None:
    groups: dict[str, argparse._SubParsersAction] = {}
    for path, help_text in STUB_COMMANDS:
        parent = sub
        if len(path) == 2:
            if path[0] not in groups:
                group = sub.add_parser(path[0], help=help_text)
                groups[path[0]] = group.add_subparsers(dest=f"{path[0]}_cmd", required=True)
            parent = groups[path[0]]
        parser = parent.add_parser(path[-1], help=help_text)
        parser.add_argument("rest", nargs=argparse.REMAINDER)
        parser.set_defaults(func=_cmd_stub)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gxwd", description="观象悟道")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="生成登记册与爻结构数据")
    init.add_argument("--force", action="store_true", help="覆盖已存在文件")
    init.set_defaults(func=_cmd_init)

    sub.add_parser("status", help="登记册状态汇总").set_defaults(func=_cmd_status)

    hexagram = sub.add_parser("hexagram", help="卦主数据")
    show = hexagram.add_subparsers(dest="hexagram_cmd", required=True).add_parser(
        "show", help="显示单卦"
    )
    show.add_argument("id", type=int)
    show.set_defaults(func=_cmd_hexagram_show)

    validate = sub.add_parser("validate", help="验证")
    binary = validate.add_subparsers(dest="validate_cmd", required=True).add_parser(
        "binary", help="二进制验证"
    )
    binary.add_argument("id", type=int, nargs="?")
    binary.add_argument("--all", action="store_true")
    binary.add_argument("--json", action="store_true", help="输出结构化 JSON（G1 报告格式）")
    binary.add_argument("--out", default=None, help="写入到指定路径而不是 stdout")
    binary.set_defaults(func=_cmd_validate_binary)

    render = sub.add_parser("render", help="渲染")
    svg = render.add_subparsers(dest="render_cmd", required=True).add_parser(
        "svg", help="渲染 SVG 卦符"
    )
    svg.add_argument("id", type=int, nargs="?")
    svg.add_argument("--all", action="store_true")
    svg.add_argument("--out", default=None)
    svg.set_defaults(func=_cmd_render_svg)

    texts_parser = sub.add_parser("texts", help="经文录入与校验")
    texts_sub = texts_parser.add_subparsers(dest="texts_cmd", required=True)
    tx_import = texts_sub.add_parser("import", help="从 CSV 录入某一卦的经文")
    tx_import.add_argument("csv", help="inputs/human/*.csv")
    tx_import.add_argument("--hexagram-id", type=int, required=True)
    tx_import.set_defaults(func=_cmd_texts_import)
    tx_validate = texts_sub.add_parser("validate", help="校验 data/canonical-texts.json")
    tx_validate.set_defaults(func=_cmd_texts_validate)

    web_parser = sub.add_parser("web", help="构建只读 64 卦查看器")
    web_sub = web_parser.add_subparsers(dest="web_cmd", required=True)
    web_build = web_sub.add_parser("build", help="重建 web/index.html")
    web_build.add_argument("--out", default=None, help="输出路径，默认 <repo>/web/index.html")
    web_build.add_argument("--repo-root", default=None, help="仓库根路径，默认由模块位置推断")
    web_build.set_defaults(func=_cmd_web_build)

    publish = sub.add_parser("publish", help="出版")
    publish_sub = publish.add_subparsers(dest="publish_cmd", required=True)
    request = publish_sub.add_parser("request", help="请求出版（重算门禁）")
    request.add_argument("id", type=int)
    request.add_argument("--approved-by", required=True, help="data/approvers.json 中的 id")
    request.add_argument("--approved-at", required=True, help="ISO8601 时间")
    request.add_argument("--reviews-dir", default=None, help="默认 projects/<id:02d>-<slug>/reviews")
    request.set_defaults(func=_cmd_publish_request)

    _add_stubs(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
