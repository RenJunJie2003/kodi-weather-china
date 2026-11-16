# 后续功能扩展建议

按「投入 / 价值」排序，每条给出实现要点与涉及文件，便于直接排期。

## P0 · 稳健性（建议优先）

| 建议 | 实现要点 | 涉及文件 |
|---|---|---|
| 接口变更监测与自动回归 | 把 `tools/selftest.py --online` 做成 GitHub Actions 定时任务（每日 1 次），接口改版即时发现；失败自动开 issue | `.github/workflows/*.yml`、`tools/selftest.py` |
| 数据源可插拔抽象 | 定义 `BaseSource` 接口（`fetch_weather` / `fetch_alerts` / `fetch_cities`），现在的两源改为实现，新增源只需加一个文件并在设置里注册 | `lib/sources/`（新）、`lib/weather.py` |
| 可配置 URL 前缀 | 把 `config.NMC_BASE` / `WCN_*` 暴露到设置，接口迁移时用户无需等新版插件 | `config.py`、`settings.xml`、`strings.po` |
| 更细的缓存策略 | 实况 10min / 预报 60min / 城市索引 30 天分别配置，减少无效请求 | `lib/net.py`、`settings.xml` |

## P1 · 功能增强

| 建议 | 实现要点 | 涉及文件 |
|---|---|---|
| **逐小时预报** | 中国天气网 `http://d1.weather.com.cn/hour{code}.html`（或 7 天页内嵌的逐三小时 JSON）解析出 24 小时温度/降水曲线；UI 加「逐小时」页，并写 `Hour1..Hour24.*` 皮肤属性 | 新 `lib/hourly.py`、`ui.py`、`windowprops.py` |
| **多城市收藏 / 城市轮换** | 设置里保存城市列表，首页横向列出多个城市；后台服务轮流刷新 | `citydb.py`、`settings.xml`、`ui.py` |
| **预警主动通知** | 后台服务对比上次 `alert.id` 集合，新增红色/橙色预警时用 `Dialog.notification` 弹窗，并可推送到手机（Kodi 事件/Webhook） | `service.py`、新增 `lib/notifier.py` |
| **空气质量独立页** | `nmc.cn` 的 `data.air` 或中国天气网 AQI 接口，展示 AQI 等级、首要污染物、六项污染物 | 新 `lib/air.py`、`ui.py` |
| **雷达图 / 卫星云图** | `nmc.cn/rest/...radar` 与 `image.nmc.cn` 的雷达图 URL，作为图片项展示并自动刷新 | `ui.py`、`icons.py` |
| **预警详情网页** | 用 `url` 在 Kodi 内置浏览器/外部打开 `nmc.cn/publish/alarm/{id}.html`；或抓取 HTML 正文补充 `content` | `alerts.py`、`ui.py` |
| **台风路径** | 中央气象台台风网公开数据，台风季展示路径与距离 | 新模块 |
| **生活指数可配置开关** | 30 项指数较多，允许只显示常用 6 项 | `settings.xml`、`ui.py` |
| **拼音全拼 / 英文城市名搜索** | 引入轻量拼音表（或 `pypinyin` 数据文件生成静态映射），支持 `beijing`、`shijiazhuang` | `citydb.py`、`tools/build_city_db.py` |
| **IP 自动定位** | 用 `nmc.cn/rest/ip` 或公开 IP 库定位到城市，首次启动免手工选择（需用户授权） | `citydb.py`、`ui.py` |

## P2 · 体验与生态

| 建议 | 实现要点 | 涉及文件 |
|---|---|---|
| **官方 weather 扩展点兼容** | 增加 `xbmc.python.weather` 扩展点与 `weather.py` 瘦入口，让 Kodi「天气」设置里也能选本插件（与现有 pluginsource 共存），由 Kodi 传 location 后写属性 | `addon.xml`、新 `weather_entry.py` |
| **提交 Kodi 官方插件仓库** | 按 `xbmc/repo-plugins` 规范补 `addon.xml.in`、图标尺寸、许可证与 CI，走 PR 流程 | 仓库元数据 |
| **皮肤天气 Widget 支持** | 提供 `script` 入口与 `Weather.*` 属性文档，配合 Estuary/Arctic Horizon 等皮肤做自定义天气面板 | `windowprops.py`、`docs/` |
| **更多语言** | 繁体中文、日文；`gen_language.py` 扩展为多列输出 | `tools/gen_language.py`、`addon.xml` |
| **设置向导** | 首次启动弹窗引导选城市、温度单位、预警等级，而不是默认北京 | `ui.py`、`config.py` |
| **可视化图表** | 用 Kodi 内置控件或生成 PNG（Pillow 仅开发期）画 7 天温度曲线、降水柱状图 | `tools/make_icons.py`、`ui.py` |
| **语音/遥控器快捷** | 注册 Kodi 全局快捷键、加入「天气」到主菜单、支持语音搜索城市 | `addon.xml`、`ui.py` |
| **数据导出** | 把标准结构导出为 JSON / CSV 供 Home Assistant、Node-RED 等消费 | 新 `lib/export.py` |

## P3 · 工程化

| 建议 | 实现要点 |
|---|---|
| 单元测试覆盖率 | 现在 60 项断言覆盖解析/搜索/预警/规则；补 `pytest` 参数化用例与边界样本（跨年日期、无高温、非法 JSON、超长文本） |
| 类型标注与静态检查 | 给 `lib/` 加 type hints，接 `ruff` / `mypy` 到 CI |
| 结构化日志与错误上报（可选、默认关） | 用户主动开启时把匿名错误摘要发到 GitHub issue 模板，便于收集接口变更样本 |
| 版本化城市索引 | `cities_*.json` 带 `generated` 时间戳与 schema 版本，插件启动时校验并在过期时提示刷新 |
| 国际化字符串校验 CI | `selftest.py` 已校验中英条目一致；可再加「新增 32xxx 未翻译」检查 |
| 发布自动化 | `make_release.py` + GitHub Release 上传 zip，用户在 Kodi 里直接从仓库 zip 安装 |

## 架构上需要注意的两点

1. **保持「数据契约」稳定**：所有新数据源都必须输出 `RULES.md` 定义的标准结构，UI 层不应再增加针对某家接口的 `if`。现有 `merge()` 的「主源优先、字段补缺」机制可直接复用。
2. **保持中文文本优先**：预警类型/等级、天气现象继续以中文文本解析为主、编码为辅；新增数据源时不要反过来依赖内部编码，这是对抗接口改版最有效的手段。
