# 中国天气 · Kodi 插件（plugin.weather.china）

一个**完整可运行**的 Kodi 中文气象插件：实时天气、7 天预报、中文城市搜索与切换、中国气象预警（含预警类型与蓝/黄/橙/红等级）。数据取自**中央气象台 nmc.cn** 与**中国天气网 weather.com.cn** 的公开接口，无需注册、无需 API Key。

> 已实测接口（2026-11-16）、内置全国 **2529 个气象站点 + 3230 个 9 位城市码**、55 项离线自测 + 真实接口端到端测试通过。

---

## 快速开始

1. 下载 `dist/plugin.weather.china-1.0.0.zip`（或执行 `python tools/make_release.py` 自行生成）。
2. Kodi → ⚙ 设置 → 插件 → **从 zip 文件安装** → 选择该 zip。
3. Kodi → 插件 → **中国天气 China Weather** → 首次进入会显示北京实况。
4. 菜单 **切换城市** → **中文城市搜索** → 输入「石家庄」→ 选中即切换。
5. 菜单 **实时天气 / 未来多日预报 / 气象预警 / 全国预警** 查看数据。

要求：**Kodi 19 (Matrix) 及以上**（使用 Python 3 与现代 settings.xml）。中文界面请把 Kodi 系统语言设为「中文(简体)」，插件会自动加载 `strings.po`。

---

## 功能

| 功能 | 说明 |
|---|---|
| 实时天气 | 温度、体感、天气现象、湿度、气压、降水、风向/风力/风速、能见度、AQI、PM2.5、日出日落、更新时间 |
| 未来多日预报 | 3 / 5 / 7 天（可设），每天含高低温、白天/夜间现象与图标、风向风力、降水量；点开看详情 |
| 中文城市搜索与切换 | 内置全国索引，支持中文子串、去后缀归一化、热门城市、拼音首字母（bj/sh/gz…）；结果同时携带两套数据源编码 |
| 中国气象预警 | 本地预警 + 全国预警；解析**预警类型**（寒潮/大雾/道路结冰/暴雨…）与**等级**（蓝/黄/橙/红），按等级着色、排序、去重、按最低等级过滤，可看预警全文 |
| 生活指数 | 中国天气网 30 项生活指数（穿衣、洗车、紫外线…） |
| 皮肤集成 | 后台服务把 `Current.*` / `Day0..Day6.*` / `Weather.Alert*` 写入 Kodi Window Properties，支持天气部件的皮肤可直接显示 |
| 中文 / UTF-8 / 本地化 | 全中文界面、UTF-8 全链路、中英双语 `strings.po`；界面文本零硬编码 |
| 健壮性 | 双数据源自动降级、文件缓存、断网使用过期缓存、重试与超时、全链路异常兜底 |

---

## 数据源与处理规则（摘要）

- **主数据源：中央气象台 nmc.cn** — `/rest/province` → `/rest/province/{code}` → `/rest/weather?stationid={code}` → `/rest/findAlarm`。官方权威、UTF-8 JSON、含 7 天预报与实时预警。
- **备用/补充源：中国天气网 weather.com.cn** — `d1.weather.com.cn/weather_index/{9位码}.html`（实况 + 5 天预报 + 预警 + 生活指数）、`d1.weather.com.cn/dingzhi/{9位码}.html`（预警详情）、`www.weather.com.cn/weather/{9位码}.shtml`（7 天预报页）。需带 `Referer`。
- **处理规则要点**：所有响应按 UTF-8 解码；`9999` / `-` / 空串统一为 `None` 并显示 `—`；温度统一摄氏度、按设置换算 °F；缓存 TTL 默认 10 分钟，网络失败允许 24 小时内过期缓存（stale-while-error）；主源失败自动切备用源，两源成功则按字段补缺合并；预警以**中文文本解析为准、编码仅作辅助**，按「红 > 橙 > 黄 > 蓝」排序。

完整说明见 [`docs/DATA_SOURCE.md`](docs/DATA_SOURCE.md) 与 [`docs/RULES.md`](docs/RULES.md)。

---

## 文档索引

| 文档 | 内容 |
|---|---|
| [docs/DATA_SOURCE.md](docs/DATA_SOURCE.md) | 数据源获取方式、接口调用流程、返回格式与字段解析、城市索引生成 |
| [docs/RULES.md](docs/RULES.md) | 标准输出结构、编码/缺失值/单位/缓存/降级/预警/展示等明确处理规则 |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | 完整目录树、每个文件职责、`addon.xml` / `settings.xml` 关键配置说明 |
| [docs/I18N.md](docs/I18N.md) | 中文输入、UTF-8 编码处理、`strings.po` 多语言本地化实现 |
| [docs/INSTALL_DEBUG.md](docs/INSTALL_DEBUG.md) | 安装、配置、调试步骤与常见问题处理 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 后续功能扩展建议 |

---

## 开发与维护

```bash
python tools/gen_language.py      # 由单一字符串表生成中/英 strings.po
python tools/make_icons.py        # 用 Pillow 重新生成图标（运行时不需要 Pillow）
python tools/build_city_db.py resources/data   # 重新抓取全国城市索引
python tools/selftest.py          # 离线自测（fixtures，无需联网）
python tools/selftest.py --online # 追加真实接口端到端测试
python tools/make_release.py      # 生成 dist/*.zip 安装包
```

插件运行时**零第三方依赖**，仅使用 Python 3 标准库 + Kodi 内置模块。

> **从 GitHub 仓库 clone 后**：二进制图标（`icon.png` / `fanart.jpg` / `resources/media/*.png`）以纯文本 `assets/binary_assets.json`（base64 清单）随仓库提交。首次运行 `python tools/make_release.py` 或 `python tools/selftest.py` 会自动调用 `tools/restore_assets.py` 还原；也可手动执行 `python tools/restore_assets.py`。这样仓库 100% 为文本，且一条命令即可生成完整可安装的 zip。
> 修改图标后运行 `python tools/pack_assets.py` 重新生成清单。

---

## 声明

气象数据来自公开接口，仅供个人参考；防灾决策请以中央气象台及当地气象部门正式发布为准。本项目为非官方第三方插件，与中央气象台、中国天气网无附属关系。接口可能随对方站点改版而调整，插件已内置双源降级与离线缓存以缓解影响。

许可：GPL-3.0（见 `LICENSE.txt`；Kodi 官方仓库要求 copyleft 许可）。
