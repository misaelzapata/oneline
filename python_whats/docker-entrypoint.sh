#!/usr/bin/env bash
pip install -r requirements.txt
mkdir -p /logs
chmod a+w /logs
chmod a+w /root/.yowsup
supervisord -c /etc/supervisord.conf
