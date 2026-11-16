# 插件目录结构与文件职责

## 1. 完整目录树

```text
kodi-weather-china/                    ← 仓库根 = Kodi 插件根（addon.xml 在根）
├── addon.xml                          插件清单：id / 版本 / 依赖 / 扩展点 / 中英文元数据 / 图标
├── default.py                         插件入口（xbmc.python.pluginsource）
├── service.py                         后台服务入口（xbmc.service，皮肤属性定时刷新）
├── icon.png                           插件图标 256×256（Kodi 插件列表显示）
├── fanart.jpg                         背景图 1280×720
├── README.md                          项目总览、快速开始、文档索引
├── LICENSE.txt                        GPL-3.0 许可全文
├── changelog.txt                      Kodi 更新日志格式
├── .gitignore
│
├── resources/
│   ├── settings.xml                   设置页（4 个分类 / 16 个设置项，label 全指向 strings.po）
│   ├── language/                      Kodi 本地化目录（目录名必须是 resource.language.<lang>）
│   │   ├── resource.language.zh_cn/
│   │   │   └── strings.po            简体中文，128 条 msgctxt "#32xxx"
│   │   └── resource.language.en_gb/
│   │       └── strings.po            英文（GB），与中文条目一一对应
│   ├── data/                          内置静态数据（运行时零网络依赖）
│   │   ├── cities_nmc.json           2529 个中央气象台站点（code/city/province/province_code）
│   │   ├── cities_weathercn.json     3230 个中国天气网 9 位城市码（省份已按 5 位码归一化）
│   │   └── conditions.json           0~53 天气现象码 → 中文名 / 英文名 / 图标 key / 关键词兜底
│   ├── lib/                           业务逻辑（纯 Python 3 标准库 + Kodi 内置模块）
│   │   ├── __init__.py               包标记
│   │   ├── config.py                 常量/URL、路径、设置读写、本地化 L()、日志、温度与数值格式化
│   │   ├── net.py                    HTTP 抓取、UTF-8 解码、sha1 文件缓存、重试、stale 降级
│   │   ├── citydb.py                 城市索引加载、中文搜索与评分、双源代码对齐、切换与在线刷新
│   │   ├── nmc.py                    中央气象台接口调用 + JSON 解析 → 标准结构
│   │   ├── weathercn.py              中国天气网接口调用 + JS 变量/HTML 解析 → 标准结构
│   │   ├── alerts.py                 预警归一化（类型/等级/颜色）、去重、排序、等级过滤
│   │   ├── icons.py                  现象码/中文描述 → condition key 与本地图标路径
│   │   ├── weather.py                多源聚合、失败降级、字段补缺、7 天补足、规则执行（数据契约）
│   │   ├── windowprops.py            写 Kodi Home Window 天气属性（Current.* / DayN.* / Alert*）
│   │   └── ui.py                     Kodi 目录菜单、中文搜索交互、详情查看、路由与导航
│   └── media/                         自带图标（20 个天气 + 5 个预警等级），均由 tools/make_icons.py 生成
│
├── docs/
│   ├── DATA_SOURCE.md                 数据源获取方式 / 接口流程 / 格式解析
│   ├── RULES.md                       标准输出结构与 12 条处理规则
│   ├── STRUCTURE.md                   本文件
│   ├── I18N.md                        中文输入、UTF-8、strings.po 本地化
│   ├── INSTALL_DEBUG.md               安装、配置、调试、常见问题
│   └── ROADMAP.md                     后续扩展建议
│
├── tests/
│   └── fixtures/                     真实接口抓取的离线样本（5 个文件，供 selftest 使用）
│       ├── nmc_weather.json           /rest/weather 完整响应
│       ├── nmc_alarm.json             /rest/findAlarm 响应
│       ├── weather_index.js          /weather_index/101010100.html 响应
│       ├── dingzhi_taiyuan.js        含「寒潮蓝色预警」的 /dingzhi 响应
│       └── weather7_fragment.html    7 天预报页 <ul class="t clearfix"> 片段
│
├── assets/
│   └── binary_assets.json          27 个二进制资源（图标/fanart）的 base64 纯文本清单
│
├── tools/                            开发/维护工具（运行时不需要）
│   ├── build_city_db.py               抓取并生成两份城市索引 JSON
│   ├── gen_language.py                由单一字符串表生成中/英 strings.po
│   ├── make_icons.py                  用 Pillow 生成全部 PNG 与 fanart
│   ├── pack_assets.py                 把二进制资源编码成 assets/binary_assets.json
│   ├── restore_assets.py              从清单还原二进制资源（打包/自测时自动调用）
│   ├── selftest.py                    注入 Kodi 桩模块的离线自测 + --online 端到端测试
│   └── make_release.py                生成 dist/plugin.weather.china-<ver>.zip
│
└── dist/
    └── plugin.weather.china-1.0.1.zip  ← 可直接用 Kodi「从 zip 安装」的成品
```

**打包约定**：zip 内顶层目录名必须等于 addon id（`plugin.weather.china/`），`addon.xml` 位于该目录根部。`make_release.py` 自动完成这一结构，并剔除 `__pycache__` / `*.pyc` / `*.tmp`。

---

## 2. 各文件职责一览

| 文件 | 职责 | 依赖 | 运行时必需 |
|---|---|---|---|
| `addon.xml` | 声明 id、版本、Python 3 依赖、插件/服务扩展点、双语元数据、图标 | — | ✔ |
| `default.py` | 把 `resources/` 加入 `sys.path`，转交 `lib/ui.py::run()` | xbmcaddon | ✔ |
| `service.py` | 登录时启动，定时抓取并发布皮肤天气属性，异常安全可中断 | xbmc / lib | 可选 |
| `icon.png` / `fanart.jpg` | 插件列表图标与背景 | — | ✔ |
| `resources/settings.xml` | 4 分类 16 项设置，全部 label/help/option 引用 32xxx | strings.po | ✔ |
| `resources/language/*/strings.po` | 中英文本地化；Kodi 按系统语言自动加载 | — | ✔ |
| `resources/data/*.json` | 城市索引与天气现象码表，保证离线搜索与统一图标 | — | ✔ |
| `resources/media/*.png` | 自包含天气/预警图标，无外部资源依赖 | — | ✔ |
| `lib/config.py` | 唯一集中导入 Kodi 专有 API 的模块；设置、路径、L()、日志、格式化 | xbmc* | ✔ |
| `lib/net.py` | Fetcher：HTTP、UTF-8、sha1 缓存、重试、stale-while-error | 标准库 | ✔ |
| `lib/citydb.py` | 城市索引、中文搜索评分、去后缀、拼音、双源代码匹配、切换与刷新 | config/net | ✔ |
| `lib/nmc.py` | 主源接口与 `9999` 哨兵处理，输出标准结构 | config/icons/alerts | ✔ |
| `lib/weathercn.py` | 备源接口、JS 变量括号平衡解析、7 天 HTML 解析 | config/nmc/icons/alerts | ✔ |
| `lib/alerts.py` | 预警类型/等级/颜色归一化、去重排序过滤 | icons | ✔ |
| `lib/icons.py` | 现象码与中文描述 → condition key / PNG 路径 | conditions.json | ✔ |
| `lib/weather.py` | 聚合器：主备选择、降级、字段补缺、7 天补足、规则执行 | 上述全部 | ✔ |
| `lib/windowprops.py` | 写 `Current.*`/`DayN.*`/`Weather.Alert*` 皮肤属性 | xbmcgui/config | 可选 |
| `lib/ui.py` | 全部目录页、中文输入、详情弹窗、URL 路由 | xbmc*/lib | ✔ |
| `tools/*` | 生成数据、语言、图标、资源清单、测试、发布包 | Python 3 + Pillow（仅生成图标时） | ✘ |
| `assets/binary_assets.json` | 二进制图标的 base64 文本清单，供纯文本仓库还原资源 | — | ✘ |
| `tests/fixtures/*` | 真实接口样本，离线回归测试基线 | — | ✘ |
| `docs/*` | 交付文档 | — | ✘ |

**模块依赖方向**（单向，无循环）：

```
default.py / service.py
        └──> lib/ui.py ──> lib/weather.py ──> lib/nmc.py / lib/weathercn.py
                                    │                └──> lib/alerts.py ──> lib/icons.py
                                    ├──> lib/citydb.py ──> lib/net.py
                                    └──> lib/windowprops.py
        所有模块 ──> lib/config.py（常量 / 设置 / L() / 日志）
```

---

## 3. `addon.xml` 关键配置

| 项 | 值 | 说明 |
|---|---|---|
| `id` | `plugin.weather.china` | 必须与 zip 顶层目录、settings.xml `section id` 一致 |
| `version` | `1.0.1` | Kodi 依据它判断升级；发布包文件名带版本号 |
| `requires` | `xbmc.python` `3.0.0` | **最低 Kodi 19 (Matrix)**；Kodi 18 为 Python 2，不兼容 |
| `xbmc.python.pluginsource` | `library="default.py"` | 交互式插件入口；`<provides>executable</provides>` 让插件出现在「程序/插件」列表 |
| `xbmc.service` | `library="service.py" start="login"` | 可选后台服务；不需要皮肤集成可在设置里关闭 `skin_props` |
| `xbmc.addon.metadata` | `summary/description/disclaimer` 带 `lang="zh_CN"` 与 `lang="en_GB"` | 插件管理器里的双语名称与说明 |
| `assets` | `icon.png` / `fanart.jpg` | Kodi 插件列表图标与背景 |

> 说明：Kodi 官方的 `xbmc.python.weather` 扩展点是「由 Kodi 天气服务调用的后台脚本」，无法提供交互式菜单与中文城市搜索；因此本插件采用 `pluginsource` 提供完整 UI，并**额外**通过 `xbmc.service` 写 Window Properties 来兼容支持天气部件的皮肤。二者结合是本方案能同时满足「交互功能」与「皮肤集成」的关键。

---

## 4. `settings.xml` 关键配置

Kodi 19+ 现代格式：`<settings version="1">` → `<section id="plugin.weather.china">` → 4 个 `<category>` → `<group>` → `<setting>`。所有 `label` / `help` / `option label` 都是 `strings.po` 里的 32xxx 编号。

| 分类 | 设置 id | 类型 | 默认值 | 作用 |
|---|---|---|---|---|
| 常规 | `city_name` | string | 北京 | 当前城市中文名 |
| | `nmc_code` | string | Wqsps | 中央气象台站点 ID |
| | `wcn_code` | string | 101010100 | 中国天气网 9 位码；留空禁用备源 |
| | `temp_unit` | enum(string) | 0 | 0=°C，1=°F |
| | `forecast_days` | enum(string) | 7 | 3 / 5 / 7 天 |
| 数据源 | `primary_source` | enum(string) | auto | auto / nmc / wcn |
| | `enable_wcn` | bool | true | 是否启用中国天气网补充 |
| | `timeout` | string | 10 | 网络超时秒（1~60） |
| | `cache_ttl` | string | 10 | 缓存分钟数（1~1440） |
| 预警 | `enable_alerts` | bool | true | 预警总开关 |
| | `alert_scope` | enum(string) | all | local / national / all |
| | `alert_min_level` | enum(string) | 0 | 0 全部 / 1 黄+ / 2 橙+ / 3 仅红 |
| | `national_limit` | string | 30 | 全国预警条数（5~100） |
| 高级 | `skin_props` | bool | true | 是否写皮肤天气属性 |
| | `refresh_interval` | string | 15 | 后台刷新分钟（1~240） |
| | `debug` | bool | false | 调试日志 |

> 设计取舍：数值/枚举设置统一用 `type="string"` 承载，由 `lib/config.py::get_int()` 做安全转换与范围钳制，避免不同 Kodi 版本对 `integer`/`slider` 控件解析差异导致设置页无法打开。
