# -*- coding: utf-8 -*-
"""
tools/restore_assets.py — 从 assets/binary_assets.json 还原二进制资源。

从 GitHub clone 后，仓库里只有纯文本；运行本脚本即可还原
icon.png / fanart.jpg / resources/media/*.png，然后可直接打包或安装。

    python tools/restore_assets.py
    python tools/make_release.py      # 生成 dist/*.zip

make_release.py / selftest.py 会在检测到图标缺失时自动调用本模块。
用法： python tools/restore_assets.py [--force]
"""
from __future__ import unicode_literals

import base64
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "assets", "binary_assets.json")


def assets_missing():
    return not (os.path.isfile(os.path.join(ROOT, "icon.png")) and
                os.path.isfile(os.path.join(ROOT, "resources", "media", "sunny.png")))


def restore(force=False, verbose=True):
    if not os.path.isfile(MANIFEST):
        if verbose:
            print("  ! 找不到 assets/binary_assets.json，跳过资源还原")
        return 0
    with open(MANIFEST, "r", encoding="utf-8") as fp:
        payload = json.load(fp)
    count = 0
    for relative, encoded in payload.get("files", {}).items():
        path = os.path.join(ROOT, relative.replace("/", os.sep))
        if os.path.isfile(path) and not force:
            continue
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(path, "wb") as fp:
            fp.write(base64.b64decode(encoded))
        count += 1
    if verbose:
        print("  还原 %d 个二进制资源（共 %d 个已登记）"
              % (count, payload.get("count", 0)))
    return count


if __name__ == "__main__":
    restore(force="--force" in sys.argv)
