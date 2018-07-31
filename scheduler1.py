import utime

def time_shift(time, years=0, days=0, hours=0, minutes=0, seconds=0):
    t1, t2, t3, t4, t5 = 0, 0, 0 ,0 ,0
    if years != 0:
        t1 = years*365*24*60*60
    if days != 0:
        t2 = days*24*60*60
    if hours != 0:
        t3 = hours*60*60
    if minutes != 0:
        t4 = minutes*60
    if seconds != 0:
        t5 = seconds

    return utime.ticks_add(time, t1+t2+t3+t4+t5)

def time_left(ticks):
    day, hours, minutes, seconds = 0, 0, 0, 0
    days = int(ticks/(24*60*60))
    hours =int((ticks - days*24*60*60)/(60*60))
    minutes = int((ticks-day*24*60*60-hours*60*60)/60)
    seconds = ticks - minutes*60 - hours*60*60 - days*24*60*60

    return (days, hours, minutes, seconds)

start_time=utime.time()
future_time=time_shift(start_time, days=20)
#print(future_time)
while True:
    rem_ticks= utime.ticks_diff(future_time,utime.time())
    if rem_ticks > 0:
        rem = time_left(rem_ticks)
        print(rem)
        utime.sleep(0.5)
        if rem[0]>0:
            print('%d days %02d:%02d:%02d' %(rem[0], rem[1], rem[2], rem[3]))
        else:
            print('%02d:%02d:%02d' %(rem[1], rem[2], rem[3]))

    else:
        break


