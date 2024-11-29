import subprocess


def give_rights():
    sudo_command = "sudo -S -i"
    password = "nageraper7"
    chmod_command = "chmod -R 777 /var/run/wpa_supplicant"
    process = subprocess.Popen(sudo_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, shell=True)
    process.communicate(input=password + '\n')
    process = subprocess.Popen(f"sudo -S {chmod_command}", stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, shell=True)
    process.communicate(input=password + '\n')