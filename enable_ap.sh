#!/bin/bash
sleep 3
sudo sed -i '/DAEMON_CONF="\/etc/s/^#//g' /etc/default/hostapd
sudo sed -i '/interface wlan0/s/^#//g' /etc/dhcpcd.conf
sudo sed -i '/static ip_address=192.168.4.1\/24/s/^#//g' /etc/dhcpcd.conf
sudo sed -i '/interface=wlan0/s/^#//g' /etc/dnsmasq.conf
sudo sed -i '/dhcp-range=/s/^#//g' /etc/dnsmasq.conf

sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

sudo reboot now
