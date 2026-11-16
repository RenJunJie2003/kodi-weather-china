# -*- coding: utf-8 -*-
"""
tools/make_release.py — 生成可直接用 Kodi「从 zip 文件安装」的分发包。

产物：dist/plugin.weather.china-<version>.zip
zip 内顶层目录必须是 addon id（plugin.weather.china/），
且 addon.xml 位于该目录根部 —— 这是 Kodi 识别插件的硬性要求。

用法： python tools/make_release.py
"""
from __future__ import unicode_literals

import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")

TOP_FILES = ["addon.xml", "default.py", "service.py", "icon.png",
             "fanart.jpg", "LICENSE.txt", "changelog.txt"]
TOP_DIRS = ["resources"]
SKIP_DIRS = {"__pycache__", ".git", ".idea"}
SKIP_EXTS = {".pyc", ".pyo", ".tmp"}


def main():
    # 从纯文本仓库 clone 时自动还原二进制图标
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        from restore_assets import assets_missing, restore
        if assets_missing():
            restore(verbose=True)
    except Exception:  # noqa: BLE001
        pass

    addon_xml = ET.parse(os.path.join(ROOT, "addon.xml")).getroot()
    addon_id = addon_xml.get("id")
    version = addon_xml.get("version")
    if not addon_id or not version:
        raise SystemExit("addon.xml 缺少 id 或 version")

    if not os.path.isdir(DIST):
        os.makedirs(DIST)

    staging = tempfile.mkdtemp(prefix="kodi-release-")
    target = os.path.join(staging, addon_id)
    os.makedirs(target)

    for name in TOP_FILES:
        src = os.path.join(ROOT, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(target, name))
        else:
            print("  ! 缺少文件 %s" % name)

    for name in TOP_DIRS:
        src = os.path.join(ROOT, name)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(target, name),
                            ignore=shutil.ignore_patterns(
                                "__pycache__", "*.pyc", "*.pyo", "*.tmp"))

    # 清理可能残留的缓存目录
    for base, dirs, files in os.walk(target):
        for dirname in list(dirs):
            if dirname in SKIP_DIRS:
                shutil.rmtree(os.path.join(base, dirname), ignore_errors=True)
                dirs.remove(dirname)
        for filename in files:
            if os.path.splitext(filename)[1] in SKIP_EXTS:
                os.remove(os.path.join(base, filename))

    zip_path = os.path.join(DIST, "%s-%s.zip" % (addon_id, version))
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for base, _dirs, files in os.walk(target):
            for filename in sorted(files):
                full = os.path.join(base, filename)
                arcname = os.path.join(addon_id,
                                       os.path.relpath(full, target)).replace("\\", "/")
                bundle.write(full, arcname)
                count += 1

    print("打包完成：%s" % zip_path)
    print("  插件目录：%s/" % addon_id)
    print("  文件数：%d，大小：%.1f KB" % (count, os.path.getsize(zip_path) / 1024.0))
    with zipfile.ZipFile(zip_path) as bundle:
        names = bundle.namelist()
    print("  顶层校验：%s" % ("通过" if any(n == addon_id + "/addon.xml"
                                           for n in names) else "失败"))
    print("  关键文件：")
    for needle in ("addon.xml", "default.py", "resources/settings.xml",
                   "resources/language/resource.language.zh_cn/strings.po",
                   "resources/data/cities_nmc.json", "icon.png"):
        print("    %s %s" % ("OK " if any(n.endswith(needle) for n in names)
                              else "MISS", needle))
    shutil.rmtree(staging, ignore_errors=True)
    return zip_path


if __name__ == "__main__":
    main()
