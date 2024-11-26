import threading
import tkinter as tk
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import matplotlib.pyplot as plt
from pywifi import PyWiFi
from data_sync import DataSync
from rssi_analysis import calculate_average_rssi, get_distance


def main():
    wifi = PyWiFi()
    interfaces = wifi.interfaces()[1:]  # Пропускаем первый адаптер
    ssid = None

    # Создаем объект синхронизации данных
    data_sync = DataSync(interfaces)

    # Поток для сбора данных
    collection_thread = threading.Thread(target=data_sync.start_collection)
    collection_thread.start()

    with data_sync.condition:
        data_sync.condition.wait()  # Ждем, пока появятся новые данные
        print('Дождались данных, можно вывести')
        distances = {ssid: get_distance(rssis[-1]) for ssid, rssis in data_sync.avg_rssi_data.items()}
        for ssid, d in distances.items():
            print(ssid, d)
        print()


if __name__ == "__main__":
    main()
