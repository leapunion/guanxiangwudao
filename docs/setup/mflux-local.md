# MFLUX 本地装机指南（Mac Apple Silicon）

> 对应 [RFC #001 图像模型选型](../rfc/001-art-model-selection.md) 的推荐实现：**FLUX.1 schnell via MFLUX (MLX backend)**。
>
> 本指南只覆盖环境装机 + hello world 验证，**不触碰**治理条款（`art-style.md` 的"本轮未选定图像模型"红线仍有效）。正式用 MFLUX 生成 64 卦画作需先走 Governance V3 提案。

---

## 一、前置要求

| 项 | 要求 | 核对命令 |
|---|---|---|
| 硬件 | Mac Apple Silicon（M1/M2/M3/M4 系列） | `uname -m` 返回 `arm64` |
| macOS | 14.0+（Sonoma 或更新） | `sw_vers -productVersion` |
| 统一内存（RAM） | 16 GB 最低（schnell 4-bit 量化版），24 GB+ 更稳 | `sysctl hw.memsize` |
| Python | 3.10+（本项目用 3.12） | `.venv/bin/python --version` |
| 磁盘空间 | ≥ 15 GB（权重 ~9 GB + 缓存） | `df -h ~` |
| 网络 | 能访问 Hugging Face；国内见下方 § 三 | `curl -sI https://huggingface.co` 返回 200 |

**权重 license 核对**（不要跳）：
- FLUX.1 **schnell** 权重：Apache 2.0（可商用、无营收上限、无注册邮箱要求）
- MFLUX 工具链：MIT
- 相关 license 文件会在第一次下载时放到 `~/.cache/huggingface/hub/models--black-forest-labs--FLUX.1-schnell/` 下

---

## 二、安装 MFLUX

### 方式 A · 用 uv tool（推荐，隔离装到 uv 的 tool 空间，不污染任何 venv）

```bash
# 如果没装 uv：
curl -LsSf https://astral.sh/uv/install.sh | sh

# 装 MFLUX 工具
uv tool install --upgrade mflux

# 核对
which mflux-generate     # 应输出 ~/.local/bin/mflux-generate 或类似
mflux-generate --help    # 应打印参数帮助
```

### 方式 B · 用 pip 装到本项目的 venv（如果你偏好 venv 统一管理）

```bash
cd /Users/cavinfu/Desktop/devs/guanxiang-wudao

# 本项目的 .venv 已经在，直接装
.venv/bin/pip install -U mflux

# 核对
.venv/bin/mflux-generate --help
```

**用 pip 装的注意**：MFLUX 会把自己和 ~2GB 的依赖（mlx、torch mac 版、diffusers、transformers）装到 venv，`.venv` 会膨胀到约 3GB。可接受，但 fresh clone 项目的人要装会较慢。更干净的做法还是 uv tool（方式 A）。

---

## 三、国内网络 · 配 HF 镜像（可选）

如果你在国内，Hugging Face 下载 9GB 可能慢到无法接受。配 **hf-mirror.com** 镜像：

```bash
# 添加到 ~/.zshrc 或 ~/.bash_profile
export HF_ENDPOINT=https://hf-mirror.com

# 当前 shell 立即生效
source ~/.zshrc
```

验证：
```bash
echo $HF_ENDPOINT   # 应打印 https://hf-mirror.com
curl -sI $HF_ENDPOINT | head -1   # 应 HTTP 200
```

> 镜像生效原理：`huggingface_hub`（MFLUX 底层用）会读 `HF_ENDPOINT` 环境变量作为下载源。设置后 MFLUX 自动走镜像，无需改代码。

---

## 四、Hello World · 第一次生成

```bash
# 建议先 cd 到项目 scratchpad，避免首图污染项目目录
mkdir -p /tmp/mflux-smoke && cd /tmp/mflux-smoke

# 第一次运行会下载 schnell 4-bit 量化权重（~9GB）到 ~/.cache/huggingface/
# 下载完后生成一张测试图。参数解释见注释。
mflux-generate \
  --model schnell \
  --prompt "a serene mountain landscape in Chinese ink painting style, mist, pine trees, cliffs, traditional composition, lots of white space" \
  --steps 2 \
  --seed 42 \
  -q 8 \
  --output smoke.png

# --model schnell:  FLUX.1 schnell（distilled 到 2-4 步）
# --steps 2:        schnell 的推荐步数（最少 2，4 质量更好）
# --seed 42:        确定性种子，可复现
# -q 8:             8-bit 量化（质量/内存平衡）；RAM < 24GB 用 -q 4 降到 4-bit
# --output:         输出路径
```

### 预期时间（基于 WebSearch 到的社区数据）

| 硬件 | 单图时间（schnell, 2 步, q8） |
|---|---|
| M1 Pro / 16GB | ~45-60s |
| M2 Max / 32GB | ~25-35s |
| M3 Max / 36GB+ | ~15-25s |
| M4 Max / 48GB+ | ~10-15s |

**首次运行额外**：下载权重 9GB，按带宽 50 Mbps 估算约 25 分钟（国内走镜像类似）。

### 验证输出

```bash
ls -lh smoke.png             # 应该 ~500KB-2MB
file smoke.png               # PNG image data, 1024x1024 ...
open smoke.png               # 用 macOS Preview 打开看
```

如果看到一张合理的山水画（哪怕质量粗糙），**装机验证通过**。

---

## 五、常见问题

### Q1. `mflux-generate: command not found`

- uv tool 装的：`~/.local/bin` 没加 PATH。加一行到 `~/.zshrc`：`export PATH="$HOME/.local/bin:$PATH"`
- pip 装的：忘了加 `.venv/bin/` 前缀

### Q2. `Cannot connect to huggingface.co` / 下载超时

- 国内网络 → 走 § 三 的 hf-mirror
- 已经设 HF_ENDPOINT 但还是不通 → 检查 shell 是否重启；或试 `curl -v $HF_ENDPOINT` 看 DNS 是否解析

### Q3. `RuntimeError: MPS backend out of memory` / 系统卡死

- 降量化：`-q 8` → `-q 4`
- 降步数：`--steps 4` → `--steps 2`
- 关掉其他吃内存的 app（Chrome / Docker 等）
- 还不行 → 你的 Mac 可能内存不够跑 FLUX，考虑换 SD 3.5 Medium（见 RFC §3）

### Q4. 第一张图全黑 / 全白 / 噪点

- 多半是 MLX 内存不够导致中间步数溢出。参考 Q3 降量化/步数
- 也可能是 random seed 刚好坏，换个 `--seed`

### Q5. 生成图里出现乱码汉字 / 涂鸦似的印章

- 这是 FLUX 家族的已知弱点（RFC §9 已列为风险）。本项目的三层合成器会覆盖掉这类"幻觉"（卦符 SVG + 文字印章层单独画），正式 POC 时在 prompt 里加 `no text, no characters, no seals, no writing` 强化抑制

### Q6. 生成的画看起来像"西洋油画水墨风"而不是真正的国画

- schnell 对"shuimo / Chinese ink painting"的 token 理解有限
- 需要在 prompt 里堆更具体的 style 词（"literati painting style"、"Song dynasty"、"minimalist composition"、"ink wash") + 五色十六进制
- 这正是 POC 要调教的（不是装机阶段问题）

---

## 六、装机验证完成后的下一步

**装机通过**（Q1-Q4 都没卡住，smoke.png 能看），告诉我 **"mflux ready"**，我继续：

1. 启动 Governance V3 提案（修 `art-style.md` 第 10 条红线，解禁"本轮未选定图像模型"）
2. 写 POC 脚本 `scripts/art/gen-poc.py`：对 H1 乾 / H29 坎 / H52 艮 三卦生成图
3. 跑 POC → 把 3 张图发给你审 → 决定是否铺开全集 64 卦

**装机卡住**（Q6 之外的问题），把具体症状/错误信息贴给我，我帮定位。

---

## 七、不要做的事

- ❌ **不要把下载的权重 commit 进 git**（9GB，git 会死）。权重在 `~/.cache/huggingface/` 系统目录，不在项目里，默认安全
- ❌ **不要用 FLUX.1 dev 代替 schnell**（dev 是非商用 license，我们要保留商用可能，见 RFC §3 blocker 1）
- ❌ **不要在 art-style.md 的"本轮未选定图像模型"红线解禁前，正式把生成图作为 PUBLISHED 作品替换 1×1 占位 PNG**。装机 + POC 阶段的输出留在 `/tmp/mflux-smoke/` 或 `scratchpad/`，不进 projects/

---

## Sources

- [MFLUX GitHub README](https://github.com/itsbrex/mflux) — 官方 install 命令
- [FLUX.1 on Mac Guide (PromptZone)](https://www.promptzone.com/noor_eriksson/flux-ai-for-mac-efficient-image-gen-2i6.md) — Mac 内存规划
- [MLX FLUX Playbook](https://svah-x.github.io/mac-playbooks/playbooks/mlx-flux) — macOS 14+ / 16GB / schnell 4-bit 下载 ~9GB
- [hf-mirror.com](https://hf-mirror.com) — 国内 HF 镜像
