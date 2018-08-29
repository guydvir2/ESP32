import utime
import machine

def loc_switch():
    import localswitchOnly


###### RUN SERVICES #########
import startWifi_staticIP
import updateClockESP

utime.sleep(3)
pin_up = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
utime.sleep(1)
if pin_up.value() == 0:
    print("BYPASS CODE")
else:
    import MQTTcom_lite



