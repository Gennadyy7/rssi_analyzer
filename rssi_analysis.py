def calculate_average_rssi(rssi_data):
    """
    Рассчитывает среднее значение RSSI из списка данных.
    :param rssi_data: Список значений RSSI.
    :return: Среднее значение.
    """
    if not rssi_data:
        raise ValueError("Данные RSSI пусты. Невозможно рассчитать среднее.")
    return sum(rssi_data) / len(rssi_data)


def get_distance(rssi_value, A=-40, n=2):
    """
    Переводит RSSI в расстояние с использованием логарифмической модели.
    :param rssi_value: Уровень сигнала RSSI.
    :param A: RSSI на расстоянии 1 метр (по умолчанию -40).
    :param n: Коэффициент ослабления сигнала (по умолчанию 2).
    :return: Оценка расстояния (в метрах).
    """
    if rssi_value is None:
        raise ValueError("RSSI значение отсутствует.")
    return 10 ** ((A - rssi_value) / (10 * n))


def stabilize_rssi(rssi_data, alpha=0.5):
    """
    Стабилизирует значения RSSI с использованием экспоненциального сглаживания.
    :param rssi_data: Список значений RSSI.
    :param alpha: Коэффициент сглаживания (0 < alpha <= 1).
    :return: Стабилизированное значение RSSI.
    """
    if not rssi_data:
        raise ValueError("Данные RSSI пусты. Невозможно выполнить стабилизацию.")
    stabilized_value = rssi_data[0]
    for value in rssi_data[1:]:
        stabilized_value = alpha * value + (1 - alpha) * stabilized_value
    return stabilized_value
