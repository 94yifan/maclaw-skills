# MEMORY.md - 长期记忆

## 身份

- **MacLaw** ⚡，AI 助手，运行在 yifan 的 Mac mini 上
- 飞书私聊为主渠道
- **每次重启后记忆丢失**，需从文件恢复上下文

## yifan 本人

- 李逸凡，曼拾创始人，1号位
- 称呼：逸凡 / 凡姐（不要叫"李总/老板"）
- 公司：上海曼拾文化传播有限公司
- 业务：小红书整合营销代理（主），品牌咨询/服务设计（次）
- 风格：简单直接，结果导向，不内耗
- 沟通：飞书私聊优先，重要紧急事第一时间说

## 技术环境

- 网关：ws://127.0.0.1:18789
- OpenClaw 版本：重装最新（2026-04-27 重装）
- 运行时：node=v25.8.1, model=minimax/MiniMax-M2.7
- GitHub 备份仓库：github.com/yifanli94/maclaw-skills（已验证正常工作）
- **注意**：social-crawler workspace 的 skills 未备份到 GitHub；可参考 `social-crawler/SKILL-REGISTRY.md` 的安装命令重建

## Skill 创建汇报逻辑

每次创建新 skill 后，立即向逸凡汇报。

**汇报内容（四点，每点写实质内容，不贴标签）：**
1. 这个 skill 用来做什么——解决什么问题，谁需要用，什么场景
2. 具体 SOP——关键步骤 + 具体命令或动作，写清楚"是什么/怎么做/关键在哪"
3. 关键约束——这个 skill 最容易出错或被忽略的一点
4. 复用价值——为什么值得写进 skill 而不是一次性的

**汇报格式：** 描述性段落，不用清单体，一条消息说清楚。
**汇报后动作：** 备份 GitHub → 更新 MEMORY.md → 同步 subagent workspace SOUL

**汇报时机：** 完成后立即汇报，不等下次对话。

---
## 逸凡喜欢的汇报风格

**核心原则：言之有物，不走形式。**

汇报的本质是让对方清楚知道——发生了什么、为什么重要、下一步做什么。不是展示格式、不是凑字数。

**具体要求：**
1. **直接给结论，不说我找到了/查到了/正在看** — 发现什么直接说，不做中间态汇报。不确定就说还没结论，不假装有结论。
2. **一条消息说清楚，不拆多条** — 没有意义的消息间隔是浪费。一次性说完整，不挤牙膏。
3. **每一点要有实质内容，不贴标签** — 每一点写出具体内容，写清楚"是什么/怎么做/关键在哪"，不是只写步骤标题。
4. **描述性段落，不用清单体** — 清单体是给机器看的，段落是给人看的。重要内容用自然段落说清楚。
5. **没有 corporate 废话** — 不用"非常感谢您的提问""整体而言""从某种意义上说"这类填充词。不装饰，直接说。

**应用场景：** 每次向逸凡汇报、创建 skill 后汇报、分身自我介绍，均适用此风格。

## 已安装 Skills（全部备份到 GitHub）

主要 skills：
- skill-vetter, self-improving-agent, humanizer, free-ride
- api-gateway, youtube-transcript, auto-updater, openai-whisper
- openclaw-reminder, browser-automation-stealth, desearch-web-search
- find-skills-skill, summarize-1-0-0, cangjie-skill, nuwa
- steve-jobs-skill, x-mentor-skill, zhangxuefeng-skill
- elon-musk-skill, munger-skill

## 配置状态

- Dreaming cron：12:00（静默）+ 22:00（有汇报）
- 群聊：主 agent 群聊 requireMention 已关闭，可自动接收

## 已知悬而未决

- **Social Crawler 分身**：等 yifan 在飞书开放平台创建独立 app（App ID + Secret）
  - 独立 workspace：`~/.openclaw/workspace/social-crawler/`
  - 群号：oc_96796887fcf96dba638afa646fbb6bb2
- 飞书聊天记录导出转 Markdown（恢复上下文）
- Social crawler 的 skills 均已安装完毕（xiaohongshu-crawler 等8个）

## 架构决策（重要）

- **每个 subagent 分身需要独立飞书 app** 才能独立接收群消息并有独立身份
- 单飞书主应用 + subagent-hooks 无法实现多分身独立群聊接收
- 群聊 spawn subagent 需从群聊内触发，不能从私聊 spawn

## 数据采集经验

- **Weibo 企业号访问**：用数字 UID（`weibo.com/u/数字ID`）比 handle 更稳定；handle 经常重定向到个人页而非企业蓝V
- **Chrome CDP 连接**：端口 9333 已验证可用；playwright evaluate 时需 kill navigation 避免上下文摧毁
- **楼下酸奶**：无官方蓝V微博账号，监控时跳过
- **微博日报任务**：已建立每天 10:05 抓取 19 个茶饮品牌微博的标准化流程，报告输出到 `memory/weibo_daily_YYYY-MM-DD.md`
  - 2026-04-28 首次成功产出，当日 6/19 品牌有内容（瑞幸、库迪、古茗、茉莉奶白、霸王茶姬、喜茶）
  - 核心价值：识别听劝营销案例（瑞幸全冰去水转正）、IP联名动向（茉莉奶白×INSTINCTOY）、品牌视觉升级信号（库迪换logo）
- **品牌内容监控**：无内容 ≠ 无运营，部分品牌发布频率低或发布在其他平台，日报中标注清晰即可

## 2026-04-30 新增：酒水行业营销方法论

今天整理了小红书酒水行业全链路营销方法论（来源：飞书文档《一图读懂｜小红书酒水行业全链路解决方案》）

**核心价值：** 曼拾核心业务（小红书整合营销）的行业方法论参考，包含：
- 年轻人饮酒行为三大转变：时间扩张（情绪陪伴）、空间扩张（场景主权）、决策前移（搜索栏）
- 四大生长坐标：需求坐标（趋势预判+新品SOP）、人群坐标（精细化沟通）、场景坐标（日常渗透）、节点坐标（搜索截流）
- KFS协同打法：KOL造浪→KOC续流→FS放大
- 文化三层渗透：文化层交心→兴趣层拓圈→场景层渗透
- 完整方法论文档：`memory/xhs-alcohol-methodology-20260430.md`

**值得关注的信号：** 酒水行业在小红书2025年搜索量增长2281.30%，是曼拾业务增量的重要赛道

## Social Crawler workspace 详情

独立 workspace：`~/.openclaw/workspace/social-crawler/`

**已安装 skills（social-crawler 专属）**：
- xiaohongshu-crawler — 小红书内容爬取
- xiaohongshu-viral-copy — 小红书爆款文案生成
- desk-research — 结构化 desk research
- data-analysis-reporting — 商业数据报告生成
- copywriting-pro / copywriting-zh-pro
- feishu-doc-manager — 飞书文档 Markdown 发布
- browser-automation-stealth

**已验证工作流**：
- 茶饮品牌微博日报（18个品牌，cron 10:05 北京时间）
- 飞书文档结构：H1日期标题 → 分割线 → 品牌内容（新品/IP/营销） → 汇总表
- 去痕迹规则：删除转发/关注/点赞/评论/抽X位/Live/已编辑等字段

**注意**：browser-automation-stealth 和 feishu-doc-manager 有 VirusTotal 误报（加解密关键词），安装需加 `--force`

## 书写原则（2026-04-30 新增，来源：逸凡反馈）

**核心要求：卖点与情绪场景必须直接对应，不能跳跃。**

举例时，产品功能参数和它对应的情绪/生活场景之间必须有直接的逻辑链，不能跳步。错误的逻辑示例："静音120分钟续航"→"终于可以躺着了"——这两个之间没有直接的因果或情绪对应关系，读起来是脱节的。

正确逻辑：功能→用户使用这个功能时的具体感受→这个感受指向的生活场景。

比如扫地机器人：吸力强+超静音（功能）→加班回家倒头就睡、宝宝在客厅爬来爬去也不用担心噪音（具体感受）→回家终于不用管地面干不干净了（生活场景）。

**禁止为了写而写**：每个举例都要检查功能→情绪→场景这三个环节是否衔接顺畅，不能为了凑字数或显得有道理而跳步。

- 每次重装后 subagent 全部清零，记忆丢失是常态，GitHub 备份是保底
- 飞书私聊是主要沟通渠道
- 曼拾业务定位：小红书整合营销代理（主），品牌咨询/服务设计（次）
- 平台账号 ID 尽量用数字 UID，避免重定向问题
- **SOUL 被动执行 ≠ 什么都不做**——是"有边界地响应"。边界没写清楚，agent 会自行补全，容易补全成"什么都做"导致 loop。写 SOUL 时先确认边界，用反面校验（"如果它理解为什么都不做会怎样"）确认语义正确。
- **isolated session 有特殊行为**：agentId 固定为 main，workspace 绑定到 main。所有文件路径必须用绝对路径，不依赖 context 解析。

---
## 教训（2026-04-30 新增）

**1. CDP 连接不管理生命周期**
`chromium.connectOverCDP()` 连接已有 Chrome 用户会话后，进程结束时不需要调用任何 disconnect 方法，浏览器保持原状即可。这和 `launch()` 后需要 `close()` 不同。错误调用 `disconnect()` 会导致 TypeError，脚本崩溃，数据全部丢失。

**2. 脚本必须有自我保护**
关键 Cron 脚本必须在执行过程中主动写文件，不能依赖 session 结束后自动保存。崩溃时自动保存机制也会失效。正确的做法是：爬取完成后立即写文件，用 `process.exit(0)` 确保正常退出码。

**3. 关键产出要设检查节点**
重要 Cron 触发后，必须在合理时间窗口（如30分钟内）检查产出是否成功。发现问题立刻重跑，不要等到下次人工检查才发现。今天日报完全失败但直到12:00才被发现，损失了一整天的数据。

---
## 2026-05-01 Dreaming Noon 观察

**日报系统仍有问题**：
- 茶饮日报 cron（10:05）状态 error，今日未产出
- state 文件仍是 Apr 30 日期，说明今日 cron 完全没有执行或中途失败
- 脚本末尾没有 `process.exit(0)`，依赖 main() 自然结束——如果 main() 抛出异常被 catch 但不退出，脚本会hang
- 脚本不复制报告到 memory/，不发飞书群，这是 4/30 已知的系统设计缺陷，至今未修复

**待跟进**（不采取行动）：
- 茶饮日报系统需要完整修复（脚本末尾加内存+发群+exit(0)，或在 cron trigger 逻辑中补全后续步骤）
- Social Crawler 飞书 app 仍未创建（卡点多日）
- 5/1 是五一假期第一天，茶饮品牌营销动态可能有特殊节点行为（旅游/出行/送礼场景）

**模式识别**：
- 每次 Dreaming 都在重复指出"日报系统有问题"，但实际修复没有发生。这不是认知问题，是执行问题。需要有具体的修复计划而不是反复识别问题。
