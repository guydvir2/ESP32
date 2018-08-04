import machine
import utime

p14_out = machine.Pin(14, machine.Pin.OUT)  # ,machine.Pin.PULL_UP)
p27_in = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
p26_in = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)

while True:
    # print("p27_in- %d, " % p27_in.value())
    # print("p26_in,", p26_in.value())
    p14_out.value(p27_in.value())
    utime.sleep(0.5)
