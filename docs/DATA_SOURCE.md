# 数据源说明：获取方式、接口调用流程与数据格式解析

> 本文所有接口均在 **2026-11-16** 于本机实测通过，返回片段为真实响应。
> 实现代码：`resources/lib/nmc.py`、`resources/lib/weathercn.py`、`resources/lib/citydb.py`。

---

## 1. 数据源选型

| | 中央气象台 nmc.cn（**主源**） | 中国天气网 weather.com.cn（**备用/补充源**） |
|---|---|---|
| 主管单位 | 中国气象局 / 国家气象中心 | 中国气象局公共气象服务中心 |
| 鉴权 | 无，公开 HTTP | 无，公开 HTTP（`d1` 域需 `Referer`） |
| 编码 | `application/json;charset=UTF-8` | `text/html; charset=utf-8` |
| 实况 | ✔ 温度/湿度/气压/风/体感/日出日落 | ✔ 另有 AQI、PM2.5、能见度、限行、生活指数 |
| 预报 | ✔ 7 天（白天/夜间分列） | ✔ 5 天（JS 变量）+ 7 天（HTML 页） |
| 预警 | ✔ 本地 `real.warn` + 全国 `findAlarm` 列表 | ✔ 城市级 `alarmDZ.w[]`（含**类型名/等级名/全文**） |
| 城市目录 | ✔ `/rest/province` 两级，2529 站点 | ✔ `/textFC` 各省页，3230 个 9 位码 |
| 稳定性 | 高，结构化 JSON | 中，返回 JS/HTML 需解析 |

**为什么不用商业天气 API**：和风天气、彩云天气等均需要注册 Key、有配额与商用限制；本项目要求「开箱即用、无 Key」，且必须拿到**中国气象预警的类型与等级**，只有国家级公开源完整提供，因此选定上述两家。Open-Meteo 等国际源没有中国预警信号体系，仅可作为未来可选的补充（见 ROADMAP）。

---

## 2. 获取方式（通用约定）

1. **无需注册、无需 Token/Cookie、无需 API Key**；直接 HTTP GET 即可。
2. 请求头建议：
   ```
   User-Agent: Mozilla/5.0 (...) Chrome/120.0 Safari/537.36
   Accept: */*
   Accept-Language: zh-CN,zh;q=0.9
   Referer: http://www.weather.com.cn/      # 访问 d1.weather.com.cn 时必须
   ```
   不带 `Referer` 时 `d1.weather.com.cn` 会返回「非常抱歉，网页无法访问」错误页。
3. 协议以 `http://` 为主（实测最稳定）；`www.weather.com.cn` 的旧 `/data/*` 接口会 301，本项目改用 `https://www.weather.com.cn/data/city3jdata/china.html` 获取省码表。
4. 所有响应体按 **UTF-8** 解码（`decode("utf-8", "replace")`），个别页面 `<meta charset=gb2312>` 但实体已是 UTF-8。
5. 数据版权归原发布单位；本项目仅做个人用途的展示与缓存，不转售、不高频抓取，插件内置文件缓存与并发限制。

---

## 3. 中央气象台 nmc.cn 接口链

| # | 接口 | 参数 | 返回 | 插件用途 |
|---|---|---|---|---|
| 1 | `GET /rest/province` | 无 | 34 个省级行政区数组 | 建城市索引 |
| 2 | `GET /rest/province/{provCode}` | `ABJ` 等 | 省内站点数组 | 中文城市搜索的站点清单 |
| 3 | `GET /rest/weather?stationid={stationCode}` | 如 `Wqsps`（北京） | `real` + `predict` + `air` 等 | **实时天气 + 7 天预报 + 本地预警** |
| 4 | `GET /rest/findAlarm?pageNo=1&pageSize=30` | 分页 | `page.list` + `provinceAlarms` | **全国预警列表** |
| 5 | `GET /publish/alarm/{alertid}.html` | `alertid` | HTML 详情 | 可选用 `url` 在浏览器打开 |

### 3.1 城市目录

```jsonc
// GET /rest/province
[{"code":"ABJ","name":"北京市","url":"/publish/forecast/ABJ.html"}, ...]

// GET /rest/province/ABJ
[{"code":"Wqsps","province":"北京市","city":"北京",
  "url":"/publish/forecast/ABJ/beijing.html"},
 {"code":"niStC","province":"北京市","city":"昌平", ...}, ...]
```

> 注意：站点 `code` 是 5 位大小写混合随机串，**不是**传统气象站号（54511）。实测 `stationid=54511` 返回 `data:""`（空），必须用 `/rest/province/{code}` 给出的 `code`。这是最容易踩的坑。

### 3.2 `/rest/weather` 返回结构（真实）

```jsonc
{
  "msg": "success", "code": 0,
  "data": {
    "real": {
      "station": {"code":"Wqsps","province":"北京市","city":"北京","url":"..."},
      "publish_time": "2026-11-16 16:30",
      "weather": {"temperature":7.8,"temperatureDiff":9999.0,
                  "airpressure":9999.0,"humidity":44.0,"rain":0.0,
                  "rcomfort":45,"icomfort":-2,"info":"-","img":"9999","feelst":5.2},
      "wind": {"direct":"西南风","degree":188.0,"power":"微风","speed":1.9},
      "warn": {"alert":"9999","pic":"9999","province":"9999","city":"9999",
               "url":"9999","issuecontent":"9999","issuetime":"",
               "fmeans":"9999","signaltype":"9999","signallevel":"9999","pic2":"9999"},
      "sunriseSunset": {"sunrise":"2026-11-16 06:59","sunset":"2026-11-16 16:57"}
    },
    "predict": {
      "publish_time": "2026-11-16 20:00",
      "detail": [
        {"date":"2026-11-16","pt":"2026-11-16 20:00",
         "day":  {"weather":{"info":"9999","img":"9999","temperature":"9999"},
                  "wind":{"direct":"9999","power":"9999"}},
         "night":{"weather":{"info":"阴","img":"2","temperature":"1"},
                  "wind":{"direct":"北风","power":"微风"}},
         "precipitation":0.3},
        {"date":"2026-11-17",
         "day":  {"weather":{"info":"小雨","img":"7","temperature":"8"}, ...},
         "night":{"weather":{"info":"多云","img":"1","temperature":"1"}, ...}},
        ... 共 7 天
      ]
    },
    "air": {...}, "tempchart": {...}, "passedchart": {...},
    "climate": {...}, "radar": {...}
  }
}
```

**字段解析要点**

| 字段 | 含义 | 处理 |
|---|---|---|
| `weather.temperature` / `feelst` / `humidity` / `rain` | 实况数值 | `num()` 转 float/int |
| `airpressure` / `temperatureDiff` | 常为 `9999.0` | 哨兵值 → `None` |
| `weather.info` | 实况天气现象，常为 `"-"` | 空时用 `predict.detail[0]` 的白天/夜间 `info` 兜底 |
| `weather.img` | 天气现象代码（0 晴 / 2 阴 / 7 小雨…） | 查 `conditions.json` |
| `predict.detail[i].day/night.weather.temperature` | 白天最高 / 夜间最低（字符串） | `num()`；第 0 天白天常为 `9999` → 高温 `None`，由中国天气网补齐 |
| `predict.detail[i].precipitation` | 降水量 mm | 直接展示 |
| `real.warn` | 本地生效预警 | `alert=="9999"` 且 `issuecontent=="9999"` 视为无预警 |
| `data.air` | 空气质量（版本间结构不一） | 宽松提取 `aqi/pm25` 等键 |

### 3.3 `/rest/findAlarm` 返回结构

```jsonc
{"msg":"success","code":0,"data":{
  "page":{"pageNo":1,"pageSize":30,"count":648,
          "list":[{"alertid":"14000041600000_20261116164500",
                   "issuetime":"2026/11/16 16:45",
                   "title":"山西省气象台发布大雾黄色预警",
                   "url":"/publish/alarm/14000041600000_20261116164500.html",
                   "pic":"https://image.nmc.cn/assets/img/alarm/p0005003.png"}],
          "totalPage":130},
  "provinceAlarms":[ ... 省级预警 ... ],
  "stat":{...}}}
```

**预警类型与等级解析规则**（实现在 `lib/alerts.py`）

- 标题格式固定为 `〈发布单位〉发布〈灾害类型〉〈颜色〉色?预警[信号]`。
- 等级：正则 `(蓝|黄|橙|红)\s*色?\s*预警` → 蓝/黄/橙/红，rank 分别 0/1/2/3。
- 类型：`发布` 之后、`色预警` 之前的片段，再用常见灾害类型词表（寒潮、大雾、道路结冰、暴雨、暴雪、大风、高温、雷电、冰雹、霜冻、霾、沙尘暴、台风…）做包含匹配。
- `pic` 文件名（如 `p0005003`）里含类型与等级编号，但**不同版本编码会变**，因此只作参考，一律以中文文本为准。
- `issuetime` 中的 `/` 统一替换为 `-`；`url` 用 `urljoin` 补成绝对地址。

---

## 4. 中国天气网 weather.com.cn 接口链

| # | 接口 | 参数 | 返回 | 插件用途 |
|---|---|---|---|---|
| 1 | `GET http://d1.weather.com.cn/weather_index/{9位码}.html` | `101010100` | 5 个 JS 变量 | 实况 + 5 天预报 + 预警 + 生活指数 |
| 2 | `GET http://d1.weather.com.cn/dingzhi/{9位码}.html` | 同上 | `cityDZ{code}` / `alarmDZ{code}` | 更及时的本地预警 |
| 3 | `GET http://www.weather.com.cn/weather/{9位码}.shtml` | 同上 | HTML 页 | 7 天预报（`<ul class="t clearfix">`） |
| 4 | `GET https://www.weather.com.cn/data/city3jdata/china.html` | 无 | 34 条省级 5 位码 | 归一化城市省份 |
| 5 | `GET http://www.weather.com.cn/textFC/{省}.shtml` | 如 `hebei` | HTML 表格 | 生成 9 位城市码索引 |

### 4.1 `weather_index` 的 JS 变量

响应不是 JSON，而是：

```javascript
var cityDZ ={"weatherinfo":{...}};var alarmDZ ={"w":[]};
var dataSK ={"nameen":"beijing","cityname":"北京","city":"101010100",
             "temp":"7.7","WD":"南风","WS":"2级","wse":"8km/h","SD":"44%",
             "qy":"1021","njd":"19km","time":"16:40","rain":"0","aqi":"30",
             "aqi_pm25":"30","weather":"阴","weathercode":"d02",
             "date":"11月16日(星期一)"};
var dataZS ={"zs":{"ct_name":"穿衣指数","ct_hint":"冷","ct_des_s":"建议着棉衣...", ...},"cn":"北京"};
var fc ={"f":[{"fa":"02","fb":"02","fc":"9","fd":"2","fe":"东北风","ff":"北风",
               "fg":"<3级","fh":"<3级","fi":"11/16","fj":"今天"}, ... 共 5 天]};
```

**解析方式**：`lib/weathercn.py::parse_js_vars()` 用「括号平衡扫描」从每个 `var NAME =` 后截取完整 `{...}` / `[...]`（正确处理字符串内的括号与转义），再 `json.loads`。比按 `;var ` 硬切分更稳健。

| 变量 | 关键字段 | 说明 |
|---|---|---|
| `dataSK` | `temp/tempf`、`WD/wde`、`WS/wse`、`SD/sd`、`qy`、`njd`、`rain/rain24h`、`aqi/aqi_pm25`、`weather/weathere/weathercode`、`time/date` | 实况；字符串数字需 `num()`，带 `%`/`km` 需去单位 |
| `fc.f[]` | `fa/fb` 白天/夜间现象码、`fc/fd` 高/低温、`fe/ff` 风向、`fg/fh` 风力、`fi` 日期 `M/D`、`fj` 星期 | 5 天预报；`fi` 无年份，用当前年份推断（跨年 +1） |
| `cityDZ.weatherinfo` | `temp/tempn/weather/wd/ws/weathercode/fctime` | 当天订制概况，作实况兜底 |
| `dataZS.zs` | 成组的 `xx_name` / `xx_hint` / `xx_des_s` | 30 项生活指数 |
| `alarmDZ.w[]` | 见下 | 城市级预警 |

天气现象码（`fa/fb/weathercode/img`）**nmc 与中国天气网共用同一套 0~53 标准码**，插件统一在 `resources/data/conditions.json` 映射为 `sunny / overcast / light_rain / …` 与本地图标。`"d02"`、`"02"`、`2` 会先 `int()` 归一化。

### 4.2 `alarmDZ.w[]` 预警字段（真实样本：太原 101100101）

```jsonc
{"w":[{"w1":"山西省","w2":"","w3":"","w4":"04","w5":"寒潮","w6":"01",
       "w7":"蓝色","w8":"2026-11-16 10:52",
       "w9":"山西省气象台2026年11月16日10时52分发布寒潮蓝色预警，预警区域：...（预警信息来源：国家预警信息发布中心）",
       "w10":"202611161052537722寒潮蓝色","w11":"10110-20261116105..."}]}
```

| 字段 | 含义 |
|---|---|
| `w1` | 发布单位 / 区域 |
| `w4` | 类型编码（辅助，不依赖） |
| `w5` | **预警类型中文名**（寒潮、暴雨、大雾…） |
| `w6` | **等级码**：`01` 蓝 / `02` 黄 / `03` 橙 / `04` 红 |
| `w7` | **等级中文名**（蓝色/黄色/橙色/红色） |
| `w8` | 发布时间 |
| `w9` | **预警全文**（含防御指南与信息来源） |
| `w10/w11` | 业务唯一编号（用于去重） |

### 4.3 7 天预报 HTML

```html
<ul class="t clearfix">
  <li class="sky skyid lv3 on">
    <h1>16日（今天）</h1>
    <big class="png40 d02"></big><big class="png40 n02"></big>
    <p title="阴" class="wea">阴</p>
    <p class="tem"><span>9</span>/<i>2℃</i></p>
    <p class="win"><em><span title="东北风" class="NE"></span>...</em><i>&lt;3级</i></p>
  </li> ... 共 7 个 li
</ul>
```

`parse_7day()` 用 `<ul class="t clearfix">…</ul>` 定位块、`<li>…</li>` 切天，正则取 `h1` 日期、`wea` 现象、`tem` 高低温、`win` 风向风力、`big` 的 `dNN/nNN` 现象码。页面只给「16日（今天）」，日期按 `today + index` 还原，避免跨年歧义。

### 4.4 城市索引生成

`tools/build_city_db.py`（开发期运行一次）：

```
/data/city3jdata/china.html  ──> 34 条 5 位省级码表（用于把 9 位码前 5 位映射成真实省份）
/textFC/hb.shtml             ──> 41 个省/区域页链接
/textFC/{省}.shtml           ──> <a href=".../weather/{9位码}.shtml">城市名</a>
/rest/province               ──> 34 省
/rest/province/{code}        ──> 各站点
                    ↓
resources/data/cities_nmc.json        (2529 站点)
resources/data/cities_weathercn.json (3230 城市码，省份按 5 位省级码归一化)
```

运行时**完全离线**用这两份索引做中文搜索；插件菜单「刷新城市索引」可在线重建 `cities_nmc.json` 到用户配置目录。

---

## 5. 插件内部接口调用流程

```
                    ┌──────────────────────────────┐
  Kodi 菜单 / 服务 ─▶│ WeatherService.fetch_all()    │
                    └──────────────┬───────────────┘
                                   │ 读 settings：city_name / nmc_code / wcn_code
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  Fetcher(缓存/重试)        NMCSource.weather()        WCNSource.index()
  sha1(URL) 文件缓存        /rest/weather              /weather_index/{code}.html
  TTL 10min / 24h stale     ↓ real + predict[7]        ↓ dataSK + fc[5] + dataZS + alarmDZ
        │                    │                          │
        │                    └──────────┬───────────────┘
        │                               ▼
        │                    失败自动降级 / 双源字段补缺 merge()
        │                               │
        │              ┌────────────────┼─────────────────┐
        │              ▼                ▼                 ▼
        │      seven_day() 7天页   dingzhi() 预警   findAlarm() 全国预警
        │              │                │                 │
        │              └────────────────┼─────────────────┘
        │                               ▼
        │                    alerts.prepare() 去重/排序/等级过滤
        │                               ▼
        └──────────────▶ 标准结果 dict ─▶ ui.py 菜单 / windowprops.py 皮肤属性
```

每次抓取经 `lib/net.py::Fetcher`：URL → sha1 缓存键 → TTL 命中直接返回；未命中则最多 3 次请求（2 次重试、0.5s/1.0s 退避、默认 10s 超时）；失败时返回 24 小时内过期缓存并标 `stale`；彻底失败返回 `None`，由聚合层降级。

---

## 6. 合规与稳定性说明

- 这些是**公开 Web 接口**，非承诺 SLA 的开放 API；对方改版可能导致字段变化。插件的双源降级、文本优先解析、离线缓存与内置城市索引就是为了把改版影响降到最低。
- 插件默认缓存 10 分钟、城市索引 1 小时/1 天、7 天页 30 分钟，避免高频请求。
- 不采集、不上传任何用户信息；日志仅记录接口 URL、缓存命中与错误信息。
- 预警与防灾决策请以中央气象台及当地气象部门正式发布为准。
