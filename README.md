# Personal Status Page
My personal status page for my UNRAID server, implemented using Websockets in Flask!

Features:
* Spotify Now Playing and Playback Control Integration (requires API access setup)
* "Real-time" log information display for all Websocket-related operations
* ZeroTier device status information, using [ztls](https://github.com/jon77p/ztls) (modified to display text instead of emoji)
* Website status lookup

## Prerequisites
* python3
* pip3
* virtualenv
* nginx
* Spotify App Token (obtained by creating a Spotify application)
* Spotify Refresh Token (obtained by following Spotify's OAUTH authentication for API access)
* ZeroTier API Token

## Getting Started

1. Create a virtual environment and install the necessary pip3 packages in the virtual environment (`pip3 install -r requirements.txt`)
2. Fill in the variables in `config.py`
3. Create a separate symlink for each file from etc/systemd/system/ into /etc/systemd/system/
```bash
sudo ln -s etc/systemd/system/status.service /etc/systemd/system/status.service
```
4. Edit the system service configuration file as needed to point to the correct directories where the status page source resides and fill in the `SPOTAPPTOKEN`, `SPOTREFRESHTOKEN`, and `ZT_API` environment variables
5. Start and enable the services on boot with 
```bash
sudo systemctl start status.service
sudo systemctl enable status.service
```
6. Create a symlink from etc/nginx/sites-available/status into /etc/nginx/sites-available/status
```bash
sudo ln -s etc/nginx/sites-available/status /etc/nginx/sites-available/status
```
7. Create a symlink in sites-enabled to the site configuration file and reload nginx.
```bash
sudo ln -s /etc/nginx/sites-available/status /etc/nginx/sites-enabled/status
```
8. Edit the nginx configuration file as needed to have uwsgi pointing to the correct directory.
9. The site should now be live.

### Setting up to work with Unraid Mounts:

`sudo vim /etc/fstab`

ADD:

	status /mnt/status 9p trans=virtio,rw 0 0

`sudo vim /etc/initramfs-tools/modules`

ADD:

	9p

	9pnet

	9pnet_virtio

`sudo update-initramfs -u`

`sudo reboot`

