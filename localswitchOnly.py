import utime
import machine


def switch_up():
    pin_down.value(1)
    utime.sleep(t_SW)
    pin_up.value(0)


def switch_down():
    pin_up.value(1)
    utime.sleep(t_SW)
    pin_down.value(0)


def switch_off():
    pin_down.value(1)
    utime.sleep(t_SW)
    pin_up.value(1)


def but_down_state():
    if pin_button_down.value() == 0:  # pressed
        return 1
    elif pin_button_down.value() == 1:  # released
        return 0


def but_up_state():
    if pin_button_up.value() == 0:  # pressed
        return 1
    elif pin_button_up.value() == 1:  # released
        return 0


def rel_up_state():
    if pin_up.value() == 1:  # open
        return 0
    elif pin_up.value() == 0:  # closed
        return 1


def rel_down_state():
    if pin_down.value() == 1:  # open
        return 0
    elif pin_down.value() == 0:  # closed
        return 1


def PBit():
    print("PowerOnBit started")
    switch_down()
    utime.sleep(t_SW * 4)
    switch_up()
    utime.sleep(t_SW * 4)
    switch_off()


def button_switch():
    # physical button switch
    last_state_register = [but_up_state(), but_down_state()]
    PBit()

    while True:
        if last_state_register != [but_up_state(), but_down_state()]:

            # switch up
            if but_up_state() == 1 and rel_up_state() == 0:
                switch_up()
                # try:
                #     A.pub("Button Switch: [UP]")
                # except NameError:
                #     print("UP")

            # switch down
            elif but_down_state() == 1 and rel_down_state() == 0:
                switch_down()
                # try:
                #     A.pub("Button Switch: [DOWN]")
                # except NameError:
                #     print("DOWN")

            elif but_down_state() == 0 and but_down_state() == 0:  # and (rel_down_state() == 1 or rel_up_state() == 1):
                switch_off()
                # try:
                #     A.pub("Button Switch: [OFF]")
                # except NameError:
                #     print("OFF")
            last_state_register = [but_up_state(), but_down_state()]
            # print("end loop")

        utime.sleep(t_SW)


# # ################ Def GPIOs ESP8266 #########################################
# pin_up = machine.Pin(12, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)  # value=1 actually is 0
# pin_down = machine.Pin(14, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
# pin_button_up = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
# pin_button_down = machine.Pin(5, machine.Pin.IN, machine.Pin.PULL_UP)
# t_SW = 0.1
# ######################################################################

# ################ Def GPIOs ESP32 #########################################
pin_up = machine.Pin(22, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)  # value=1 actually is 0
pin_down = machine.Pin(19, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
pin_button_up = machine.Pin(25, machine.Pin.IN, machine.Pin.PULL_UP)
pin_button_down = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
t_SW = 0.1
######################################################################
button_switch()
