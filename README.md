# Instructions for making a turn-key image

## Flash Raspbian Stretch Lite

Starting from version [Raspbian Stretch Lite](https://www.raspberrypi.org/downloads/raspbian/) version 2017-11-29.

```
sudo dd bs=4M if=2017-11-29-raspbian-stretch-lite.img of=/dev/mmcblk0 conv=fsync status=progress
```

Change `/dev/mmcblk0` to whatever your SD card is (find it using `fdisk -l`).

After flashing, for the first time use, just plug in ethernet and you can SSH into the Pi. To activate SSH on boot just do

```
touch /media/YOURUSER/boot/ssh
```

## Add libraries onto the Pi

```
sudo apt-get update
sudo apt-get dist-upgrade -y
sudo apt-get install -y dnsmasq hostapd vim python3-flask git
```

## Install node 

```
wget https://nodejs.org/dist/v8.9.4/node-v8.9.4-linux-armv6l.tar.xz
sudo mkdir /usr/lib/nodejs
sudo tar -xJvf node-v8.9.4-linux-armv6l.tar.xz -C /usr/lib/nodejs 
rm -rf node-v8.9.4-linux-armv6l.tar.xz
sudo mv /usr/lib/nodejs/node-v8.9.4-linux-armv6l /usr/lib/nodejs/node-v8.9.4
echo 'export NODEJS_HOME=/usr/lib/nodejs/node-v8.9.4' >> ~/.profile
echo 'export PATH=$NODEJS_HOME/bin:$PATH' >> ~/.profile
source ~/.profile
```

## Install Go

```
wget https://dl.google.com/go/go1.10.linux-armv6l.tar.gz
sudo tar -C /usr/local -xzf go*gz
rm go*gz
echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >>  ~/.profile
echo 'export GOPATH=$HOME/go' >>  ~/.profile
source ~/.profile
```

# Install base station

```
git clone https://github.com/schollz/raspberry-pi-turnkey.git
```

# Install Hostapd

```
sudo systemctl stop dnsmasq && sudo systemctl stop hostapd

echo 'interface wlan0
static ip_address=192.168.4.1/24' | sudo tee --append /etc/dhcpcd.conf
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig  

sudo systemctl daemon-reload
sudo systemctl restart dhcpcd

echo 'interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h' | sudo tee --append /etc/dnsmasq.conf

echo 'interface=wlan0
driver=nl80211
ssid=ConnectToConnect
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=ConnectToConnect
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP' | sudo tee --append /etc/hostapd/hostapd.conf

echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee --append /etc/default/hostapd

sudo systemctl start hostapd && sudo systemctl start dnsmasq
```

Add to cron

```
@reboot cd /home/pi/raspberry-pi-turnkey && /usr/bin/sudo /usr/bin/python3 startup.py
```


