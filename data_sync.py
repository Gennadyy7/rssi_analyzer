import threading
import time
from collections import deque

class DataSync:
    def __init__(self, interfaces, ssid, rssi_buffer_size=7, avg_buffer_size=7):
        self.interfaces = interfaces
        self.ssid = ssid
        self.rssi_data = {i: deque(maxlen=rssi_buffer_size) for i in range(len(interfaces))}
        self.avg_rssi_data = deque(maxlen=avg_buffer_size)
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
            time.sleep(interval)
            self.barrier.wait()
            iface_count = len(self.rssi_data)
            with self.condition:
                avg_rssi = sum(self.rssi_data[i][-1] for i in range(iface_count)) / iface_count
                self.avg_rssi_data.append(avg_rssi)
                print("Среднее RSSI:", avg_rssi)
                self.condition.notify()  # Уведомляем о новых данных

    def collect_rssi_thread(self, iface, index):
        """
        Поток для сбора данных с одного интерфейса.
        """
        from wifi_collector import get_rssi_readings  # Импорт из другого модуля
        while True:
            rssi_value = get_rssi_readings(iface, self.ssid)
            print(f'Интерфейс {iface.name()}, RSSI: {rssi_value}')
            self.rssi_data[index].append(rssi_value)
            self.barrier.wait()
