import threading
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from pywifi import PyWiFi
from data_sync import DataSync
from rssi_analysis import calculate_average_rssi, get_distance


def main():
    # Настройка интерфейса Tkinter
    root = tk.Tk()
    root.title("Сбор RSSI с адаптеров")

    wifi = PyWiFi()
    interfaces = wifi.interfaces()[1:]  # Пропускаем первый адаптер
    ssid = 'tyanka'

    # Создаем объект синхронизации данных
    data_sync = DataSync(interfaces, ssid)

    # Поток для сбора данных
    collection_thread = threading.Thread(target=data_sync.start_collection)
    collection_thread.start()

    # Настройка графика
    fig, ax = plt.subplots()
    ax.set_title("Среднее значение RSSI")
    ax.set_xlabel("Время (сек)")
    ax.set_ylabel("RSSI")
    ax.set_xlim(0, 60)
    ax.set_ylim(-100, 0)
    x_data, y_data = [], []

    # Встраиваем график в Tkinter
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack()

    # Обновление графика
    def update_plot():
        with data_sync.condition:
            data_sync.condition.wait()  # Ждем, пока появятся новые данные
            if data_sync.avg_rssi_data:
                avg_rssi = data_sync.avg_rssi_data[-1]
                distance = get_distance(avg_rssi)
                print(f"Среднее RSSI: {avg_rssi}, Расстояние: {distance} м")

                # Добавляем данные для графика
                x_data.append(len(x_data))
                y_data.append(avg_rssi)

                # Обновляем график
                ax.clear()
                ax.set_title("Среднее значение RSSI")
                ax.set_xlabel("Время (сек)")
                ax.set_ylabel("RSSI")
                ax.set_xlim(0, 60)
                ax.set_ylim(-100, 0)
                ax.plot(x_data, y_data, marker='o')
                canvas.draw()
        root.after(100, update_plot)

    # Запуск первого обновления
    root.after(100, update_plot)
    root.mainloop()


if __name__ == "__main__":
    main()
