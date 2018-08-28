import machine
import utime
def start_telnet():
    import utelnet  # .utelnetserver as telnet
    # utelnetserver.start()
    # telnet.start()


def start_ftp():
    import uftpd



def loc_switch():
    import localswitch_only


###### RUN SERVICES #########
import start_wifi
utime.sleep(3)
import update_time_2
import MQTTcom_lite


# pin_up = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
# utime.sleep(1)
# if pin_up.value() != 0:
#     # loc_switch()


