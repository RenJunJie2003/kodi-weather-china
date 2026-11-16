# -*- coding: utf-8 -*-
"""
lib/windowprops.py — 把标准天气结构写入 Kodi 皮肤可读取的 Window Properties。

Kodi 的天气部件读取 Home Window(10000) 上的属性。本模块按官方约定写出
  Weather.Location / Weather.IsFetched
  Current.Temperature / Current.Condition / Current.ConditionIcon / ...
  Day0.Title / Day0.HighTemp / Day0.LowTemp / Day0.Outlook / Day0.OutlookIcon ...
  Weather.AlertCount / Weather.Alert1.Title / ...
这样即使不使用本插件的菜单，支持天气的皮肤也能显示中国天气数据。

由 service.py 定时调用；也可在插件菜单刷新时即时调用。
"""
from __future__ import unicode_literals

import datetime

import xbmcgui

from . import config


def weekday_label(date_str, index):
    if index == 0:
        return config.L(32117)
    if index == 1:
        return config.L(32118)
    if index == 2:
        return config.L(32119)
    try:
        date = datetime.date.fromisoformat(date_str)
        return config.L(32200 + date.weekday())
    except (ValueError, TypeError):
        return ""


def publish(result):
    if not config.get_bool("skin_props", True):
        return False
    try:
        window = xbmcgui.Window(10000)
    except Exception:  # noqa: BLE001
        return False

    location = result.get("location") or {}
    current = result.get("current") or {}
    forecast = result.get("forecast") or []
    alert_list = result.get("alerts") or []

    window.setProperty("Weather.Location", str(location.get("name", "")))
    window.setProperty("Weather.IsFetched", "true" if result.get("ok") else "false")
    window.setProperty("Weather.Provider", config.L(32180))
    window.setProperty("Weather.Source", str(result.get("source", "")))
    window.setProperty("Weather.Updated", str(result.get("updated", "")))

    window.setProperty("Current.Temperature", config.format_temp(current.get("temp")))
    window.setProperty("Current.FeelsLike", config.format_temp(current.get("feels_like")))
    window.setProperty("Current.Condition", str(current.get("condition") or config.DASH))
    window.setProperty("Current.ConditionIcon", str(current.get("condition_icon") or ""))
    window.setProperty("Current.OutlookIcon", str(current.get("condition_icon") or ""))
    window.setProperty("Current.Humidity", config.format_value(current.get("humidity"), "%"))
    window.setProperty("Current.Pressure", config.format_value(current.get("pressure")))
    window.setProperty("Current.Precipitation", config.format_value(current.get("rain"), " mm"))
    window.setProperty("Current.Wind", str(current.get("wind_power") or config.DASH))
    window.setProperty("Current.WindDirection", str(current.get("wind_dir") or config.DASH))
    window.setProperty("Current.WindSpeed", config.format_value(current.get("wind_speed")))
    window.setProperty("Current.Visibility", config.format_value(current.get("visibility")))
    window.setProperty("Current.UVIndex", config.DASH)
    window.setProperty("Current.DewPoint", config.DASH)
    window.setProperty("Current.AQI", config.format_value(current.get("aqi")))
    window.setProperty("Current.PM25", config.format_value(current.get("pm25")))
    window.setProperty("Current.Sunrise", str(current.get("sunrise") or config.DASH))
    window.setProperty("Current.Sunset", str(current.get("sunset") or config.DASH))
    window.setProperty("Current.FanartCode", str(current.get("condition_key") or "unknown"))

    for index, day in enumerate(forecast[:7]):
        prefix = "Day%d." % index
        title = weekday_label(day.get("date", ""), index) or str(day.get("date", ""))
        window.setProperty(prefix + "Title", title)
        window.setProperty(prefix + "Date", str(day.get("date", "")))
        window.setProperty(prefix + "HighTemp", config.format_temp(day.get("high")))
        window.setProperty(prefix + "LowTemp", config.format_temp(day.get("low")))
        condition = (day.get("day") or {}).get("condition") or \
                    (day.get("night") or {}).get("condition") or config.DASH
        icon = (day.get("day") or {}).get("icon") or ""
        key = (day.get("day") or {}).get("key") or "unknown"
        window.setProperty(prefix + "Outlook", str(condition))
        window.setProperty(prefix + "Condition", str(condition))
        window.setProperty(prefix + "OutlookIcon", str(icon))
        window.setProperty(prefix + "FanartCode", str(key))
        window.setProperty(prefix + "Wind", str((day.get("day") or {}).get("wind_power") or config.DASH))
        window.setProperty(prefix + "Precipitation",
                           config.format_value(day.get("precipitation"), " mm"))

    window.setProperty("Weather.AlertCount", str(len(alert_list)))
    for index, alert in enumerate(alert_list[:10], start=1):
        prefix = "Weather.Alert%d." % index
        window.setProperty(prefix + "Title", alert.get("title", ""))
        window.setProperty(prefix + "Type", alert.get("type", ""))
        window.setProperty(prefix + "Level", alert.get("level", ""))
        window.setProperty(prefix + "Time", alert.get("issue_time", ""))
        window.setProperty(prefix + "Icon", alert.get("icon", ""))
    return True


def clear():
    try:
        window = xbmcgui.Window(10000)
        window.clearProperty("Weather.IsFetched")
    except Exception:  # noqa: BLE001
        pass
