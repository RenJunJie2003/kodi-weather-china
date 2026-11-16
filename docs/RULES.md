# 输出与处理规则约定

> 本文件是插件的「数据契约」。所有解析模块（`nmc.py` / `weathercn.py`）输出同一结构，
> 聚合层（`weather.py`）按本规则加工，UI 层（`ui.py` / `windowprops.py`）只消费该结构。
> 实现位置：`lib/nmc.py::blank()`、`lib/weather.py::merge()`、`lib/config.py::format_*()`、
> `lib/alerts.py::prepare()`、`lib/net.py::Fetcher`。

---

## 1. 标准输出结构

```jsonc
{
  "ok": true,                         // 是否至少有一个数据源成功
  "source": "mixed",                  // nmc | wcn | mixed | unknown
  "source_list": ["nmc", "wcn"],
  "location": {"name":"北京","nmc_code":"Wqsps","wcn_code":"101010100"},
  "updated": "2026-11-16 16:30",     // 数据源发布时间，原样保留
  "current": {
    "temp": 7.8, "feels_like": 5.2, "humidity": 44, "pressure": null,
    "rain": 0.0, "condition": "阴", "condition_key": "overcast",
    "condition_icon": "/…/resources/media/overcast.png",
    "wind_dir": "西南风", "wind_power": "微风", "wind_speed": 1.9,
    "aqi": 28, "pm25": 30, "visibility": null,
    "sunrise": "06:59", "sunset": "16:57", "time": "16:30"
  },
  "forecast": [
    {"date": "2026-11-16", "high": 9, "low": 1,
     "day":   {"condition":"阴","key":"overcast","icon":"…/overcast.png",
               "wind_dir":"东北风","wind_power":"<3级"},
     "night": {"condition":"阴","key":"overcast","icon":"…/overcast.png",
               "wind_dir":"北风","wind_power":"微风"},
     "precipitation": 0.3}
    /* …按日期升序，最多 7 条… */
  ],
  "alerts": [
    {"id":"…", "title":"山西省气象台发布寒潮蓝色预警", "issuer":"山西省气象台",
     "type":"寒潮", "type_code":"04",
     "level":"蓝色", "level_key":"blue", "level_rank":0, "level_code":"01",
     "level_color":"FF2E7CF6", "level_label_id":32145, "level_en":"Blue",
     "issue_time":"2026-11-16 10:52", "content":"预警全文…",
     "source":"wcn", "url":"http://…", "icon":"…/alert_blue.png"}
  ],
  "indices": [{"name":"穿衣指数","hint":"冷","desc":"建议着棉衣…"}],
  "notes": ["cached"],               // cached | stale | all-sources-failed
  "errors": [],                      // 各数据源失败原因
  "cached": false, "stale": false,
  "fetched_at": 1763289000
}
```

---

## 2. 处理规则（逐条硬性约定）

### R1 编码
- 所有网络响应按 **UTF-8** 解码（`errors="replace"`）；缓存文件、JSON 数据、`strings.po`、`addon.xml`、`settings.xml` 全部 UTF-8 无 BOM。
- 插件 URL 参数用 `urlencode(encoding="utf-8")` 编码、`parse_qs(encoding="utf-8")` 解码，中文城市名在 Kodi 内传递不乱码。
- 任何地方不做 GBK/GB2312 猜测转码（实测目标接口实体已是 UTF-8）。

### R2 缺失值
- 哨兵值集合：`"9999"` / `9999.0` / `"-"` / `"--"` / `""` / `None` / `"null"` → 统一 `None`。
- 界面统一显示 `—`（全角破折号）；`None` 不参与排序、极值、温度换算。
- `real.warn.alert == "9999"` 且 `issuecontent == "9999"` → 判定「无生效预警」。

### R3 数值与单位
- 温度内部**一律摄氏度数值**（int/float）；展示时按设置换算：`°F = °C × 9/5 + 32`，实况保留 1 位小数、整数不带小数点，预报取整数。
- 湿度 `%`、气压 `hPa`、降水 `mm`、风速 `m/s`、能见度 `km` 为展示后缀，内部只存数值。
- 字符串型数字（`"7.7"`）、带单位字符串（`"44%"`、`"8km/h"`）统一经 `num()` / `_percent()` / `_speed()` 清洗。

### R4 时间
- 数据源时间字符串**原样保留**（均为北京时间，不做时区换算）；`/` 统一替换为 `-`。
- 日出日落、发布时间取 `HH:MM` 部分；预报日期统一 `YYYY-MM-DD`，页面里中国天气网只给 `M/D` 时按当前年份推断（跨年 +1）；7 天 HTML 页按 `today + index` 还原。
- 星期由日期计算，经本地化字符串输出（今天/明天/后天/星期一…星期日）。

### R5 天气现象与图标
- 两套数据源共用 0~53 现象码，统一 `int()` 归一化（`d02` / `02` / `2` 等价），查 `conditions.json` 得中文名、英文名、`key` 与图标。
- 代码无效时用中文描述做**关键词最早位置匹配**（"阴转多云" → 阴）；仍失败 → `unknown`。
- 图标一律指向 `resources/media/*.png`，文件缺失自动回退 `unknown.png`。
- 预警等级对应 `alert_blue/yellow/orange/red/unknown.png`。

### R6 缓存
- 缓存键 = `sha1(URL)`，文件位于 Kodi 用户配置目录 `cache/*.json`，内容含 `ts` 与 UTF-8 原文。
- TTL：实况/预报 = 设置「缓存有效期」×60（默认 10 分钟）；全国预警 5 分钟；7 天页 30 分钟；省份/站点目录 24 小时。
- **stale-while-error**：网络失败时允许使用 24 小时内的过期缓存，`stale=True`；超过 24 小时丢弃。
- 「刷新」动作清空缓存并 `force=True` 重新抓取；切换城市也会清缓存。

### R7 网络与重试
- 默认超时 10 秒（可设 1~60），最多 2 次重试，退避 0.5s / 1.0s。
- 所有异常在 `Fetcher` 内吞掉并转成 `FetchResult(error=...)`，**任何情况下不把异常抛到 Kodi UI**。
- 请求头固定带 UA / Accept / Accept-Language；`d1.weather.com.cn` 额外带 `Referer: http://www.weather.com.cn/`。

### R8 数据源选择、合并与降级
- `primary_source = auto | nmc | wcn`；`auto/nmc` 以中央气象台为骨架，`wcn` 以中国天气网为骨架。
- 两源都成功 → 标记 `mixed`，按 **主源优先、字段补缺** 合并：仅当主源字段为 `None`/空/`unknown` 时才用备用源补；预报按 `date` 对齐补 `high/low/condition/wind`。
- 主源失败 → 自动降级到另一源（不受 `enable_wcn` 限制）；两源都失败 → 返回 `ok=False` 的完整空结构 + `errors`，UI 显示「数据获取失败」并引导检查设置/缓存。
- 预报不足设置天数且配置了 9 位码时，追加中国天气网 7 天页补足。
- 最后按 `forecast_days`（3/5/7）裁剪并按日期升序输出。

### R9 预警
- 归一化字段固定：`title / issuer / type / type_code / level / level_key / level_rank / level_code / level_color / issue_time / content / source / url / icon`。
- 等级严格按国家标准四级：蓝(Ⅳ, rank 0) < 黄(Ⅲ, rank 1) < 橙(Ⅱ, rank 2) < 红(Ⅰ, rank 3)；未知 = -1。
- 颜色 ARGB：蓝 `FF2E7CF6`、黄 `FFF5C518`、橙 `FFEE8A17`、红 `FFD93025`、未知 `FF9AA0A6`。
- **类型与等级以中文文本解析为准，编码仅作辅助**（接口编码跨版本会变）。
- 去重键 = `(发布单位, 类型, 等级, 时间, 全文前 40 字)`；排序 = 等级降序 + 发布时间倒序。
- 过滤：`alert_min_level` 0=全部 / 1=黄色及以上 / 2=橙色及以上 / 3=仅红色。
- 条数：全国预警 `national_limit`（默认 30），合并预警上限 `2×national_limit`。
- 预警范围 `local | national | all`：`all` 时额外把标题中包含当前城市/省份关键词的全国预警并入本地列表。
- 预警全文在英文界面下仍为中文（源数据本身为中文），这是预期行为。

### R10 中文城市搜索与切换
- 归一化：去掉「省/市/区/县/自治区/自治州/特别行政区/地区/盟/旗」等后缀再比对。
- 评分：精确 (0) > 前缀 (1) > 包含 (2) > 所在省包含 (3)；同分按名称短、省份字典序。
- 去重键 `(省, 市, 站点码)`，默认最多 50 条；结果展示「城市 · 省份」并同时给出两套编码。
- 选中后写入 `city_name / nmc_code / wcn_code` 三项设置，清缓存、立即刷新并发布皮肤属性。
- 支持热门城市与拼音首字母快捷入口（bj/sh/gz…）；无匹配时提示使用更短关键词。
- 9 位码由「归一化省份 + 归一化城市」在内置索引中匹配，另有 24 个常用城市码兜底表；匹配不到则留空，备用源自动跳过，主源不受影响。

### R11 界面输出
- 所有界面文本经 `ADDON.getLocalizedString(32xxx)`，UI 代码零硬编码中文。
- 数值一律半角；缺失值 `—`；预警等级用 `[COLOR ARGB]…[/COLOR]` 着色。
- 数据来源显示「中央气象台 / 中国天气网 / 中央气象台 + 中国天气网」；缓存时追加「（缓存数据）」，过期缓存追加「（离线缓存，可能已过期）」。
- 详情（预警全文、单日预报、生活指数）用 Kodi 文本查看器展示，展示后重绘当前列表，不使用播放器路径。

### R12 皮肤属性与隐私
- `skin_props=true` 时写 `Weather.*` / `Current.*` / `Day0..Day6.*` / `Weather.Alert1..10.*` 到 Home Window(10000)。
- 后台服务按 `refresh_interval`（默认 15 分钟）刷新，全程异常安全，`Monitor.waitForAbort` 保证 Kodi 退出时立即结束。
- 日志只含接口 URL、缓存命中与错误；不记录任何账号、位置以外的个人信息；插件无账号体系、无 Key、不上传数据。

---

## 3. `notes` / `errors` 取值

| 值 | 含义 | UI 表现 |
|---|---|---|
| `cached` | 命中有效缓存 | 标题追加「（缓存数据）」 |
| `stale` | 使用了过期缓存 | 标题追加「（离线缓存，可能已过期）」 |
| `all-sources-failed` | 两个数据源均失败 | 显示「数据获取失败」+ 错误摘要 |
| `errors[]` | 各源失败原因（`NMC: …` / `WCN: …`） | 调试日志 / 失败项副标题 |

---

## 4. 降级矩阵

| 主源 | 备用源 | 结果 |
|---|---|---|
| 成功 | 成功 | `mixed`，主源优先 + 字段补缺 |
| 成功 | 失败 | 主源，`errors` 记录备用源失败 |
| 失败 | 成功 | 备用源提升为骨架，`ok=True` |
| 失败 | 失败，有过期缓存 | 过期缓存，`stale=True` |
| 失败 | 失败，无缓存 | `ok=False` 空结构 + 提示，插件不崩溃 |
