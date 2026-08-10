# @areslabs/data-charts-visualization

CLI for rendering ECharts charts to PNG or SVG in a Node.js environment.

## Install

Use the published package directly:

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 --help
```

After installation, the exposed bin is:

```bash
areslabs-data-charts
```

## Usage

```bash
areslabs-data-charts --chart-type <type> (--data <json> | --data-file <file>) (--config <json> | --config-file <file>) [--variant <json>] [--width <px>] [--height <px>] [--out <dir|file>]
```

Supported chart types:

```text
line, bar, pie, gauge, area, dualAxis, scatter, radar, funnel
```

## Parameters

- `--chart-type`: chart type.
- `--data`: raw chart data as inline JSON.
- `--data-file`: raw chart data file path.
- `--config`: complete helper config as inline JSON.
- `--config-file`: complete helper config file path.
- `--variant`: one-off render strategy as inline JSON.
- `--width`: output width in pixels. Default: `650`.
- `--height`: output height in pixels. Default: `360`.
- `--out`: output directory or output file path. Default: system temp directory under `areslabs-data-charts`.

Rules:

- One of `--data` or `--data-file` is required.
- One of `--config` or `--config-file` is required.
- `--data` and `--data-file` are mutually exclusive.
- `--config` and `--config-file` are mutually exclusive.
- `--variant` only accepts inline JSON.
- `--config` must be a complete helper config object with both `common` and `specific`.

## Payloads

The CLI input is made of three payloads:

- `data`: raw ECharts data fragment.
- `config`: complete helper config payload.
- `variant`: one-off render strategy payload.

`data` and `config` are required. `variant` is optional.

### Data Payload

`--data` and `--data-file` both accept a raw ECharts data fragment. The CLI merges this payload with the generated base option and style config.

Common top-level keys:

- `series`: chart series array.
- `xAxis`: x-axis config or x-axis array.
- `yAxis`: y-axis config or y-axis array.
- `dataset`: optional ECharts dataset.
- `radar`: radar indicator config.
- Any other ECharts option fragment needed by the chart data layer.

Typical shapes:

Line, bar, area:

```json
{
  "xAxis": { "data": ["Mon", "Tue", "Wed"] },
  "yAxis": {},
  "series": [
    { "type": "line", "name": "Visits", "data": [120, 132, 101] }
  ]
}
```

Scatter:

```json
{
  "xAxis": { "type": "value" },
  "yAxis": { "type": "value" },
  "series": [
    { "type": "scatter", "name": "North", "data": [[10, 18], [14, 22], [18, 28]] }
  ]
}
```

Pie:

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

Gauge:

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

Dual-axis:

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

Radar:

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

Funnel:

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

Dataset mode is also supported. Example:

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

### Config Payload

`--config` and `--config-file` accept a complete helper config object:

```json
{
  "chartType": "line",
  "common": {},
  "specific": {}
}
```

Rules:

- `chartType` is optional, but if present it must match `--chart-type`.
- `common` is required.
- `specific` is required.
- The CLI treats `config` as a full payload, not as a patch over defaults.

### `common`

`common` uses this structure:

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

Title copy does not belong in `config.common.title`. Put it in `data.title.text` and `data.title.subtext` instead.

`common.title.main`:

- `show`
- `text`
- `align`
- `fontSize`
- `color`
- `bold`

`common.title.subtitle`:

- `show`
- `text`
- `fontSize`
- `color`

`common.canvas`:

- `backgroundColor`
- `palette`: array of colors
- `plotArea.left`
- `plotArea.right`
- `plotArea.top`
- `plotArea.bottom`

`common.legend`:

- `show`
- `position`: `top-left`, `top-center`, `top-right`, `middle-left`, `middle-right`, `bottom-left`, `bottom-center`, `bottom-right`
- `orient`: `horizontal` or `vertical`
- `fontSize`
- `color`

`common.axes.x` and `common.axes.y`:

- `lineShow`
- `tickShow`
- `scale`: y-axis only, default `false`
- `rotate`: x-axis only
- `labelFontSize`
- `labelColor`
- `lineColor`
- `formatter`

`common.splitLines.horizontal` and `common.splitLines.vertical`:

- `show`
- `color`
- `type`: `solid`, `dashed`, `dotted`
- `width`

### `specific`

`specific` depends on `--chart-type`.

`line`:

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

`bar`:

- `bar.barGap`
- `bar.itemOpacity`
- `bar.borderRadius`
- `bar.borderWidth`
- `bar.borderColor`
- `dataLabels.show`
- `dataLabels.position`
- `dataLabels.fontSize`
- `dataLabels.color`

`area`:

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

`scatter`:

- `point.symbol`
- `point.symbolSize`
- `point.itemOpacity`
- `point.borderWidth`
- `point.borderColor`
- `dataLabels.show`
- `dataLabels.formatter`
- `dataLabels.fontSize`
- `dataLabels.color`

`pie`:

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

`dualAxis`:

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

`gauge`:

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

`radar`:

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

`funnel`:

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

### Variant Payload

`--variant` is optional and only accepts inline JSON.

It is used for one-off render strategy and is not part of persisted helper config. `variant` is applied at render time and should be used for temporary preview behavior instead of editing the saved config payload.

Structure:

```json
{
  "stack": true,
  "layout": "horizontal",
  "pieMode": "donut",
  "leftSeriesType": "bar",
  "rightSeriesType": "line"
}
```

Supported fields:

- `stack`: boolean
- `layout`: `horizontal` or `vertical`
- `pieMode`: `pie`, `donut`, `roseArea`, `roseRadius`
- `leftSeriesType`: usually `bar` or `line`
- `rightSeriesType`: usually `bar` or `line`

Behavior by chart type:

- `line`: supports `stack`.
- `bar`: supports `stack` and `layout`.
- `area`: supports `stack`.
- `pie`: supports `pieMode`.
- `dualAxis`: supports `layout`, `leftSeriesType`, and `rightSeriesType`.
- `gauge`, `scatter`, `radar`, `funnel`: no current variant fields are consumed.

Precedence:

- `variant` does not replace `config`.
- `variant` only affects temporary render strategy fields.
- For `dualAxis`, `layout`, `leftSeriesType`, and `rightSeriesType` in `variant` override the base dual-axis render strategy for this render only.
- For `dualAxis`, horizontal split-line side stays in persisted `config.common.splitLines.horizontal.display`; supported values are `left` and `right`. Use `config.common.splitLines.horizontal.show = false` to hide them.
- For bar layout and stack preview behavior, `variant` is applied at render time and does not mutate the saved helper config.

## Output

- If `--out` is a file path ending in `.png` or `.svg`, the CLI writes to that file.
- If `--out` is a directory path, the CLI writes a timestamped PNG into that directory.
- If `--out` is omitted, the CLI writes a timestamped PNG into the system temp directory.

## Examples

Render from JSON files:

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type line \
  --data-file ./data/line.json \
  --config-file ./config/line_style.json \
  --out ./output/line.png
```

Render from inline JSON:

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type pie \
  --data '{"series":[{"type":"pie","data":[{"name":"A","value":40},{"name":"B","value":60}]}]}' \
  --config '{"common":{"title":{"main":{"show":true,"text":"Pie Demo","align":"center","fontSize":18,"color":"#111827","bold":true},"subtitle":{"show":false,"text":"","fontSize":12,"color":"#6b7280"}},"canvas":{"backgroundColor":"#ffffff","palette":["#5470c6","#91cc75"],"plotArea":{"left":"6%","right":"6%","top":"12%","bottom":"6%"}},"legend":{"show":true,"position":"bottom-center","orient":"horizontal","fontSize":12,"color":"#374151"},"axes":{"x":{},"y":{}},"splitLines":{"horizontal":{},"vertical":{}}},"specific":{"labelPosition":"outside","startAngle":90,"showLabel":true,"labelFontSize":11,"labelColor":"#334155","labelFormatter":"{b} {d}%","labelLineShow":true,"labelLineColor":"#94a3b8","labelLineWidth":1,"itemOpacity":0.96,"borderWidth":0,"borderColor":"#ffffff"}}' \
  --out ./output/pie.svg
```

Render with one-off variant:

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type bar \
  --data-file ./data/bar.json \
  --config-file ./config/bar_style.json \
  --variant '{"layout":"horizontal","stack":true}' \
  --out ./output/
```

Dual-axis type override:

```bash
npx -y @areslabs/data-charts-visualization@1.0.1 \
  --chart-type dualAxis \
  --data-file ./data/dual-axis.json \
  --config-file ./config/dual_axis_style.json \
  --variant '{"leftSeriesType":"bar","rightSeriesType":"line"}' \
  --out ./output/dual-axis.png
```
