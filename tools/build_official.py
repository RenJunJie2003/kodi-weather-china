# -*- coding: utf-8 -*-
"""生成提交给 Kodi 官方 repo-plugins 的纯运行时插件目录。

只保留运行所需文件，剔除 docs/ tools/ tests/ assets/ dist/ 等开发内容，
统一 UNIX 行尾、无 BOM、文件名全小写。审核往返修改后重新运行本脚本即可。

用法： python tools/build_official.py
输出： ../_official/plugin.weather.china/
"""
from __future__ import unicode_literals

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
DST = os.path.join(os.path.dirname(SRC), "_official", "plugin.weather.china")

TOP_FILES = [
    "addon.xml", "default.py", "service.py", "LICENSE.txt",
    "changelog.txt", "icon.png", "fanart.jpg",
]

README = """# China Weather for Kodi

A Kodi weather add-on for China, powered by the public endpoints of the
China National Meteorological Center (`nmc.cn`) and China Weather Network
(`weather.com.cn`). No API key or registration is required.

## Features

- Current conditions: temperature, feels-like, humidity, pressure, rain,
  wind, visibility, AQI/PM2.5, sunrise/sunset.
- 3 / 5 / 7 day forecast with day and night conditions, high/low, wind.
- Chinese city search and switching, with a bundled index of 2529 NMC
  stations and 3230 weather.com.cn city codes.
- Official CMA severe-weather alerts, including alert type and
  White / Blue / Yellow / Orange / Red severity, full alert text and a
  nationwide alert list.
- 30 life indices, UTF-8 Chinese UI, English and Simplified Chinese
  `strings.po` localisation, and Kodi skin Window Properties.
- Two-source failover with file caching and stale-cache fallback.

## Requirements

Kodi 19 (Matrix) or newer (Python 3). Set the Kodi language to
Chinese (Simplified) for the Chinese UI; English is available as well.

## Source and documentation

Full source, design notes, data-source analysis, offline tests and build
tools: https://github.com/RenJunJie2003/kodi-weather-china

## License

GPL-3.0. See `LICENSE.txt`. Weather data is provided by public endpoints
for personal reference only; always follow official issuances for
safety-critical decisions.
"""

CHANGELOG = """[B]1.0.1[/B] - 2026-11-16
- Fix: weather location buttons did nothing (unified plugin/weather entry point)
- Add: manual Chinese city-name input for each location, station codes resolved automatically
- Add: background service also publishes Kodi weather window (12600) properties
- Add: logging and exception handling for weather provider calls

[B]1.0.0[/B] - 2026-11-16
- Initial release
- Current conditions: temperature, feels-like, humidity, pressure, rain, wind, visibility, AQI/PM2.5, sunrise/sunset
- 3/5/7 day forecast with day/night conditions, high/low temperatures, wind and precipitation
- Chinese city search and switching: 2529 NMC stations + 3230 weather.com.cn city codes
- CMA severe-weather alerts: type, Blue/Yellow/Orange/Red severity, colour coding, filtering, full text, nationwide list
- 30 life indices
- Two-source failover (nmc.cn / weather.com.cn), file cache and stale-cache fallback
- UTF-8 Chinese UI with English and Simplified Chinese strings.po localisation (129 strings)
- 20 condition icons, 5 alert-level icons, icon.png and fanart.jpg
- Background service publishing Kodi weather Window Properties
"""


def copy_file(rel, dest_rel=None):
    src = os.path.join(SRC, rel)
    dst = os.path.join(DST, dest_rel or rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)


def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)

    for f in TOP_FILES:
        copy_file(f)

    for sub in ("resources/data", "resources/lib", "resources/media",
                "resources/language/resource.language.zh_cn",
                "resources/language/resource.language.en_gb"):
        base = os.path.join(SRC, sub)
        for name in sorted(os.listdir(base)):
            p = os.path.join(base, name)
            if not os.path.isfile(p):
                continue
            if name.endswith((".pyc", ".pyo")) or name.startswith("."):
                continue
            copy_file(os.path.join(sub, name).replace("\\", "/"))
    copy_file("resources/settings.xml")

    with open(os.path.join(DST, "README.md"), "w", encoding="utf-8", newline="\n") as fp:
        fp.write(README)
    with open(os.path.join(DST, "changelog.txt"), "w", encoding="utf-8", newline="\n") as fp:
        fp.write(CHANGELOG)

    fixed = 0
    for base, dirs, files in os.walk(DST):
        for name in files:
            p = os.path.join(base, name)
            raw = open(p, "rb").read()
            if name.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            out = raw.replace(b"\r\n", b"\n")
            if out.startswith(b"\xef\xbb\xbf"):
                out = out[3:]
            if out != raw:
                open(p, "wb").write(out)
                fixed += 1

    total = sum(len(fs) for _, _, fs in os.walk(DST))
    size = sum(os.path.getsize(os.path.join(b, f))
               for b, _, fs in os.walk(DST) for f in fs)
    print("生成完成：%s" % DST)
    print("  文件 %d 个 / %.1f KB / 规范化文本 %d 个" %
          (total, size / 1024.0, fixed))
    print("  请再运行：python -m kodi_addon_checker --branch matrix --PR "
          "--skip-dependency-checks --reporter console \"%s\"" % DST)


if __name__ == "__main__":
    main()
