# -*- coding: utf-8 -*-
"""
tools/gen_language.py — 由单一字符串表生成 Kodi strings.po 中/英文语言文件。

Kodi 通过 resources/language/resource.language.<lang>/strings.po 加载界面文本，
代码里统一用 ADDON.getLocalizedString(32xxx) 取词。用本脚本生成可保证
两种语言的 msgctxt 编号完全一致，不会出现「设置项找不到翻译」的情况。

用法： python tools/gen_language.py
"""
from __future__ import unicode_literals

import os

# id: (简体中文, English)
STRINGS = {
    # ---- settings.xml：分类 / 分组 ----
    32000: ("常规", "General"),
    32001: ("城市与显示", "Location & Display"),
    32002: ("数据源", "Data Sources"),
    32003: ("气象预警", "Weather Alerts"),
    32004: ("高级", "Advanced"),
    # ---- settings.xml：常规 ----
    32010: ("当前城市", "Current city"),
    32011: ("在插件菜单中使用「切换城市」可中文搜索并切换；此处可查看或直接填写中文城市名。",
            "Use 'Change city' in the add-on menu to search in Chinese. You may also type a Chinese city name here."),
    32012: ("中央气象台站点 ID", "NMC station ID"),
    32013: ("由「切换城市」自动写入，对应 nmc.cn/rest/weather 的 stationid 参数。",
            "Written automatically by 'Change city'; maps to the stationid parameter of nmc.cn/rest/weather."),
    32014: ("中国天气网 9 位城市码", "weather.com.cn city code"),
    32015: ("留空表示禁用中国天气网备用数据源。", "Leave empty to disable the weather.com.cn fallback source."),
    32016: ("温度单位", "Temperature unit"),
    32017: ("摄氏度 °C", "Celsius °C"),
    32018: ("华氏度 °F", "Fahrenheit °F"),
    32019: ("预报天数", "Forecast days"),
    32020: ("3 天", "3 days"),
    32021: ("5 天", "5 days"),
    32022: ("7 天", "7 days"),
    # ---- settings.xml：数据源 ----
    32023: ("主数据源", "Primary source"),
    32024: ("自动（失败自动切换备用源）", "Auto (fallback on failure)"),
    32025: ("仅中央气象台", "NMC only"),
    32026: ("仅中国天气网", "weather.com.cn only"),
    32027: ("网络超时（秒）", "Network timeout (sec)"),
    32028: ("缓存有效期（分钟）", "Cache TTL (min)"),
    32029: ("启用中国天气网补充数据", "Enable weather.com.cn supplement"),
    32030: ("补充实况 AQI、生活指数、5~7 天预报与预警详情；关闭后只用中央气象台。",
            "Adds AQI, life indices, 5-7 day forecast and alert details. Turn off to use NMC only."),
    # ---- settings.xml：预警 ----
    32031: ("启用气象预警", "Enable weather alerts"),
    32032: ("预警范围", "Alert scope"),
    32033: ("仅当前城市", "Current city only"),
    32034: ("全国预警", "Nationwide"),
    32035: ("当前城市 + 全国", "Current city + Nationwide"),
    32036: ("最低显示等级", "Minimum severity"),
    32037: ("全部（含蓝色）", "All (incl. Blue)"),
    32038: ("黄色及以上", "Yellow and above"),
    32039: ("橙色及以上", "Orange and above"),
    32040: ("仅红色", "Red only"),
    32041: ("全国预警最大条数", "Max nationwide alerts"),
    # ---- settings.xml：高级 ----
    32042: ("写入皮肤天气属性", "Publish skin window properties"),
    32043: ("供支持天气部件的皮肤读取 Current.* / Day0.* 等 Window Properties。",
            "Allows skins with weather widgets to read Current.* / Day0.* window properties."),
    32044: ("后台刷新间隔（分钟）", "Background refresh (min)"),
    32045: ("调试日志", "Debug logging"),
    32046: ("把接口请求、缓存命中与解析结果写入 kodi.log，排查问题时开启。",
            "Write requests, cache hits and parse results to kodi.log for troubleshooting."),
    # ---- 主菜单 ----
    32100: ("实时天气", "Current conditions"),
    32101: ("未来多日预报", "Multi-day forecast"),
    32102: ("气象预警", "Weather alerts"),
    32103: ("切换城市", "Change city"),
    32104: ("中文城市搜索", "Search Chinese city"),
    32105: ("全国预警", "Nationwide alerts"),
    32106: ("刷新城市索引", "Refresh city index"),
    32107: ("设置", "Settings"),
    32108: ("暂无数据", "No data"),
    32109: ("数据获取失败", "Failed to fetch data"),
    32110: ("刷新", "Refresh"),
    32111: ("输入城市中文名（如 北京 / 石家庄 / 朝阳）", "Enter a Chinese city name (e.g. 北京 / 石家庄)"),
    32112: ("搜索结果", "Search results"),
    32113: ("未找到匹配城市，请尝试更简短的关键词", "No matching city, try a shorter keyword"),
    32114: ("已切换到：{0}", "Switched to: {0}"),
    32115: ("城市索引已更新，共 {0} 个站点", "City index updated: {0} stations"),
    32116: ("城市索引更新失败，继续使用内置索引", "City index update failed, using bundled index"),
    32117: ("今天", "Today"),
    32118: ("明天", "Tomorrow"),
    32119: ("后天", "Day after tomorrow"),
    32120: ("白天", "Day"),
    32121: ("夜间", "Night"),
    32122: ("温度", "Temperature"),
    32123: ("体感温度", "Feels like"),
    32124: ("相对湿度", "Humidity"),
    32125: ("气压", "Pressure"),
    32126: ("降水量", "Precipitation"),
    32127: ("风向", "Wind direction"),
    32128: ("风力", "Wind force"),
    32129: ("风速", "Wind speed"),
    32130: ("能见度", "Visibility"),
    32131: ("空气质量 AQI", "Air quality (AQI)"),
    32132: ("PM2.5", "PM2.5"),
    32133: ("日出", "Sunrise"),
    32134: ("日落", "Sunset"),
    32135: ("更新时间", "Updated at"),
    32136: ("数据来源", "Data source"),
    32137: ("未知", "Unknown"),
    32138: ("无", "None"),
    32139: ("当前无生效预警", "No active alerts"),
    32140: ("预警详情", "Alert details"),
    32141: ("发布单位", "Issued by"),
    32142: ("预警类型", "Alert type"),
    32143: ("预警等级", "Severity level"),
    32144: ("发布时间", "Issue time"),
    32145: ("蓝色预警", "Blue alert"),
    32146: ("黄色预警", "Yellow alert"),
    32147: ("橙色预警", "Orange alert"),
    32148: ("红色预警", "Red alert"),
    32149: ("未知等级", "Unknown level"),
    32150: ("中央气象台", "NMC / CMA"),
    32151: ("中国天气网", "China Weather Network"),
    32152: ("（缓存数据）", "(cached)"),
    32153: ("（离线缓存，可能已过期）", "(offline cache, may be stale)"),
    32154: ("最高 / 最低气温", "High / Low"),
    32155: ("生活指数", "Life indices"),
    32156: ("未来 {0} 天预报", "{0}-day forecast"),
    32157: ("共 {0} 条预警", "{0} alert(s)"),
    32158: ("查看详情", "View details"),
    32159: ("当前城市", "Current city"),
    32160: ("热门城市", "Popular cities"),
    32161: ("所属：{0}", "Region: {0}"),
    32162: ("站点：{0}", "Station: {0}"),
    32163: ("确定", "OK"),
    32164: ("取消", "Cancel"),
    32165: ("错误", "Error"),
    32166: ("提示", "Information"),
    32167: ("尚未配置城市，请先使用「切换城市」", "No city configured, please use 'Change city' first"),
    32168: ("刷新完成", "Refresh completed"),
    32169: ("本地预警", "Local alerts"),
    32170: ("天气现象", "Condition"),
    32171: ("预警全文", "Full alert text"),
    32172: ("国家预警信息发布中心 / 中央气象台", "National Early Warning Center / NMC"),
    32173: ("数据为 UTF-8 中文，若出现乱码请检查系统语言与字体", "Data is UTF-8 Chinese; check Kodi language and fonts if you see mojibake"),
    32174: ("白色 / 蓝色 / 黄色 / 橙色 / 红色", "White / Blue / Yellow / Orange / Red"),
    32175: ("点击查看预警全文", "Select to read the full alert text"),
    32176: ("（来自 {0}）", "(from {0})"),
    32177: ("离线数据", "Offline data"),
    32178: ("已定位城市", "Located city"),
    32180: ("中国天气", "China Weather"),
    # ---- 星期 ----
    32200: ("星期一", "Monday"),
    32201: ("星期二", "Tuesday"),
    32202: ("星期三", "Wednesday"),
    32203: ("星期四", "Thursday"),
    32204: ("星期五", "Friday"),
    32205: ("星期六", "Saturday"),
    32206: ("星期日", "Sunday"),
}

HEADER = '''# Kodi Media Center language file
# Addon Name: 中国天气 China Weather
# Addon id: plugin.weather.china
# Generated by tools/gen_language.py -- DO NOT EDIT MANUALLY
msgid ""
msgstr ""
"Project-Id-Version: plugin.weather.china\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2026-11-16 00:00+0800\\n"
"PO-Revision-Date: 2026-11-16 00:00+0800\\n"
"Last-Translator: RenJunJie2003\\n"
"Language-Team: {team}\\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"
'''


def esc(text):
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render(index):
    """index=0 -> 中文 msgstr, index=1 -> 英文 msgstr"""
    lang = "zh_cn" if index == 0 else "en_gb"
    team = "Chinese (Simplified)" if index == 0 else "English (United Kingdom)"
    lines = [HEADER.format(team=team, lang=lang)]
    for sid in sorted(STRINGS):
        zh, en = STRINGS[sid]
        lines.append('\nmsgctxt "#%d"\nmsgid "%s"\nmsgstr "%s"\n'
                     % (sid, esc(en), esc(zh if index == 0 else en)))
    return "".join(lines)


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    targets = [
        (os.path.join(root, "resources", "language", "resource.language.zh_cn", "strings.po"), 0),
        (os.path.join(root, "resources", "language", "resource.language.en_gb", "strings.po"), 1),
    ]
    for path, idx in targets:
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(render(idx))
        print("生成 %s (%d 条)" % (path, len(STRINGS)))


if __name__ == "__main__":
    main()
