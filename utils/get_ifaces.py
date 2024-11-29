from pywifi import PyWiFi
from utils.give_rights import give_rights

class IfacesProvider:
    WIFI = PyWiFi()

    @classmethod
    def get_ifaces(cls):
        while True:
            give_rights()
            try:
                interfaces = cls.WIFI.interfaces()[1:]
            except FileNotFoundError as err:
                print('Либа не справилась с отслеживанием файлов для адаптеров', err)
                continue
            return interfaces