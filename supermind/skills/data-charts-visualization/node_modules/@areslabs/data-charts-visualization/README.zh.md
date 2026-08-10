# @areslabs/data-charts-visualization

一个在 Node.js 环境中将 ECharts 渲染为 PNG 或 SVG 的命令行工具。

## 安装与调用

发布后推荐直接通过 `npx` 调用：

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 --help
```

包暴露的 bin 名称为：

```bash
areslabs-data-charts
```

## 用法

```bash
areslabs-data-charts --chart-type <type> (--data <json> | --data-file <file>) (--config <json> | --config-file <file>) [--variant <json>] [--width <px>] [--height <px>] [--out <dir|file>]
```

支持的图表类型：

```text
line, bar, pie, gauge, area, dualAxis, scatter, radar, funnel
```

## 参数说明

- `--chart-type`：图表类型。
- `--data`：图表数据，使用内联 JSON 传递。
- `--data-file`：图表数据文件路径。
- `--config`：完整 helper config，使用内联 JSON 传递。
- `--config-file`：完整 helper config 文件路径。
- `--variant`：一次性渲染策略，使用内联 JSON 传递。
- `--width`：输出宽度，单位像素，默认 `650`。
- `--height`：输出高度，单位像素，默认 `360`。
- `--out`：输出目录或输出文件路径。默认写入系统临时目录下的 `areslabs-data-charts`。

约束：

- `--data` 和 `--data-file` 二选一，必须传一个。
- `--config` 和 `--config-file` 二选一，必须传一个。
- `--variant` 只支持内联 JSON，不支持文件。
- `--config` 必须是完整配置对象，且同时包含 `common` 和 `specific`。

## Payload 说明

CLI 输入由三部分组成：

- `data`：原始 ECharts 数据片段。
- `config`：完整 helper config。
- `variant`：一次性渲染策略。

其中 `data` 和 `config` 必填，`variant` 可选。

### Data 传递说明

`--data` 和 `--data-file` 接收的都是原始 ECharts 数据片段。CLI 会把这份数据与生成出的基础 option 和样式配置合并后再渲染。

常见顶层字段：

- `series`：系列数组。
- `xAxis`：x 轴配置或 x 轴数组。
- `yAxis`：y 轴配置或 y 轴数组。
- `dataset`：可选的 ECharts dataset。
- `radar`：雷达图 indicator 配置。
- 其他数据层需要的 ECharts option 片段。

常见数据结构：

折线图、柱状图、面积图：

```json
{
  "xAxis": { "data": ["Mon", "Tue", "Wed"] },
  "yAxis": {},
  "series": [
    { "type": "line", "name": "Visits", "data": [120, 132, 101] }
  ]
}
```

散点图：

```json
{
  "xAxis": { "type": "value" },
  "yAxis": { "type": "value" },
  "series": [
    { "type": "scatter", "name": "North", "data": [[10, 18], [14, 22], [18, 28]] }
  ]
}
```

饼图：

```json
{
  "series": [
    {
      "type": "pie",
      "data": [
        { "name": "A", "value": 40 },
        { "name": "B", "value": 60 }
      ]
    }
  ]
}
```

仪表盘：

```json
{
  "series": [
    {
      "type": "gauge",
      "data": [
        { "name": "Completion", "value": 68 }
      ]
    }
  ]
}
```

双轴图：

```json
{
  "xAxis": { "data": ["Mon", "Tue", "Wed"] },
  "yAxis": [{ "name": "Volume" }, { "name": "Rate" }],
  "series": [
    { "name": "Sales", "yAxisIndex": 0, "data": [320, 332, 301] },
    { "name": "Rate", "yAxisIndex": 1, "data": [10, 12, 9] }
  ]
}
```

雷达图：

```json
{
  "radar": {
    "indicator": [
      { "name": "Quality", "max": 100 },
      { "name": "Speed", "max": 100 }
    ]
  },
  "series": [
    {
      "type": "radar",
      "data": [
        { "name": "Team A", "value": [90, 82] }
      ]
    }
  ]
}
```

漏斗图：

```json
{
  "series": [
    {
      "type": "funnel",
      "data": [
        { "name": "Visit", "value": 100 },
        { "name": "Signup", "value": 60 },
        { "name": "Pay", "value": 20 }
      ]
    }
  ]
}
```

也支持 dataset 模式，例如：

```json
{
  "dataset": {
    "source": [
      ["day", "visits", "orders"],
      ["Mon", 120, 32],
      ["Tue", 132, 41]
    ]
  },
  "xAxis": { "type": "category" },
  "yAxis": { "type": "value" },
  "series": [
    { "type": "line", "name": "Visits", "encode": { "x": "day", "y": "visits" } },
    { "type": "line", "name": "Orders", "encode": { "x": "day", "y": "orders" } }
  ]
}
```

### Config 字段说明

`--config` 和 `--config-file` 接收完整 helper config 对象：

```json
{
  "chartType": "line",
  "common": {},
  "specific": {}
}
```

约束：

- `chartType` 可选，但如果传了，必须与 `--chart-type` 一致。
- `common` 必填。
- `specific` 必填。
- CLI 将 `config` 视为完整载荷，不会再和默认配置做补丁合并。

### `common`

`common` 结构如下：

```json
{
  "title": {
    "main": {
      "show": true,
      "align": "left",
      "fontSize": 18,
      "color": "#111827",
      "bold": true
    },
    "subtitle": {
      "show": false,
      "fontSize": 12,
      "color": "#6b7280"
    }
  },
  "canvas": {
    "backgroundColor": "#ffffff",
    "palette": ["#5470c6", "#91cc75"],
    "plotArea": {
      "left": "6%",
      "right": "6%",
      "top": "12%",
      "bottom": "6%"
    }
  },
  "legend": {
    "show": true,
    "position": "top-right",
    "orient": "horizontal",
    "fontSize": 12,
    "color": "#374151"
  },
  "axes": {
    "x": {
      "lineShow": true,
      "tickShow": true,
      "rotate": 0,
      "labelFontSize": 12,
      "labelColor": "#374151",
      "lineColor": "#9ca3af",
      "formatter": "{value}"
    },
    "y": {
      "lineShow": true,
      "tickShow": true,
      "scale": false,
      "labelFontSize": 12,
      "labelColor": "#374151",
      "lineColor": "#9ca3af",
      "formatter": "{value}"
    }
  },
  "splitLines": {
    "horizontal": {
      "show": true,
      "color": "#e5e7eb",
      "type": "dashed",
      "width": 1
    },
    "vertical": {
      "show": false,
      "color": "#e5e7eb",
      "type": "dashed",
      "width": 1
    }
  }
}
```

标题文案不属于 `config.common.title`，应放在 `data.title.text` 和 `data.title.subtext` 中。

`common.title.main`：

- `show`
- `text`
- `align`
- `fontSize`
- `color`
- `bold`

`common.title.subtitle`：

- `show`
- `text`
- `fontSize`
- `color`

`common.canvas`：

- `backgroundColor`
- `palette`：颜色数组
- `plotArea.left`
- `plotArea.right`
- `plotArea.top`
- `plotArea.bottom`

`common.legend`：

- `show`
- `position`：`top-left`、`top-center`、`top-right`、`middle-left`、`middle-right`、`bottom-left`、`bottom-center`、`bottom-right`
- `orient`：`horizontal` 或 `vertical`
- `fontSize`
- `color`

`common.axes.x` 和 `common.axes.y`：

- `lineShow`
- `tickShow`
- `scale`：仅 y 轴使用，默认 `false`
- `rotate`：仅 x 轴使用
- `labelFontSize`
- `labelColor`
- `lineColor`
- `formatter`

`common.splitLines.horizontal` 和 `common.splitLines.vertical`：

- `show`
- `color`
- `type`：`solid`、`dashed`、`dotted`
- `width`

### `specific`

`specific` 的字段依赖 `--chart-type`。

`line`：

- `line.smooth`
- `line.showSymbol`
- `line.connectNulls`
- `line.symbol`
- `line.symbolSize`
- `line.lineStyleType`
- `line.lineWidth`
- `dataLabels.show`
- `dataLabels.fontSize`
- `dataLabels.color`

`bar`：

- `bar.barGap`
- `bar.itemOpacity`
- `bar.borderRadius`
- `bar.borderWidth`
- `bar.borderColor`
- `dataLabels.show`
- `dataLabels.position`
- `dataLabels.fontSize`
- `dataLabels.color`

`area`：

- `area.smooth`
- `area.showSymbol`
- `area.symbol`
- `area.symbolSize`
- `area.connectNulls`
- `area.areaOpacity`
- `area.areaFillMode`
- `area.lineStyleType`
- `area.lineWidth`
- `dataLabels.show`
- `dataLabels.fontSize`
- `dataLabels.color`

`scatter`：

- `point.symbol`
- `point.symbolSize`
- `point.itemOpacity`
- `point.borderWidth`
- `point.borderColor`
- `dataLabels.show`
- `dataLabels.formatter`
- `dataLabels.fontSize`
- `dataLabels.color`

`pie`：

- `labelPosition`
- `startAngle`
- `showLabel`
- `labelFontSize`
- `labelColor`
- `labelFormatter`
- `labelLineShow`
- `labelLineColor`
- `labelLineWidth`
- `itemOpacity`
- `borderWidth`
- `borderColor`

`dualAxis`：

- `leftAxis.labelFontSize`
- `leftAxis.labelColor`
- `leftAxis.lineShow`
- `leftAxis.lineColor`
- `leftAxis.tickShow`
- `leftAxis.formatter`
- `rightAxis.labelFontSize`
- `rightAxis.labelColor`
- `rightAxis.lineShow`
- `rightAxis.lineColor`
- `rightAxis.tickShow`
- `rightAxis.formatter`
- `leftBar.showLabel`
- `leftBar.labelPosition`
- `leftBar.labelFontSize`
- `leftBar.labelColor`
- `leftBar.opacity`
- `leftBar.barGap`
- `leftBar.borderRadius`
- `leftBar.borderWidth`
- `leftBar.borderColor`
- `leftBar.colors`
- `rightBar.showLabel`
- `rightBar.labelPosition`
- `rightBar.labelFontSize`
- `rightBar.labelColor`
- `rightBar.opacity`
- `rightBar.barGap`
- `rightBar.borderRadius`
- `rightBar.borderWidth`
- `rightBar.borderColor`
- `rightBar.colors`
- `leftLine.smooth`
- `leftLine.area`
- `leftLine.showSymbol`
- `leftLine.connectNulls`
- `leftLine.showLabel`
- `leftLine.colors`
- `leftLine.lineStyleType`
- `leftLine.lineWidth`
- `leftLine.symbol`
- `leftLine.symbolSize`
- `leftLine.labelFontSize`
- `leftLine.labelColor`
- `rightLine.smooth`
- `rightLine.area`
- `rightLine.showSymbol`
- `rightLine.connectNulls`
- `rightLine.showLabel`
- `rightLine.colors`
- `rightLine.lineStyleType`
- `rightLine.lineWidth`
- `rightLine.symbol`
- `rightLine.symbolSize`
- `rightLine.labelFontSize`
- `rightLine.labelColor`

`gauge`：

- `startAngle`
- `endAngle`
- `progressShow`
- `progressWidth`
- `progressColor`
- `axisWidth`
- `bandStops`
- `titleShow`
- `titleFontSize`
- `titleColor`
- `detailShow`
- `detailFormatter`
- `detailFontSize`
- `detailColor`
- `axisLabelShow`
- `axisLabelDistance`
- `axisLabelFontSize`
- `axisLabelColor`
- `splitLineShow`
- `splitLineLength`
- `splitLineWidth`
- `splitLineColor`
- `axisTickShow`
- `axisTickLength`
- `axisTickWidth`
- `axisTickColor`
- `pointerShow`
- `pointerWidth`
- `pointerColor`
- `anchorShow`
- `anchorSize`
- `anchorColor`

`radar`：

- `shape`
- `splitNumber`
- `showSymbol`
- `showLabel`
- `labelFormatter`
- `areaOpacity`
- `splitLineColor`
- `splitLineWidth`
- `splitLineType`
- `axisLineColor`
- `axisLineWidth`
- `axisLineType`
- `axisNameFontSize`
- `axisNameColor`
- `axisNameBold`
- `symbol`
- `symbolSize`
- `lineStyleType`
- `lineWidth`
- `labelFontSize`
- `labelColor`

`funnel`：

- `sort`
- `gap`
- `minSize`
- `maxSize`
- `itemOpacity`
- `labelPosition`
- `showLabel`
- `labelFormatter`
- `labelFontSize`
- `labelColor`

### Variant 完整说明

`--variant` 是可选参数，只支持内联 JSON。

它用于一次性渲染策略，不属于持久化 helper config 的一部分。适合临时预览策略，不适合替代正式配置文件。

结构示例：

```json
{
  "stack": true,
  "layout": "horizontal",
  "pieMode": "donut",
  "leftSeriesType": "bar",
  "rightSeriesType": "line"
}
```

支持字段：

- `stack`：布尔值
- `layout`：`horizontal` 或 `vertical`
- `pieMode`：`pie`、`donut`、`roseArea`、`roseRadius`
- `leftSeriesType`：通常为 `bar` 或 `line`
- `rightSeriesType`：通常为 `bar` 或 `line`

按图表类型的生效范围：

- `line`：支持 `stack`
- `bar`：支持 `stack` 和 `layout`
- `area`：支持 `stack`
- `pie`：支持 `pieMode`
- `dualAxis`：支持 `layout`、`leftSeriesType` 和 `rightSeriesType`
- `gauge`、`scatter`、`radar`、`funnel`：当前没有消费任何 variant 字段

优先级说明：

- `variant` 不会替代 `config`
- `variant` 只影响一次性的临时渲染策略
- 对 `dualAxis` 来说，`variant.layout`、`variant.leftSeriesType` 和 `variant.rightSeriesType` 会覆盖本次渲染使用的双轴基础策略，但不会回写持久化配置
- 对 `dualAxis` 来说，水平分割线显示轴仍来自持久化 `config.common.splitLines.horizontal.display`，只支持 `left`、`right`；如需隐藏，使用 `config.common.splitLines.horizontal.show = false`，不通过 `variant` 传递
- 对柱状布局和堆叠预览来说，`variant` 只在本次渲染生效，不会回写到 helper config

## 输出规则

- 如果 `--out` 是以 `.png` 或 `.svg` 结尾的文件路径，则直接写到该文件。
- 如果 `--out` 是目录路径，则在目录下生成带时间戳的 PNG 文件。
- 如果不传 `--out`，则默认输出到系统临时目录。

## 示例

使用数据文件和配置文件渲染：

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type line \
  --data-file ./data/line.json \
  --config-file ./config/line_style.json \
  --out ./output/line.png
```

使用内联 JSON 渲染：

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type pie \
  --data '{"series":[{"type":"pie","data":[{"name":"A","value":40},{"name":"B","value":60}]}]}' \
  --config '{"common":{"title":{"main":{"show":true,"text":"Pie Demo","align":"center","fontSize":18,"color":"#111827","bold":true},"subtitle":{"show":false,"text":"","fontSize":12,"color":"#6b7280"}},"canvas":{"backgroundColor":"#ffffff","palette":["#5470c6","#91cc75"],"plotArea":{"left":"6%","right":"6%","top":"12%","bottom":"6%"}},"legend":{"show":true,"position":"bottom-center","orient":"horizontal","fontSize":12,"color":"#374151"},"axes":{"x":{},"y":{}},"splitLines":{"horizontal":{},"vertical":{}}},"specific":{"labelPosition":"outside","startAngle":90,"showLabel":true,"labelFontSize":11,"labelColor":"#334155","labelFormatter":"{b} {d}%","labelLineShow":true,"labelLineColor":"#94a3b8","labelLineWidth":1,"itemOpacity":0.96,"borderWidth":0,"borderColor":"#ffffff"}}' \
  --out ./output/pie.svg
```

带一次性 variant 的渲染：

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type bar \
  --data-file ./data/bar.json \
  --config-file ./config/bar_style.json \
  --variant '{"layout":"horizontal","stack":true}' \
  --out ./output/
```

双轴图临时指定左右系列类型：

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type dualAxis \
  --data-file ./data/dual-axis.json \
  --config-file ./config/dual_axis_style.json \
  --variant '{"leftSeriesType":"bar","rightSeriesType":"line"}' \
  --out ./output/dual-axis.png
```
