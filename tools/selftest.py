# -*- coding: utf-8 -*-
"""
tools/selftest.py — 不启动 Kodi 的离线自测。

做法：向 sys.modules 注入 xbmc / xbmcaddon / xbmcvfs / xbmcgui / xbmcplugin
桩模块，再用 tests/fixtures 里从真实接口抓取的样本，验证：
  XML/PO/JSON 配置完整性、中文城市搜索、JS 变量解析、实况/7 天预报解析、
  预警类型与等级归一化、图标映射、温度换算、皮肤属性输出。

用法：
  python tools/selftest.py            # 纯离线（用 fixtures）
  python tools/selftest.py --online   # 额外跑一次真实接口端到端抓取
"""
from __future__ import unicode_literals

import io
import json
import os
import re
import sys
import tempfile
import types
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
SETTINGS = {
    "city_name": "北京", "nmc_code": "Wqsps", "wcn_code": "101010100",
    "temp_unit": "0", "forecast_days": "7", "primary_source": "auto",
    "enable_wcn": "true", "timeout": "10", "cache_ttl": "10",
    "enable_alerts": "true", "alert_scope": "all", "alert_min_level": "0",
    "national_limit": "30", "skin_props": "true",
    "refresh_interval": "15", "debug": "false",
}
RESULTS = []
PROPERTIES = {}


def check(name, condition, detail=""):
    RESULTS.append((name, bool(condition), detail))
    print("  [%s] %s%s" % ("PASS" if condition else "FAIL", name,
                           ("  -> " + str(detail)) if detail else ""))
    return bool(condition)


def fixture(name):
    with io.open(os.path.join(FIXTURES, name), "r", encoding="utf-8") as fp:
        return fp.read()


# ---------------------------------------------------------------- Kodi 桩
def load_po(lang):
    path = os.path.join(ROOT, "resources", "language",
                        "resource.language." + lang, "strings.po")
    out = {}
    context = None
    for line in io.open(path, "r", encoding="utf-8"):
        line = line.strip()
        if line.startswith("msgctxt"):
            match = re.search(r'msgctxt "#(\d+)"', line)
            context = match.group(1) if match else None
        elif line.startswith("msgstr ") and context:
            match = re.search(r'msgstr "(.*)"', line)
            if match:
                out[context] = (match.group(1)
                                .replace('\\"', '"').replace("\\n", "\n"))
                context = None
    return out


PO_ZH = {}


class FakeAddon(object):
    def __init__(self, addon_id="plugin.weather.china"):
        self.id = addon_id

    def getAddonInfo(self, key):
        return {"path": ROOT, "profile": tempfile.mkdtemp(prefix="kodi-wx-"),
                "name": "中国天气", "version": "1.0.2"}.get(key, "")

    def getSetting(self, key):
        return SETTINGS.get(key, "")

    def setSetting(self, key, value):
        SETTINGS[key] = value
        return True

    def getLocalizedString(self, string_id):
        return PO_ZH.get(str(string_id), "")

    def openSettings(self):
        return True


class FakeWindow(object):
    def __init__(self, window_id):
        self.id = window_id

    def setProperty(self, key, value):
        PROPERTIES[key] = value

    def clearProperty(self, key):
        PROPERTIES.pop(key, None)


class FakeDialog(object):
    def notification(self, *args, **kwargs):
        return True

    def textviewer(self, *args, **kwargs):
        return True

    def input(self, *args, **kwargs):
        return "北京"


class FakeMonitor(object):
    def abortRequested(self):
        return False

    def waitForAbort(self, seconds):
        return True


def install_stubs():
    xbmc = types.ModuleType("xbmc")
    xbmc.LOGDEBUG, xbmc.LOGINFO = 0, 1
    xbmc.LOGWARNING, xbmc.LOGERROR = 2, 4
    xbmc.log = lambda msg, level=1: None
    xbmc.Monitor = FakeMonitor
    xbmc.executebuiltin = lambda command: None
    sys.modules["xbmc"] = xbmc

    xbmcaddon = types.ModuleType("xbmcaddon")
    xbmcaddon.Addon = FakeAddon
    sys.modules["xbmcaddon"] = xbmcaddon

    xbmcvfs = types.ModuleType("xbmcvfs")
    xbmcvfs.translatePath = lambda path: path
    sys.modules["xbmcvfs"] = xbmcvfs

    xbmcgui = types.ModuleType("xbmcgui")
    xbmcgui.Window = FakeWindow
    xbmcgui.Dialog = FakeDialog
    xbmcgui.ListItem = lambda *a, **k: types.SimpleNamespace(
        setArt=lambda art: None, setProperty=lambda k, v: None)
    xbmcgui.INPUT_ALPHANUM = 0
    sys.modules["xbmcgui"] = xbmcgui

    xbmcplugin = types.ModuleType("xbmcplugin")
    xbmcplugin.addDirectoryItem = lambda *a, **k: True
    xbmcplugin.endOfDirectory = lambda *a, **k: True
    xbmcplugin.setPluginCategory = lambda *a, **k: True
    xbmcplugin.setContent = lambda *a, **k: True
    sys.modules["xbmcplugin"] = xbmcplugin


# ---------------------------------------------------------------- 测试
def main():
    # 从纯文本仓库 clone 时自动还原二进制图标
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        from restore_assets import assets_missing, restore
        if assets_missing():
            restore(verbose=True)
    except Exception:  # noqa: BLE001
        pass

    global PO_ZH
    online = "--online" in sys.argv
    PO_ZH = load_po("zh_cn")
    PO_EN = load_po("en_gb")
    install_stubs()
    old_argv = sys.argv
    sys.argv = ["plugin://plugin.weather.china/", "0", ""]
    sys.path.insert(0, os.path.join(ROOT, "resources"))

    from lib import alerts, config, icons, nmc, weathercn, windowprops
    from lib.citydb import CityDB, norm_city, norm_prov
    from lib.weather import WeatherService, merge

    print("\n=== 1. 配置文件 ===")
    addon_xml = ET.parse(os.path.join(ROOT, "addon.xml")).getroot()
    check("addon.xml id 正确", addon_xml.get("id") == "plugin.weather.china")
    check("addon.xml 含 pluginsource + service 扩展点",
          len([e for e in addon_xml.findall("extension")
               if e.get("point") in ("xbmc.python.pluginsource", "xbmc.service")]) == 2)
    settings_xml = ET.parse(os.path.join(ROOT, "resources", "settings.xml")).getroot()
    setting_ids = [s.get("id") for s in settings_xml.iter("setting")]
    check("settings.xml 设置项 >= 15", len(setting_ids) >= 15, len(setting_ids))
    labels = set()
    for element in settings_xml.iter():
        for attr in ("label", "help"):
            value = element.get(attr)
            if value and value.isdigit():
                labels.add(value)
        for option in element.findall(".//option"):
            if option.get("label"):
                labels.add(option.get("label"))
    missing = sorted(labels - set(PO_ZH))
    check("settings.xml 引用的 32xxx 全部有中文翻译", not missing, missing)
    check("中英语言文件条目数一致",
          len(PO_ZH) == len(PO_EN) and len(PO_ZH) >= 128,
          "%d/%d" % (len(PO_ZH), len(PO_EN)))
    check("zh_cn strings.po 含中文", "实时天气" in PO_ZH.get("32100", ""))
    check("en_gb strings.po 含英文", "Current" in PO_EN.get("32100", ""))

    print("\n=== 2. 中文城市索引与搜索 ===")
    db = CityDB(debug=lambda msg: None)
    check("内置 nmc 站点 >= 2000", len(db.nmc_items) >= 2000, len(db.nmc_items))
    check("内置中国天气网 9 位码 >= 2500", len(db.wcn_items) >= 2500, len(db.wcn_items))
    for word, expect in (("北京", "北京"), ("石家庄", "石家庄"),
                         ("朝阳", "朝阳"), ("上海", "上海")):
        hits = db.search(word, 5)
        check("搜索「%s」命中" % word,
              bool(hits) and hits[0]["name"] == expect,
              hits[0]["display"] if hits else "无")
        if hits:
            check("「%s」匹配到 9 位城市码" % word,
                  bool(hits[0]["wcn_code"]), hits[0]["wcn_code"])
    check("拼音首字母 bj 命中北京",
          db.search("bj", 1) and db.search("bj", 1)[0]["name"] == "北京")
    check("热门城市列表非空", len(db.popular()) >= 15, len(db.popular()))
    check("中文去后缀归一化", norm_city("北京市") == "北京" and
          norm_prov("新疆维吾尔自治区") == "新疆")

    print("\n=== 3. 中国天气网解析 ===")
    variables = weathercn.parse_js_vars(fixture("weather_index.js"))
    check("weather_index 解析出 5 个 JS 变量", len(variables) == 5, list(variables))
    check("dataSK 中文城市名 UTF-8 正确", variables["dataSK"]["cityname"] == "北京")
    wcn = weathercn.WCNSource(None, debug=lambda msg: None)
    wcn_result = wcn.parse_index(variables, {"name": "北京"})
    check("实况温度解析", wcn_result["current"]["temp"] is not None,
          wcn_result["current"]["temp"])
    check("实况 AQI / PM2.5 解析", wcn_result["current"]["aqi"] == 30,
          wcn_result["current"]["aqi"])
    check("fc 5 天预报", len(wcn_result["forecast"]) == 5,
          len(wcn_result["forecast"]))
    check("生活指数解析", len(wcn_result["indices"]) >= 20,
          len(wcn_result["indices"]))
    seven = weathercn.WCNSource.parse_7day(fixture("weather7_fragment.html"))
    check("7 天 HTML 页解析出 7 天", len(seven) == 7, len(seven))
    check("7 天页首日有温度", seven and seven[0]["high"] is not None,
          seven[0]["high"] if seven else None)
    dz_vars = weathercn.parse_js_vars(fixture("dingzhi_taiyuan.js"))
    dz_alert = alerts.from_wcn(
        (weathercn._pick(dz_vars, "alarmDZ") or {})["w"][0], "太原")
    check("太原预警类型=寒潮", dz_alert and dz_alert["type"] == "寒潮",
          dz_alert["type"] if dz_alert else None)
    check("太原预警等级=蓝色", dz_alert and dz_alert["level"] == "蓝色",
          dz_alert["level"] if dz_alert else None)
    check("太原预警含全文", dz_alert and len(dz_alert["content"]) > 50)

    print("\n=== 4. 中央气象台解析 ===")
    nmc_payload = json.loads(fixture("nmc_weather.json"))
    nmc_result = nmc.NMCSource(None).parse(nmc_payload["data"], {"name": "北京"})
    check("实况温度/湿度解析", nmc_result["current"]["temp"] is not None and
          nmc_result["current"]["humidity"] == 44,
          nmc_result["current"]["temp"])
    check("7 天预报解析", len(nmc_result["forecast"]) == 7,
          len(nmc_result["forecast"]))
    check("日出日落解析", nmc_result["current"]["sunrise"] == "06:59",
          nmc_result["current"]["sunrise"])
    check("9999 哨兵被归一化为 None",
          nmc_result["current"]["pressure"] is None,
          nmc_result["current"]["pressure"])
    check("无预警时本地预警为空", len(nmc_result["alerts"]) == 0)

    print("\n=== 5. 全国预警归一化 / 等级规则 ===")
    alarm_payload = json.loads(fixture("nmc_alarm.json"))["data"]
    raw = alarm_payload["page"]["list"] + alarm_payload["provinceAlarms"]
    normalized = [alerts.from_nmc_list(x) for x in raw]
    check("findAlarm 条目全部解析", all(normalized) and len(normalized) >= 5,
          len(normalized))
    check("标题解析出预警类型", normalized[0]["type"] in ("大雾", "寒潮", "道路结冰"),
          normalized[0]["type"])
    check("标题解析出预警等级", normalized[0]["level"] in
          ("蓝色", "黄色", "橙色", "红色"), normalized[0]["level"])
    check("等级颜色为 ARGB", normalized[0]["level_color"].startswith("FF"))
    mixed = [dict(normalized[0], title="x", issue_time="t"),
             dict(normalized[0], title="x", issue_time="t"),
             dict(normalized[0], title="y", issue_time="t", level_rank=3,
                  level="红色", level_key="red")]
    prepared = alerts.prepare(mixed, min_rank=2, limit=10)
    check("去重 + 等级过滤（橙色及以上）",
          len(prepared) == 1 and prepared[0]["level"] == "红色",
          [(a["level"], a["title"]) for a in prepared])

    print("\n=== 6. 图标 / 输出规则 / 皮肤属性 ===")
    check("d02 -> 阴", icons.from_code("d02")["key"] == "overcast",
          icons.from_code("d02")["zh"])
    check("7 -> 小雨", icons.from_code("7")["key"] == "light_rain",
          icons.from_code("7")["zh"])
    check("'阴转多云' 取最早现象", icons.from_text("阴转多云")["key"] == "overcast",
          icons.from_text("阴转多云")["zh"])
    check("9999 回退 unknown", icons.resolve("9999", "")["key"] == "unknown")
    check("图标文件存在", os.path.isfile(icons.icon_path("sunny")))
    check("预警图标文件存在", os.path.isfile(icons.alert_icon("red")))
    check("温度 °C 格式", config.format_temp(7.8) == "7.8°C",
          config.format_temp(7.8))
    SETTINGS["temp_unit"] = "1"
    check("温度 °F 换算", config.format_temp(0) == "32°F", config.format_temp(0))
    SETTINGS["temp_unit"] = "0"
    check("缺失值统一显示 —", config.format_temp(None) == "—")
    merged = merge(nmc_result, wcn_result)
    check("双源合并后预报 >= 7 天", len(merged["forecast"]) >= 7,
          len(merged["forecast"]))
    check("双源合并后 AQI 有值（主源优先）",
          merged["current"]["aqi"] is not None, merged["current"]["aqi"])
    check("双源来源标记为 mixed", merged["source_list"] == ["nmc", "wcn"],
          merged["source_list"])
    windowprops.publish(nmc_result)
    check("皮肤属性 Current.Temperature 已写入",
          "Current.Temperature" in PROPERTIES,
          PROPERTIES.get("Current.Temperature"))
    check("皮肤属性 Day0.Title=今天", PROPERTIES.get("Day0.Title") == "今天",
          PROPERTIES.get("Day0.Title"))

    print("\n=== 6b. Kodi 天气服务（xbmc.python.weather） ===")
    addon_tree = ET.parse(os.path.join(ROOT, "addon.xml")).getroot()
    points = [e.get("point") for e in addon_tree.findall("extension")]
    check("addon.xml 注册 xbmc.python.weather",
          "xbmc.python.weather" in points, points)
    check("weather 为首个扩展点（决定插件进入「天气」分类）",
          bool(points) and points[0] == "xbmc.python.weather", points[:3])
    weather_ext = [e for e in addon_tree.findall("extension")
                   if e.get("point") == "xbmc.python.weather"]
    check("天气入口与插件入口共用 default.py",
          bool(weather_ext) and weather_ext[0].get("library") == "default.py")
    with io.open(os.path.join(ROOT, "default.py"), "r", encoding="utf-8") as fp:
        entry_source = fp.read()
    check("default.py 能区分 plugin:// 与 RunScript",
          'startswith("plugin://")' in entry_source and
          "weatherprovider" in entry_source)
    check("冗余 weather.py 已移除",
          not os.path.isfile(os.path.join(ROOT, "weather.py")))
    settings_tree = ET.parse(os.path.join(ROOT, "resources", "settings.xml")).getroot()
    setting_ids = [s.get("id") for s in settings_tree.iter("setting")]
    check("settings.xml 含 location1..3 按钮",
          all("location%d" % i in setting_ids for i in (1, 2, 3)))
    action_data = [d.text for d in settings_tree.iter("data")]
    check("地点按钮 action 为紧凑单行 RunScript",
          len(action_data) == 3 and
          all(d and d == d.strip() and d.startswith("RunScript(")
              for d in action_data), action_data)
    check("地点设置字符串已中英本地化",
          "32181" in PO_ZH and "32188" in PO_EN and
          "32190" in PO_ZH and "32191" in PO_EN)
    check("settings.xml 含 3 个手动输入备用框",
          all("location%d_name" % i in setting_ids for i in (1, 2, 3)))

    PROPERTIES.clear()
    SETTINGS["location1"] = "北京"
    SETTINGS["location2"] = ""
    SETTINGS["location3"] = ""
    windowprops.publish_weather(nmc_result, 1)
    check("天气窗口 Current.Temperature 为纯数字（供 Kodi 换算单位）",
          PROPERTIES.get("Current.Temperature", "").lstrip("-").isdigit(),
          PROPERTIES.get("Current.Temperature"))
    check("天气窗口 Current.OutlookIcon 为 Kodi 图标文件名",
          bool(re.match(r"^(\d+|na)\.png$",
                        PROPERTIES.get("Current.OutlookIcon", ""))),
          PROPERTIES.get("Current.OutlookIcon"))
    check("天气窗口 Daily.1.ShortDay=今天",
          PROPERTIES.get("Daily.1.ShortDay") == "今天",
          PROPERTIES.get("Daily.1.ShortDay"))
    check("天气窗口 Day0.HighTemp 为纯数字",
          PROPERTIES.get("Day0.HighTemp", "").lstrip("-").isdigit(),
          PROPERTIES.get("Day0.HighTemp"))
    check("天气窗口 Locations=1 / Location1=北京",
          PROPERTIES.get("Locations") == "1" and
          PROPERTIES.get("Location1") == "北京",
          (PROPERTIES.get("Locations"), PROPERTIES.get("Location1")))
    check("天气窗口 IsFetched 标记已写入",
          PROPERTIES.get("Weather.IsFetched") == "true" and
          PROPERTIES.get("Current.IsFetched") == "true")
    check("Kodi 条件代码映射",
          windowprops.kodi_code("sunny") == 32 and
          windowprops.kodi_code("unknown") == "na")
    check("风速 m/s → km/h", windowprops._wind_kmh({"wind_speed": 10}) == "36")

    from lib import weatherprovider
    SETTINGS["location1"] = ""
    SETTINGS["location1_name"] = "石家庄"
    SETTINGS["location1_nmc"] = ""
    count = windowprops.publish_locations()
    check("手动输入地点也能登记到天气窗口",
          count == 1 and PROPERTIES.get("Location1") == "石家庄",
          (count, PROPERTIES.get("Location1")))
    loc = weatherprovider._location(1)
    check("手填中文城市名自动解析气象站点编码",
          bool(loc.get("nmc_code")) and loc.get("name") == "石家庄", loc)
    SETTINGS["location1"] = "北京"
    SETTINGS["location1_name"] = ""

    if online:
        print("\n=== 7. 真实接口端到端（--online） ===")
        try:
            result = WeatherService().fetch_all(force=True)
            check("真实接口返回 ok", result["ok"], result["errors"])
            check("实况温度非空", result["current"]["temp"] is not None,
                  result["current"]["temp"])
            check("预报 7 天", len(result["forecast"]) == 7,
                  len(result["forecast"]))
            check("预警列表可用", isinstance(result["alerts"], list),
                  len(result["alerts"]))
            national, meta = WeatherService().national_alerts(force=True)
            check("全国预警抓取成功", len(national) > 0, len(national))
        except Exception as exc:  # noqa: BLE001
            check("真实接口端到端", False, repr(exc))

    sys.argv = old_argv
    passed = sum(1 for _n, ok, _d in RESULTS if ok)
    failed = len(RESULTS) - passed
    print("\n=== 汇总：%d 通过 / %d 失败 / 共 %d 项 ===" %
          (passed, failed, len(RESULTS)))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
