# import streamlit as st
# import pandas as pd
# import numpy as np

# import gettext
# _ = gettext.gettext

from os import system, path

# from zenserp import Client


seq = 4

if seq == 1: #  .pot file
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d main -o locales/main.pot source/main.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 00_Simplified -o locales/00_Simplified.pot source/pages/00_Simplified.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 01_orbital_elements -o locales/01_orbital_elements.pot source/pages/01_orbital_elements.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 02_orbit_propagation -o locales/02_orbit_propagation.pot source/pages/02_orbit_propagation.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 03_map -o locales/03_map.pot source/pages/03_map.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 04_orbit_compare -o locales/04_orbit_compare.pot source/pages/04_orbit_compare.py')
    system(f'cd {path.dirname(path.realpath(__file__))} & pygettext3 -d 05_trajectory -o locales/05_trajectory.pot source/pages/05_trajectory.py')
    print('Arquivos criados .pot')
    # system(f'cd {path.dirname(path.realpath(__file__))} & cp locales/main.pot locales/pt_BR/LC_MESSAGES/main.po')

if seq == 4: # compile to .mo file:
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/main.mo locales/pt-BR/LC_MESSAGES/main')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/00_Simplified.mo locales/pt-BR/LC_MESSAGES/00_Simplified')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/01_orbital_elements.mo locales/pt-BR/LC_MESSAGES/01_orbital_elements')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/02_orbit_propagation.mo locales/pt-BR/LC_MESSAGES/02_orbit_propagation')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/03_map.mo locales/pt-BR/LC_MESSAGES/03_map')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/04_orbit_compare.mo locales/pt-BR/LC_MESSAGES/04_orbit_compare')
    system(f'cd {path.dirname(path.realpath(__file__))} & msgfmt -o locales/pt-BR/LC_MESSAGES/05_trajectory.mo locales/pt-BR/LC_MESSAGES/05_trajectory')
    print('Arquivos compilados para .mo')


if seq == 2: # localazy upload
    system(f'cd {path.dirname(path.realpath(__file__))} & localazy upload')
    print('upload completo')

if seq == 3: # localazy download
    system(f'cd {path.dirname(path.realpath(__file__))} & localazy download')
    print('download completo')
