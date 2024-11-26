def ssid_update(ssid):
    if not ssid.strip().startswith('\\x'):
        return ssid
    decoded_ssid = bytes(ssid, "utf-8").decode("unicode_escape").encode("latin1").decode("utf-8")
    return decoded_ssid