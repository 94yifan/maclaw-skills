# 电商数据强制采集指令

项目: 度亚 智能窗帘行业品牌扫描
采集时间: 2026-08-10 16:53
覆盖品牌: 度亚（DUYAAR）, 杜亚 DOOYA, Aqara 绿米, 欧瑞博 ORVIBO, LifeSmart 云起, 邦先生 Mr.Bond, 小米米家

## 采集平台与数据类型

### 1. 天猫旗舰店
URL格式: https://list.tmall.com/search_product.htm?q={品牌名}+旗舰店
采集字段: 品牌名、爆款产品名、已付款数/评价数、价格、回头客率(标签)
示例: 搜索「品牌名 旗舰店」→ 按销量排序 → 取Top5产品

### 2. 京东自营/旗舰店
URL格式: https://search.jd.com/Search?keyword={品牌名}+旗舰店
采集字段: 品牌名、产品名、累计评价数(万+)、价格
示例: 搜索 → 按销量排序 → 取Top5产品

### 3. 抖音电商
URL格式: https://www.douyin.com/search/{品牌名}+旗舰店
采集字段: 品牌名、爆款、销量数据
示例: 搜索 → 品牌橱窗 → 商品销量

## 品牌级采集清单

| 品牌 | 天猫 | 京东 | 抖音 |
|------|------|------|------|
|------|------|------|------|
| 度亚（DUYAAR） | Tmall搜「度亚（DUYAAR） 旗舰店」| JD搜「度亚（DUYAAR）」| 抖音搜「度亚（DUYAAR）」|
| 杜亚 DOOYA | Tmall搜「杜亚 DOOYA 旗舰店」| JD搜「杜亚 DOOYA」| 抖音搜「杜亚 DOOYA」|
| Aqara 绿米 | Tmall搜「Aqara 绿米 旗舰店」| JD搜「Aqara 绿米」| 抖音搜「Aqara 绿米」|
| 欧瑞博 ORVIBO | Tmall搜「欧瑞博 ORVIBO 旗舰店」| JD搜「欧瑞博 ORVIBO」| 抖音搜「欧瑞博 ORVIBO」|
| LifeSmart 云起 | Tmall搜「LifeSmart 云起 旗舰店」| JD搜「LifeSmart 云起」| 抖音搜「LifeSmart 云起」|
| 邦先生 Mr.Bond | Tmall搜「邦先生 Mr.Bond 旗舰店」| JD搜「邦先生 Mr.Bond」| 抖音搜「邦先生 Mr.Bond」|
| 小米米家 | Tmall搜「小米米家 旗舰店」| JD搜「小米米家」| 抖音搜「小米米家」|

## 数据质量标准
- 每个品牌至少采集天猫 + 京东两个平台
- 每个平台至少Top5产品
- 必须包含：已付款数(天猫)、累计评价数(京东)、价格、产品名
- 回头客率(天猫)有标签则采集，无标签标记N/A
- 数据日期标注：采集当天

## 保存格式
每品牌每平台保存为一个JSON文件到 data/raw/ 目录
命名格式: ecommerce_tmall_{品牌}.json / ecommerce_jd_{品牌}.json

采集完成后再运行 collect_all() 验证完整性。