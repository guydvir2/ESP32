from umqtt.simple import MQTTClient
import utime
import machine


class MQTTCom:
    def __init__(self, server, client_id, topic1, topic2=None, pin_in1=4, pin_in2=5, pin_out1=14, pin_out2=12):
        self.server = server
        self.client_id = client_id
        self.topic1, self.topic2 = topic1, topic2
        self.client, self.arrived_msg = None, None
        self.t_SW = 0.1

        self.pin_up = machine.Pin(pin_out1, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_down = machine.Pin(pin_out2, machine.Pin.OUT, machine.Pin.PULL_UP, value=1)
        self.pin_button_up = machine.Pin(pin_in1, machine.Pin.IN, machine.Pin.PULL_UP)
        self.pin_button_down = machine.Pin(pin_in2, machine.Pin.IN, machine.Pin.PULL_UP)

        self.start_client()
        self.PBit()
        utime.sleep(1)

        self.pub('System Boot')
        self.wait_for_msg()

    def start_client(self):
        self.client = MQTTClient(self.client_id, self.server, 0)
        self.client.set_callback(self.on_message)
        self.client.connect()
        for topic in self.topic1:
            self.client.subscribe(topic)

    def pub(self, msg):
        self.client.publish(self.topic2, "%s Topic: [%s] Message: %s" % (self.time_stamp(),
                                                                         self.topic1[0], msg))

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
                if last_state_register != [self.but_up_state(), self.but_down_state()]:
                    self.button_switch()
                    last_state_register = [self.but_up_state(), self.but_down_state()]

                # This is listening for MQTT commands
                self.client.check_msg()

                utime.sleep(self.t_SW)
        finally:
            self.client.disconnect()

    @staticmethod
    def time_stamp():
        t_tup = utime.localtime()
        t = "[%d-%02d-%02d %02d:%02d:%02d.%02d]" % (t_tup[0], t_tup[1], t_tup[2],
                                                    t_tup[3], t_tup[4], t_tup[5], t_tup[6])
        return t

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


# ############### Def MQTT Communicator ##############################
SERVER = '192.168.2.113'
# SERVER = 'iot.eclipse.org'
CLIENT_ID = 'ESP8266_1'
TOPIC_LISTEN = ['HomePi/Dvir/Windows/ESP8266_1', 'HomePi/Dvir/Windows/All']
TOPIC_OUT = 'HomePi/Dvir/Messages'  # Messages Topic

A = MQTTCom(server=SERVER, client_id=CLIENT_ID, topic1=TOPIC_LISTEN, topic2=TOPIC_OUT)
####################################################################
