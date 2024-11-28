import threading
import time
from collections import deque, defaultdict
import copy


class DataSync:
    def __init__(self, interfaces, avg_buffer_size=8):
        self.interfaces = interfaces
        # self.rssi_data = {i: deque(maxlen=rssi_buffer_size) for i in range(len(interfaces))}
        self.rssi_data = {i: defaultdict(int) for i in range(len(interfaces))}
        self.avg_rssi_data = defaultdict(lambda: deque(maxlen=avg_buffer_size))
        self.last_rssi_snapshot = None
        self.barrier = threading.Barrier(len(interfaces) + 1)
        self.condition = threading.Condition()

    def start_collection(self, interval=1):
        """
        Запускает сбор данных с интерфейсов.
        :param interval: Интервал между итерациями сбора (в секундах).
        """
        threads = []
        for i, iface in enumerate(self.interfaces):
            t = threading.Thread(target=self.collect_rssi_thread, args=(iface, i))
            threads.append(t)
            t.start()

        while True:
            # print(self.avg_rssi_data)
            time.sleep(interval)
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
        """
        Поток для сбора данных с одного интерфейса.
        """
        from wifi_collector import get_rssi_readings  # Импорт из другого модуля
        while True:
            rssi_dict = get_rssi_readings(iface)
            # print(f'Интерфейс {index}, Длина словаря: {len(rssi_dict)}, Словарь устройство-rssi: {rssi_dict}')
            for ssid, rssi in rssi_dict.items():
                self.rssi_data[index][ssid] = rssi
            self.barrier.wait()
