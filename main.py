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

    # Обновление графика
    def update_plot():
        with data_sync.condition:
            data_sync.condition.wait()  # Ждем, пока появятся новые данные
            avg_rssi = data_sync.avg_rssi_data[-1]
            distance = get_distance(avg_rssi)
            print(f"Среднее RSSI: {avg_rssi}, Расстояние: {distance} м")


if __name__ == "__main__":
    main()
