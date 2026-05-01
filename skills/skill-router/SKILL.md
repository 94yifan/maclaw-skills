---
name: skill-router
description: 任务分类与 skill 主动调用路由。**默认启用，每次处理重要任务前自动运行。**
---

# skill-router

## 一、这个 skill 用来做什么？

**功能：** 任务进来时，自动分析任务类型，主动推荐或调用最合适的 skill，而不是只用模型硬做。

**解决的问题：** 有时候逸凡的问题我不确定用哪个 skill 更合适，导致用模型硬做，效果不如用专门的 skill。这个 skill 把"任务分析 → skill 推荐 → 调用决策"变成标准化流程。

---

## 二、具体工作 SOP

### 第一步：任务分类

根据问题特征，先判断任务属于哪一类：

| 任务类型 | 特征关键词 | 对应 skill |
|----------|-----------|-----------|
| 研究调查 | 搜索、查找、调研、分析数据 | find-skills-skill / desearch-web-search |
| 内容创作 | 写、创作、生成内容、文案 | x-mentor-skill（X内容）/ human-writing（润色） |
| 复杂决策 | 这个成本合理吗、怎么选、第一性原理 | elon-musk-skill / munger-skill / thinking-model-enhancer |
| 人物思维 | 像XX一样、XX会怎么做、召唤 | wukong / steve-jobs-skill / zhangxuefeng-skill / elon-musk-skill |
| 技术实现 | 写代码、实现功能、技术方案 | find-skills-skill + skill-creator |
| 分身创建 | 新建 subagent、创建分身 | create-subagent |
| 系统监控 | 每天定时任务、自动更新 | openclaw-updater / openclaw-reminder |
| 数据采集 | 爬取、监控、微博、小红书 | tea-brand-daily-report / spider |
| 汇报优化 | 润色、改写、去AI腔 | human-writing / communication-skill |

### 第二步：扫描相关 skill

找到匹配的 skill 后，快速过一遍它的 SKILL.md，确认：
- 它能处理这个任务的具体哪个部分
- 调用它的最佳时机（before / during / after 主任务）

### 第三步：给出建议或直接调用

**建议格式（轻量）：**
- 直接调用：说清楚我决定调用哪个 skill、为什么、预期效果
- 询问确认：适合不确定或影响大的任务，说明选项让逸凡选

**注意：**
- 简单任务（30秒内能答完的）不用走这个流程
- Skill 调用要有明确理由，不为了用而用
- 不确定用哪个 → 直接说"这个问题我直接回答/我建议用XX skill"，不要假装很确定

---

## 三、Skill 分类索引

### 思维决策类
- wukong — 召唤任意名人思维框架
- elon-musk-skill — 马斯克第一性原理思维
- munger-skill — 芒格逆向思考/跨学科模型
- zhangxuefeng-skill — 张雪峰学业/职业规划
- steve-jobs-skill — 乔布斯产品/决策视角
- thinking-model-enhancer — 高级思维模型框架

### 内容创作类
- x-mentor-skill — X/Twitter 内容创作
- human-writing — 去AI腔润色
- communication-skill — 上下文感知回复
- image-remaster — 图片重制

### 研究调查类
- find-skills-skill — 搜索 ClawHub/GitHub 找 skill
- desearch-web-search — 网页搜索
- spider — 通用网页爬取
- web-scraping — 内容抓取
- youtube-transcript — 视频内容提取

### 技术实现类
- skill-creator — 创建/编辑 skill 文件
- skill-vetter — 安全审查
- create-subagent — 部署新 subagent
- browser-automation — 浏览器自动化

### 自动化运营类
- openclaw-updater — 每日 OpenClaw 更新检查（22:30）
- openclaw-reminder — 定时提醒
- tea-brand-daily-report — 茶饮品牌微博日报（10:05）
- create-subagent — 部署新分身

---

## 四、未来可复用价值

每次遇到需要用 skill 的场景，走这个标准化路由流程：分析任务类型 → 扫描索引 → 推荐/调用 skill。

这个 skill 本身不需要被调用，它的价值是让我养成"先想有没有更好的 tool"的习惯，而不是上来就用模型硬做。
