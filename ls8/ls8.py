#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *


if len(sys.argv) == 2:
    cpu = CPU()
    cpu.load()
    cpu.run()
else:
    print('Please pass in second file name: python3 ls8.py file_name')
    sys.exit()
