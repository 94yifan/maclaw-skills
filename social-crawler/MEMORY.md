# MEMORY.md - 长期记忆

## 身份

- **MacLaw** ⚡,AI 助手,运行在 yifan 的 Mac mini 上
- 飞书私聊为主渠道
- **每次重启后记忆丢失**,需从文件恢复上下文

## yifan 本人

- 李逸凡,曼拾创始人,1号位
- 称呼:逸凡 / 凡姐(不要叫"李总/老板")
- 公司:上海曼拾文化传播有限公司
- 业务:小红书整合营销代理(主),品牌咨询/服务设计(次)
- 风格:简单直接,结果导向,不内耗
- 沟通:飞书私聊优先,重要紧急事第一时间说

## 技术环境

- 网关:ws://127.0.0.1:18789
- OpenClaw 版本:重装最新(2026-04-27 重装)
- 运行时:node=v25.8.1, model=minimax/MiniMax-M2.7
- GitHub 备份仓库:github.com/yifanli94/maclaw-skills(已验证正常工作)
- **注意**:social-crawler workspace 的 skills 未备份到 GitHub;可参考 `social-crawler/SKILL-REGISTRY.md` 的安装命令重建

## Skill 创建汇报逻辑

每次创建新 skill 后,立即向逸凡汇报。

**汇报内容(四点,每点写实质内容,不贴标签):**
1. 这个 skill 用来做什么--解决什么问题,谁需要用,什么场景
2. 具体 SOP--关键步骤 + 具体命令或动作,写清楚"是什么/怎么做/关键在哪"
3. 关键约束--这个 skill 最容易出错或被忽略的一点
4. 复用价值--为什么值得写进 skill 而不是一次性的

**汇报格式:** 描述性段落,不用清单体,一条消息说清楚。
**汇报后动作:** 备份 GitHub → 更新 MEMORY.md → 同步 subagent workspace SOUL

**汇报时机:** 完成后立即汇报,不等下次对话。

---
## 逸凡喜欢的汇报风格

**核心原则:言之有物,不走形式。**

汇报的本质是让对方清楚知道--发生了什么、为什么重要、下一步做什么。不是展示格式、不是凑字数。

**具体要求:**
1. **直接给结论,不说我找到了/查到了/正在看** - 发现什么直接说,不做中间态汇报。不确定就说还没结论,不假装有结论。
2. **一条消息说清楚,不拆多条** - 没有意义的消息间隔是浪费。一次性说完整,不挤牙膏。
3. **每一点要有实质内容,不贴标签** - 每一点写出具体内容,写清楚"是什么/怎么做/关键在哪",不是只写步骤标题。
4. **描述性段落,不用清单体** - 清单体是给机器看的,段落是给人看的。重要内容用自然段落说清楚。
5. **没有 corporate 废话** - 不用"非常感谢您的提问""整体而言""从某种意义上说"这类填充词。不装饰,直接说。

**应用场景:** 每次向逸凡汇报、创建 skill 后汇报、分身自我介绍,均适用此风格。

## 已安装 Skills(全部备份到 GitHub)

主要 skills:
- skill-vetter, self-improving-agent, humanizer, free-ride
- api-gateway, youtube-transcript, auto-updater, openai-whisper
- openclaw-reminder, browser-automation-stealth, desearch-web-search
- find-skills-skill, summarize-1-0-0, cangjie-skill, nuwa
- steve-jobs-skill, x-mentor-skill, zhangxuefeng-skill
- elon-musk-skill, munger-skill

## 配置状态

- Dreaming cron:12:00(静默)+ 22:00(有汇报)
- 群聊:主 agent 群聊 requireMention 已关闭,可自动接收
- **茶饮日报启动通知**:cron 触发时立即向群聊发一条"开始跑今天的日报了"再开始爬数据

## 已知悬而未决

- **Social Crawler 分身**:等 yifan 在飞书开放平台创建独立 app(App ID + Secret)
  - 独立 workspace:`~/.openclaw/workspace/social-crawler/`
  - 群号:oc_96796887fcf96dba638afa646fbb6bb2
- 飞书聊天记录导出转 Markdown(恢复上下文)
- Social crawler 的 skills 均已安装完毕(xiaohongshu-crawler 等8个)

## 架构决策(重要)

- **每个 subagent 分身需要独立飞书 app** 才能独立接收群消息并有独立身份
- 单飞书主应用 + subagent-hooks 无法实现多分身独立群聊接收
- 群聊 spawn subagent 需从群聊内触发,不能从私聊 spawn

## 数据采集经验

- **Weibo 企业号访问**:用数字 UID(`weibo.com/u/数字ID`)比 handle 更稳定;handle 经常重定向到个人页而非企业蓝V
- **Chrome CDP 连接**:端口 9333(用户真实Chrome,有登录态),端口 18800(openclaw浏览器,已禁用);**爬微博只用9333,不用18800**
- **楼下酸奶**:无官方蓝V微博账号,监控时跳过
- **微博日报任务**:已建立每天 10:05 抓取 19 个茶饮品牌微博的标准化流程,报告输出到 `memory/weibo_daily_YYYY-MM-DD.md`
  - 2026-04-28 首次成功产出,当日 6/19 品牌有内容(瑞幸、库迪、古茗、茉莉奶白、霸王茶姬、喜茶)
  - 2026-04-29 第二次执行,18/18全部成功,效率稳定
  - **核心价值**:识别听劝营销案例(瑞幸全冰去水转正)、IP联名动向(茉莉奶白×INSTINCTOY)、品牌视觉升级信号(库迪换logo)、季节性回归产品(古茗超A芝士葡萄第8年、奈雪霸气杨梅第11年)
- **品牌内容监控**:无内容 ≠ 无运营,部分品牌发布频率低或发布在其他平台,日报中标注清晰即可
- **飞书文档更新**:必须经过用户确认,不得自行写入
- **爬虫稳定性**:2026-04-28-29连续两次成功,CDP端口9333稳定,选择器`article`标签稳定,随机等待12-18秒有效防风控;断点续跑state文件机制有效
- **2026-04-30重大故障**:browser.disconnect() TypeError导致脚本以exit(1)崩溃,18个品牌数据全部丢失;根因是CDPBrowser对象没有disconnect()方法;已修复(删除该行),同时认识到Cron session自动保存不可靠,必须主动写文件才算完成

## 品牌内容洞察(长期追踪)

### 季节规律
- **4月底-5月**:茶饮年度重磅新品密集期(杨梅、葡萄等时令水果回归)
- **听劝营销成标配**:瑞幸全冰去水转正、古茗"真的听劝了",用户共创影响产品开发

### 重点品牌动态
- **古茗**:超A芝士葡萄第8年回归,4月30日上线;Pingu IP联名第二弹
- **奈雪**:霸气杨梅第11年,4月28日上线;高圆圆代言纤果茶
- **瑞幸**:小黄油美式听劝转正;蛋仔派对联动
- **茉莉奶白**:温哥华列治文店4月18日开业,国际化扩张信号
- **茶百道**:黑糖粉粿(闽南糖水元素),4月29日上新

### IP联名趋势
- 游戏联动(CoCo×Nikke)、明星+IP双线(爷爷不泡茶)、传统文化(星巴克×只此青绿)多元路线并行

## Social Crawler workspace 详情

独立 workspace:`~/.openclaw/workspace/social-crawler/`

**已安装 skills(social-crawler 专属)**:
- xiaohongshu-crawler - 小红书内容爬取
- xiaohongshu-viral-copy - 小红书爆款文案生成
- desk-research - 结构化 desk research
- data-analysis-reporting - 商业数据报告生成
- copywriting-pro / copywriting-zh-pro
- feishu-doc-manager - 飞书文档 Markdown 发布
- browser-automation-stealth

**报告输出流程（2026-04-30调整）**：
- 日报完成后，先在群里发文字完整版（格式与云文档一致：品牌分【新品】【IP联名】【营销活动】三块+汇总表）
- 等逸凡确认（说"可以"或类似确认语）后再写云文档
- 如有修改意见，等修改，不自行决定
- 写入云文档：找到文档中最底部的日期块（H1)，把当日日报整块 append 到该日期块下方空白处
- 永远不修改已有内容，只在末尾追加
- 禁止用 `insert` / `write`（会叠加旧内容或产生包含关系错误）
- 文档token: `PEJadXoKiorPI2xNFgvcqdOFnHL`

**品牌监控列表（2026-04-30起增至19个）**：
1. 瑞幸咖啡 | 6349791448
2. 库迪 | 7791266545
3. 古茗 | 2809775704
4. 幸运咖 | 6519396553
5. 茉莉奶白 | 7577524421
6. 霸王茶姬 | 5652018762
7. 喜茶 | 2804387887
8. 星巴克 | starbucks
9. 茶百道 | 6502206666
10. 奈雪的茶 | 5884674413
11. CoCo | 2030619861
12. 爷爷不泡茶 | 7769072120
13. 沪上阿姨 | 3921865344
14. 乐乐茶 | 6253473981
15. 皮爷咖啡 | 6360528436
16. M Stand | 6345199298
17. Manner | 6808111794
18. 茉酸奶 | 5188894132
19. 树夏酸奶 | 7144806571

**去重规则（2026-04-30新增）**：
- 每条内容与前一天同品牌内容比对
- 雷同/相同：标注"🔄 重复推老内容：[内容简述]"，整条保留
- 连续多日重复推广同一活动：标注"🔄 第X天重复推广：[内容简述]"
- 确实为新发布：正常录入
- 24小时内无新增发布：注明"无新增发布"

**格式规范（2026-04-30新增）**：
- 同一品牌多个新品/IP联名/营销活动各自单独成行，不合并一行

**已验证工作流**:
- 茶饮品牌微博日报(18个品牌,cron 10:05 北京时间)
- 飞书文档结构:H1日期标题 → 分割线 → 品牌内容(新品/IP/营销) → 汇总表
- 去痕迹规则:删除转发/关注/点赞/评论/抽X位/Live/已编辑等字段

**注意**:browser-automation-stealth 和 feishu-doc-manager 有 VirusTotal 误报(加解密关键词),安装需加 `--force`

## 重大教训

- 每次重装后 subagent 全部清零,记忆丢失是常态,GitHub 备份是保底
- 飞书私聊是主要沟通渠道
- 曼拾业务定位:小红书整合营销代理(主),品牌咨询/服务设计(次)
- 平台账号 ID 尽量用数字 UID,避免重定向问题

## 2026-04-30 复盘补充（Dreaming Night）

### 今日实际情况（与中午复盘不同）

中午复盘说"日报数据完全丢失"是**错的**。实际：
- `/tmp/tea-report-2026-04-30.md` 在 10:11 生成，45KB，18/18品牌数据完整
- `/tmp/tea-crawl-state.json` 也在 10:11 更新，两文件均存在
- **真正丢失的是**：日报没有写入 `memory/weibo_daily_2026-04-30.md`，也没有发飞书群

### 根因分析

两个脚本并存造成混乱：
- `/private/tmp/crawl-tea.mjs` — 旧版脚本，cron 触发它（10:05），包含 `browser.disconnect()` 错误
- `/tmp/tea-brand-crawler-v3.mjs` — 新版脚本，有 `browser.close()` 但**没有发飞书群和写 memory 的逻辑**

脚本生成报告文件后没有后续动作（不写 memory，不发群），是设计缺陷——脚本只管爬，不管产出后处理。

### 错误根因重新定性

| 错误 | 性质 | 严重程度 |
|------|------|----------|
| 日报没写 memory | 设计缺陷 | 高——无积累、无长期可查 |
| 日报没发飞书群 | 设计缺陷 | 高——用户看不到 |
| `browser.disconnect()` | 代码 bug | 已修复 |
| 脚本设计只爬不管发 | 系统设计漏洞 | 高——每次都丢后半段 |

### 修复方案（必须执行）

**方案A（推荐）：让脚本管到底**
在 `tea-brand-crawler-v3.mjs` 末尾的 `main()` 里，生成报告后：
1. 复制报告到 `~/.openclaw/workspace/memory/weibo_daily_YYYY-MM-DD.md`
2. 调用飞书 API 把报告发到群聊

**方案B（过渡）：cron trigger 捕获输出**
cron 的 `announce` delivery 机制应该在脚本 stdout 有输出时自动发群，但目前没有生效。

### 明日必须检查

1. **明天 10:05 触发后，10:30 前检查**：
   - `memory/weibo_daily_2026-04-30.md` 是否存在（今日补写）
   - 飞书群是否收到日报
2. 如果群没收到日报，手动发今日报告（`/tmp/tea-report-2026-04-30.md` 内容）
3. 确认新脚本（`/tmp/tea-brand-crawler-v3.mjs`）有完整的后续处理逻辑

### 今日数据亮点（值得记住）

从 `/tmp/tea-report-2026-04-30.md` 提取的品牌动态：
- **瑞幸**：小黄油美式（全冰去水）正式转正，蛋仔派对联动延续，江苏省门店突破3000家
- **古茗**：超A芝士葡萄第8年回归（4月30日）
- **奈雪**：霸气杨梅第11年（4月28日上线）
- **茶百道**：黑糖粉粿（闽南糖水元素）4月29日上新
- **茉莉奶白**：温哥华列治文店已于4月18日开业，国际化扩张信号

### 效率数据

- 爬取 18 个品牌（树夏酸奶无蓝V），耗时约 18×15s = 4.5分钟（不含页面加载）
- 加上滚动等待，总时长约 18×20s = 6分钟
- 断点续跑机制有效（`/tmp/tea-crawl-state.json`），崩溃后可续跑

### 预防措施

1. **日报脚本必须包含写 memory + 发群逻辑**，不能只爬不处理
2. **cron 触发后主动检查产出**：10:05 触发 → 10:30 前检查 memory 文件
3. **删除旧版 `/private/tmp/crawl-tea.mjs`**，避免脚本版本混乱
4. **统一脚本版本**：只用 `/tmp/tea-brand-crawler-v3.mjs`，明确它是唯一执行脚本

### 逸凡的沟通偏好（持续观察）

- 从今天的交互看，她对报告的期待是：**群里有完整日报 + 云文档有存档**
- 今天两个都没做到，说明脚本设计必须补全这两个环节

## 2026-05-01 Dreaming Noon 复盘

### 今日致命错误：CDP 9333 端口不可用

**现象：** 10:05 AM cron 触发，状态 `error`，爬虫未执行。

**根因：** 
- CDP 9333 端口不可用（yifan Chrome remote debugging）
- 当前只有 18800 可用（openclaw browser，无登录态）
- 脚本写死 9333，无 fallback

**修复（具体代码）：**
在脚本启动时自动探测可用端口：

```javascript
const CDP_PORTS = [9333, 18800];
let browser;
for (const port of CDP_PORTS) {
  try {
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
    console.log(`Connected via CDP port ${port}`);
    break;
  } catch (e) {
    if (port === CDP_PORTS[CDP_PORTS.length - 1]) throw new Error('All CDP ports failed');
  }
}
```

**预防：**
- 脚本永远不能写死端口，必须自动探测
- 每次 cron 前做端口预检测，结果写入 `/tmp/cdp-status-YYYY-MM-DD.json`

### 仍悬而未决的系统缺陷（从4月30日延续）

| 问题 | 状态 | 严重程度 |
|------|------|----------|
| 脚本无写 memory 逻辑 | ⏳ 未修复 | 高 |
| 脚本无发飞书群逻辑 | ⏳ 未修复 | 高 |
| cron announce 机制不生效 | ⏳ 未修复 | 中 |
| state 文件跨日未重置 | ⏳ 未修复（今日未跑） | 低 |

### CDP 端口当前状态

| 端口 | 状态 | 说明 |
|------|------|------|
| 9333 | ❌ 不可用 | yifan Chrome remote debugging |
| 18800 | ✅ 可用 | openclaw browser，无登录态 |

**关键问题：** yifan 的 Chrome 是否还开着 remote debugging？需确认。

### 明日行动项

1. **P0**：向逸凡确认她的 Chrome 9333 是否开着
2. **P0**：修改脚本增加 CDP 端口自动探测 + fallback
3. **P1**：给脚本加写 memory 和发飞书群逻辑
4. **P2**：cron 前做 CDP 端口预检测

### 今日数据亮点（来自4月30日 state 文件）

- **古茗听劝2.0**：超A芝士葡萄第8年，强调"我们真的听劝了"，用户共创语言化
- **五一营销窗口**：库迪/瑞幸都有五一内容，假期是重要营销节点
- **Pingu系列联名**：古茗Pingu第二弹距第一弹不到一个月，系列化联名趋势

### 今日效率数据

- 今日爬虫未执行（连接失败）
- 4月30日数据：18品牌，耗时约18×20s = 6分钟（含等待）

### 5月2日预判

- 如果CDP 9333恢复，脚本需要重置 state 文件（今天是5月1日但state仍是4月30日）
- 需要在 cron 触发前确认端口状态
