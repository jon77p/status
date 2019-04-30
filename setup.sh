#!/bin/bash

CURR="$(pwd)"
USER="$(whoami)"

sudo ln -s $CURR/etc/systemd/system/status.service /etc/systemd/system/status.service

sudo ln -s $CURR/etc/nginx/sites-available/status /etc/nginx/sites-available/status
sudo ln -s /etc/nginx/sites-available/status /etc/nginx/sites-enabled/status

sudo mkdir -p /var/log/status
sudo chown $USER:$USER /var/log/status

sudo systemctl daemon-reload
sudo systemctl start status.service
sudo systemctl enable status.service
sudo systemctl restart nginx.service
echo "Done!"
