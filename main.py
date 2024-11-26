import threading
import tkinter as tk
from tkinter import Canvas, Frame, Scrollbar
from pywifi import PyWiFi
from data_sync import DataSync

# Путь к иконке Wi-Fi
ICON_PATH = "wifi_icon.png"  # Замените на ваш путь к иконке Wi-Fi


class WiFiApp(tk.Tk):
    def __init__(self, data_sync):
        super().__init__()
        self.data_sync = data_sync

        # Настройка окна
        self.title("Wi-Fi RSSI Monitor")
        self.geometry("400x600")
        self.resizable(False, True)
        self.minsize(400, 325)
        self.maxsize(400, 600)
        self.configure(bg="#0D0D0D")

        # Создаем виджеты
        self.create_widgets()

        # Настраиваем прокрутку колесиком
        self.scroll_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.scroll_canvas.bind_all("<Button-4>", self.on_mouse_wheel)  # Linux вверх
        self.scroll_canvas.bind_all("<Button-5>", self.on_mouse_wheel)  # Linux вниз

        # Храним виджеты для обновления
        self.items = {}

        # Запускаем поток обновления интерфейса
        self.update_thread = threading.Thread(target=self.update_interface)
        self.update_thread.daemon = True
        self.update_thread.start()

    def create_widgets(self):
        # Заголовок приложения
        title = tk.Label(
            self,
            text="Wi-Fi RSSI Monitor",
            font=("Arial", 16),
            fg="#007FD0",
            bg="#0D0D0D"
        )
        title.pack(pady=10, fill="x")

        # Создаем прокручиваемую область
        self.scroll_canvas = Canvas(self, bg="#0D0D0D", highlightthickness=0)
        self.scroll_frame = Frame(self.scroll_canvas, bg="#0D0D0D")
        self.scrollbar = Scrollbar(
            self, orient="vertical", command=self.scroll_canvas.yview, background="#007FD0", highlightthickness=0,
            borderwidth=0
        )
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Размещение виджетов
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scroll_window = self.scroll_canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw"
        )

        # Привязка события изменения размеров
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)

    def on_frame_configure(self, event=None):
        """
        Обновляем область прокрутки, когда содержимое Frame изменяется.
        """
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        self.scroll_canvas.itemconfig(self.scroll_window, width=self.scroll_canvas.winfo_width())

    def on_mouse_wheel(self, event):
        """
        Обрабатывает прокрутку колесиком мыши.
        """
        if event.num == 4 or event.delta > 0:  # Вверх (Linux или Windows)
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Вниз (Linux или Windows)
            self.scroll_canvas.yview_scroll(1, "units")

    def update_interface(self):
        """
        Обновление интерфейса при появлении новых данных.
        """
        while True:
            with self.data_sync.condition:
                self.data_sync.condition.wait()  # Ждем новые данные

                # Обновляем список устройств
                self.update_list()

    def update_list(self):
        """
        Обновляет список устройств на основе avg_rssi_data.
        """
        # Пройдем по текущим данным
        for ssid, rssis in self.data_sync.avg_rssi_data.items():
            avg_rssi = rssis[-1]  # Берем последнее среднее значение RSSI

            # Если элемент уже существует, обновим его
            if ssid in self.items:
                self.update_list_item(self.items[ssid], ssid, avg_rssi)
            else:
                # Если элемента нет, создаем его
                self.items[ssid] = self.create_list_item(ssid, avg_rssi)

        # Удаляем лишние элементы, которых больше нет в данных
        current_ssids = set(self.data_sync.avg_rssi_data.keys())
        for ssid in list(self.items.keys()):
            if ssid not in current_ssids:
                self.items[ssid].destroy()
                del self.items[ssid]

    def create_list_item(self, ssid, avg_rssi):
        """
        Создает один элемент списка.
        """
        # Контейнер для элемента
        frame = Frame(self.scroll_frame, bg="#000000", pady=5)
        frame.pack(fill="x", padx=10, pady=5)

        # Иконка Wi-Fi
        if ICON_PATH:
            try:
                icon = tk.PhotoImage(file=ICON_PATH)
                icon_label = tk.Label(frame, image=icon, bg="#000000")
                icon_label.image = icon  # Хранение ссылки, чтобы не удалялось
                icon_label.pack(side="left", padx=10)
            except Exception as e:
                print(f"Ошибка загрузки иконки: {e}")

        # Текстовая информация
        ssid_label = tk.Label(
            frame, text=ssid, font=("Arial", 12), fg="#FFFFFF", bg="#000000"
        )
        ssid_label.pack(anchor="e", padx=10)

        rssi_label = tk.Label(
            frame,
            text=f"RSSI: {avg_rssi:.2f}",
            font=("Arial", 12),
            fg="#007FD0",
            bg="#000000",
        )
        rssi_label.pack(anchor="w")

        # Кнопка для подробностей
        details_button = tk.Button(
            frame,
            text="Подробнее",
            font=("Arial", 10),
            bg="#007FD0",
            fg="#0D0D0D",
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.show_details(ssid),
        )
        details_button.pack(anchor="e", padx=10)

        # Вернем контейнер элемента
        return frame

    def update_list_item(self, frame, ssid, avg_rssi):
        """
        Обновляет существующий элемент списка.
        """
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Label):
                if widget.cget("text").startswith("RSSI:"):
                    widget.config(text=f"RSSI: {avg_rssi:.2f}")

    def show_details(self, ssid):
        """
        Заглушка для перехода на подробности устройства.
        """
        print(f"Показать подробности для {ssid}")


def main():
    # Настройка Wi-Fi
    wifi = PyWiFi()
    interfaces = wifi.interfaces()[1:]  # Пропускаем первый адаптер

    # Создаем объект синхронизации данных
    data_sync = DataSync(interfaces)

    # Поток для сбора данных
    collection_thread = threading.Thread(target=data_sync.start_collection)
    collection_thread.daemon = True
    collection_thread.start()

    # Запускаем приложение
    app = WiFiApp(data_sync)
    app.mainloop()


if __name__ == "__main__":
    main()
