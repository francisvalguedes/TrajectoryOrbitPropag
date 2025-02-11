import streamlit as st
import pandas as pd
import numpy as np

import gettext
_ = gettext.gettext

from os import system, path

from zenserp import Client


seq = 1

if seq == 1: #  .pot file
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d main -o locales/main.pot source/main.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 00_Simplified -o locales/00_Simplified.pot source/pages/00_Simplified.py')

    # system(f'cd {path.dirname(path.realpath(__file__))} & cp locales/main.pot locales/pt_BR/LC_MESSAGES/main.po')

if seq == 4: # compile to .mo file:
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/main.mo locales/pt-BR/LC_MESSAGES/main')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/00_Simplified.mo locales/pt-BR/LC_MESSAGES/00_Simplified')

if seq == 2: # localazy upload
    system(f'cd {path.dirname(path.realpath(__file__))} & localazy upload')

if seq == 3: # localazy download
    system(f'cd {path.dirname(path.realpath(__file__))} & localazy download')


