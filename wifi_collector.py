import time
from pywifi import const

def safe_scan(iface):
    """Проверяет статус адаптера и выполняет безопасное сканирование."""
    print(f'Статус ({iface.name()}):', iface.status())
    while iface.status() == const.IFACE_SCANNING:
        print(f'Пропуск хода для {iface.name()}')
        time.sleep(0.1)
    iface.scan()

def get_rssi_readings(iface, ssid):
    """
    Получает RSSI для указанного SSID.
    :param iface: Wi-Fi интерфейс.
    :param ssid: Название сети.
    :return: Значение RSSI.
    """
    rssi_value = None
    safe_scan(iface)
    scan_results = iface.scan_results()
    for network in scan_results:
        if network.ssid == ssid:
            rssi_value = network.signal
            break
    if not rssi_value:
        raise Exception('Отсутствует нужный источник Wi-Fi')
    return rssi_value

def collect_rssi_thread(iface, ssid, rssi_data, index, barrier):
    """
    Собирает RSSI с интерфейса и обновляет данные.
    :param iface: Wi-Fi интерфейс.
    :param ssid: Название сети.
    :param rssi_data: Хранилище данных RSSI.
    :param index: Индекс интерфейса.
    :param barrier: Барьер для синхронизации.
    """
    while True:
        rssi_value = get_rssi_readings(iface, ssid)
        print(f'Интерфейс {iface.name()}, RSSI: {rssi_value}')
        rssi_data[index].append(rssi_value)
        barrier.wait()
