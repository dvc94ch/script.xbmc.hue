import sys
import xbmcaddon

__addon__      = sys.modules[ "__main__" ].__addon__

class settings():
  def __init__( self, *args, **kwargs ):
    self.readxml()
    self.addon = xbmcaddon.Addon()

  def readxml(self):
    self.bridge_ip              = __addon__.getSetting("bridge_ip")
    self.bridge_user            = __addon__.getSetting("bridge_user")
    self.light_name             = __addon__.getSetting("light_name")
    self.light_type             = int(__addon__.getSetting("light_type"))
    self.dim_brightness         = int(int(__addon__.getSetting("dim_brightness").split(".")[0])*254/100)
    self.misc_initialflash      = __addon__.getSetting("misc_initialflash") == "true"
    
    self.backlight_enable       = __addon__.getSetting("backlight_enable") == "true"
    self.backlight_name         = __addon__.getSetting("backlight_name")
    self.backlight_type         = int(__addon__.getSetting("backlight_type"))
    self.backlight_brightness   = int(int(__addon__.getSetting("backlight_brightness").split(".")[0])*254/100)

  def update(self, **kwargs):
    self.__dict__.update(**kwargs)
    for k, v in kwargs.iteritems():
      self.addon.setSetting(k, v)
