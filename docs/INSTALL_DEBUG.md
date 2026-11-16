# 安装、配置、调试与常见问题

## 1. 环境要求

| 项 | 要求 |
|---|---|
| Kodi | **19 (Matrix) 及以上**（20 Nexus / 21 Omega / 22 均适用）。Kodi 18 Leia 是 Python 2，无法运行本插件 |
| Python | 由 Kodi 内置提供（`xbmc.python` 3.0.0），无需另装 |
| 第三方库 | **运行时零依赖**；仅生成图标时开发机需要 Pillow |
| 网络 | 能访问 `www.nmc.cn` 与 `d1.weather.com.cn`（HTTP 80）。纯离线时仍可搜索城市并显示缓存数据 |
| 中文界面 | Kodi 系统语言设为「中文(简体)」，字体需含中文字形 |

---

## 2. 安装

### 方式 A：从 zip 安装（推荐）

1. 取得 `dist/plugin.weather.china-1.0.1.zip`（仓库 Release 里直接下载；或本地执行 `python tools/make_release.py` 生成）。
2. Kodi → ⚙ 设置 → **插件** → 打开「未知来源」（首次需要）→ **从 zip 文件安装** → 选择 zip。
3. 提示「插件安装成功」后即可在 **插件 → 程序 / 我的插件 → 中国天气 China Weather** 找到。
4. 若想常驻主菜单：在插件上长按/右键 → **添加到收藏**，或在皮肤设置里把它加入主菜单项。

> zip 内顶层目录必须是 `plugin.weather.china/`，`addon.xml` 在该目录根部。`make_release.py` 已保证这一点；手工打包时请勿把 `addon.xml` 直接放在 zip 根。

### 方式 B：手工拷贝（开发调试用）

把整个仓库目录复制到 Kodi 的 `addons` 目录，并重命名为插件 id：

| 平台 | addons 路径 |
|---|---|
| Windows | `%APPDATA%\Kodi\addons\plugin.weather.china\` |
| Linux | `~/.kodi/addons/plugin.weather.china/` |
| macOS | `~/Library/Application Support/Kodi/addons/plugin.weather.china/` |
| Android | `Android/data/org.xbmc.kodi/files/.kodi/addons/plugin.weather.china/` |
| LibreELEC / CoreELEC | `/storage/.kodi/addons/plugin.weather.china/` |

复制后重启 Kodi（或 设置 → 插件 → 检查更新）让 Kodi 重新扫描插件清单。

### 方式 C：从源码构建

```bash
git clone https://github.com/RenJunJie2003/kodi-weather-china.git
cd kodi-weather-china
python tools/restore_assets.py   # 还原二进制图标（源码仓库以 base64 清单存放）
python tools/selftest.py            # 离线自测，应有 55 项全通过
python tools/selftest.py --online   # 追加真实接口测试，应有 60 项全通过
python tools/make_release.py        # 生成 dist/*.zip（缺图标时会自动还原）
```

---

## 3. 首次配置

1. 打开插件，默认城市为**北京**（`city_name=北京`、`nmc_code=Wqsps`、`wcn_code=101010100`），首页立即显示实况。
2. **切换城市**：
   - 菜单 →「切换城市」→「中文城市搜索」→ 输入中文名（如 `太原`、`朝阳区`、`乌鲁木齐`）；
   - 或「热门城市」里直接选；
   - 或输入拼音首字母（`bj` / `sh` / `gz` / `sjz`）。
   - 选中结果后插件自动写入三项设置、清缓存并刷新。
3. **设置**（菜单 →「设置」，或插件右键 → 设置）：

| 想做的事 | 改哪项 |
|---|---|
| 换温度单位 | 常规 → 温度单位（°C / °F） |
| 预报只要 3 天 | 常规 → 预报天数 |
| 只用某一个数据源 | 数据源 → 主数据源；或关闭「启用中国天气网补充数据」 |
| 网络慢 / 请求超时 | 数据源 → 网络超时（秒）调大、缓存有效期调大 |
| 只看红色预警 | 预警 → 最低显示等级 = 仅红色 |
| 关闭全国预警 | 预警 → 预警范围 = 仅当前城市 |
| 让皮肤天气部件显示数据 | 高级 → 保持「写入皮肤天气属性」开启 |
| 排查问题 | 高级 → 打开「调试日志」 |

4. **中文界面**：设置 → Interface → Regional → Language → 中文(简体)。插件会自动加载 `resource.language.zh_cn/strings.po`；英文系统加载 `en_gb`。

---

## 4. 调试

### 4.1 打开插件日志

插件设置 → 高级 → **调试日志 = 开**。日志以 `[plugin.weather.china]` 为前缀，会输出：
- 每次菜单 action 与参数；
- HTTP 请求 URL、缓存命中（age）、重试与失败原因；
- 城市索引数量、皮肤属性发布结果。

### 4.2 kodi.log 位置

| 平台 | 路径 |
|---|---|
| Windows | `%APPDATA%\Kodi\kodi.log` |
| Linux | `~/.kodi/temp/kodi.log` |
| macOS | `~/.kodi/temp/kodi.log`（旧版 `~/Library/Logs/kodi.log`） |
| Android | Kodi 内「设置 → 系统 → 日志查看器」或 `Android/data/org.xbmc.kodi/files/.kodi/temp/kodi.log` |
| LibreELEC / CoreELEC | `ssh root@设备` → `tail -f /storage/.kodi/temp/kodi.log` |

Kodi 20+ 也可在界面里直接看：设置 → 系统 → 日志查看器 → 选 `kodi.log`。

### 4.3 直接在电脑上验证接口（不启 Kodi）

```bash
# 中央气象台：实况 + 7 天预报 + 本地预警
curl "http://www.nmc.cn/rest/weather?stationid=Wqsps"

# 全国预警
curl "http://www.nmc.cn/rest/findAlarm?pageNo=1&pageSize=5"

# 中国天气网：实况 + 5 天预报 + 生活指数（必须带 Referer）
curl -e "http://www.weather.com.cn/" \
     "http://d1.weather.com.cn/weather_index/101010100.html"

# 城市级预警详情（太原示例）
curl -e "http://www.weather.com.cn/" \
     "http://d1.weather.com.cn/dingzhi/101100101.html"

# 省级站点目录
curl "http://www.nmc.cn/rest/province/ABJ"
```

若这些命令都返回空/超时，先排查网络、DNS、代理或运营商对 HTTP 的拦截，而不是改插件代码。

### 4.4 离线回归测试

```bash
python tools/selftest.py            # 用 tests/fixtures 真实样本，55 项
python tools/selftest.py --online   # 追加真实接口端到端，60 项
```

`selftest.py` 会注入 Kodi 桩模块，因此无需安装 Kodi 即可验证解析、搜索、预警等级、图标、温度换算、皮肤属性等全部纯逻辑。

---

## 5. 常见问题

| # | 现象 | 原因 | 处理 |
|---|---|---|---|
| 1 | 安装报「依赖项不满足 / The dependency could not be satisfied」 | Kodi 18 或更早（Python 2），或 `xbmc.python 3.0.0` 不满足 | 升级到 Kodi 19+ |
| 2 | 插件列表里找不到 | 插件菜单入口是 `pluginsource`，出现在「插件 → 程序」分类；天气服务入口则在「设置 → 服务 → 天气」 | 用 Kodi 全局搜索「中国天气」，或添加到收藏/主菜单；见第 19 条 |
| 3 | 打开插件空白、报 Python 错误 | `resources/lib` 未完整复制、或被 zip 工具破坏了目录结构 | 重新用 `make_release.py` 打包；确认 zip 内 `plugin.weather.china/resources/lib/*.py` 齐全；看 `kodi.log` 的 Traceback |
| 4 | 设置页打不开 / 设置项空白 | Kodi 版本过旧，不识别现代 `settings.xml` | 升级 Kodi 19+；或检查 `settings.xml` 的 `section id` 是否等于 `plugin.weather.china` |
| 5 | 中文显示为方框 □□□ | 皮肤字体不含 CJK 字形 | 换用含中文字形的字体（如 Noto Sans CJK），或换皮肤 |
| 6 | 中文变问号 / 乱码「鍖椾含」 | 系统语言不是 UTF-8 环境、`strings.po` 被转成 GBK/BOM、或 Git 自动转码破坏了文件 | 确认 `strings.po` 为 UTF-8 无 BOM；检查 `.gitattributes`；把 Kodi 语言设为中文(简体)；重新 `gen_language.py` 生成 |
| 7 | 一直显示「数据获取失败」 | 设备无法访问 `nmc.cn` / `weather.com.cn`；HTTP 被代理/防火墙拦；DNS 异常 | 用 4.3 的 curl 自检；调大「网络超时」；确认未知来源与网络权限；必要时换网络 |
| 8 | 有实况但没有 AQI、PM2.5、生活指数 | 备用源未启用或 9 位城市码为空 | 设置里打开「启用中国天气网补充数据」，并在「切换城市」重选一次以写入 `wcn_code` |
| 9 | 预警列表一直显示「当前无生效预警」 | **多数情况是正常的**（该城市确实无生效预警）；也可能是开关/等级过滤 | 到「全国预警」确认接口有数据；检查 `enable_alerts`、`alert_scope`、`alert_min_level` |
| 10 | 预警等级显示「未知等级」 | 新发布的预警标题格式与常规不同（如「继续发布…」「提示」类） | 属文本兜底行为，不影响使用；把标题样本提交 issue，扩展 `alerts.py` 的 `KNOWN_TYPES` / 正则即可 |
| 11 | 搜不到某城市 | 关键词太长/带后缀；索引里是区县名 | 输入更短关键词（「朝阳」而非「北京市朝阳区」）；用热门城市或拼音；菜单「刷新城市索引」在线重建 |
| 12 | 切换城市后还显示旧城市数据 | 缓存未清或 Kodi 界面未刷新 | 菜单点「刷新」；确认设置里 `city_name / nmc_code` 已变；必要时重启插件 |
| 13 | 图标不显示 / 显示默认图标 | `resources/media` 缺失，或皮肤不显示 directory item 的 icon | 确认 media 目录有 25 个 PNG；换皮肤验证；`conditions.json` 的 key 与图标名一致 |
| 14 | 皮肤天气部件没有数据 | `skin_props` 关闭、`xbmc.service` 未启动、或皮肤读取的属性名不同 | 打开「写入皮肤天气属性」，重启 Kodi；确认皮肤用的是 `Current.*` / `Day0.*` 标准键；看日志里 `skin properties published` |
| 15 | 后台服务频繁请求 / 耗电 | 刷新间隔太短 | 调大「后台刷新间隔」（默认 15 分钟），或关闭 `skin_props` |
| 16 | 接口突然全变 404 / 字段变了 | 数据源站点改版 | 先用 curl 确认；运行 `build_city_db.py` 重建索引；在 `nmc.py` / `weathercn.py` 调整解析；插件有双源降级与 24h 过期缓存可临时兜底 |
| 17 | 只想完全重置插件 | — | 删除用户配置目录 `userdata/addon_data/plugin.weather.china/`（内含缓存与在线城市索引），重启插件；不会删除内置数据 |
| 18 | 7 天预报里今天最高温显示 `—` | 中央气象台当日白天数据已过期（返回 `9999`） | 属正常；开启中国天气网补充后会自动用 `fc.f` 补齐当天高温 |
| 19 | **「设置 → 服务 → 天气」的选择列表里没有「中国天气」** | 插件只注册了 `xbmc.python.pluginsource`（程序插件）；Kodi 只把带 `xbmc.python.weather` 扩展点的插件列为天气源 | 升级到含天气服务扩展点的版本；安装后在「插件 → 程序」里确认能打开，再到天气设置里选；选中后点「地点 1」配置中文城市 |
| 20 | **天气设置里点「地点 1」没动静 / 不弹城市搜索** | Kodi 的 `RunScript(addonid,location1)` 解析到插件菜单入口，把 `location1` 当插件句柄 `int()` 转换而异常退出；也可能是升级后未重启、Kodi 缓存了旧的扩展点信息 | 覆盖安装最新版并**重启 Kodi**；先用插件菜单「切换城市」设好当前城市（天气服务会自动回退使用它，天气数据照常显示）；在 `kodi.log` 搜 `weather provider called` / `weather provider failed` 定位。新版的 `pluginsource` 与 `weather` 共用 `default.py`，按 `sys.argv[0]` 判别来源 |
| 21 | **覆盖安装时报错「安装失败 / 已安装相同或更新版本」** | Kodi 按 `addon.xml` 的 `version` 判断是否为升级；用与已装版本相同的 zip 覆盖可能被拒绝 | 使用**版本号更高**的 zip（当前 `1.0.1`，旧版 `1.0.0`）；必要时先在插件管理里卸载旧版再安装；不要手动解压 zip，直接选 `.zip` 文件 |

---

## 6. 卸载与升级

- **卸载**：设置 → 插件 → 我的插件 → 中国天气 → 卸载。用户配置目录可能被保留，需要时手工删除。
- **升级**：下载新版本 zip，用「从 zip 文件安装」覆盖安装；`changelog.txt` 会显示更新说明。升级不会丢失已选城市（设置保存在 Kodi 用户配置里）。
