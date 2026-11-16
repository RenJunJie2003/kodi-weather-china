# -*- coding: utf-8 -*-
"""
tools/pack_assets.py — 把二进制资源（PNG/JPG）打包成纯文本 base64 清单。

用途：通过只支持文本内容的 API（例如 GitHub Contents API / MCP）上传仓库时，
二进制文件无法直接提交。本脚本把它们编码成 assets/binary_assets.json，
仓库端配合 tools/restore_assets.py 即可 100% 还原。

维护：改动图标后运行本脚本重新生成清单，再提交 json。
用法： python tools/pack_assets.py
"""
from __future__ import unicode_literals

import base64
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "binary_assets.json")

FILES = ["icon.png", "fanart.jpg"]
MEDIA = os.path.join(ROOT, "resources", "media")


def main():
    items = {}
    for name in FILES:
        path = os.path.join(ROOT, name)
        if os.path.isfile(path):
            with open(path, "rb") as fp:
                items[name.replace("\\", "/")] = base64.b64encode(fp.read()).decode("ascii")
    for name in sorted(os.listdir(MEDIA)):
        if not name.lower().endswith(".png"):
            continue
        with open(os.path.join(MEDIA, name), "rb") as fp:
            items["resources/media/" + name] = base64.b64encode(fp.read()).decode("ascii")
    if not os.path.isdir(os.path.dirname(OUT)):
        os.makedirs(os.path.dirname(OUT))
    with open(OUT, "w", encoding="utf-8", newline="\n") as fp:
        json.dump({"version": 1, "count": len(items), "files": items},
                  fp, ensure_ascii=True, separators=(",", ":"))
    total = sum(len(v) * 3 // 4 for v in items.values())
    print("打包 %d 个二进制文件，原始约 %.1f KB，清单 %.1f KB -> %s"
          % (len(items), total / 1024.0, os.path.getsize(OUT) / 1024.0, OUT))


if __name__ == "__main__":
    main()
