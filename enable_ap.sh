#!/bin/bash
sleep 3

sudo cp config/hostapd /etc/default/hostapd
sudo cp config/dhcpcd.conf /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf /etc/dnsmasq.conf
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

sudo reboot now
