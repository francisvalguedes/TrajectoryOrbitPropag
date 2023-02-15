#!/bin/bash

pip install --upgrade pip
virtualenv env
source env/bin/activate
pip install -r requirements.txt