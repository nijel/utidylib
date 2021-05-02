#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup file for easy installation"""

import os

from setuptools import setup

with open("requirements.txt") as handle:
    REQUIRES = handle.read().splitlines()

setup(
    install_requires=REQUIRES,
)
