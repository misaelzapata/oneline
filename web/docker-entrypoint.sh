#!/usr/bin/env bash
pip install -r requirements.txt
mkdir -p /logs
chmod a+w /logs
supervisord -c /etc/supervisord.conf
