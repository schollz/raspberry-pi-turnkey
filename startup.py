import subprocess
import signal
import string
import random
import re
import json
import time
import os
import socket
import requests

from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
app = Flask(__name__, static_url_path='')

currentdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentdir)

ssid_list = []


def getssid():
    """

    Returns:
        List with all SSIDs from the system
    """
    global ssid_list

    if len(ssid_list) > 0:
        return ssid_list
    ssid_list = []
    get_ssid_list = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
    ssids = get_ssid_list.splitlines()

    for ssid in ssids:
        ssid = ssid.strip().decode('utf-8')

        if ssid.startswith("SSID"):
            try:
                ssid_list.append(ssid.split(": ")[1])
            except:
                pass
    print(ssid_list)
    ssid_list = sorted(list(set(ssid_list)))
    return ssid_list


def id_generator():
    """
    Try to get the unique serial number from hardware, if not possible generate it randomly.

    Returns:
        String with the serial number
    """
    serial_cpu = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                serial_cpu = line[10:26]
        f.close()
    except:
        serial_cpu = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

    return serial_cpu



wpa_conf = """country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
    ssid="%s"
    %s
}"""

wpa_conf_default = """country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
"""


@app.route('/')
def main():
    piid = open('pi.id', 'r').read().strip()
    return render_template('index.html', ssids=getssid(), message="Once connected you'll find IP address @ <a href='https://snaptext.live/{}' target='_blank'>snaptext.live/{}</a>.".format(piid,piid))


@app.route('/generate_204')
def redirect204():
    """
    Captive portal when connected with iOS or Android.

    Returns:
        redirect
    """
    return redirect("http://192.168.4.1", code=302)


@app.route('/hotspot-detect.html')
def applecaptive():
    """
    Mac OS captive portal when connected.

    Returns:
        redirect
    """
    return redirect("http://192.168.4.1", code=302)


@app.route('/ncsi.txt')
def windowscaptive():
    """
    Windows OS based captive portal. (Not working for Windows, needs work!)

    Returns:
        redirect
    """
    return redirect("http://192.168.4.1", code=302)


def check_credentials(ssid, password):
    """
    Validates SSID and password and returns True if valid and False if not valid

    Args:
        ssid: String with the SSID to validate
        password: String with the password to validate

    Returns:
        Boolean
    """

    wpadir = currentdir + '/wpa/'
    testconf = wpadir + 'test.conf'
    wpalog = wpadir + 'wpa.log'
    wpapid = wpadir + 'wpa.pid'

    if not os.path.exists(wpadir):
        os.mkdir(wpadir)

    for _file in [testconf, wpalog, wpapid]:
        if os.path.exists(_file):
            os.remove(_file)

    # Generate temp wpa.conf
    result = subprocess.check_output(['wpa_passphrase', ssid, password])
    with open(testconf, 'w') as f:
        f.write(result.decode('utf-8'))

    def stop_ap(blnstop):

        if blnstop:
            # Services need to be stopped to free up wlan0 interface
            print(subprocess.check_output(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"]))
        else:
            print(subprocess.check_output(['systemctl', "restart", "dnsmasq", "dhcpcd"]))
            time.sleep(15)
            print(subprocess.check_output(['systemctl', "restart", "hostapd"]))

    # Sentences to check for
    fail = "pre-shared key may be incorrect"
    success = "WPA: Key negotiation completed"

    stop_ap(True)

    result = subprocess.check_output(['wpa_supplicant',
                                      "-Dnl80211",
                                      "-iwlan0",
                                      "-c/" + testconf,
                                      "-f", wpalog,
                                      "-B",
                                      "-P", wpapid])

    checkwpa = True
    while checkwpa:
        with open(wpalog, 'r') as f:
            content = f.read()

            if success in content:
                valid_psk = True
                checkwpa = False

            elif fail in content:
                valid_psk = False
                checkwpa = False

            else:
                continue

    # Kill wpa_supplicant to stop it from setting up dhcp, dns
    with open(wpapid, 'r') as p:
        pid = p.read()
        pid = int(pid.strip())
        os.kill(pid, signal.SIGTERM)

    # Restart services
    stop_ap(False)
    return valid_psk

@app.route('/static/<path:path>')
def send_static(path):
    """
    Send all needed resources from static folder.

    Args:
        path: String with path from where resources are taken.

    Returns:
        send_from_directory
    """
    return send_from_directory('static', path)


@app.route('/signin', methods=['POST'])
def signin():
    """
    Verification and configuration for the WiFi connection.

    Returns:
        render_template
    """
    email = request.form['email']
    ssid = request.form['ssid']
    password = request.form['password']

    pwd = 'psk="' + password + '"'
    if password == "":
        # Open APs
        pwd = "key_mgmt=NONE"

    print(email, ssid, password)
    valid_psk = check_credentials(ssid, password)
    if not valid_psk:
        # User will not see this because they will be disconnected but we need to break here anyway
        return render_template('ap.html', message="Wrong password!")

    # Save configuration on the wpa.conf file
    with open('wpa.conf', 'w') as f:
        f.write(wpa_conf % (ssid, pwd))

    # Save status
    with open('status.json', 'w') as f:
        f.write(json.dumps({'status':'disconnected'}))
    subprocess.Popen(["./disable_ap.sh"])
    piid = open('pi.id', 'r').read().strip()

    return render_template('index.html', message="Please wait 2 minutes to connect. Then your IP address will show up at <a href='https://snaptext.live/{}'>snaptext.live/{}</a>.".format(piid,piid))

def wificonnected():
    """
    Check whether it connected to WiFi or not and return a boolean if connected.

    Returns:
        Boolean
    """
    result = subprocess.check_output(['iwconfig', 'wlan0'])
    matches = re.findall(r'\"(.+?)\"', result.split(b'\n')[0].decode('utf-8'))
    blnReturn = False

    if len(matches) > 0:
        print("Got connected to " + matches[0])
        blnReturn = True

    return blnReturn


if __name__ == "__main__":
    # Things to run the first time it boots
    if not os.path.isfile('pi.id'):
        with open('pi.id', 'w') as f:
            f.write(id_generator())
        subprocess.Popen("./expand_filesystem.sh")
        time.sleep(300)
    piid = open('pi.id', 'r').read().strip()
    print(piid)
    time.sleep(15)

    # Set default status
    s = {'status': 'disconnected'}

    if not os.path.isfile('status.json'):
        with open('status.json', 'w') as f:
            f.write(json.dumps(s))
    else:
        s = json.load(open('status.json'))

    # Check connection
    if wificonnected():
        s['status'] = 'connected'

    # Don't change if status in status.json is hostapd
    else:
        if s['status'] == 'connected':
            s['status'] = 'disconnected'

    with open('status.json', 'w') as f:
        f.write(json.dumps(s))

    if s['status'] == 'disconnected':
        s['status'] = 'hostapd'
        with open('status.json', 'w') as f:
            f.write(json.dumps(s))
        with open('wpa.conf', 'w') as f:
            f.write(wpa_conf_default)
        subprocess.Popen("./enable_ap.sh")

    elif s['status'] == 'connected':
        piid = open('pi.id', 'r').read().strip()

        # Get IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipaddress = s.getsockname()[0]
        s.close()

        # Alert user on snaptext
        r = requests.post("https://snaptext.live", data=json.dumps({"message": "Your Pi is online at {}".format(ipaddress), "to" : piid, "from": "Raspberry Pi Turnkey"}))
        print(r.json())
        subprocess.Popen("./startup.sh")
        while True:
            time.sleep(60000)
    else:
        app.run(host="0.0.0.0", port=80, threaded=True)
