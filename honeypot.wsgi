#!/usr/bin/env python

import sys
import os
honeypot_path = "/srv/honeypot"
sys.path.append(honeypot_path)
os.chdir(honeypot_path)
from honeypot import app as application
