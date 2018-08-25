import ntptime
import machine
import utime

ntptime.settime()
rtc = machine.RTC()
utc_shift = 3

tm = utime.localtime(utime.mktime(utime.localtime()) + utc_shift*3600)
tm = tm[0:3] + (0,) + tm[3:6] + (0,)
rtc.datetime(tm)
