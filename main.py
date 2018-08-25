def start_wifi():
    import start_wifi


def start_clock_update():
    import utime
    # utime.sleep(2)
    import update_time_2
    print(utime.localtime())


def start_telnet():
    import utelnet  # .utelnetserver as telnet
    # utelnetserver.start()
    # telnet.start()

def start_ftp():
    import uftpd

def start_MQTT():
    import MQTTcom

###### RUN SERVICES #########
start_wifi()
start_clock_update()
# start_ftp()
start_MQTT()
