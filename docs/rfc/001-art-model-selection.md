# RFC 001 · 国画生成模型选型

- **状态**：Proposed
- **作者**：research pass by autopilot agent
- **日期**：2026-11-03
- **影响范围**：`.claude/rules/art-style.md`、`docs/image-and-licensing-decisions.md`、未来 `art/` 层工作流
- **决策者**：项目所有者

---

## 1. Summary（一句话建议）

在当前硬红线（Mac Apple Silicon 本地、免费、未来可商用、国画水墨风格）下，推荐把 **FLUX.1 \[schnell\]（Apache 2.0）走 MFLUX（MLX 后端）** 作为主生成模型，并在 Draw Things / Diffusers 侧保留 **SDXL 1.0 base + 一个已知许可的中文水墨 LoRA** 作为风格对照与回退路线；**Qwen-Image（Apache 2.0 原版 20B）** 作为"想要更地道中式水墨、愿意为 64 GB 统一内存买单"时的进阶选择；**SD 3.5 系列**由于 Community License 的 $1M 年营收上限与 MPS 后端的可用性不确定性暂不作为默认，但保留在"未来商用边界明确后"的候选位。

> 所有判断均为"研究阶段"结论，不等于已验收；真正进入 art/ 层前仍需按本 RFC 第 6 节 POC 计划实测。

---

## 2. Context（为什么写这个 RFC）

### 2.1 项目现状

- 目前 L0 经文一律 `SOURCE_PENDING`（见 `.claude/rules/classics.md`），因此图像生成流程在数据层尚未解锁，但艺术红线和图像模型选型可以先行。
- `.claude/rules/art-style.md` 明文规定：
  - **本轮未选定图像模型**；
  - **图像模型不得绘制汉字、卦符或印章**（这些是 Layer 2 / Layer 3）；
  - 五色体系必须兼容：青黛 `#273F52`、石青 `#547A83`、石绿 `#A2B4A1`、赭石 `#B58C69`、朱砂 `#A74439`（朱砂少量）；
  - 留白参考 35%–45%；
  - 一卦一象，一象一境——不是统一构图模板，而是统一艺术语言。

### 2.2 硬红线（不可妥协）

| # | 约束 | 来源 |
|---|------|------|
| R1 | 可在 Mac Apple Silicon 本地运行（假设 M-series Max 级，统一内存≥64 GB 为上限，常规 32–64 GB 必须能跑） | 用户环境 |
| R2 | POC 阶段总花费 < $1 USD | 预算 |
| R3 | 许可必须明确允许商用（research-only 不接受） | 项目愿景 |
| R4 | 水墨/文人画风格表现要好（非写实、非油画） | `docs/art-style-guide.md` |
| R5 | 不得绘制汉字、卦符、印章（三者由 SVG + 合成层负责） | `.claude/rules/art-style.md` |
| R6 | 五色调性要可控，不得色彩漂移到饱和现代色 | 同上 |
| R7 | 留白 35%–45% 可以通过 prompt 或后处理达到 | 同上 |

### 2.3 为什么现在要决策

- 艺术红线中的"主图须保存模型、prompt、参数、版本"需要明确的 provenance；一个真正被选中的模型是 provenance 的前提。
- Governance V2 允许 Agent 批准，但 `art/` 层的签字必须指向一个确定的工具链，否则 autopilot 无法展开。
- 国画 LoRA 的许可生态在 2026 年发生了明显位移（Qwen-Image 从 Apache 2.0 收紧到 Research License，参见 Sources），选型越晚风险越大。

---

## 3. Options evaluated（候选模型全景）

> 下表的"商用 OK"仅反映本轮搜索到的证据，非法律意见。任何模糊项（列为 "unclear"）必须在真正商用前查阅模型页的 LICENSE 原文。

| 模型 | 许可 | Mac 本地可行 | 商用 OK | 水墨质量 | 安装成本 | 单图耗时（M-series Max 级，1024×1024） |
|------|------|--------------|---------|----------|----------|----------------------------------------|
| **FLUX.1 \[schnell\]** | Apache 2.0（HF 卡明示） | ✅ via MFLUX / Draw Things | ✅ 清晰 | 中（无原生水墨，需 prompt 工程或社区 LoRA） | 低（`pip install mflux`） | ~20s（社区上报 M3 Max 4-step 1024²，无官方 benchmark） |
| **FLUX.1 \[dev\]** | FLUX.1 \[dev\] Non-Commercial License | ✅ 技术可行 | ❌ 权重非商用；输出能否商用来源互相矛盾，BFL 没给过 2026 公开声明 | 中（同 schnell，社区微调更多） | 低 | ~45–60s（schnell 的 ~7–8× 慢档） |
| **FLUX.2 Klein 4B** | FLUX Non-Commercial License（2026，同 \[dev\]） | ✅ MFLUX 已适配 | ❌ 非商用 | 未测 | 中 | 105s（M3 Max，lilting.ch 报告） |
| **Stable Diffusion 3.5 Large** | Stability Community License | ✅ Diffusers MPS 可跑，但内存压力大 | ✅ 年营收 < $1M 免费商用；超过需 Enterprise 合同 | 未确认（国画/水墨未见独立评测） | 中（Diffusers + transformers） | 未测，Large 比 Medium 慢几倍 |
| **Stable Diffusion 3.5 Medium** | 同上 | ✅（有用户以 fp16 + 手动卸 T5 的方式在 M3 Max 36 GB 跑通，峰值 ~11.6 GB） | ✅ 同上 | 未确认 | 中（需手动管内存） | ~100s（M3 Pro，Habr 报告） |
| **SDXL 1.0 base + 水墨 LoRA** | SDXL: CreativeML Open RAIL-M (OpenRAIL++)；LoRA 许可因作者而异 | ✅ Draw Things / Diffusers 都原生支持 | ✅ base 允许商用，但 **LoRA 可能带自己的限制**（如 bespoke-lora-trained-license） | 中-高（现成的 shuimo / Chinese-inkwash LoRA 数量最多） | 低 | ~5–15s（成熟路径） |
| **Qwen-Image（原版 20B）** | Apache 2.0（官方 HF 卡） | ⚠️ 需要 4-bit MLX 量化 + 64 GB 统一内存，或 96 GB 跑 Edit 变体 | ✅ Apache 2.0 清晰 | 中-高（厂商样例含 shuimo，但为 marketing 材料，缺独立评测） | 中（vmlx / mlx-runner / Rapid-MLX） | 未测，20B MMDiT 比 FLUX 慢 |
| **Qwen-Image 2.1 / 3.0** | Qwen Research License（2.1 收紧）/ API-only（3.0） | — | ❌ 2.1 不允许商用；3.0 没有权重 | — | — | — |
| **Kolors** | HF tag 写 Apache-2.0，但官方 README 要求发邮件到 `kwai-kolors@kuaishou.com` 注册才能商用 | ✅ | ⚠️ "unclear, verify before commercial use" | 未测 | 中 | — |
| **PixArt-Σ** | OpenRAIL++ | ✅ | ✅ OpenRAIL++ 允许商用（含 use restrictions） | 未测，但国风样例少 | 中 | — |
| **HunyuanDiT** | `tencent-hunyuan-community`（custom）；Reddit 概括为 "<100M MAU 可商用"，但需查原 LICENSE.txt | ✅ 技术可行 | ⚠️ "unclear, verify before commercial use" | 高（研究号称强于对比模型，尤其中文语义） | 中-高（Tencent 自家工具链较少 Mac 原生支持） | — |
| **ERNIE-ViLG（文心）** | 未在本轮搜索中找到开源权重 | ❌ | ❌（若无开源权重则不在范围内） | — | — | — |
| **Wanxiang（通义万相）** | 2026 最新版 API-only；早期 Wan2.1 系列在 HF 有开源权重，但重点是视频 | ⚠️ | ⚠️ "unclear, verify before commercial use" | 未针对水墨评测 | — | — |

### 2026 新模型观察

搜索中出现但**不建议进 POC**：

- **FLUX.2 Klein 9B / 32B dev**（Black Forest Labs 2026 新品）：同样 FLUX Non-Commercial License，排除。
- **FLUX 3 Max**：视频模型，不是本项目目标。
- **Qwen-Image 3.0 / 3.0 Pro**：仅 Alibaba Cloud Model Studio API，无开源权重，违反 R1。

---

## 4. Recommendation（推荐与理由）

### 4.1 主路线：FLUX.1 \[schnell\] via MFLUX

**理由**：

1. **许可最干净**：Apache 2.0 是本轮候选里唯一"无隐藏条款、无营收上限、无注册邮件"的 OSI 许可（Kolors、HunyuanDiT、SD 3.5 都有某种附加条件）。
2. **Mac 工具链成熟**：MFLUX 是 Diffusers 的 MLX 逐行移植，`pip install mflux` 即可；Draw Things 作为 GUI 回退也支持 schnell。
3. **速度合格**：社区上报 M3 Max 4-step 1024² 约 20s，一卦 30–50 张候选图可在半小时内产出。
4. **风格可塑**：FLUX 系列的社区 LoRA（如 CivArchive 上 2026-01 的 `shuimo_animals` FLUX LoRA）正在增长，可以在后续按卦叠加。
5. **可保留 provenance**：MFLUX 的调用参数（seed、steps、guidance）可一次性写进 YAML，满足艺术红线"主图须保存模型、prompt、参数、版本"。

**已知弱项**（会在第 8 节 Risks 展开）：

- 水墨不是 FLUX 的训练强项；开箱即用效果偏"插画水墨"而非"文人水墨"。需要 LoRA 补齐或 prompt 工程。
- FLUX 系列已知对非拉丁文字（含汉字）出现"幻影文字" —— 必须用"no text, no writing, no letters"类 prompt 抑制，并在交付前人工审图（见 R5）。
- schnell 是 guidance-distilled，许多宿主 UI 的 negative prompt 字段对它无效；抑制文字只能靠 positive prompt 措辞。

### 4.2 风格对照 / 回退路线：SDXL 1.0 base + 中文水墨 LoRA

**理由**：

1. **LoRA 生态最厚**：HF 上 `ming-yang/sdxl_chinese_ink_lora`、`taki0112/lora-trained-xl_colorful-chinese-ink-paintings_split`、xbesing 系列、CivArchive 上的 `shuimo` 触发词 LoRA 都基于 SDXL，不必重训。
2. **Draw Things 开箱即用**：对 Mac 用户来说 Draw Things 的 UI 成本比写 Python 脚本低；适合艺术 Agent 在"看图调参"阶段使用。
3. **许可**：SDXL base 采用 CreativeML Open RAIL-M (OpenRAIL++)，允许商用但有 use restrictions（不得生成违法/伤害性内容）；**LoRA 作者的许可需逐个确认**（部分 LoRA 带 "bespoke-lora-trained-license"）。

### 4.3 进阶路线：Qwen-Image 原版 20B（4-bit MLX）

仅当主路线水墨质量不达标、且用户机器有 ≥64 GB 统一内存时考虑：

- 唯一一个原厂就宣传"支持中国水墨风格"的大体量开源模型，Apache 2.0 清晰。
- Rapid-MLX 的 `qwen-image` 档位：28.9 GB 权重、64 GB 最低统一内存；mlx-runner 提供 `toxicdog/Qwen-Image-2.1-MLX` 4-bit checkpoint（**注意：2.1 已收紧许可，需用 Apache 2.0 的原版 1.x 而不是 2.1 的 4-bit 量化**）。
- 速度未测；厂商对比样例显示其 Chinese text rendering 表现强，但这正是我们要抑制的能力（R5）。

### 4.4 明确排除

- **FLUX.1 \[dev\]** 与 **FLUX.2 Klein 全系**：非商用权重；输出商用性有争议，与 R3 冲突。
- **Qwen-Image 2.1 / 3.0 / Pro**：Research License 或 API-only。
- **ERNIE-ViLG / Wanxiang 3.x**：没找到开源权重或只有视频向，与 R1/R3 冲突。
- **Kolors**：Apache tag 与官方 README 的"注册邮件才能商用"存在矛盾，直到 Kuaishou 方给出书面确认之前，不纳入主路线。

---

## 5. Setup instructions（推荐方案的落地步骤）

> 以下命令给出 FLUX.1 \[schnell\] + MFLUX 的最小可运行路径；SDXL + LoRA 的备用路径附在 5.4。

### 5.1 环境前置

```bash
# 项目已有 .venv，直接复用
source /Users/cavinfu/Desktop/devs/guanxiang-wudao/.venv/bin/activate

# 确认 macOS 版本与架构
sw_vers           # 需要 13.0+ 推荐 14+
uname -m          # arm64
python -c "import platform; print(platform.processor(), platform.machine())"
```

### 5.2 安装 MFLUX

```bash
# 建议单独建一个轻量虚拟环境避免冲突，但本项目的 .venv 也可
pip install mflux   # 会自动拉 mlx, mlx-lm 等 Apple MLX 栈
# 或固定版本（需要查 pypi）
# pip install "mflux==<X.Y.Z>"
```

**内存预算**（根据社区/非官方汇报，未自测）：

| 量化 | 近似内存占用 | 适用机器 |
|------|--------------|----------|
| FP16（全精度） | 20–24 GB | 32 GB 统一内存即可，推荐 48 GB+ |
| FP8 | ~12 GB | 24 GB 统一内存 |
| INT4 | ~7 GB | 16 GB 统一内存，但画质受损 |

> 注：这些数字来自 NVIDIA / 第三方 blog；Apple Silicon 的 unified memory 行为与独立 VRAM 不同，实际读数以 `sudo powermetrics --samplers gpu_power` 或 Xcode 的 Memory Debugger 为准。

### 5.3 已知 Mac 坑

1. **MPS 后端对部分算子支持不完整**：Diffusers 侧的 SD 3.5 需要手动把 T5 文本编码器加载→用完→释放，再加载 MMDiT；MFLUX 因为是纯 MLX 栈不走 MPS，这个坑不复现。
2. **首次推理结果与后续略有差异**：Diffusers 官方文档已警告，第一次 pass 做 warmup（空跑一张）。
3. **"上下文切换零成本"的误区**：CPU 与 MPS 共享同一块物理内存，`enable_model_cpu_offload()` 并不真释放。
4. **Rosetta / x86_64 Python**：必须用 arm64 Python；检查 `python -c "import sys; print(sys.platform, sys.version)"` 输出里的 arch。
5. **MFLUX 的模型下载**：首次运行会从 HF 拉权重（约 30 GB 级），确认磁盘有 50 GB+ 余量；可以用 `HF_HOME=/path/to/large/disk` 重定向。

### 5.4 SDXL + LoRA 的回退路径（可选，用于艺术对照）

```bash
# 需要 diffusers + torch + safetensors
pip install "diffusers>=0.28" "torch>=2.1" "transformers" "safetensors" "accelerate"

# 下载 base（约 6.6 GB）与 LoRA（通常 <200 MB）
# 不在 RFC 范围内下载任何权重；只给命令示意
```

**LoRA 候选**（**许可必须逐个确认**）：

| LoRA | HF 路径 | 许可 | 备注 |
|------|---------|------|------|
| `ming-yang/sdxl_chinese_ink_lora` | HF | creativeml-openrail-m | 一年前更新 |
| `taki0112/lora-trained-xl_colorful-chinese-ink-paintings_split` | HF | 未在搜索结果中明示，需打开模型卡 | DreamBooth-based |
| `xbesing/chinese_ink_style2` | HF | 未明示 | SD1.5 为主，SDXL 版本需确认 |
| CivArchive `shuimo_animals` | Civitai 镜像 | Civitai 原页面 | FLUX-based，可直接接 FLUX 路线 |

---

## 6. POC Plan（三卦试炼）

### 6.1 选哪三卦

按"构图差异最大、风格难度覆盖最全"的原则：

1. **卦 1 · 乾（Qian）**：纯阳六爻，象为天。构图挑战——**纯净留白 + 云气**，几乎没有具体物象，考验模型能不能 hold 住极简水墨。
2. **卦 29 · 坎（Kan）**：象为水、险。构图挑战——**流动笔墨 + 明暗对比**，考验模型对水墨渲染中"湿笔"与"焦墨"过渡的理解。
3. **卦 52 · 艮（Gen）**：象为山、止。构图挑战——**山石皴法 + 远近三远法**，考验模型能不能画出"文人山水"而不是"3D 渲染风景"。

三卦覆盖了"虚—动—实"三种水墨母题，足以判断模型基线。

### 6.2 Prompt 模板

**原则**：

- 用英文为主（FLUX / SDXL 英文语义最强），**在正向 prompt 里显式压制文字与印章**；
- 用十六进制颜色词或颜色名锚定五色；
- 用"留白"相关的英语词汇（negative space, empty space, unpainted silk/paper）锚定 R7；
- **不在 prompt 中写汉字**（避免模型尝试生成汉字作为装饰）。

**模板（主路线 FLUX.1 schnell）**：

```
A traditional Chinese literati ink-wash painting (shuimo),
subject: {subject_phrase},
composition: {composition_phrase, e.g. "high-distance mountain with low horizon"},
palette: muted indigo #273F52, stone-blue #547A83, soft greenstone #A2B4A1,
earthy ochre #B58C69, a single small accent of cinnabar #A74439,
executed with wet and dry brush strokes on aged xuan paper,
40% negative space in the upper field, atmospheric mist, three-distance method,
minimalist, serene, sparse,
no text, no calligraphy, no Chinese characters, no letters, no seals, no stamps,
no signatures, no watermarks, no borders, no frames.
```

**每卦的 `{subject_phrase}` / `{composition_phrase}`**：

| 卦 | subject_phrase | composition_phrase |
|----|----------------|--------------------|
| 乾 | six dragons rising through layered clouds above a receding ridge | high-distance, 45% upper negative space, no ground figures |
| 坎 | a rushing mountain stream between two rocky cliffs, a lone boatman | deep-distance, mid-valley focal, dark wet ink on the cliffs |
| 艮 | still mountain peaks with a small hermit hut at the base, pines | level-distance left-to-right, dry brush rock texturing (皴法) |

**Negative prompt（SDXL 路径时使用；FLUX schnell 不保证生效）**：

```
photorealistic, 3d render, oil painting, acrylic, anime, cartoon,
modern objects, smartphone, car, skyscraper, Western architecture,
text, Chinese characters, kanji, letters, signature, watermark, seal,
red stamp, border, frame, color-saturated, neon, oversaturated.
```

### 6.3 评估矩阵

每卦生成 N≥16 张候选，由评估者按四轴 1–5 分打分：

| 轴 | 问题 | 否决阈 |
|----|------|--------|
| A · 卦意契合 | 画面传达的意象是否与经义一致（独立于审美）？ | ≤2 直接淘汰 |
| B · 水墨质感 | 笔墨是真的水墨还是数字描边？皴法 / 晕染 / 飞白是否有？ | ≤2 直接淘汰 |
| C · 五色合规 | 颜色是否落在 `#273F52 #547A83 #A2B4A1 #B58C69 #A74439` 的邻域？朱砂占比 <5%？ | ≤2 直接淘汰 |
| D · 红线违反 | 画面里是否出现汉字 / 卦符 / 印章 / 签名 / 边框？ | 任一出现→直接废图 |

**量化辅助**（可选脚本）：

- 对每张图做颜色直方图，计算五色邻域（CIELAB ΔE < 15）的覆盖占比；
- 对每张图做 OCR（Tesseract，中文语言包），返回是否有可读字符；
- 对画面上 1/5 高度边缘做留白检测（HSV V>235 且 S<15 的像素比例），判断留白率是否 ∈ \[35%, 45%\]。

这些脚本不在本 RFC 范围内落地，但记录在 DEVLOG 的"待实现工具"条目。

### 6.4 成本预算

- FLUX.1 schnell MFLUX 本地跑：**0 美元**。
- 若需要对照一张商业 API（例如 SD 3.5 Large via Stability API）：Stability 的 image 单价 ~$0.04 起，20 张对照 ≈ $0.8，仍在 R2 范围内。
- SDXL + LoRA 本地跑：**0 美元**。

---

## 7. Governance V3 proposal（红线修订文本模板）

当前 `.claude/rules/art-style.md` 关键条款：

> 主图须保存模型、prompt、参数、版本；**本轮未选定图像模型**。

一旦项目所有者批准本 RFC，`.claude/rules/art-style.md` 需要从 "本轮未选定" 过渡到 "已登记"。以下是建议的修订文本（**不自动落地，必须由人工 PR 并经过本 RFC 的 approver 签字**）：

### 7.1 建议新增条款（append，不删除原文）

```md
## 艺术红线补充（RFC 001 批准后生效）

- 本项目当前登记的主图生成模型为 **FLUX.1 [schnell]（Apache 2.0）**，
  运行入口为 **MFLUX（MLX 后端，macOS arm64）**，通过 `.venv` 中的
  `mflux` 包调用。切换到任何其他模型需要新的 RFC（001-xx 系列）或 ADR。
- 风格对照路线为 **SDXL 1.0 base + 已审计许可的中文水墨 LoRA**，
  LoRA 的具体 HF 路径与许可必须登记在 `data/sources.json` 下的
  `art_loras` 新字段，且不得混入 L0 经典底本的 sources。
- 每一张主图的 provenance 记录必须包含：
  `model_id`, `model_revision`, `license_snapshot_sha256`,
  `prompt`, `negative_prompt_or_null`, `seed`, `steps`, `guidance`,
  `sampler`, `resolution`, `generation_time_ms`,
  `evaluator_scores_abcd`, `human_sign_off`.
- 若 BFL 或 HF 对 schnell 的许可发布更新（例如从 Apache 2.0 变为非商用），
  所有已发布作品冻结，重启 RFC 001 评审。
- Governance V2 规定的 approver 仍适用；艺术层的 Agent approver 必须在
  approval 中标记 `signed_by_agent=true`，且 approved_by ≠ 产生该主图的
  Agent id（见 `.claude/rules/publication.md`）。
```

### 7.2 需要新增/修订的其他文件（本 RFC 不写，只列）

- `data/sources.json`：新增顶层 `art_loras: []`（schema 另议）。
- `docs/image-and-licensing-decisions.md`：引用本 RFC 的最终决议，并记录 Qwen-Image 2.1 / Kolors / HunyuanDiT 的"已评估但未选"的理由。
- `templates/`：追加 `art/provenance.template.yaml`，字段对齐 7.1 的 provenance 列表。

### 7.3 Approver 期望

根据 `.claude/rules/publication.md` 与 `docs/GOVERNANCE.md`：

- 本 RFC 由 autopilot agent 产出，**必须**由 `approvers.json` 中的一位非生产者/非验证者签字；
- 若 approver 为 Agent 身份（治理 V2），approval 需携带 `signed_by_agent=true`；
- Approver 签字前**必须**核查第 8 节列出的风险条目，逐项标记"接受/拒绝"。

---

## 8. Known risks（已知风险，必须在 approver 签字前阅读）

| # | 风险 | 可能性 | 影响 | 缓解 |
|---|------|--------|------|------|
| K1 | **水墨风格不够地道**：FLUX schnell 的训练分布更偏插画/概念图，开箱水墨看起来会像"数字插画风水墨"。 | 高 | 艺术红线中 "笔墨是真的水墨还是数字描边" 不达标 | 优先用 CivArchive 上 2026-01 的 `shuimo_animals` FLUX LoRA；若仍不行则切 SDXL + `ming-yang/sdxl_chinese_ink_lora`；最坏回到 Qwen-Image 20B。 |
| K2 | **模型幻影汉字**：FLUX 对非拉丁文字的处理已被论文 (FLUX-Text, 2505.03329) 证实"经常生成不可读字符"；即便 prompt 显式压制，仍可能在题款区域出现乱码汉字。 | 高 | 违反 R5（不得绘制汉字） | (a) 正向 prompt 必须显式写 "no text, no Chinese characters, no calligraphy, no seals"；(b) 禁止在 prompt 中出现 "scroll"、"calligraphy"、"stamp" 等诱导词；(c) 人工审图阶段用 OCR 脚本做自动过滤，出现任一字符即废图。 |
| K3 | **五色漂移**：扩散模型对十六进制颜色的服从度中等，一不小心会偏到饱和现代色。 | 中 | 违反 R6 | 用颜色词（"muted indigo"、"cinnabar accent"）而非纯十六进制；对结果做 CIELAB ΔE 检查；必要时在 Layer 3 合成阶段做色调映射。 |
| K4 | **留白不足**：Flux schnell 常常把画面画满。 | 中 | 违反 R7 | prompt 中显式写 "40% negative space in upper field"、"unpainted xuan paper"；对结果做留白率检测；必要时后处理（canvas crop / resize）。 |
| K5 | **许可变更**：Qwen-Image 从 1.x 的 Apache 2.0 收紧到 2.x 的 Research License，证明开源大模型许可"随时可能回收"。schnell 虽然 Apache 2.0 已定锚，但未来新版本可能换许可。 | 中 | 违反 R3 | 在 provenance 中记录 `license_snapshot_sha256`，发布前重新拉取当前许可文本与锚定哈希对比；若不一致触发 RFC 复审。 |
| K6 | **LoRA 许可不干净**：SDXL 路线上，LoRA 作者可能用 "bespoke-lora-trained-license" 或 CC-BY-NC；LoRA 本身若用了版权保护的艺术家画作训练，还有潜在著作权风险。 | 中 | 违反 R3 | 每一个 LoRA 必须在 `data/sources.json` 的 `art_loras` 字段登记 HF URL、许可、训练数据来源；训练数据不明的 LoRA 一律不进生产。 |
| K7 | **MFLUX 版本化缺失**：MFLUX 发展快、API 偶有 breaking change。provenance 中的 `model_revision` 不等于 MFLUX 版本。 | 低 | 作品不可复现 | provenance 记录 `mflux_version` + `python_version` + `mlx_version`。 |
| K8 | **Mac MPS / MLX 升级破坏可重现性**：macOS 大版本升级（Sonoma→Sequoia→Tahoe）常常让旧的 MPS 核函数行为变化。 | 中 | 作品不可复现 | 严肃发布前"同一 seed + 同一 prompt 在当前机器复跑一次" 作为 G2 子检查。 |
| K9 | **卦象倒置或错误**：模型可能把六龙画成五龙、把下卦画成外卦。 | 中 | 违反艺术红线 "自然景物可艺术化，卦符结构必须精确" | 由于卦符走 Layer 2 SVG，这个风险在合成阶段天然缓解；但主画若出现与卦象矛盾的"数数元素"（五龙、三爻堆砌），仍需 G2 审查剔除。 |
| K10 | **"没有中立独立评测"**：所有 2026 新模型的中式水墨质量均来自厂商或社区的 showcase，没有可信的 head-to-head benchmark。 | 高 | 决策建立在不充分证据上 | 用本 RFC 第 6 节的 POC 自测当作第一手证据；对任何声称"最强中式水墨"的新模型默认持怀疑态度。 |

---

## 9. Open questions（留给 approver / 后续 RFC）

1. 是否允许在 LoRA 训练阶段使用公有领域（Public Domain）的古代画家作品（如赵孟頫、黄公望）？——涉及中国著作权法与国际公约解释，不在本 RFC 范围。
2. 是否允许"让 FLUX 先出草图、再让 SDXL+水墨 LoRA 做 img2img 风格化"的二段流水线？——会让 provenance 变复杂，倾向于第二轮再议。
3. 若未来采购 Mac Studio（≥192 GB 统一内存），是否直接切 Qwen-Image 原版 20B？——取决于届时 Qwen-Image 1.x Apache 2.0 分支是否仍可获取。

---

## 10. Sources（本 RFC 引用的所有搜索结果）

> 以下 URL 在 2026-11-03 由本次 WebSearch 获得；二手博客标注 "(secondary)"，优先官方来源。

### 10.1 FLUX 系列

- [FLUX.1 \[schnell\] Hugging Face 模型卡 (mirror)](https://huggingface.co/cocktailpeanut/xulf-s)
- [Hugging Face 论坛：Copyright FLUX.1 \[schnell\]](https://discuss.huggingface.co/t/copyright-flux-1-schnell/122631)
- [FLUX.1 \[schnell\] README (AITRADER mirror)](https://huggingface.co/AITRADER/MFLUXUI.1-schnell/raw/main/README.md)
- [PromptZone · FLUX AI for Mac (secondary)](https://www.promptzone.com/noor_eriksson/flux-ai-for-mac-efficient-image-gen-2i6.md)
- [PromptZone · FLUX License Guide (secondary)](https://www.promptzone.com/zuzanna_choi/flux-ai-license-key-insights-2g8d.md)
- [invideo.io · Flux 2 and Flux Kontext Explained (August 2026, secondary)](https://invideo.io/blog/flux-ai-image-generator/)
- [localaimaster.com · local image model licenses commercial use (secondary)](https://localaimaster.com/blog/local-image-model-licenses-commercial-use)
- [Flux Schnell on Morphic AI glossary (secondary)](https://morphic.com/ai-glossary/flux1-schnell)
- [lilting.ch · Running FLUX.2 Klein 9B on Apple Silicon Macs](https://lilting.ch/en/articles/flux2-klein-apple-silicon)
- [arxiv 2505.03329 · FLUX-Text: scene text editing with FLUX](https://arxiv.org/html/2505.03329v4)
- [arxiv 2508.14405 · CTA-Flux: Chinese Cultural Semantics in Flux](https://arxiv.org/html/2508.14405v1)

### 10.2 Stable Diffusion 3.5

- [Stability AI · Introducing Stable Diffusion 3.5 (official)](https://stability.ai/news/introducing-stable-diffusion-3-5)
- [Stability AI · Select a license / Membership page (official)](https://stability.ai/membership)
- [Hugging Face · Stable Diffusion 3.5 Large (mirror cocktailpeanut)](https://huggingface.co/cocktailpeanut/sd35)
- [Habr · SD 3.5 Medium on Apple Silicon MPS memory analysis (secondary, Russian)](https://habr.com/en/articles/1014496)
- [Medium / Hannecke · Apple MPS Beginner's Guide (secondary)](https://medium.com/@michael.hannecke/apple-mps-beginners-guide-ai-image-generation-on-apple-silicon-made-simple-44cfae16e049)
- [Hugging Face Diffusers docs · MPS optimization](https://huggingface.co/docs/diffusers/v0.13.0/optimization/mps)
- [Fast.io · Stability AI Review 2026 (secondary)](https://fast.io/resources/stability-ai-review-2026/)
- [Krea.ai · Is Stable Diffusion free in 2026 (secondary)](https://www.krea.ai/blog/is-stable-diffusion-free-where-to-get-it-and-what-it-costs-in-2026)
- [SiliconANGLE · Stability AI releases SD 3.5 (2024 launch coverage)](https://siliconangle.com/2024/10/22/stable-ai-releases-next-gen-open-source-stable-diffusion-3-5-text-image-ai-model-family)
- [Tom's Guide · SD 3.5 launch coverage](https://www.tomsguide.com/ai/stabilityai-releases-stable-diffusion-3-5-a-step-up-in-realism)

### 10.3 SDXL / 中文水墨 LoRA

- [HF · taki0112/lora-trained-xl_colorful-chinese-ink-paintings_split](https://huggingface.co/taki0112/lora-trained-xl_colorful-chinese-ink-paintings_split)
- [HF · ming-yang/sdxl_chinese_ink_lora](https://huggingface.co/ming-yang/sdxl_chinese_ink_lora)
- [HF · xbesing/chinese_ink_style2](https://huggingface.co/xbesing/chinese_ink_style2)
- [HF · ZeroFLN/LoRA-Collection (Chinese Inkwash trigger)](https://huggingface.co/ZeroFLN/LoRA-Collection/blob/995492e63c489dc2db770c0eb599cd38185895c5/Lora/ArtStyle/Chinese%20Inkwash%20Painting/Trigger.txt)
- [HF · Andyrasika/lora_diffusion (shuimobysim trigger)](https://huggingface.co/Andyrasika/lora_diffusion)
- [Civitai mirror · FLUX shuimo_animals LoRA (2026-01)](https://civarchive.com/seaart/models/245ad530810b9bbc79b489f403644fa3/versions/c0ecfa1711adcbd8d698a8b1aa64b351)
- [Civitai mirror · Mo_Xin (Qwen-Image-Edit-2511 shuimo LoRA, 2026-03)](https://civarchive.com/models/2472317)
- [ComfyUI.org · Chinese Ink Painting with FLUX (secondary)](https://www.comfyui.org/en/chinese-ink-painting-with-flux)
- [terms.law · SDXL commercial use forum (secondary)](https://terms.law/forum/thread/stable-diffusion-commercial-use-license.html)

### 10.4 Qwen-Image / HunyuanDiT / Kolors / PixArt-Σ

- [HF · Qwen-Image (chunru623 mirror)](https://huggingface.co/chunru623/Qwen-Image)
- [HF · Qwen-Image (meteorlad mirror)](https://huggingface.co/meteorlad/qwen-image)
- [apidog · What is Qwen-Image-2.1 (secondary)](https://apidog.com/blog/what-is-qwen-image-2-1/)
- [Latenode · Qwen-Image 2.1 commercial licence (PT-BR, secondary)](https://latenode.com/pt-br/ai-trends/qwen-image-2-1-commercial-licence)
- [Tech-Insider · Qwen-Image 2.0 vs 2.1 license (secondary)](https://tech-insider.org/au/?p=2053)
- [SiliconFlow · Qwen-Image showcase (vendor marketing)](https://www.siliconflow.com/blog/qwen-image-is-here-on-siliconflow-superior-text-rendering-precise-image-editing)
- [Rapid-MLX GitHub · qwen-image MLX bundle sizes](https://github.com/chethanuk/Rapid-MLX)
- [vmlx PyPI 1.5.13](https://pypi.org/project/vmlx/1.5.13/)
- [mlx-runner release notes](https://github.com/domhofer/mlx-runner/releases)
- [HF · Tencent-Hunyuan/HunyuanDiT (official)](https://huggingface.co/Tencent-Hunyuan/HunyuanDiT-v1.1)
- [Tencent/HunyuanDiT GitHub (official)](https://github.com/Tencent/HunyuanDiT)
- [arxiv 2405.08748 · Hunyuan-DiT paper](https://arxiv.org/pdf/2405.08748v1.pdf)
- [HF · Kwai-Kolors/Kolors README](https://huggingface.co/Kwai-Kolors/Kolors/blob/main/README.md)
- [HF · PixArt-alpha/PixArt-Sigma README](https://huggingface.co/PixArt-alpha/PixArt-Sigma/blob/main/README.md)
- [HF · PixArt-Sigma-XL-2-1024-MS model card](https://huggingface.co/PixArt-alpha/PixArt-Sigma-XL-2-1024-MS/blob/main/README.md?code=true)

### 10.5 Mac / MLX / Benchmark

- [MFLUX GitHub (elitexp mirror)](https://github.com/elitexp/mflux)
- [MFLUX GitHub (naz mirror)](https://github.com/naz/mflux)
- [CSDN · MFLUX 技术介绍 (secondary, Chinese)](https://blog.csdn.net/lovechris00/article/details/147597528)
- [Anakin · FLUX Schnell on M3 Max MacBook Pro (secondary)](https://anakin.ai/blog/how-to-flux-schnell-locally-on-an-m3-max-macbook-pro-2)
- [MacStadium · M3 Max benchmarks (older SD 1.5 data)](https://www.macstadium.com/blog/m3-max-benchmarks)
- [modelfit.io · FLUX on Mac](https://modelfit.io/guides/flux-on-mac/)
- [Apple Machine Learning Research · exploring LLMs with MLX on M5](https://machinelearning.apple.com/research/exploring-llms-mlx-m5)

### 10.6 其它

- [HF · stillerman/poke-lora MPS guide mirror](https://huggingface.co/stillerman/poke-lora/blob/main/docs/source/en/optimization/mps.md)
- [Reddit (FluxAI) · license discussion (2024, secondary)](https://redlib.ssps.io/r/FluxAI/comments/1hhsjaf/ask_chatgpt_about_licensing)
- [landian.news · Stability AI New License (secondary, Chinese)](https://landian.news/article/2496.html)

---

## 11. Appendix · 决策总结表

| 类别 | 选择 | 替代 | 已排除 |
|------|------|------|--------|
| 主生成模型 | FLUX.1 \[schnell\] + MFLUX | SDXL 1.0 base + 水墨 LoRA | FLUX.1 \[dev\]、FLUX.2 Klein、Qwen-Image 2.1、Kolors、Wanxiang、ERNIE-ViLG |
| 高端进阶 | Qwen-Image 原版 20B (Apache 2.0 分支) | — | Qwen-Image 2.1 / 3.0 |
| 商用边界待定 | SD 3.5 Medium（<$1M 营收）、HunyuanDiT（需查原 LICENSE） | — | — |
| 回退 GUI | Draw Things（Mac 原生） | — | — |
| Prompt 策略 | 显式"no text/char/seals/stamps"，颜色词+十六进制混用 | 后处理色调映射 | 在 prompt 中写汉字 |
| 评估 | 四轴 1–5 评分 + OCR 废图过滤 + 五色 ΔE 检查 + 留白率检测 | — | 任何红线违反直接废图，不扣分 |

---

**本 RFC 结束**。等待 approvers.json 中非生产者 approver 签字（Governance V2 允许 Agent approver，但 `signed_by_agent=true` 必须明示）。
