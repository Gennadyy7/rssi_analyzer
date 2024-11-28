def get_distance(rssi_value, A=-35, n=2):
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