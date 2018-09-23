from umqtt.simple import MQTTClient
import utime
import network
import ntptime
import machine


class Connect2Wifi:
    def __init__(self, ip=None):
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)
        self.connect(ip)

    def is_connected(self):
        return self.sta_if.isconnected()

    def connect(self, ip=None):
        if not self.sta_if.isconnected():
            print('connecting to network...')
            self.sta_if.connect("HomeNetwork_2.4G", "guyd5161")

            # assign staticIP
            # if ip is not None:
            #     self.sta_if.ifconfig((ip, "255.255.255.0", "192.168.2.1", "192.168.2.1"))  # static IP
            # while not self.sta_if.isconnected():
            #     pass
            # utime.sleep(2)
        print('network config:', self.sta_if.ifconfig())


class ClockUpdate:
    def __init__(self, utc_shift=0, update_int=1):
        self.utc_shift = utc_shift
        self.update_int = update_int
        self.future_clock_update = None

        self.create_new_update_time()
        self.update()

    def update(self):
        try:
            ntptime.settime()
            rtc = machine.RTC()

            # daylight saving
            if 9 >= utime.localtime()[1] >= 4:
                daylight = 1
            else:
                daylight = 0

            tm = utime.localtime(utime.mktime(utime.localtime()) + (self.utc_shift + daylight) * 3600)
            tm = tm[0:3] + (0,) + tm[3:6] + (0,)
            rtc.datetime(tm)
            print("clock update successful", utime.localtime())
        except OSError:
            self.notify_error("fail getting NTP server")

    def clock_update(self):
        if utime.ticks_diff(self.future_clock_update, utime.ticks_ms()) < 0:
            self.update()
            self.create_new_update_time()
            return 1
        else:
            return 0

    def create_new_update_time(self):
        update_int = self.update_int * 60 * 60 * 1000  # result in milli-seconds
        self.future_clock_update = utime.ticks_add(utime.ticks_ms(), int(update_int))


class MQTTCommander(Connect2Wifi, ClockUpdate):
    def __init__(self, server, client_id, device_topic, listen_topics, msg_topic=None, static_ip=None, qos=0, user=None,
                 password=None):
        self.server, self.mqtt_client_id = server, client_id
        self.user, self.password, self.qos = user, password, qos
        self.listen_topics, self.msg_topic, self.device_topic = listen_topics, msg_topic, device_topic
        self.mqtt_client, self.arrived_msg = None, None
        self.last_buttons_state, self.last_ping_time = [], None

        self.boot_time = utime.localtime()

        # ########### Time related Parameters ##################
        clock_update_interval = 4  # [hours]
        self.num_of_fails = 2  # reach broker
        self.minutes_in_emergency_mode = 1  # [min]
        self.keep_alive_interval = 60  # [sec]
        # ######################################################

        # ################ Start Services #################################
        Connect2Wifi.__init__(self, static_ip)
        ClockUpdate.__init__(self, utc_shift=2, update_int=clock_update_interval)
        # #################################################################

        self.startMQTTclient()
        utime.sleep(1)

        self.pub('Boot- connected to broker: [%s], device ip: [%s]' % (server, self.sta_if.ifconfig()[0]))
        self.mqtt_wait_loop()

    def startMQTTclient(self):
        self.mqtt_client = MQTTClient(self.mqtt_client_id, self.server, self.qos, user=self.user,
                                      password=self.password, keepalive=self.keep_alive_interval)
        self.mqtt_client.set_callback(self.on_message)
        self.mqtt_client.set_last_will(topic=self.msg_topic,
                                       msg=self.time_stamp() + ' [' + self.device_topic + ']' + ' died', retain=False)

        try:
            self.mqtt_client.connect()
            self.listen_topics.append(self.device_topic)
            for topic in self.listen_topics:
                self.mqtt_client.subscribe(topic)
            self.last_ping_time = utime.ticks_ms()
            return 1
        except OSError:
            self.notify_error("Error connecting MQTT broker")
            return 0

    def pub(self, msg, topic=None):
        try:
            if topic is not None:
                self.mqtt_client.publish(topic, "%s [%s] %s" % (self.time_stamp(), self.device_topic, msg))
            else:
                self.mqtt_client.publish(self.msg_topic, "%s [%s] %s" % (self.time_stamp(), self.device_topic, msg))
        except OSError:
            self.notify_error("fail to publish to broker")

    def on_message(self, topic, msg):
        def mqtt_commands(msg):
            msgs = ['reset', 'up', 'down', 'status', 'off', 'info']
            output1 = "Topic:[%s], Message: " % (topic.decode("UTF-8").strip())
            if msg == msgs[0]:
                self.pub(output1 + "[Reset CMD]")
                # emergnecy()
            elif msg.lower() == msgs[1]:
                self.switch_up()
                self.pub(output1 + "Remote CMD: [UP]")
            elif msg.lower() == msgs[2]:
                self.switch_down()
                self.pub(output1 + "Remote CMD: [DOWN]")
            elif msg.lower() == msgs[3]:
                self.pub(output1 + "Status CMD: [%s,%s,%s,%s]" % (
                    self.but_up_state(), self.rel_up_state(), self.but_down_state(), self.rel_down_state()))
            elif msg.lower() == msgs[4]:
                self.switch_off()
                self.pub(output1 + "Remote CMD: [OFF]")
            elif msg.lower() == msgs[5]:
                p = '%d-%d-%d %d:%d:%d' % (
                    self.boot_time[0], self.boot_time[1], self.boot_time[2], self.boot_time[3], self.boot_time[4],
                    self.boot_time[5])
                self.pub('Boot time: [%s], ip: [%s]' % (p, self.sta_if.ifconfig()[0]))

        self.arrived_msg = msg.decode("UTF-8").strip()
        mqtt_commands(msg=self.arrived_msg)

    def mqtt_wait_loop(self):
        fails_counter, off_timer, tot_disconnections = 0, 0, 0

        self.last_buttons_state = [self.but_up_state(), self.but_down_state()]

        while True:
            # detect button press
            self.check_switch_change()
            self.clock_update()
            self.ping_broker(keep_time=self.keep_alive_interval)

            try:
                # verify existance of MQTT server
                self.mqtt_client.check_msg()
                fails_counter = 0

            except OSError:
                fails_counter += 1

                self.notify_error("Fail Status #%d: Wifi is Connected: %s " % (fails_counter, self.is_connected()))

                # Check Wifi connectivity
                if self.is_connected() == 0:
                    self.notify_error("Try reconnect wifi #%d" % fails_counter)
                else:
                    # wifi is connected.Try reconnect MQTT client
                    if fails_counter <= self.num_of_fails:
                        # connection failed:
                        if self.startMQTTclient() == 0:
                            utime.sleep(2)
                        else:
                            continue
                    else:
                        # Emeregncy mode- stop looking for MQTT for some time, and comply only to physical switches
                        self.notify_error(
                            "fail reaching MQTT server- %d times, entering emergency mode for %d minutes" % (
                                self.num_of_fails, self.minutes_in_emergency_mode))

                        start_timeout = utime.ticks_ms()
                        time_in_loop = 0
                        while time_in_loop < self.minutes_in_emergency_mode:
                            # accept button switch during this time
                            self.check_switch_change()
                            time_in_loop = (utime.ticks_ms() - start_timeout) / 1000 / 60
                            utime.sleep(self.t_SW)
                        fails_counter = 0
                        # exiting emergency
            utime.sleep(self.t_SW)


    def check_switch_change(self):
        current_buttons_state = [self.but_up_state(), self.but_down_state()]
        if self.last_buttons_state != current_buttons_state:
            # debounce
            utime.sleep(self.t_SW)
            # check again
            if self.last_buttons_state != [self.but_up_state(), self.but_down_state()]:
                self.button_switch()
                self.last_buttons_state = [self.but_up_state(), self.but_down_state()]

    @staticmethod
    def time_stamp():
        t_tup = utime.localtime()
        t = "[%d-%02d-%02d %02d:%02d:%02d.%02d]" % (t_tup[0], t_tup[1], t_tup[2],
                                                    t_tup[3], t_tup[4], t_tup[5], t_tup[6])
        return t

    def notify_error(self, msg):
        self.append_log(msg)

    def ping_broker(self, keep_time):
        # for keepalive purposes
        if utime.ticks_ms() > self.last_ping_time + keep_time * 1000:
            try:
                self.mqtt_client.ping()
                self.last_ping_time = utime.ticks_ms()
            except OSError:
                # fail
                pass
