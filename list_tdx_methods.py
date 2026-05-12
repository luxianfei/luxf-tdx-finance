#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 pytdx API 的可用方法"""

from pytdx.hq import TdxHq_API

api = TdxHq_API()
print("pytdx API 可用方法:")
methods = [m for m in dir(api) if not m.startswith('_')]
for method in sorted(methods):
    print(f"  {method}")