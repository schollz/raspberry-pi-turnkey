#!/bin/bash

sleep 3

# enable the AP
sudo systemctl stop dnsmasq && sudo systemctl stop hostapd
sudo cp config/hostapd /etc/default/hostapd
sudo cp config/dhcpcd.conf /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf /etc/dnsmasq.conf
sudo systemctl daemon-reload
sudo systemctl restart dhcpcd
sudo systemctl start hostapd && sudo systemctl start dnsmasq

# load wan configuration
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

sudo reboot now
