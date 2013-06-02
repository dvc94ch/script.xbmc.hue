import time
import os
import socket
import json
import random
import hashlib

import xbmc
import xbmcaddon
import urllib2


__addon__ = xbmcaddon.Addon()
__cwd__ = __addon__.getAddonInfo('path')
__icon__ = os.path.join(__cwd__, "icon.png")
__settings__ = os.path.join(__cwd__, "resources", "settings.xml")


def log(msg):
    xbmc.log("%s: %s" % ("Hue", msg))


def notify(title, msg=""):
    global __icon__
    xbmc.executebuiltin("XBMC.Notification(%s, %s, 3, %s)" %
                       (title, msg, __icon__))
    #log(str(title) + " " + str(msg))


def start_autodisover():
    port = 1900
    ip = "239.255.255.250"

    address = (ip, port)
    data = """M-SEARCH * HTTP/1.1
    HOST: %s:%s
    MAN: ssdp:discover
    MX: 3
    ST: upnp:rootdevice""" % (ip, port)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    hue_ip = None
    num_retransmits = 0
    while(num_retransmits < 10) and hue_ip is None:
        num_retransmits += 1
        client_socket.sendto(data, address)
        recv_data, addr = client_socket.recvfrom(2048)
        if "IpBridge" in recv_data and "description.xml" in recv_data:
            hue_ip = recv_data.split("LOCATION: http://")[1].split(":")[0]
        time.sleep(1)

    return hue_ip


def register_user(hue_ip):
    username = hashlib.md5(str(random.random())).hexdigest()
    device = "xbmc-player"
    data = '{"username": "%s", "devicetype": "%s"}' % (username, device)

    # use urllib2 as it's included in Python
    response = urllib2.urlopen('http://%s/api' % hue_ip, data)
    response = response.read()
    while "link button not pressed" in response:
        notify("Bridge discovery", "press link button on bridge")
        response = urllib2.urlopen('http://%s/api' % hue_ip, data)
        response = response.read()
        time.sleep(3)

    return username


class Light:

    def __init__(self, bridge_ip, bridge_user, name=None, id=0, group=False):
        """If no name is given self.id be set to id."""

        self.bridge_ip = bridge_ip
        self.bridge_user = bridge_user
        self.bridge_url = ("http://%s/api/%s" %
                          (self.bridge_ip, self.bridge_user))
        self.name = name
        self.group = group

        if self.group:
            self.base_url = "%s/groups"
        else:
            self.base_url = "%s/lights"

        self.base_url = self.base_url % self.bridge_url

        if name is None:
            self.id = id
        else:
            self.id = self.get_id_by_name(name)

        self.url = "%s/%s" % (self.base_url, self.id)

        self.last_state = self.get_state()

    def get_id_by_name(self, name):
        r = urllib2.urlopen(self.base_url)
        j = json.loads(r.read())

        for k, v in j.iteritems():
            if v['name'] == name:
                return k

        raise NameDoesntExistError()

    def request_url_put(self, url, data):
        log("sending %s to %s" % (data, url))
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, data=data)
        request.get_method = lambda: 'PUT'
        url = opener.open(request)

    def get_state(self, url=None):
        if url is None:
            url = self.url
        r = urllib2.urlopen(url)
        j = json.loads(r.read())
        state = j.get('state', j.get('action'))

        return {"on": state['on'], "bri": state['bri'],
                "hue": state['hue'], "sat": state['sat']}

    def set_state(self, data):
        log("sending command to light %s" % self.id)
        self.request_url_put("%s/state" % self.url, data=data)

    def flash_light(self):
        self.dim_light(10)
        self.brighter_light()

    def dim_light(self, bri=0, hue=None, sat=None):
        """Remembers the state of the light how it is now, and sets the
        lights bri to bri.
        """

        self.last_state = self.get_state()

        if hue is None:
            hue = self.last_state['hue']

        if sat is None:
            sat = self.last_state['sat']

        if bri == 0:
            on = False
        else:
            on = True

        new_state = {"on": on, "bri": bri, "hue": hue, "sat": sat}

        self.transition_state(self.last_state, new_state)

    def brighter_light(self):
        """Reverts light state to before playback."""

        self.transition_state(self.get_state(), self.last_state)

    def transition_state(self, start_state, end_state):
        #if start_state['on'] == end_state['on']:
        transition = ('{"on": %s, "bri": %d, "hue": %d, "sat": %d, "transitiontime": 4}' %
                     (str(end_state['on']).lower(), end_state['bri'],
                      end_state['hue'], end_state['sat']))
        self.set_state(transition)


class Group(Light):

    def __init__(self, bridge_ip, bridge_user, name=None, id=0):
        Light.__init__(self, bridge_ip, bridge_user, name, id, group=True)

    def set_state(self, data):
        log("sending command to group %s" % self.id)
        Light.request_url_put(self, "%s/action" % self.url, data=data)

    def get_state(self):
        r = urllib2.urlopen(self.url)
        j = json.loads(r.read())
        id = j['lights'][0]
        return Light.get_state(self,
                               url="%s/lights/%s" % (self.bridge_url, id))


class NameDoesntExistError:
    pass
