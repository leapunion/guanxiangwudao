"""gxwd.web — 构建只读 64 卦查看器（self-contained HTML）。

从仓库现成的数据与资产重建，不依赖后端：
- data/hexagrams.json
- assets/hexagram-svg/<id>-<slug>.svg
- projects/<id>-<slug>/reviews/g1-binary-validation.json
- projects/<id>-<slug>/research/candidate-text-from-ching.json

公开接口：
    build(repo_root=None, out_path=None) -> Path
    collect_bundle(repo_root=None) -> dict

CLI 入口：`gxwd web build [--repo-root ...] [--out ...]`。
scripts/build-web.py 是薄壳 shim，保留历史命令兼容。
"""
from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_REPO = Path(__file__).resolve().parents[2]

# 国画风格候选归属。
# 与 docs/art-style-assignment-candidate.md 一致。
# 待艺术主编签字后，建议迁移到 data/art-style.json。
STYLE: dict[int, str] = {
    1: "G", 2: "G", 3: "S", 4: "P", 5: "M", 6: "P", 7: "P", 8: "P",
    9: "M", 10: "P", 11: "G", 12: "S", 13: "P", 14: "G", 15: "M", 16: "G",
    17: "P", 18: "P", 19: "P", 20: "M", 21: "P", 22: "M", 23: "S", 24: "G",
    25: "M", 26: "M", 27: "M", 28: "S", 29: "S", 30: "G", 31: "P", 32: "M",
    33: "M", 34: "G", 35: "G", 36: "S", 37: "P", 38: "P", 39: "S", 40: "P",
    41: "P", 42: "G", 43: "P", 44: "P", 45: "P", 46: "G", 47: "S", 48: "M",
    49: "P", 50: "P", 51: "S", 52: "M", 53: "M", 54: "P", 55: "G", 56: "P",
    57: "M", 58: "P", 59: "M", 60: "M", 61: "M", 62: "S", 63: "M", 64: "S",
}
STYLE_LABEL = {
    "G": "工写青绿",
    "M": "文人水墨",
    "S": "苍润山水",
    "P": "人物故事",
}
STYLE_COLOR = {"G": "#547A83", "M": "#273F52", "S": "#B58C69", "P": "#A74439"}
PALETTE = {
    "ink": "#273F52", "stone_blue": "#547A83", "jade": "#A2B4A1",
    "ochre": "#B58C69", "cinnabar": "#A74439", "paper": "#F5EFE2",
}


def _read_optional_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def collect_bundle(repo_root: Path | None = None) -> dict:
    repo = Path(repo_root) if repo_root is not None else _DEFAULT_REPO
    hexagrams = json.loads((repo / "data" / "hexagrams.json").read_text(encoding="utf-8"))
    items: list[dict] = []
    for h in hexagrams:
        hid, slug = h["hexagram_id"], h["slug"]
        style_code = STYLE.get(hid, "M")
        proj = repo / "projects" / f"{hid:02d}-{slug}"
        g1 = _read_optional_json(proj / "reviews" / "g1-binary-validation.json")
        cand = _read_optional_json(proj / "research" / "candidate-text-from-ching.json")
        research_dir = proj / "research"
        items.append({
            **h,
            "style_code": style_code,
            "style_label": STYLE_LABEL[style_code],
            "svg": _read_optional_text(repo / "assets" / "hexagram-svg" / f"{hid:02d}-{slug}.svg"),
            "g1_result": (g1 or {}).get("result"),
            "candidate_entries": (cand or {}).get("entries", []),
            "candidate_source": ((cand or {}).get("provenance") or {}).get("source_file"),
            # WP6 研究初稿（本轮只有第 37 卦有）
            "interpretation_md": _read_optional_text(research_dir / "interpretation.md"),
            "yao_cases": (_read_optional_json(research_dir / "yao-cases.json") or []),
            "business_philosophy_md": _read_optional_text(research_dir / "business-philosophy.md"),
            "skill_result": _read_optional_json(research_dir / "skill-result.json"),
        })
    return {
        "hexagrams": items,
        "palette": PALETTE,
        "style_labels": STYLE_LABEL,
        "style_colors": STYLE_COLOR,
        "art_style_guide_md": _read_optional_text(repo / "docs" / "art-style-guide.md"),
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>观象悟道 · 六十四卦查看器</title>
<style>
:root {
  --ink: #273F52;
  --stone-blue: #547A83;
  --jade: #A2B4A1;
  --ochre: #B58C69;
  --cinnabar: #A74439;
  --paper: #F5EFE2;
  --paper-shade: #ECE5D4;
  --divider: rgba(39,63,82,0.15);
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  font-family: -apple-system, "PingFang SC", "Noto Serif CJK SC", "Songti SC", serif;
  background: var(--paper);
  color: var(--ink);
}
header {
  padding: 20px 32px 12px;
  border-bottom: 1px solid var(--divider);
  background: var(--paper);
  position: sticky; top: 0; z-index: 10;
}
h1 {
  margin: 0;
  font-size: 24px;
  letter-spacing: 2px;
  font-weight: 500;
}
.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--stone-blue);
  letter-spacing: 1px;
}
nav.filters {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.filter-btn {
  padding: 6px 14px;
  border: 1px solid var(--divider);
  background: transparent;
  color: var(--ink);
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  border-radius: 2px;
  transition: all 0.2s;
}
.filter-btn:hover { background: var(--paper-shade); }
.filter-btn.active {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
}
.filter-label { font-size: 12px; color: var(--stone-blue); margin-right: 4px; }
main {
  display: grid;
  grid-template-columns: 1fr 480px;
  min-height: calc(100vh - 110px);
}
.grid {
  padding: 24px 32px;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 10px;
  align-content: start;
}
.cell {
  background: var(--paper-shade);
  border: 1px solid transparent;
  cursor: pointer;
  padding: 10px 6px 8px;
  text-align: center;
  position: relative;
  transition: all 0.15s;
  border-radius: 2px;
}
.cell:hover {
  background: var(--paper);
  border-color: var(--divider);
  transform: translateY(-1px);
}
.cell.active {
  background: var(--paper);
  border-color: var(--ink);
  box-shadow: 0 2px 6px rgba(39,63,82,0.1);
}
.cell.dim { opacity: 0.22; }
.cell svg {
  width: 100%;
  height: auto;
  max-width: 56px;
  display: block;
  margin: 0 auto 4px;
}
.cell .id {
  font-size: 10px;
  color: var(--stone-blue);
  letter-spacing: 1px;
}
.cell .name {
  font-size: 13px;
  margin-top: 1px;
  color: var(--ink);
}
.cell .style-dot {
  position: absolute;
  top: 4px; right: 4px;
  width: 6px; height: 6px;
  border-radius: 50%;
}
aside {
  background: var(--paper-shade);
  border-left: 1px solid var(--divider);
  padding: 24px 28px;
  overflow-y: auto;
  max-height: calc(100vh - 110px);
}
.detail-empty { color: var(--stone-blue); font-size: 13px; }
.detail h2 {
  margin: 0 0 4px;
  font-size: 20px;
  letter-spacing: 2px;
}
.detail .full-name {
  color: var(--stone-blue);
  font-size: 13px;
  letter-spacing: 1px;
  margin-bottom: 14px;
}
.detail .big-svg {
  background: var(--paper);
  padding: 12px;
  margin-bottom: 14px;
  border: 1px solid var(--divider);
  display: flex; justify-content: center;
}
.detail .big-svg svg { width: 180px; height: 180px; }
.detail .meta {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 4px 12px;
  font-size: 13px;
  margin-bottom: 14px;
}
.detail .meta .k { color: var(--stone-blue); }
.detail .meta .v { color: var(--ink); font-family: ui-monospace, "SF Mono", Menlo, monospace; }
.detail .section-title {
  font-size: 12px;
  color: var(--stone-blue);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin: 18px 0 8px;
  border-bottom: 1px solid var(--divider);
  padding-bottom: 4px;
}
.entry {
  margin-bottom: 10px;
  font-size: 13px;
  line-height: 1.75;
}
.entry .label {
  color: var(--stone-blue);
  font-size: 11px;
  letter-spacing: 1px;
  margin-right: 6px;
}
.entry .text { color: var(--ink); }
.badge {
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  letter-spacing: 1px;
  background: var(--jade);
  color: var(--paper);
  border-radius: 2px;
}
.badge.cinnabar { background: var(--cinnabar); }
.badge.ochre { background: var(--ochre); }
.candidate-note {
  background: var(--paper);
  padding: 8px 12px;
  font-size: 11px;
  color: var(--stone-blue);
  line-height: 1.6;
  border-left: 2px solid var(--ochre);
  margin: 10px 0;
}
.md { font-size: 13px; line-height: 1.75; color: var(--ink); }
.md h3, .md h4, .md h5 { color: var(--ink); margin: 14px 0 6px; font-weight: 500; }
.md h3 { font-size: 15px; letter-spacing: 1px; border-bottom: 1px solid var(--divider); padding-bottom: 3px; }
.md h4 { font-size: 14px; color: var(--stone-blue); }
.md p { margin: 6px 0; }
.md ul { margin: 6px 0; padding-left: 20px; }
.md li { margin: 2px 0; }
.md code { background: var(--paper); padding: 1px 5px; font-size: 12px; font-family: ui-monospace, "SF Mono", Menlo, monospace; }
.md code.xref { color: var(--cinnabar); background: transparent; }
.about {
  padding: 24px 32px;
  border-top: 1px solid var(--divider);
  background: var(--paper-shade);
}
.about details { margin-top: 8px; }
.about summary {
  cursor: pointer;
  padding: 8px 0;
  font-size: 13px;
  letter-spacing: 1px;
  color: var(--stone-blue);
}
.about summary:hover { color: var(--ink); }
.about .md { max-width: 820px; }
footer {
  text-align: center;
  padding: 12px;
  font-size: 11px;
  color: var(--stone-blue);
  border-top: 1px solid var(--divider);
}
@media (max-width: 1000px) {
  main { grid-template-columns: 1fr; }
  aside { border-left: none; border-top: 1px solid var(--divider); max-height: none; }
  .grid { grid-template-columns: repeat(4, 1fr); }
}
</style>
</head>
<body>
<header>
  <h1>观象悟道 · 六十四卦查看器</h1>
  <div class="subtitle">I Ching 64 Hexagrams · Chinese Classics &amp; Ink Painting Agentic Studio</div>
  <nav class="filters" id="filters">
    <span class="filter-label">国画风格：</span>
    <button class="filter-btn active" data-style="all">全部</button>
  </nav>
</header>
<main>
  <section class="grid" id="grid"></section>
  <aside id="detail">
    <div class="detail-empty">← 点击任一卦查看详情</div>
  </aside>
</main>
<section class="about">
  <details>
    <summary>国画风格规范（docs/art-style-guide.md）</summary>
    <div class="md" id="art-style-md"></div>
  </details>
</section>
<footer id="footer"></footer>
<script id="data" type="application/json">__DATA_PLACEHOLDER__</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const grid = document.getElementById("grid");
const filters = document.getElementById("filters");
const detail = document.getElementById("detail");
const footer = document.getElementById("footer");

let activeStyle = "all";
let activeId = null;

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
}

/** 极简 markdown → HTML（支持 # 标题、- 列表、空行分段、`inline code`、**粗体**、
 *  [[text]] 显示为 <code>text</code>）。够看结构，不是完整 CommonMark。 */
function mdToHtml(md) {
  if (!md) return "";
  const lines = md.replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let inList = false, inPara = [];
  const flushPara = () => {
    if (inPara.length) {
      let text = escapeHtml(inPara.join(" "));
      text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
      text = text.replace(/\[\[([^\]]+)\]\]/g, '<code class="xref">$1</code>');
      html.push(`<p>${text}</p>`);
      inPara = [];
    }
  };
  const closeList = () => { if (inList) { html.push("</ul>"); inList = false; } };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) { flushPara(); closeList(); continue; }
    const h = line.match(/^(#{1,6})\s+(.+)/);
    if (h) {
      flushPara(); closeList();
      const level = Math.min(h[1].length + 2, 6);  // 文档 # 对应 h3
      html.push(`<h${level}>${escapeHtml(h[2])}</h${level}>`);
      continue;
    }
    const li = line.match(/^[-*]\s+(.+)/);
    if (li) {
      flushPara();
      if (!inList) { html.push("<ul>"); inList = true; }
      let text = escapeHtml(li[1]);
      text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
      text = text.replace(/\[\[([^\]]+)\]\]/g, '<code class="xref">$1</code>');
      html.push(`<li>${text}</li>`);
      continue;
    }
    closeList();
    inPara.push(line);
  }
  flushPara(); closeList();
  return html.join("\n");
}

function renderFilters() {
  for (const [code, label] of Object.entries(DATA.style_labels)) {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.dataset.style = code;
    btn.textContent = `${code} ${label}`;
    btn.style.borderColor = DATA.style_colors[code];
    filters.appendChild(btn);
  }
  filters.addEventListener("click", (e) => {
    if (!e.target.matches(".filter-btn")) return;
    activeStyle = e.target.dataset.style;
    [...filters.querySelectorAll(".filter-btn")].forEach(b => b.classList.toggle("active", b.dataset.style === activeStyle));
    renderGrid();
  });
}

function renderGrid() {
  grid.innerHTML = "";
  for (const h of DATA.hexagrams) {
    const cell = document.createElement("div");
    cell.className = "cell";
    const matches = activeStyle === "all" || h.style_code === activeStyle;
    if (!matches) cell.classList.add("dim");
    if (h.hexagram_id === activeId) cell.classList.add("active");
    cell.innerHTML = `
      <div class="style-dot" style="background:${DATA.style_colors[h.style_code]}"></div>
      ${h.svg}
      <div class="id">${String(h.hexagram_id).padStart(2, "0")}</div>
      <div class="name">${h.name}</div>
    `;
    cell.addEventListener("click", () => {
      activeId = h.hexagram_id;
      renderGrid();
      renderDetail(h);
    });
    grid.appendChild(cell);
  }
}

function renderDetail(h) {
  const typeLabel = {
    gua_ci: "卦辞", tuan: "彖传", da_xiang: "大象传",
    yao_ci: "爻辞", xiao_xiang: "小象", yong: "用爻",
  };
  const sortKey = { gua_ci: 0, tuan: 1, da_xiang: 2, yao_ci: 3, xiao_xiang: 4, yong: 5 };
  const entries = [...h.candidate_entries].sort((a, b) => {
    const ka = sortKey[a.text_type] || 9;
    const kb = sortKey[b.text_type] || 9;
    if (ka !== kb) return ka - kb;
    const la = a.line_position || 0;
    const lb = b.line_position || 0;
    return (typeof la === "number" ? la : 7) - (typeof lb === "number" ? lb : 7);
  });

  const g1Badge = h.g1_result === "pass"
    ? `<span class="badge">G1 pass</span>`
    : h.g1_result === "fail"
    ? `<span class="badge cinnabar">G1 fail</span>`
    : `<span class="badge ochre">G1 —</span>`;

  detail.innerHTML = `
    <div class="detail">
      <h2>第 ${h.hexagram_id} 卦 · ${h.name}</h2>
      <div class="full-name">${h.full_name} · ${h.symbol}</div>
      <div class="big-svg">${h.svg}</div>
      <div class="meta">
        <div class="k">上卦</div><div class="v">${h.upper_trigram.name} (${h.upper_trigram.binary})</div>
        <div class="k">下卦</div><div class="v">${h.lower_trigram.name} (${h.lower_trigram.binary})</div>
        <div class="k">编码</div><div class="v">${h.binary_bottom_to_top}</div>
        <div class="k">显示</div><div class="v">${h.lines_top_to_bottom.map(l => l === "yang" ? "⚊" : "⚋").join(" ")}</div>
      </div>
      <div style="margin: 10px 0;">
        <span class="badge" style="background:${DATA.style_colors[h.style_code]}">${h.style_code} ${h.style_label}</span>
        ${g1Badge}
      </div>
      <div class="section-title">候选经文（来自 Ching · 通行本）</div>
      <div class="candidate-note">
        仅作参考；本项目 <code>data/canonical-texts.json</code> 本轮仍空。
        主编对实物签字后才会进 L0。来源：${escapeHtml(h.candidate_source || "—")}
      </div>
      ${entries.length === 0 ? '<div class="detail-empty">暂无候选条目</div>' : entries.map(e => `
        <div class="entry">
          <span class="label">${typeLabel[e.text_type] || e.text_type}${e.line_name ? " · " + escapeHtml(e.line_name) : ""}</span>
          <span class="text">${escapeHtml(e.candidate_text)}</span>
        </div>
      `).join("")}
      ${renderResearch(h)}
    </div>
  `;
}

function renderResearch(h) {
  const hasAny = h.interpretation_md || (h.yao_cases && h.yao_cases.length) || h.business_philosophy_md;
  if (!hasAny) return "";
  const yaoCasesBlock = (h.yao_cases && h.yao_cases.length) ? `
    <div class="section-title">六爻历史故事（WP6 研究稿，候选等级 A/B/C/D）</div>
    ${h.yao_cases.map(yc => `
      <div class="entry">
        <span class="label">${yc.line_position}爻</span>
        ${(yc.candidates && yc.candidates.length) ? yc.candidates.map(c => `
          <div style="margin-left: 10px; margin-top: 4px;">
            <span class="badge ochre">${escapeHtml(c.evidence_grade)}</span>
            <strong>${escapeHtml(c.title || "")}</strong> · ${escapeHtml(c.summary || "")}
          </div>
        `).join("") : `<span class="detail-empty"> ${escapeHtml(yc.note || "尚无案例")}</span>`}
      </div>
    `).join("")}
  ` : "";
  return `
    <div class="section-title">研究初稿（WP6 · classics-researcher）</div>
    <div class="candidate-note">
      本节内容是 Agent 产出的研究草稿。涉及经文均以 <code class="xref">[[H.. ..]]</code> 的
      text_id 引用，不摘抄原文。
    </div>
    ${h.interpretation_md ? `<div class="md">${mdToHtml(h.interpretation_md)}</div>` : ""}
    ${yaoCasesBlock}
    ${h.business_philosophy_md ? `
      <div class="section-title">企业哲学映射</div>
      <div class="md">${mdToHtml(h.business_philosophy_md)}</div>
    ` : ""}
  `;
}

function renderFooter() {
  const total = DATA.hexagrams.length;
  const g1pass = DATA.hexagrams.filter(h => h.g1_result === "pass").length;
  const candidates = DATA.hexagrams.filter(h => h.candidate_entries.length > 0).length;
  footer.innerHTML = `${total} 卦 · G1 通过 ${g1pass}/${total} · 候选经文 ${candidates}/${total} · 本页面为只读查看器，不修改任何数据`;
}

renderFilters();
renderGrid();
renderFooter();
document.getElementById("art-style-md").innerHTML = mdToHtml(DATA.art_style_guide_md || "");
</script>
</body>
</html>
"""


def build(repo_root: Path | None = None, out_path: Path | None = None) -> Path:
    repo = Path(repo_root) if repo_root is not None else _DEFAULT_REPO
    out = Path(out_path) if out_path is not None else (repo / "web" / "index.html")
    bundle = collect_bundle(repo)
    data_json = json.dumps(bundle, ensure_ascii=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(HTML_TEMPLATE.replace("__DATA_PLACEHOLDER__", data_json), encoding="utf-8")
    return out


def serve(
    repo_root: Path | None = None,
    port: int = 8000,
    host: str = "127.0.0.1",
    build_first: bool = True,
) -> None:
    """启本地静态服务；阻塞运行到 Ctrl-C。"""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    repo = Path(repo_root) if repo_root is not None else _DEFAULT_REPO
    web_dir = repo / "web"
    if build_first:
        build(repo_root=repo)
    handler = partial(SimpleHTTPRequestHandler, directory=str(web_dir))
    with ThreadingHTTPServer((host, port), handler) as srv:
        url = f"http://{host}:{port}/index.html"
        print(f"serving {web_dir} at {url}（Ctrl-C 停止）", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("stopped")


def main(argv: list[str] | None = None) -> int:
    out = build()
    size_kb = out.stat().st_size / 1024
    print(f"wrote: {out} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
