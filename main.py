import threading
import tkinter as tk
from fcntl import FASYNC
from tkinter import Canvas, Frame, Scrollbar
from pywifi import PyWiFi
from data_sync import DataSync
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

# Путь к иконке Wi-Fi
ICON_PATH = "wifi_icon.png"  # Замените на ваш путь к иконке Wi-Fi


class WiFiApp(tk.Tk):
    def __init__(self, data_sync):
        super().__init__()
        self.data_sync = data_sync
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.current_page = None
        self.selected_ssid = None

        # Настройка окна
        self.title("Wi-Fi RSSI Monitor")
        self.geometry("400x600")
        self.resizable(False, True)
        self.minsize(400, 325)
        self.maxsize(800, 600)
        self.configure(bg="#0D0D0D")

        self.container = Frame(self, bg="#0D0D0D")
        self.container.pack(fill="both", expand=True)

        self.pages = {}

        self.show_page("MainPage")

    def on_close(self):
        if self.current_page == "DetailsPage":
            self.pages[self.current_page].stop_update()
        self.destroy()

    def create_page(self, page_name):
        """
        Создаёт страницу по имени и добавляет её в словарь страниц.
        """
        if page_name == "MainPage":
            self.pages[page_name] = MainPage(self.container, self, self.data_sync)
        elif page_name == "DetailsPage":
            self.pages[page_name] = DetailsPage(
                self.container, self, self.data_sync
            )
        self.pages[page_name].place(relwidth=1, relheight=1)

    def show_page(self, page_name, ssid=None):
        """
        Переключает видимость между страницами.
        """
        if page_name not in self.pages:
            self.create_page(page_name)

        if self.current_page and \
            hasattr(self.pages[self.current_page], "stop_update"):
            self.pages[self.current_page].stop_update()

        self.current_page = page_name

        page = self.pages[page_name]
        page.tkraise()

        self.selected_ssid = ssid
        if hasattr(page, "ssid"):
            if not self.selected_ssid:
                raise Exception("ssid не был передан, хотя вроде как вызывается detailpage")
            page.ssid = self.selected_ssid

        if hasattr(page, "start_update"):
            page.start_update()

        # Настраиваем размеры окна для страницы
        self.resizable(True, True)
        if page_name == "DetailsPage":
            self.geometry("800x600")  # Изменяем размер для подробностей
        else:
            self.geometry("400x600")  # Возвращаем размер для главной страницы
        self.resizable(False, True)


class MainPage(Frame):
    def __init__(self, parent, controller, data_sync):
        super().__init__(parent, bg="#0D0D0D")
        self.controller = controller
        self.data_sync = data_sync

        self.create_widgets()

        # Настраиваем прокрутку колесиком
        self.scroll_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.scroll_canvas.bind_all("<Button-4>", self.on_mouse_wheel)  # Linux вверх
        self.scroll_canvas.bind_all("<Button-5>", self.on_mouse_wheel)  # Linux вниз

        # Храним виджеты для обновления
        self.items = {}

        self.update_thread = None
        self.running = False

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
        print('Запустился frame_config для main')
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        self.scroll_canvas.itemconfig(self.scroll_window, width=self.scroll_canvas.winfo_width())

    def on_mouse_wheel(self, event):
        """
        Обрабатывает прокрутку колесиком мыши.
        """
        print('Крутится колесо мыши в main page')
        if event.num == 4 or event.delta > 0:  # Вверх (Linux или Windows)
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:  # Вниз (Linux или Windows)
            self.scroll_canvas.yview_scroll(1, "units")

    def start_update(self):
        """Запускает обновление интерфейса."""
        self.running = True
        self.update_thread = threading.Thread(target=self.update_interface)
        self.update_thread.daemon = True
        self.update_thread.start()

    def stop_update(self):
        """Останавливает обновление интерфейса."""
        self.running = False

    def update_interface(self):
        """
        Обновление интерфейса при появлении новых данных.
        """
        while self.running:
            with self.data_sync.condition:
                self.data_sync.condition.wait()  # Ждем новые данные

                if not self.running:
                    break
                print("MainPage пошел обновляться")
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
            command=lambda: self.controller.show_page("DetailsPage", ssid),
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


class DetailsPage(Frame):
    def __init__(self, parent, controller, data_sync):
        super().__init__(parent, bg="#0D0D0D")
        self.controller = controller
        self.data_sync = data_sync
        self.ssid = None

        self.window_size = 4
        self.threshold = 7

        self.create_widgets()

        self.update_thread = None
        self.running = False

    def analyze_trend(self, last_values):
        """
        Анализирует тренд на основе последних значений.
        Возвращает одну из аннотаций: 'up', 'down', 'stationary' или 'uncertain'.
        """
        if len(last_values) < 2 * self.window_size:
            return "uncertain"

        values_list = list(last_values)

        # Разделяем окно на два перекрывающихся
        window1 = values_list[:self.window_size]
        window2 = values_list[self.window_size:2*self.window_size]

        # Средние значения окон
        avg1 = sum(window1) / len(window1)
        avg2 = sum(window2) / len(window2)

        # Анализируем изменения
        if abs(avg1 - avg2) <= self.threshold:
            return "stationary"  # Малое изменение
        elif avg1 < avg2:
            return "up"  # Сигнал увеличивается (приближение)
        else:
            return "down"  # Сигнал уменьшается (удаление)

    def update_interface(self):
        """
        Обновление интерфейса при появлении новых данных.
        """
        while self.running:
            with self.data_sync.condition:
                self.data_sync.condition.wait()  # Ждем новые данные

                if not self.running:
                    break
                print("DetailPage пошел обновляться")
                last_values = self.data_sync.avg_rssi_data.get(self.ssid, None)

                annotation_type = "uncertain"
                if last_values:
                    annotation_type = self.analyze_trend(last_values)

                self.update_graph(last_values, annotation_type)
                if last_values:
                    value_str = f"{last_values[-1]:.2f}"
                else:
                    value_str = "-"

                self.device_rssi_label.config(text=f"RSSI: {value_str}")

    def update_graph(self, last_values, annotation_type="uncertain"):
        """
        Обновляет данные графика.
        """
        if hasattr(self, "line"):
            self.line.remove()

        if hasattr(self, "annotation"):
            self.annotation.remove()

        if last_values:
            x_data = np.arange(8 - len(last_values), 8)
            y_data = list(last_values)
            self.line, = self.ax.plot(x_data, y_data, marker='o', color='white')

        if annotation_type:
            x_position = 7.5
            y_position = -50

            annotation_map = {
                "uncertain": {"text": "?", "color": "white", "size": 60},
                "stationary": {"text": "≈", "color": "white", "size": 60},
                "down": {"text": "↓", "color": "#FF073A", "size": 60},
                "up": {"text": "↑", "color": "#39FF14", "size": 60},
            }

            if annotation_type in annotation_map:
                props = annotation_map[annotation_type]
                # Основная аннотация
                self.annotation = self.ax.annotate(
                    props["text"],
                    xy=(x_position, y_position),
                    color=props["color"],
                    fontsize=props["size"],
                    ha="center",
                    va="center",
                    fontfamily="monospace"
                )

        self.canvas.draw()

    def create_widgets(self):
        back_button = tk.Button(
            self,
            text="🢀",
            font=("Arial", 10),
            bg="#007FD0",
            fg="#0D0D0D",
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.controller.show_page("MainPage"),
        )
        back_button.pack(anchor="nw")

        graph_frame = tk.Frame(self, bg="#0D0D0D")
        graph_frame.pack(fill="both", expand=False, padx=10, pady=5)

        self.fig = plt.figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)

        num_ticks = 9
        x_ticks = np.linspace(0, 8, num_ticks)
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(['8 секунд', '', '', '', '', '', '', '1', 'Вердикт'])
        self.ax.set_xlim(0, 8)

        y_ticks = np.arange(-100, 1, 10)
        self.ax.set_yticks(y_ticks)
        self.ax.set_ylim(-100, 0)

        self.ax.grid(True, which='major', color='#007FD0', linestyle='--', linewidth=0.5, alpha=0.2)

        self.fig.patch.set_facecolor("#0D0D0D")
        self.ax.set_facecolor("#0D0D0D")
        self.ax.spines['bottom'].set_color("#007FD0")
        self.ax.tick_params(axis='x', colors='#007FD0')
        self.ax.spines['left'].set_color("#007FD0")
        self.ax.tick_params(axis='y', colors='#007FD0')
        self.ax.spines['top'].set_color("none")
        self.ax.spines['right'].set_color("none")

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # RSSI Информация
        bottom_section = tk.Frame(self, bg="#0D0D0D")
        bottom_section.pack(fill="x", padx=10, pady=10)

        info_frame = tk.Frame(bottom_section, bg="#0D0D0D")
        info_frame.pack(side="left", fill="y", padx=10, pady=5)

        self.title = tk.Label(
            info_frame,
            text=f"SSID: -",
            font=("Arial", 16),
            fg="#007FD0",
            bg="#0D0D0D"
        )
        self.title.pack(anchor="w", pady=5)

        self.device_rssi_label = tk.Label(
            info_frame,
            text=f"RSSI: -",
            font=("Arial", 16),
            fg="#007FD0",
            bg="#0D0D0D"
        )
        self.device_rssi_label.pack(anchor="w", pady=5)

        controls_frame = tk.Frame(bottom_section, bg="#0D0D0D")
        controls_frame.pack(side="right", fill="y", padx=10, pady=5)

        window_size_label = tk.Label(
            controls_frame,
            text="Размер окна:",
            font=("Arial", 12),
            fg="#007FD0",
            bg="#0D0D0D"
        )
        window_size_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)  # Левый край

        self.window_size_entry = tk.Entry(
            controls_frame,
            font=("Arial", 12),
            bg="#0D0D0D",
            fg="#007FD0",
            highlightthickness=1,
            highlightbackground="#007FD0",
            highlightcolor="#FFFFFF",
            borderwidth=0,
            insertbackground="#007FD0",
            width=20  # Одинаковая ширина для всех полей
        )
        self.window_size_entry.insert(0, "4")  # Значение по умолчанию
        self.window_size_entry.grid(row=0, column=1, padx=5, pady=5)

        threshold_label = tk.Label(
            controls_frame,
            text="Порог:",
            font=("Arial", 12),
            fg="#007FD0",
            bg="#0D0D0D"
        )
        threshold_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.threshold_entry = tk.Entry(
            controls_frame,
            font=("Arial", 12),
            bg="#0D0D0D",
            fg="#007FD0",
            highlightthickness=1,
            highlightbackground="#007FD0",
            highlightcolor="#FFFFFF",
            borderwidth=0,
            insertbackground="#007FD0",
            width=20  # Одинаковая ширина для всех полей
        )
        self.threshold_entry.insert(0, "7")  # Значение по умолчанию
        self.threshold_entry.grid(row=1, column=1, padx=5, pady=5)


    def start_update(self):
        self.title.config(text=f"SSID: {self.ssid}")
        self.running = True
        self.update_thread = threading.Thread(target=self.update_interface)
        self.update_thread.daemon = True
        self.update_thread.start()

    def stop_update(self):
        self.title.config(text=f"SSID: -")
        self.device_rssi_label.config(text=f"RSSI: -")
        self.running = False
        self.update_thread.join()
        self.close_graph()

    def close_graph(self):
        if self.fig:
            plt.close(self.fig)
            self.fig = None


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
