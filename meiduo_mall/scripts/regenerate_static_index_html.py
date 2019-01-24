#!/usr/bin/env python

import os
import sys
import django

sys.path.insert(0, '../')

if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'

django.setup()

from contents.crons import generate_static_index_html

if __name__ == '__main__':
    generate_static_index_html()