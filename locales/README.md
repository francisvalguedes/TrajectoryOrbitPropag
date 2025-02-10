## Tradução

Criar os arquivos .pot
~~~
pygettext3 -d base -o locales/base.pot source/main.py
~~~

Copiar traduzir e criar os arquivos .mo
~~~
msgfmt -o locales/en/LC_MESSAGES/base.mo locales/en/LC_MESSAGES/base
~~~