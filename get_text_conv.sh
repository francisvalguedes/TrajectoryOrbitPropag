#!/bin/bash

#pygettext3 -d main -o locales/main.pot source/main.py

# Copiar traduzir e criar os arquivos .mo

msgfmt -o locales/en/LC_MESSAGES/main.mo locales/en/LC_MESSAGES/main
msgfmt -o locales/pt/LC_MESSAGES/main.mo locales/pt/LC_MESSAGES/main

msgfmt -o locales/en/LC_MESSAGES/00_Simplified.mo locales/en/LC_MESSAGES/00_Simplified
msgfmt -o locales/pt/LC_MESSAGES/00_Simplified.mo locales/pt/LC_MESSAGES/00_Simplified