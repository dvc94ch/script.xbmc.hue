import urllib2
import time
import os
import socket
import json
import random
import hashlib
import xbmc
import xbmcaddon

__addon__      = xbmcaddon.Addon()
__cwd__        = __addon__.getAddonInfo('path')
__icon__       = os.path.join(__cwd__,"icon.png")
__settings__   = os.path.join(__cwd__,"resources","settings.xml")

def log(msg):
  xbmc.log("%s: %s" % ("Hue", msg))

def notify(title, msg=""):
  global __icon__
  xbmc.executebuiltin("XBMC.Notification(%s, %s, 3, %s)" % (title, msg, __icon__))
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
  while(num_retransmits < 10) and hue_ip == None:
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
  start_setting = None

  def __init__(self, bridge_ip, bridge_user, name, group=False):
    self.bridge_ip = bridge_ip
    self.bridge_user = bridge_user
    self.name = name
    self.group = group
    
    if self.group:
        self.url = "http://%s/api/%s/groups" 
    else:
        self.url = "http://%s/api/%s/lights"
        
    self.url = self.url % \
      (self.bridge_ip, self.bridge_user)
      
    if name is None:
        self.id = 0
    else:
        self.id = self.get_id_by_name(name)
    
    self.url = "%s/%s" % (self.url, self.id)
    
    self.get_current_setting()

  def request_url_put(self, url, data):
    if self.start_setting['on'] is False and self.group is False:
      return
      
    log("sending %s to %s" % (data, url))
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(url, data=data)
    request.get_method = lambda: 'PUT'
    url = opener.open(request)

  def get_current_setting(self):
    r = urllib2.urlopen(self.url)
    j = json.loads(r.read())
    state = j.get('state', j.get('action'))
    
    self.start_setting = {
      "on": state['on'],
      "bri": state['bri'],
      "hue": state['hue'],
      "sat": state['sat'],
    }

  def get_id_by_name(self, name):
    r = urllib2.urlopen(self.url)
    j = json.loads(r.read())
    
    for k, v in j.iteritems():
        if v['name'] == name:
            return k
  
  def set_light(self, data):
    log("sending command to light %s" % self.id)
    self.request_url_put("%s/state" % self.url, data=data)

  def flash_light(self):
    self.dim_light(10)
    self.brighter_light()

  def dim_light(self, bri):
    # Setting the brightness of a group to 0 does not turn the lights off
    # Turning the lights off with a transitiontime does not work as expected
    # workaround: dim the lights first, then turn them off
    dimmed = '{"on":true,"bri":%s,"transitiontime":4}' % bri
    self.set_light(dimmed)
    if bri == 0:
        off = '{"on":false}'
        self.set_light(off)

  def brighter_light(self):
    on = '{"on":true,"bri":%d,"hue":%d,"sat":%d,"transitiontime":4}' % /
      (self.start_setting['bri'], self.start_setting['hue'], self.start_setting['sat'])
    self.set_light(on)

class Group(Light):
  def __init__(self, bridge_ip, bridge_user, name=None):
    Light.__init__(self, bridge_ip, bridge_user, name, group=True)

  def set_light(self, data):
    log("sending command to group %s" % self.id)
    Light.request_url_put(self, "%s/action" % self.url, data=data)

