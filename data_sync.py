import re
import threading
from collections import deque, defaultdict
import copy

from utils.get_ifaces import IfacesProvider


import time
from pywifi import const

from utils.ssid_update import ssid_update


class DataSync:
    condition = threading.Condition()

    def __init__(self, interfaces=None, avg_buffer_size=8):
        if not interfaces:
            interfaces = []
        self.interfaces = interfaces
        # self.rssi_data = {i: deque(maxlen=rssi_buffer_size) for i in range(len(interfaces))}
        self.rssi_data = {i: defaultdict(int) for i in range(len(interfaces))}
        self.avg_rssi_data = defaultdict(lambda: deque(maxlen=avg_buffer_size))
        self.last_rssi_snapshot = None
        self.barrier = threading.Barrier(len(interfaces) + 1)
        # self.condition = threading.Condition()
        self.actual_adapters = len(interfaces)
        self.is_only_init = True
        self.run_adapters = True

    def start_collection(self, interval=1):
        """
        Запускает сбор данных с интерфейсов.
        :param interval: Интервал между итерациями сбора (в секундах).
        """


        while True:
            if self.is_only_init:
                print('Запускаются потоки для адаптеров')
                self.is_only_init = False
                threads = []
                for i, iface in enumerate(self.interfaces):
                    t = threading.Thread(target=self.collect_rssi_thread, args=(iface, i))
                    threads.append(t)
                    t.start()


            # print(self.avg_rssi_data)
            time.sleep(interval)
            print('В это же время я прямо сейчас тут')
            print('Количество потоков вообще:', len(threading.enumerate()))
            temp_actual_adapters_threads = []
            for t in threading.enumerate():
                match = re.search(r'\((.*?)\)', t.name)
                if match:
                    thread_name = match.group(1)
                    if thread_name == 'collect_rssi_thread':
                        temp_actual_adapters_threads.append(t)

            interfaces = IfacesProvider.get_ifaces()

            if len(temp_actual_adapters_threads) == 0:
                print('Все адаптеры были изъяты, проивзодится ожидание методом пуллинга')
                for ssid in self.avg_rssi_data:
                    del self.avg_rssi_data[ssid]
                print('Удалены данные о rssi')
                while not len(IfacesProvider.get_ifaces()):
                    with self.condition:
                        print('Еще ждем...')
                        self.condition.notify()
                    time.sleep(1)
                self.run_adapters = False
                try:
                    self.barrier.abort()
                except threading.BrokenBarrierError:
                    print('Барьер уже был сломан.')
                for t in temp_actual_adapters_threads:
                    t.join()  # Дожидаемся завершения всех потоков
                print('Старые потоки для адаптеров завершены')
                temp_actual_adapters_threads.clear()
                self.__init__(interfaces)
                print('Атрибуты класса переинициализированы')
                continue
            elif len(temp_actual_adapters_threads) != len(interfaces):
                print(temp_actual_adapters_threads, interfaces, sep='\n')
                print('Какие-то адаптеры еще остались, поэтому попробуем еще поработать')
                self.run_adapters = False
                try:
                    self.barrier.abort()
                except threading.BrokenBarrierError:
                    print('Барьер уже был сломан.')
                for t in temp_actual_adapters_threads:
                    t.join()  # Дожидаемся завершения всех потоков
                print('Старые потоки для адаптеров завершены')
                temp_actual_adapters_threads.clear()
                self.__init__(interfaces)
                print('Атрибуты класса переинициализированы')
                continue

            iface_count = len(self.interfaces)
            all_ssids = [set(self.rssi_data[i].keys()) for i in range(iface_count)]
            common_ssids = set.intersection(*all_ssids)
            rssi_values = defaultdict(list)
            for i in range(iface_count):
                for ssid in common_ssids:
                    rssi = self.rssi_data[i][ssid]
                    rssi_values[ssid].append(rssi)
            avg_rssi = {ssid: sum(values) / len(values) for ssid, values in rssi_values.items()}
            # print('Нижний уровень готов записать данные для верхнего')
            with self.condition:
                # print('Нижний уровень начал запись данных')

                self.last_rssi_snapshot = copy.deepcopy(self.rssi_data)

                # Обновляем avg_rssi_data
                for ssid, new_avg in avg_rssi.items():
                    # Добавляем новое среднее значение.
                    self.avg_rssi_data[ssid].append(new_avg)

                # Удаляем устройства, которые больше не существуют в avg_rssi
                devices_to_remove = [ssid for ssid in self.avg_rssi_data if ssid not in avg_rssi]

                for ssid in devices_to_remove:
                    del self.avg_rssi_data[ssid]
                self.condition.notify()  # Уведомляем о новых данных
            for values in self.rssi_data.values():
                values.clear()
            # print('Замеры собраны и обработаны, адаптеры могут начать новую итерацию получения замеров!')
            self.barrier.wait()

    def collect_rssi_thread(self, iface, index):
        while self.run_adapters:
            try:
                rssi_dict = self.get_rssi_readings(iface)
                if not rssi_dict:
                    print(f'Адаптер {iface} завершает работу.')
                    break

                for ssid, rssi in rssi_dict.items():
                    self.rssi_data[index][ssid] = rssi

                # Барьер
                self.barrier.wait()

            except threading.BrokenBarrierError:
                print(f'Барьер сломан. Поток {iface} завершает работу.')
                break
        print(f'Поток {iface} завершён.')

    def safe_scan(self, iface):
        """Проверяет статус адаптера и выполняет безопасное сканирование."""
        # print(f'Статус ({iface.name()}):', iface.status())
        try:
            while self.run_adapters and iface.status() == const.IFACE_SCANNING:
                print(f'Пропуск хода для {iface.name()}')
                time.sleep(0.1)
            else:
                # print('Проверка цикла')
                if not self.run_adapters:
                    print('Мне запретили работать с адаптером, я ухожу')
                    return
            iface.scan()
        except ConnectionRefusedError:
            print('Я словил ошибку, все хорошо!!!')
            raise ConnectionRefusedError(f'Адаптер {iface} был неожиданно отключен')

    def get_rssi_readings(self, iface):
        rssi_value = None
        try:
            self.safe_scan(iface)
            scan_results = iface.scan_results()
        except ConnectionRefusedError as er:
            print(f'Внешний слой поймал искусственную ошибку: {er}')
            return None
        wifi_dict = {ssid_update(result.ssid): result.signal for result in scan_results if result.ssid}
        # print(len(wifi_dict))
        # result_dict = {ssid: wifi_dict[ssid]} if ssid and ssid in wifi_dict else (wifi_dict if ssid is None else {})
        return wifi_dict
