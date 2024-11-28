from utils.options import options_dict, options


def get_distance(rssi_value, P=-35, N=None):
    if not N:
        N = options_dict[options[1]]
    if rssi_value is None:
        raise ValueError("RSSI значение отсутствует.")
    return 10 ** ((P - rssi_value) / (10 * N))