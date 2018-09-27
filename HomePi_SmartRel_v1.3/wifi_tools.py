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
            if ip is not None:
                self.sta_if.ifconfig((ip, "255.255.255.0", "192.168.2.1", "192.168.2.1"))  # static IP
            while not self.sta_if.isconnected():
                pass
            utime.sleep(2)
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

            tm = utime.localtime(utime.mktime(utime.localtime()) + self.utc_shift * 3600)
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
    def __init__(self, server, client_id, topic1, topic2=None, static_ip='', qos=0, user=None, password=None):
        self.server, self.mqtt_client_id = server, client_id
        self.user, self.password, self.qos = user, password, qos
        self.topic1, self.topic2 = topic1, topic2
        self.state_topic = "HomePi/Dvir/Windows/kRoomWindows/State"
        self.mqtt_client, self.arrived_msg = None, None
        self.last_buttons_state = []

        # ########### Parameters ##################
        clock_update_interval = 2  # [hours]
        self.num_of_fails = 2  # reach broker
        self.minutes_in_emergency_mode = 1  # [min]
        # ##########################################

        # ################ Start Services ########################################
        Connect2Wifi.__init__(self, static_ip)
        ClockUpdate.__init__(self, utc_shift=3, update_int=clock_update_interval)
        # ########################################################################

        self.startMQTTclient()
        utime.sleep(1)

        self.pub('Boot- Broker IP: [%s], device ip: [%s]' % (server, self.sta_if.ifconfig()[0]))
        self.mqtt_wait_loop()

    def startMQTTclient(self):
        self.mqtt_client = MQTTClient(self.mqtt_client_id, self.server, self.qos, user=self.user,
                                      password=self.password)  # , keepalive=60)
        self.mqtt_client.set_callback(self.on_message)
        # self.mqtt_client.set_last_will(topic=self.topic2, msg="last_will", retain=False)

        try:
            self.mqtt_client.connect()
            for topic in self.topic1:
                self.mqtt_client.subscribe(topic)
            print("Connected to MQTT server")
            return 1
        except OSError:
            self.notify_error("Error connecting MQTT broker")
            return 0

    def pub(self, msg):
        # publish to "HomePi/Dvir/Messages"
        try:
            self.mqtt_client.publish(self.topic2, "%s [%s] %s" % (self.time_stamp(), self.topic1[0], msg))
        except OSError:
            self.notify_error("fail to publish to broker")

    def on_message(self, topic, msg):
        def mqtt_commands(msg):
            msgs = ['reset', 'up', 'down', 'status', 'off', 'info']

            if msg.lower() == msgs[1]:
                self.switch_up()
                self.pub("Switch CMD: [UP]")
                self.mqtt_client.publish(topic=self.state_topic, payload="up", retain=True)
            elif msg.lower() == msgs[2]:
                self.switch_down()
                self.pub("Switch CMD: [DOWN]")
                self.mqtt_client.publish(topic=self.state_topic, payload="down", retain=True)
            elif msg.lower() == msgs[3]:
                self.pub("Status CMD: Button_UP:[%s], Relay_UP:[%s], Button_Down:[%s], Relay_Down:[%s]" % (
                    self.but_up_state(), self.rel_up_state(), self.but_down_state(), self.rel_down_state()))
            elif msg.lower() == msgs[4]:
                self.switch_off()
                self.pub("OFF")
            elif msg.lower() == msgs[5]:
                self.pub([msg1 for msg1 in msgs])

        self.arrived_msg = msg.decode("UTF-8").strip()
        mqtt_commands(msg=self.arrived_msg)

    def mqtt_wait_loop(self):
        fails_counter = 0
        self.last_buttons_state = [self.but_up_state(), self.but_down_state()]
        while True:
            # detect button press
            self.check_switch_change()
            self.clock_update()

            try:
                # verify existance of MQTT server
                self.mqtt_client.check_msg()

            except OSError:
                fails_counter += 1
                self.notify_error("Fail Status #%d: Wifi is: %s" % (fails_counter, self.is_connected()))

                # Check Wifi connectivity
                if self.is_connected() == 0:
                    self.notify_error("Try reconnect wifi #%d" % fails_counter)
                else:
                    # Try reconnect MQTT client
                    if fails_counter <= self.num_of_fails:
                        if self.startMQTTclient() == 0:
                            utime.sleep(2)
                        else:
                            fails_counter = 0
                    # after  - only button switch without MQTT for some time
                    else:

                        # if self.startMQTTclient() == 0 and fails_counter > self.num_of_fails:
                        #     # Emeregncy mode- stop looking for MQTT for some time, and comply only to physical switches
                        self.notify_error(
                            "fail reaching MQTT server- %d times, entering emergency mode for %d minutes" % (
                                self.num_of_fails, self.minutes_in_emergency_mode))

                        while fails_counter < (60 / self.t_SW) * self.minutes_in_emergency_mode + self.num_of_fails:
                            self.check_switch_change()
                            utime.sleep(self.t_SW)
                            fails_counter += 1

                        fails_counter = 0

            utime.sleep(self.t_SW)

        # Try to disconnect

        # self.mqtt_client.disconnect()
        # except OSError:
        #     self.notify_error("fail to disconnect broker")

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
