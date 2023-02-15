#!/bin/bash
sudo apt install -y python3.9
sudo apt install -y python3-pip
pip install virtualenv
pip install --upgrade pip
virtualenv env
source env/bin/activate
pip install -r requirements.txt