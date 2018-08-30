from umqtt.simple import MQTTClient
import utime
import machine
import network
import ntptime


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
        print('network config:', self.sta_if.ifconfig())


class MQTTCommander(Connect2Wifi):
    def __init__(self, server, client_id, topic1, topic2=None, static_ip=''):
        self.server = server
        self.client_id = client_id
        self.topic1, self.topic2 = topic1, topic2
        self.client, self.arrived_msg = None, None

        Connect2Wifi.__init__(self, static_ip)

        # update clock for drifts
        self.clock = ClockUpdate(utc_shift=3, update_int=24)

        self.start_client()
        utime.sleep(1)

        self.pub('System Boot')
        self.wait_for_msg()

    def start_client(self):
        self.client = MQTTClient(self.client_id, self.server, 0)
        self.client.set_callback(self.on_message)
        try:
            self.client.connect()
            for topic in self.topic1:
                self.client.subscribe(topic)
        except OSError:
            print("Error connecting MQTT broker")

    def pub(self, msg):
        try:
            self.client.publish(self.topic2, "%s Topic: [%s] Message: %s" % (self.time_stamp(),
                                                                             self.topic1[0], msg))
        except OSError:
            print("Not connected to MQTT server")

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
            last_state_register = [self.but_up_state(), self.but_down_state()]
            while True:
                # This part belongs define input ( button ) behaviour
                nowState = [self.but_up_state(), self.but_down_state()]
                if last_state_register != nowState:
                    # debounce
                    utime.sleep(self.t_SW)
                    if last_state_register != nowState:
                        print(nowState)
                        self.button_switch()
                        last_state_register = [self.but_up_state(), self.but_down_state()]

                # This is listening for MQTT commands
                try:
                    self.client.check_msg()
                except OSError:
                    # Reconnect Wifi
                    if self.is_connected() != 0:
                        print("Try reconnect wifi")
                        self.connect()
                    # Reconnect MQTT client
                    self.start_client()
                    utime.sleep(3)
                    print("Not connected to MQTT server- trying to re-establish connection")

                utime.sleep(self.t_SW)
                self.clock.check_update()
        finally:
            try:
                self.client.disconnect()
            except OSError:
                print("Not connected to MQTT server")

    @staticmethod
    def time_stamp():
        t_tup = utime.localtime()
        t = "[%d-%02d-%02d %02d:%02d:%02d.%02d]" % (t_tup[0], t_tup[1], t_tup[2],
                                                    t_tup[3], t_tup[4], t_tup[5], t_tup[6])
        return t


class DualRelaySwitcher(MQTTCommander):
    def __init__(self, pin_in1=4, pin_in2=5, pin_out1=14, pin_out2=12,
                 server=None, client_id=None, topic1=None, topic2=None,
                 static_ip=''):

        # Pin definitions
        self.pin_up = machine.Pin(pin_out1, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_down = machine.Pin(pin_out2, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_button_up = machine.Pin(pin_in1, machine.Pin.IN, machine.Pin.PULL_UP)
        self.pin_button_down = machine.Pin(pin_in2, machine.Pin.IN, machine.Pin.PULL_UP)

        self.t_SW = 0.1
        self.PBit()

        # Class can be activated without MQTTcommander
        if server is not None and client_id is not None and topic1 is not None:
            MQTTCommander.__init__(self, server, client_id, topic1, topic2, static_ip)
        utime.sleep(2)

    # Define Relay states as Up, Down and Off
    def switch_up(self):
        self.pin_down.value(1)
        utime.sleep(self.t_SW)
        self.pin_up.value(0)

    def switch_down(self):
        self.pin_up.value(1)
        utime.sleep(self.t_SW)
        self.pin_down.value(0)

    def switch_off(self):
        self.pin_down.value(1)
        utime.sleep(self.t_SW)
        self.pin_up.value(1)

    #

    # Define hardware state retrieval
    def but_down_state(self):
        if self.pin_button_down.value() == 0:  # pressed
            return 1
        elif self.pin_button_down.value() == 1:  # released
            return 0

    def but_up_state(self):
        if self.pin_button_up.value() == 0:  # pressed
            return 1
        elif self.pin_button_up.value() == 1:  # released
            return 0

    def rel_up_state(self):
        if self.pin_up.value() == 1:  # open
            return 0
        elif self.pin_up.value() == 0:  # closed
            return 1

    def rel_down_state(self):
        if self.pin_down.value() == 1:  # open
            return 0
        elif self.pin_down.value() == 0:  # closed
            return 1

    #

    # Define Physical button operation
    def button_switch(self):
        # switch_up.
        if self.but_up_state() == 1 and self.rel_up_state() == 0:
            self.switch_up()
            try:
                self.pub("Button Switch: [UP]")
            except NameError:
                print("UP")
        # switch down
        elif self.but_down_state() == 1 and self.rel_down_state() == 0:
            self.switch_down()
            try:
                self.pub("Button Switch: [DOWN]")
            except NameError:
                print("DOWN")
        # switch off
        elif self.but_down_state() == 0 and self.but_down_state() == 0:
            self.switch_off()
            try:
                self.pub("Button Switch: [OFF]")
            except NameError:
                print("OFF")

    def PBit(self):
        print("PowerOnBit started")
        self.switch_down()
        utime.sleep(self.t_SW * 4)
        self.switch_up()
        utime.sleep(self.t_SW * 4)
        self.switch_off()


class ClockUpdate:
    def __init__(self, utc_shift=0, update_int=24):
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
            # return "clock update failed"

    def check_update(self):
        if utime.ticks_diff(self.future_clock_update, utime.ticks_ms()) < 0:
            self.update()
            self.create_new_update_time()

    def create_new_update_time(self):
        update_int = self.update_int * 60 * 60 * 1000  # result in milli-seconds
        self.future_clock_update = utime.ticks_add(utime.ticks_ms(), update_int)


# ############### CHANGE values each PORT  ##################################
CLIENT_ID = 'ESP32_1'
client_topic = 'HomePi/Dvir/Windows/fRoomWindow'

# # ESP8266 pins
# pin_in1 = 4
# pin_in2 = 5
# pin_out1 = 14
# pin_out2 = 12
# #

# ESP32 pins
pin_in1 = 22
pin_in2 = 19
pin_out1 = 23
pin_out2 = 18
#
static_ip = '192.168.2.201'
# static_ip = None  ## Optional ##
# #############################################################################

# ############################## Leave AS IS ##################################
SERVER = '192.168.2.113'
# SERVER = 'iot.eclipse.org' ## Optional ##
TOPIC_LISTEN = [client_topic, 'HomePi/Dvir/Windows/All']
TOPIC_OUT = 'HomePi/Dvir/Messages'  # Messages Topic
# wifi = Connect2Wifi(static_ip)
SmartRelay = DualRelaySwitcher(pin_in1=pin_in1, pin_in2=pin_in2, pin_out1=pin_out1, pin_out2=pin_out2,
                               server=SERVER, client_id=CLIENT_ID, topic1=TOPIC_LISTEN, topic2=TOPIC_OUT,
                               static_ip=static_ip)
# ##############################################################################
