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
        # while not self.sta_if.isconnected():
            print('connecting to network...')
            self.sta_if.connect("HomeNetwork_2.4G", "guyd5161")

            # assign staticIP
            if ip is not None:
                self.sta_if.ifconfig((ip, "255.255.255.0", "192.168.2.1", "192.168.2.1"))  # static IP
            while not self.sta_if.isconnected():
                pass
            utime.sleep(2)
        print('network config:', self.sta_if.ifconfig())


class MQTTCommander(Connect2Wifi):
    def __init__(self, server, client_id, topic1, topic2=None, static_ip='', qos=0):
        self.server = server
        self.client_id = client_id
        self.qos = qos
        self.topic1, self.topic2 = topic1, topic2
        self.client, self.arrived_msg = None, None

        Connect2Wifi.__init__(self, static_ip)

        # update clock for drifts
        self.clock = ClockUpdate(utc_shift=3, update_int=1)

        self.startMQTTclient()
        utime.sleep(1)

        self.pub('Boot- server: %s, ip: %s' %(server, self.sta_if.ifconfig()[0]))
        self.wait_for_msg()

    def startMQTTclient(self):
        self.client = MQTTClient(self.client_id, self.server, self.qos)
        self.client.set_callback(self.on_message)
        try:
            self.client.connect()
            for topic in self.topic1:
                self.client.subscribe(topic)
        except OSError:
            print("Error connecting MQTT broker")
            self.append_log("Error connecting MQTT broker")

    def pub(self, msg):
        try:
            self.client.publish(self.topic2, "%s Topic: [%s] Message: %s" % (self.time_stamp(),
                                                                             self.topic1[0], msg))
        except OSError:
            print("fail to publish to broker")
            self.append_log("fail to publish to broker")

    def on_message(self, topic, msg):
        def mqtt_commands(msg):
            msgs = ['reset', 'up', 'down', 'status', 'off', 'info']
            if msg == msgs[0]:
                self.pub("[Reset CMD]")
                # emergnecy()
            elif msg.lower() == msgs[1]:
                self.switch_up()
                self.pub("Switch CMD: [UP]")
            elif msg.lower() == msgs[2]:
                self.switch_down()
                self.pub("Switch CMD: [DOWN]")
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

    def wait_for_msg(self):
        try:
            last_buttons_state = [self.but_up_state(), self.but_down_state()]

            while True:
                # This part belongs define input ( button ) behaviour
                current_buttons_state = [self.but_up_state(), self.but_down_state()]
                if last_buttons_state != current_buttons_state:
                    # debounce
                    utime.sleep(self.t_SW)
                    if last_buttons_state != current_buttons_state:
                        self.button_switch()
                        last_buttons_state = [self.but_up_state(), self.but_down_state()]

                # This is listening for MQTT commands
                try:
                    self.client.check_msg()
                except OSError:
                    self.append_log("fail to access broker for messages")
                    # Reconnect Wifi
                    if self.is_connected() != 0:
                        print("Try reconnect wifi")
                        self.connect()
                    # Reconnect MQTT client
                    self.startMQTTclient()
                    utime.sleep(3)
                    print("Not connected to MQTT server- trying to re-establish connection")

                utime.sleep(self.t_SW)
                # if self.clock.check_update() == 1:
                #     self.pub("Clock update successfully")
        finally:
            try:
                self.client.disconnect()
            except OSError:
                self.append_log("fail to disconnect broker")
                print("Not connected to MQTT server")

    @staticmethod
    def time_stamp():
        t_tup = utime.localtime()
        t = "[%d-%02d-%02d %02d:%02d:%02d.%02d]" % (t_tup[0], t_tup[1], t_tup[2],
                                                    t_tup[3], t_tup[4], t_tup[5], t_tup[6])
        return t


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
            print("fail getting NTP server")
            self.append_log("fail getting NTP server")

    def check_update(self):
        if utime.ticks_diff(self.future_clock_update, utime.ticks_ms()) < 0:
            self.update()
            self.create_new_update_time()
            return 1
        else:
            return 0

    def create_new_update_time(self):
        update_int = self.update_int * 60 * 60 * 1000  # result in milli-seconds
        self.future_clock_update = utime.ticks_add(utime.ticks_ms(), int(update_int))