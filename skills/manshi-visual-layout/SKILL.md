---
name: "manshi-visual-layout"
description: "曼拾品牌图片排版流水线：拆素材、CSS排版、无头渲染、自动适配、OCR与视觉校验、飞书交付"
---

# 曼拾图片排版流水线（manshi-visual-layout）

给曼拾及其关联公司做**品牌级图片产出**的标准编排（orchestration）。不是「一次生成」，而是一条可重复的 pipeline：**对齐 → 拆素材 → 排版规格 → 渲染 → 自动适配 → 校验 → 交付 → 记忆**。

适用产出：名片（效果图 / 平面稿）、PPT 通用浅色底背景、品牌释义一页、提案封面、社媒方图 / 竖版图、logo 尺寸化交付（白底 / 透明底 / 指定尺寸）。

---

## 0. 铁律（先于一切）

1. **先文字，后做图。** 涉及品牌文案的产出，先把文字版发逸凡确认，确认后才动图。禁止先出成品再解释。（2026-10-14 逸凡明确：不要急吼吼做图）
2. **核心正文用黑色 `#1A1A1A`**，红色只用于标题 / 编号 / 强调词。整页红字＝阅读困难，会被退回。
3. **不要堆叠。** 少嵌套色块，色块间留白；宁减装饰，不缩字号。
4. **色块只用四个 VI 色**：白 `#FFFFFF` / 红 `#F8223E` / 浅红 `#F93957` / 淡粉 `#FFEADF`（历史版曾用元素色 青绿 `#65CDBC`、绿 `#8CF160`、黄 `#EFFD5B`、橙 `#D27D33`，仅用于旧版装饰）。
5. **交付形态**：竖版 A4（2480×3508 @300dpi）是主力；16:9（3840×2160）只在明确要提案/屏幕时做。
6. **本地路径不等于交付。** 逸凡只看飞书；图片走消息附件（一条消息一张），真文件走 `scripts/feishu_send_file.py`。
7. **文字用词固定**：对外传播署名 `曼拾·社交媒体整合营销`，英文名连写 `MEANSPLUS`；法律文件才用全称 `上海曼拾文化传播有限公司`。
8. **编码由主会话直接写**（逸凡 2026-10-14 20:59 明确：你写的挺好的，后面不用交给 GLM 了）。排版类脚本不转 GLM 子任务。

---

## 1. 编排总览

| 阶段 | 动作 | 主责 | 工具 / 模型 |
|---|---|---|---|
| S0 对齐 | 文案定稿、交付形态、尺寸 | 主会话 | DeepSeek（复杂用 v4-pro） |
| S1 拆素材 | 从现有品牌资产拆 logo / 元素 / 纹样 | 主会话 | `scripts/extract_elements.py`（PIL + numpy） |
| S2 排版规格 | 字号 / 行距 / 留白 / 色块 / 水印透明度 | 主会话判断 | `templates/page_a4.html` |
| S3 渲染 | HTML+CSS → 300dpi PNG | 主会话 | `scripts/render_page.py`（Chrome headless） |
| S4 自动适配 | 全局系数 K 二分，量测定最优缩放 | 主会话 | `scripts/render_page.py --fit` |
| S5 校验 | OCR 文字完整性 + ink/密度量测 + VLM 审美 | 主会话 | `scripts/ocr_check.sh`（含 `scripts/ocr.swift`）、`glm-5v-turbo` |
| S6 交付 | 预览图 + 真文件，分条发飞书 | 主会话 | `message` 工具、`scripts/feishu_send_file.py` |
| S7 记忆 | 交付记录、待确认项、坑 | 主会话 | `memory/YYYY-MM-DD.md` |

**模型分工**：编码与排版由**主会话**（DeepSeek v4-flash，复杂结构判断可切 v4-pro）直接完成；**视觉检查** → `glm/glm-5v-turbo`，必须传 ≤600px 缩略图。GLM 只在明确的大规模独立编码任务（如多文件重构）时才考虑调用，不作为本流水线默认环节。

---

## 2. S1 拆素材（读图能力）

**原则：素材只能从品牌自有资产里拆，不引入外部图片，不重新画 logo。**

- logo 主体：`output/manshi-logo/manshi_logo_transparent_2000.png`（浅色底：红圆 + 白五叶草 + 浅红凤纹，透明底）
- 五叶草元素：取 logo 中「白色像素」（R/G/B>235 且 alpha>128）→ 重着色（红 / 浅红 / 淡粉）→ 裁 bbox → 得 `clover_shape.png`
- 凤纹元素：取 logo 中「`#F93957` 颜色层」（色差 <40）→ 得 `phoenix_pattern.png`，做水印用
- 纸质实拍感 mockup：不用 CSS，用 PIL 合成（纸纹、三层阴影、透视、颗粒、暗角）
- 收到的截图稿（CMYK JPEG）：先 `convert("RGB")` 再裁内容 bbox，LANCZOS 放大 + UnsharpMask 找回锐度

**禁止**：把 logo 中间元素称作「蒲公英」——是**五叶草**，代表幸运的传播（2026-10-14 逸凡纠正）。

---

## 3. S2 排版规格（基准值，按 K 缩放）

以 A4 2480×3508 为基准（300dpi，1px ≈ 0.0847mm）：

- 页边距：左右 112px、上 98px、下 76px（`pad` 绝对定位 + flex 列，页脚 `margin-top:auto`）
- 正文 `44px / line-height 1.68`（≈10.5pt，A4 单页约 900 字的可读上限）
- 引文块 `42px`、结尾三色块正文 `38px`、序号圆形 `60px`
- 大标题 `62px`（宋体）、板块副标 `26–30px`
- 页头品牌名 `86px`（宋体）+ `MEANSPLUS`（浅红，字距 9px）+「第十年」红胶囊
- 最小字号不低于 `26px`（≈2.2mm），小字必须能看清
- 水印元素：宽 `285–450px`、透明度 `0.10–0.13`，压在标题与段落右侧，`z-index:0`，正文 `z-index:1`

**结构范式（2026-10-14 逸凡认可）**：每个元素独立成板块 = **板块大标题 + 元素水印**。
- 五叶草 · 幸运的传播（元素：五叶草）
- 凤纹 · 中华的来处（元素：凤纹）
- 结尾三个说法用三色并排色块

---

## 4. S3+S4 渲染与自动适配

```bash
# 单页渲染
python3 scripts/render_page.py --html page.html --png out.png --width 2480 --height 3508
# 自动定缩放（builder 模块里暴露 build(K)）
python3 scripts/render_page.py --builder make_page:build --png out.png --fit 0.90 1.05
```

Chrome 命令（本机已验证）：
```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --hide-scrollbars --no-sandbox \
  --force-device-scale-factor=1 --default-background-color=ffffffff \
  --window-size=2480,3508 --screenshot=out.png file:///abs/path.html
```

**适配判据（必须用数字，不靠眼睛）**：
1. 取渲染图 `lum<245` 的行覆盖率
2. 从底部往上找「页脚块」起点；其上最近的内容行＝正文底
3. 要求 `页脚顶 - 正文底 ≥ 60px` 且最后 30 行无 ink（未被裁）
4. 通栏色块（宽 >1500px 的连续行）底部必须高于页脚顶，否则换行悬崖导致溢出
5. 二分搜索 K：`gap < 阈值 → 降 K`，否则升 K；注意换行悬崖（K 从 1.0→1.04 可能突然溢出）

---

## 5. S5 校验（三重，禁止只看一眼就说好了）

1. **文字完整性**：`scripts/ocr_check.sh out.png`（swift + Vision，带坐标，依赖同目录 `ocr.swift`）。逐条比对待确认文案，确认没漏字、没串行、没被裁。CJK OCR 对英文小字会出错，英文用 `en` 对照或忽略噪音。
2. **几何量测**：ink bbox 查四边留白（logo / 名片类要求四边对称且留白达标）；10×12 密度网格一次看空档与拥堵；水印用「与原图 diff」定位占位区，确认不压正文。
3. **审美检查**：`glm-5v-turbo` 传 ≤600px 缩略图，问三件事——是否平衡、有无堆叠/重叠、文字是否被截止。**VLM 结论只作参考**，它读小字中文会幻觉（曾把 蓁熹 读成 嘉薰、编出整段假文案），字面内容一律以 OCR 与量测为准。

---

## 6. S6 交付

1. 一条消息只带一张图；多图分条发（`message` 工具 `attachments` 一次一张）
2. 预览用 JPG（quality 93–94, subsampling 0）；**真文件**（PNG 无损 / 带 alpha）走：
   `python3 scripts/feishu_send_file.py <abs_path> [open_id]`
   （message 工具传 PNG 时 `type=file` 会被飞书降级成 image 消息，必须走 API）
3. 交付话术要带：做了什么、改了什么、尺寸、下一步选项、需要她定的事项

---

## 7. S7 记忆与版本

- 每次交付写 `memory/YYYY-MM-DD.md`：文件路径、尺寸、脚本名、待确认项
- 同一页面多版并列时用 `v3/ v4/ …` 分目录，**不覆盖旧版**（逸凡常回头说「刚才那版更好」）
- 品牌级事实（文案、五心、用词规则）写入 `memory/manshi-brand-identity.md` 与 `MEMORY.md`
- 追加当日记忆时先读全文再写完整内容（该文件 write 语义不稳定，曾把全文截断）

---

## 8. 常见返工清单（正面回应过的反馈）

| 反馈 | 正确做法 |
|---|---|
| 阅读困难 | 正文改黑、字号 +25%、行距放宽、去掉实心色块堆叠 |
| 不要堆叠 | 用淡粉细线或留白分隔，替代嵌套色块 |
| 有凤凰底纹那版更好 | 元素水印要保留；凤纹/五叶草各自成板块 |
| 只做竖版 | 不主动加 16:9，先确认交付形态 |
| 这个尺寸（如 702×180） | 尺寸化交付要出白底 + 透明底 + @2x 三件套 |
| 文字里某词要换 | 全局替换（含页头/页脚/其他页面），避免混用 |
| logo 元素讲错 | 五叶草（幸运的传播），不是蒲公英 |

---

## 9. 校验标准（这个 skill 值不值得留）

- 出图一次通过率（逸凡不要求返工的比例）
- 文案零错字、零漏字（OCR 证据）
- 同一版式在名片 / PPT / 一页纸之间可复用，改文案即可换题材
- 单页产出耗时 ≤ 30 分钟（含渲染与校验）
- 每次返工都能追溯到具体清单项，而不是「感觉不对」

---

## 支持文件

- `templates/page_a4.html` —— A4 竖版模板（四 VI 色、黑字优先、元素水印、页脚 flex 布局）
- `scripts/render_page.py` —— 渲染 + 自动适配（K 二分 + 裁切/通栏块/间距三重校验）
- `scripts/extract_elements.py` —— 拆五叶草 / 凤纹 + 指定尺寸 logo 交付（白底 / 透明底）
- `scripts/ocr_check.sh` + `scripts/ocr.swift` —— macOS Vision OCR 校验（带坐标）
- `scripts/feishu_send_file.py` —— 飞书真文件发送（绕开 image 降级）
- `references/brand-assets.md` —— 资产路径、四 VI 色、字体、用词规则、关联实体
