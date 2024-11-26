import time
from pywifi import const

from utils.ssid_update import ssid_update


def safe_scan(iface):
    """Проверяет статус адаптера и выполняет безопасное сканирование."""
    # print(f'Статус ({iface.name()}):', iface.status())
    while iface.status() == const.IFACE_SCANNING:
        print(f'Пропуск хода для {iface.name()}')
        time.sleep(0.1)
    iface.scan()

def get_rssi_readings(iface):
    """
    Получает RSSI для указанного SSID.
    :param iface: Wi-Fi интерфейс.
    :param ssid: Название сети.
    :return: Значение RSSI.
    """
    rssi_value = None
    safe_scan(iface)
    scan_results = iface.scan_results()
    wifi_dict = {ssid_update(result.ssid): result.signal for result in scan_results if result.ssid}
    # print(len(wifi_dict))
    # result_dict = {ssid: wifi_dict[ssid]} if ssid and ssid in wifi_dict else (wifi_dict if ssid is None else {})
    return wifi_dict
