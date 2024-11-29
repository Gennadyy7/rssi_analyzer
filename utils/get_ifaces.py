from pywifi import PyWiFi
from utils.give_rights import give_rights

class IfacesProvider:
    WIFI = PyWiFi()

    @classmethod
    def get_ifaces(cls):
        give_rights()
        interfaces = cls.WIFI.interfaces()[1:]
        return interfaces