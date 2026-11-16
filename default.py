# -*- coding: utf-8 -*-
"""Kodi plugin entry point for plugin.weather.china.

Keep this file minimal: all logic lives in resources/lib (see lib/ui.py).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources"))

from lib import ui  # noqa: E402

if __name__ == "__main__":
    ui.run()
