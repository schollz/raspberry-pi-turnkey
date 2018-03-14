import subprocess
import string
import random
import re
import json
import time
import os.path 
import os
import subprocess
import socket

import requests
from flask import Flask, request, send_from_directory,jsonify, render_template
app = Flask(__name__, static_url_path='')

def getssid():
    ssid_list = []
    get_ssid_list = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
    ssids = get_ssid_list.splitlines()
    for s in ssids:
        s = s.strip().decode('utf-8')
        if s.startswith("SSID"):
            a = s.split(": ")
            try:
                ssid_list.append(a[1])
            except:
                pass
    print(ssid_list)
    return sorted(list(set(ssid_list)))

def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

os.chdir('/home/pi/raspberry-pi-turnkey')

wpa_conf = """country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
    ssid="_ssid_"
    psk="_password_"
}"""

wpa_conf_default = """country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
"""



@app.route('/')
def main():
    return render_template('index.html', ssids=getssid())

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/signin', methods=['POST'])
def signin():
    email = request.form['email']
    ssid = request.form['ssid']
    password = request.form['password']
    print(email,ssid,password)
    with open('wpa.conf','w') as f:
        f.write(wpa_conf.replace('_ssid_',ssid).replace('_password_',password))
    with open('status.json','w') as f:
        f.write(json.dumps({'status':'disconnected'}))
    subprocess.Popen(["./disable_ap.sh"])
    piid = open('pi.id','r').read().strip()
    return render_template('index.html', message="Please wait 2 minutes to connect. Then your IP address will show up at <a href='https://snaptext.live/{}'>snaptext.live/{}</a>.".format(piid,piid))

def wificonnected():
    result = subprocess.check_output(['iwconfig', 'wlan0'])
    matches = re.findall(r'\"(.+?)\"', result.split(b'\n')[0].decode('utf-8'))
    if len(matches) > 0:
        return True
        print("got connected to " + matches[0])
    return False

if __name__ == "__main__":
    # things to run the first time it boots
    if not os.path.isfile('pi.id'):
        with open('pi.id','w') as f:
            f.write(id_generator())
        subprocess.Popen("./expand_filesystem.sh")
        time.sleep(300)
    piid = open('pi.id','r').read().strip()
    print(piid)
    time.sleep(15)
    # get status
    s = {'status':'disconnected'}
    if not os.path.isfile('status.json'):
        with open('status.json','w') as f:
            f.write(json.dumps(s))
    else:
        s = json.load(open('status.json'))

    # check connection
    if wificonnected():
        s['status'] = 'connected'
    if not wificonnected():
        if s['status'] == 'connected': # Don't change if status in status.json is hostapd
            s['status'] = 'disconnected'

    with open('status.json','w') as f:
        f.write(json.dumps(s))   
    if s['status'] == 'disconnected':
        s['status'] = 'hostapd'
        with open('status.json','w') as f:
            f.write(json.dumps(s))   
        with open('wpa.conf','w') as f:
            f.write(wpa_conf_default)
        subprocess.Popen("./enable_ap.sh")
    elif s['status'] == 'connected':
        piid = open('pi.id','r').read().strip()
        
        # get ip address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ipaddress = s.getsockname()[0]
        s.close()

        # alert user on snaptext
        r = requests.post("https://snaptext.live",data=json.dumps({"message":"Your Pi is online at {}".format(ipaddress),"to":piid,"from":"Raspberry Pi Turnkey"}))
        print(r.json())
        subprocess.Popen("./startup.sh")
        while True:
            time.sleep(60000)
    else:
        app.run(host="0.0.0.0",port=80)
