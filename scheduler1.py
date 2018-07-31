import utime
import _thread


class uScheduler():
    def __init__(self):#, task_dict=None):
        self.weekly_sched = []
        self.utc = 3


    def get_task(self, task_time):
        if task_time is None:
            task_time = {'start_days': [3, 4], 'start_time': '19:00:00', 'end_days': [2, 5], 'end_time': '23:59:00'}
        m = len(self.weekly_sched)+1 #task_time['start_days'])

        for i in range(len(task_time['start_days'])):
            temp = task_time.copy()
            temp['task_num'] = '%d/%d' % (m, i + 1)
            temp['start_days'] = task_time['start_days'][i]
            temp['end_days'] = task_time['end_days'][i]
            temp['start_time'] = task_time['start_time'].strip()
            temp['end_time'] = task_time['end_time'].strip()
            temp['switched'] = 0
            temp['state'] = 0

            self.update_schedule(temp)
            self.weekly_sched.append(temp)

    def start(self):
        _thread.start_new_thread(self.run_schedule,())

    @staticmethod
    def add_time(time, years=0, days=0, hours=0, minutes=0, seconds=0):
        # This methods adds given amount of time for a reference start time
        t1, t2, t3, t4, t5 = 0, 0, 0, 0, 0
        if years != 0:
            t1 = years * 365 * 24 * 60 * 60
        if days != 0:
            t2 = days * 24 * 60 * 60
        if hours != 0:
            t3 = hours * 60 * 60
        if minutes != 0:
            t4 = minutes * 60
        if seconds != 0:
            t5 = seconds

        return utime.ticks_add(time, t1 + t2 + t3 + t4 + t5)

    @staticmethod
    def tics2time_tuple(ticks):
        # convert clicks to clock format
        days = int(ticks / (24 * 60 * 60))
        hours = int((ticks - days * 24 * 60 * 60) / (60 * 60))
        minutes = int((ticks - days * 24 * 60 * 60 - hours * 60 * 60) / 60)
        seconds = ticks - minutes * 60 - hours * 60 * 60 - days * 24 * 60 * 60

        return days, hours, minutes, seconds

    @staticmethod
    def time2ticks(time):
        for i in range(8 - len(time)):
            time = time + (0,)
        return utime.mktime(time)

    def update_schedule(self, time_tuple):
        today = utime.localtime()[6]
        now = utime.time()
        clock_s, clock_e = (), ()
        day_diff_s, day_diff_e = 0, 0

        sp_clock_s = time_tuple['start_time'].split(':')
        sp_clock_e = time_tuple['end_time'].split(':')

        for i, current_val in enumerate(sp_clock_s):
            clock_s = clock_s + (int(current_val),)

        for i, current_val in enumerate(sp_clock_e):
            clock_e = clock_e + (int(current_val),)

        time_tuple['start_time'] = utime.localtime()[:3] + clock_s
        time_tuple['end_time'] = utime.localtime()[:3] + clock_e

        # on and off are in same week
        if time_tuple['start_days'] <= time_tuple['end_days']:
            if today + 2 > time_tuple['start_days'] and today + 2 > time_tuple['end_days']:
                day_diff_s = 7 - abs(today + 2 - time_tuple['start_days'])
                # print('a')
            elif today + 2 > time_tuple['start_days'] and today + 2 <= time_tuple['end_days']:
                day_diff_s = 0
                # print('a')

            elif today + 2 < time_tuple['start_days']:
                day_diff_s = time_tuple['start_days'] - (today + 2)
                # print('c')

            if today + 2 > time_tuple['end_days']:
                day_diff_e = 7 - abs(today + 2 - time_tuple['start_days'])
                # print('d')
            else:
                day_diff_e = time_tuple['end_days'] - (today + 2)
                # print('f')

        # off is next week
        if time_tuple['start_days'] > time_tuple['end_days']:
            if today + 2 > time_tuple['start_days']:
                day_diff_s = 7 - abs(today + 2 - time_tuple['start_days'])
                day_diff_e = day_diff_s - (time_tuple['start_days'] - time_tuple['end_days'])
                # print('g')
            else:
                day_diff_s = time_tuple['start_days'] - (today + 2)
                day_diff_e = day_diff_s + 7 - (time_tuple['start_days'] - time_tuple['end_days'])
                # print('h')

        temp_s = self.add_time(now, days=day_diff_s)
        temp_e = self.add_time(now, days=day_diff_e)
        time_tuple_s = utime.localtime(temp_s)[:3] + clock_s
        ticks_s = self.time2ticks(time_tuple_s)
        time_tuple_e = utime.localtime(temp_e)[:3] + clock_e
        ticks_e = self.time2ticks(time_tuple_e)

        time_tuple['start_ticks'] = ticks_s
        time_tuple['end_ticks'] = ticks_e
        time_tuple['start_time'] = utime.localtime(temp_s)[:3]
        time_tuple['end_time'] = utime.localtime(temp_e)[:3]

        print("Schedule created: ", time_tuple)
        return time_tuple

    @staticmethod
    def timetuple2clock( time_tuple):
        if time_tuple[0] > 0:
            time_str = '%d days %02d:%02d:%02d' % (time_tuple[0], time_tuple[1], time_tuple[2], time_tuple[3])
        else:
            time_str = '%02d:%02d:%02d' % (time_tuple[1], time_tuple[2], time_tuple[3])
        return time_str

    def run_schedule(self):

        while True:
            for i, current_sched in enumerate(self.weekly_sched):
                ticks2start = utime.ticks_diff(current_sched['start_ticks'], utime.time() + self.utc * 3600)
                ticks2end = utime.ticks_diff(current_sched['end_ticks'], utime.time() + self.utc * 3600)

                if ticks2start <= 0 and ticks2end > 0 and current_sched['switched'] == 0:
                    # inside ON interval - turn on
                    print('Task %s is %s, Start:%s ,End:%s, remain:%s' % (
                        current_sched['task_num'], "ON", current_sched['start_time'], current_sched['end_time'],
                        self.timetuple2clock(self.tics2time_tuple(ticks2end))))

                    current_sched['switched'] = 1  # flag that schedule has switched
                    current_sched['state'] = 1  # flag ON STATE
                    self.switch_on()

                elif ticks2end < 0 and current_sched['state'] == 1:
                    # turn off
                    print('Task %s is %s, Start:%s ,End:%s, remain:%s' % (
                        current_sched['task_num'], "OFF", current_sched['start_time'], current_sched['end_time'],
                        self.timetuple2clock(self.tics2time_tuple(ticks2end))))

                    current_sched['state'] = 0  # flag off state
                    current_sched['switched'] = 0  # succesfull end of sched state
                    self.switch_off()
                    self.update_schedule(i)

                elif ticks2start > 0 and current_sched['switched'] == 0:
                    print('Task %s is %s, Start:%s ,End:%s, remain:%s' % (
                        current_sched['task_num'], "WAIT", current_sched['start_time'], current_sched['end_time'],
                        self.timetuple2clock(self.tics2time_tuple(ticks2end))))

            utime.sleep(2)

    def switch_on(self):
        pass

    def switch_off(self):
        pass

def on_command():
    print("ON")

def off_command():
    print("OFF")

b = uScheduler()
# b.get_task({'start_days': [3, 4, 7], 'start_time': '19:00:00', 'end_days': [2, 5, 7], 'end_time': '23:59:00'})
b.get_task({'start_days': [3], 'start_time': '00:00:00', 'end_days': [3], 'end_time': '05:48:30'})
b.switch_on = lambda :on_command()
b.switch_off = lambda :off_command()
b.start()
