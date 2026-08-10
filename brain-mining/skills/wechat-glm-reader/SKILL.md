# WeChat GLM Reader — 微信公众号文章读取工具

## 能力定位

只做一件事：**给一个公众号链接，返回完整内容（文字 + 图片里的文字）**，不做任何分析。

## 前置条件

- Python venv: `/tmp/wechat_venv/bin/python3`
- GLM API Key: `~/.openclaw/config/glm.json`
- Playwright chromium: 已安装
- 脚本: `scripts/wechat_glm_reader.py`

## 使用命令

```bash
/tmp/wechat_venv/bin/python3 \
  /Users/yifansmacmini/.openclaw/workspace/brain-mining/scripts/wechat_glm_reader.py \
  "<文章URL>" \
  --model glm-4v \
  --output-dir /tmp/wechat_reader
```

参数说明：
- `--model glm-4v`：GLM 视觉模型（也可用 glm-4v-plus）
- `--max-images N`：只分析前 N 张图（0 = 全部）
- `--skip-glm`：跳过图片分析（只下载图片）
- `--json`：输出 JSON 格式

## 输出格式

```json
{
  "url": "",
  "title": "",
  "article_source": "",
  "publish_date": "",
  "text_content": "HTML提取的文字",
  "images": [
    {
      "index": 0,
      "url": "mmbiz.qpic.cn/...",
      "local_path": "/tmp/.../img_000.png",
      "size_bytes": 64859,
      "width": 378,
      "height": 79,
      "ocr_text": "GLM-4V读出的图片文字"
    }
  ]
}
```

## 触发条件

用户发送 mp.weixin.qq.com 链接并要求读内容。

## 关键约束

- GLM-4V max_tokens 上限 2048
- 45 张图全部分析约 3-5 分钟
- 超大图（>5MB）可能失败，跳过并说明
- 只采集不分析——不添加任何判断
