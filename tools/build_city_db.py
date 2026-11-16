# -*- coding: utf-8 -*-
"""
tools/build_city_db.py — 生成插件内置的全国城市索引。

数据来源（均为公开、无需 API Key 的接口/页面）：
  1. 中央气象台 nmc.cn
     GET /rest/province            -> 省级列表
     GET /rest/province/{code}     -> 该省全部站点（code 为站点 ID）
  2. 中国天气网 weather.com.cn
     GET /textFC/hb.shtml          -> 全国省份页面索引
     GET /textFC/{prov}.shtml      -> 该省全部城市（9 位城市代码）

输出：
  resources/data/cities_nmc.json
  resources/data/cities_weathercn.json

本脚本仅在开发/维护时运行，插件运行时不依赖它。
"""
from __future__ import print_function

import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
NMC = "http://www.nmc.cn"
WCN = "http://www.weather.com.cn"


def fetch(url, referer=None, timeout=25, retries=2):
    headers = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "zh-CN,zh;q=0.9"}
    if referer:
        headers["Referer"] = referer
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            # 所有目标接口/页面均为 UTF-8，统一按 UTF-8 解码，避免中文乱码
            return raw.decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.6 * (attempt + 1))
    print("  ! FAIL %s -> %s" % (url, last), file=sys.stderr)
    return ""


def build_nmc():
    print("[1/2] 中央气象台 nmc.cn ...")
    raw = fetch(NMC + "/rest/province", NMC + "/")
    provinces = json.loads(raw)
    print("  省级行政区: %d" % len(provinces))

    def one(prov):
        txt = fetch(NMC + "/rest/province/" + prov["code"], NMC + "/")
        try:
            stations = json.loads(txt)
        except Exception:  # noqa: BLE001
            stations = []
        out = []
        for st in stations:
            if not isinstance(st, dict) or not st.get("code"):
                continue
            out.append({
                "code": st["code"],
                "city": st.get("city", "").strip(),
                "province": st.get("province", prov["name"]).strip(),
                "province_code": prov["code"],
            })
        return prov["name"], out

    result = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(one, p) for p in provinces]
        for fut in as_completed(futures):
            name, rows = fut.result()
            print("  %-8s %4d 站点" % (name, len(rows)))
            result.extend(rows)

    # 去重（同一站点可能被多个接口返回）
    seen = set()
    uniq = []
    for row in result:
        if row["code"] in seen:
            continue
        seen.add(row["code"])
        uniq.append(row)
    uniq.sort(key=lambda r: (r["province"], r["city"]))
    print("  合计 %d 个站点" % len(uniq))
    return uniq


def build_weathercn():
    print("[2/2] 中国天气网 weather.com.cn ...")
    # 9 位城市代码前 5 位 = 省级行政区代码，用它归一化省份名，
    # 避免区域汇总页（东北/华东/港澳台…）把省份字段污染成区域名。
    prov_raw = fetch(WCN + "/data/city3jdata/china.html", WCN + "/")
    try:
        prov_map = json.loads(prov_raw)
    except Exception:  # noqa: BLE001
        print("  ! 省码表获取失败，省份字段留空", file=sys.stderr)
        prov_map = {}
    print("  省级码表: %d 条" % len(prov_map))

    index = fetch(WCN + "/textFC/hb.shtml", WCN + "/")
    slugs = sorted(set(re.findall(r"/textFC/([a-z0-9_-]+)\.shtml", index)))
    slugs = [s for s in slugs if s not in ("hb", "index")]
    print("  待抓取页面: %d" % len(slugs))

    def one(slug):
        url = "%s/textFC/%s.shtml" % (WCN, slug)
        page = fetch(url, WCN + "/textFC/hb.shtml")
        if not page:
            return []
        # 表格中形如 <a href="http://www.weather.com.cn/weather/101090101.shtml" target="_blank">石家庄</a>
        pairs = re.findall(
            r"weather(?:1d)?/(\d{9})\.shtml\"[^>]*>([^<]{1,20})</a>", page)
        rows = []
        for code, city in pairs:
            city = city.strip()
            prefix = code[:5]
            if not city or prefix not in prov_map:
                continue
            rows.append({"code": code, "city": city,
                         "province": prov_map[prefix]})
        return rows

    result = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(one, s) for s in slugs]
        for fut in as_completed(futures):
            result.extend(fut.result())

    seen = set()
    uniq = []
    for row in result:
        if row["code"] in seen:
            continue
        seen.add(row["code"])
        uniq.append(row)
    uniq.sort(key=lambda r: (r["province"], r["city"]))
    print("  合计 %d 个城市代码（已按省级码表归一化）" % len(uniq))
    return uniq


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "resources/data"
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    for name, builder in (("cities_nmc.json", build_nmc),
                          ("cities_weathercn.json", build_weathercn)):
        try:
            rows = builder()
        except Exception as exc:  # noqa: BLE001
            print("  ! %s 生成失败: %s" % (name, exc), file=sys.stderr)
            continue
        if not rows:
            print("  ! %s 无数据，跳过写入" % name, file=sys.stderr)
            continue
        path = os.path.join(out_dir, name)
        payload = {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(rows),
            "items": rows,
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, separators=(",", ":"))
        print("  写入 %s (%d 字节)" % (path, os.path.getsize(path)))


if __name__ == "__main__":
    main()
