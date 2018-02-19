import subprocess
import string
import random
import re
import json
import time
import os.path 
import subprocess
import requests


import requests
from flask import Flask, request, send_from_directory,jsonify, render_template
app = Flask(__name__, static_url_path='')

def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

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
    return render_template('index.html')

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

if __name__ == "__main__":
    if not os.path.isfile('pi.id'):
        with open('pi.id','w') as f:
            f.write(id_generator())
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
    result = subprocess.run(['iwconfig', 'wlan0'], stdout=subprocess.PIPE)
    matches=re.findall(r'\"(.+?)\"',result.stdout.split(b'\n')[0].decode('utf-8'))
    if len(matches) > 0:
        s['status'] = 'connected'
        print("got connected to " + matches[0])

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
        result = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE)
        ipaddress =  result.stdout.strip().split(b' ')[-1].decode('utf-8')
        r = requests.post("https://snaptext.live",data=json.dumps({"message":"Your Pi is online at {}".format(ipaddress),"to":piid,"from":"Raspberry Pi Turnkey"}))
        print(r.json())
        subprocess.Popen("./startup.sh")
    else:
        app.run(host="0.0.0.0",port=80)
