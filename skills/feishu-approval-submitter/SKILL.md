---
name: "feishu-approval-submitter"
description: "通过飞书API自动提交付款申请等审批实例，含附件上传和表单填写"
version: "v1"
date: "2026-07-13"
---

# Feishu Approval Submitter — 飞书审批自动提交流程

通过飞书 Open API 自动创建审批实例。通用型 Skill，适配付款申请、报销、费用申请等所有飞书审批模板。

## 适用场景

- 需要代用户提交飞书审批（付款申请、报销、费用申请、备用金等）
- 表单包含 input、textarea、radioV2、checkboxV2、amount、date、attachmentV2、connect、department、contact 等控件
- 需要自动上传发票/凭据附件

## 前置条件

飞书自建应用需要以下 scope（在开放平台配置）：
- `approval:approval:readonly`（tenant）
- `approval:instance`（tenant）
- `approval:approval`（tenant）
- `approval:definition`（tenant）

## 关键约束（必读）

| 项目 | 限制 |
|------|------|
| account 控件（收款账户） | **API 不支持**，需将信息写入同级 textarea 字段（付款明细/备注）|
| form 参数 | 必须是 JSON **字符串**，不是 JSON 数组 |
| 用户 ID | 用 `open_id` 字段（值 `ou_xxx`），不用 `user_id` 字段 |
| 鉴权 | 使用 `tenant_access_token` 即可 |
| 附件上传端点 | `https://www.feishu.cn/approval/openapi/v2/file/upload`（不是 v4）|

## 控件 value 格式速查表

| 控件类型 | value 格式 | 示例 |
|---------|-----------|------|
| input | string | `"曼拾"` |
| textarea | string | `"樱桃26箱"` |
| radioV2 | string（选项 value 编码） | `"luth75r8-6008cpvhsk-0"` |
| checkboxV2 | string[]（选项 value 编码数组） | `["k2b8..."]` |
| amount | number（浮点数） | `6968.00` |
| date | string（RFC3339） | `"2026-07-13T00:00:00+08:00"` |
| attachmentV2 | string[]（file_code 数组） | `["C4C9365B-..."]` |
| connect | string[]（关联审批实例编码） | `["19EAC829-..."]` |
| account | ❌ API 不支持 | 转 textarea 写入备注/付款明细 |
| input 默认值 | 直接从定义中读取 | "曼拾" / "逸淼芃" |

## 标准操作流程

### 第一步：获取审批定义并解析表单

```
GET https://open.feishu.cn/open-apis/approval/v4/approvals/{approval_code}
```

从返回的 `form` 字段解析所有控件（widget）：
- 记录每个控件的 id、type、name、required、default_value
- 记录 option 列表（radioV2/checkboxV2 的可用选项）
- 记录 display_condition（联动/条件显示逻辑）
- 记录 form_widget_relation（选项联动关系：父控件选择值后，子控件可用选项变化）

### 第二步：匹配用户输入，识别缺口

将用户提供的信息逐一匹配到控件：
- 文本类（input/textarea）：name 和 value 匹配即可
- 单选类（radioV2）：从 option 列表中匹配用户提到的最匹配项
- 金额/日期：格式转换后直接填入
- 附件：先上传获取 file_code 再填入

识别出所有必填控件中用户未提供、也无默认值的字段。

### 第三步：向用户提问缺口

仅询问「必填且无法推断」的字段：
- 单选/联动类的选项（用户没说选哪个）
- 需要选择的附件内容（对私付款账户等）
- 关联审批（connect 类型）

一句话问，不给用户列清单。

### 第四步：上传附件

```
POST https://www.feishu.cn/approval/openapi/v2/file/upload
Authorization: Bearer {tenant_access_token}
Content-Type: multipart/form-data

name: invoice.png
type: image   （图片用 image，文件用 attachment）
content: <file binary>
```

返回 `data.code` → 用于 attachmentV2 控件的 value 数组。

### 第五步：构造 form 并创建实例

```python
form_data = [
    {"id": "widget_xxx", "type": "input", "value": "曼拾"},
    {"id": "widget_yyy", "type": "radioV2", "value": "luth75r8-..."},
    {"id": "widget_zzz", "type": "amount", "value": 6968.00},
    ...
]

payload = {
    "approval_code": "{approval_code}",
    "open_id": "{user_open_id}",
    "form": json.dumps(form_data)   # !! 必须是 JSON 字符串 !!
}

POST https://open.feishu.cn/open-apis/approval/v4/instances
```

成功返回 `data.instance_code`。

## 对接用户时的习惯

- 用户给的信息（事由、金额、收款方、付款类型）直接匹配字段
- 有默认值的字段自动填，不再询问
- 只问必填且无法推断的选项
- 发送审批结果时附带实例编码和最终摘要，一句话说完

## 完整 Python 示例

```python
import json, requests

def get_token(app_id, app_secret):
    resp = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
        json={"app_id": app_id, "app_secret": app_secret})
    return resp.json()['tenant_access_token']

def upload_file(token, filepath, filename, file_type="image"):
    with open(filepath, "rb") as f:
        resp = requests.post('https://www.feishu.cn/approval/openapi/v2/file/upload',
            headers={"Authorization": f"Bearer {token}"},
            files={"content": (filename, f, "image/png")},
            data={"name": filename, "type": file_type})
    return resp.json()['data']['code']

def get_approval_form(token, approval_code):
    resp = requests.get(f'https://open.feishu.cn/open-apis/approval/v4/approvals/{approval_code}',
        headers={"Authorization": f"Bearer {token}"})
    data = resp.json()['data']
    form = json.loads(data['form'])
    relation = json.loads(data.get('form_widget_relation', '{}'))
    return form, relation

def create_instance(token, approval_code, open_id, form_data):
    payload = {
        "approval_code": approval_code,
        "open_id": open_id,
        "form": json.dumps(form_data)
    }
    resp = requests.post('https://open.feishu.cn/open-apis/approval/v4/instances',
        headers={"Authorization": f"Bearer {token}"}, json=payload)
    return resp.json()['data']['instance_code']
```

## account（收款账户）控件实测结论（2026-10-18 补充）

官方文档明确 account 属于「创建审批实例 API 不支持的控件」，实战结论：

| 字段 | 可用性 | 正确写法 |
|------|--------|----------|
| widgetAccountName | ✅ 字符串 | `"公司/个人名"` |
| widgetAccountNumber | ✅ 字符串 | `"账号"` |
| widgetAccountBankName | ✅ 只能是对象，key 必须是 `bankNameZh` | `{"bankNameZh":"中国银行"}`；错 key（如 bankName）会写入空对象 |
| widgetAccountBankBranch | ❌ 支行写不进去（bankBranchName / bankBranchNameZh 均失败） | 支行信息写入「付款明细」textarea |
| widgetAccountBankArea | ❌ 空 | 同上 |
| plain string | ❌ 报 1395006 控件值不合法 | 不要用字符串 |

**标准做法：** account 只传 户名 + 账号 + `{"bankNameZh":"开户行总行名"}`，完整开户行（含支行）写进付款明细，提交后回查 instance 确认户名/账号正确。
回查响应里 text 若是 `[123 34 ...]` 形式，是服务端字节序列化，用 `bytes(json.loads(text)).decode()` 还原可读。
