from time import sleep
from umqtt.simple import MQTTClient
from machine import Pin
import _thread
import utime
import machine


class MQTTCom:
    def __init__(self, server, client_id, topic1, topic2=None):
        self.server = server
        self.client_id = client_id
        self.topic1, self.topic2 = topic1, topic2
        self.client, self.arrived_msg = None, None

        self.start_client()

    def start_client(self):
        self.client = MQTTClient(self.client_id, self.server, 0)
        self.client.set_callback(self.on_message)
        self.client.connect()
        for topic in self.topic1:
            self.client.subscribe(topic)
            print("%s Connected to %s, subscribed to %s" % (self.time_stamp(),
                                                        self.server, topic))

    def pub(self, msg):
        self.client.publish(self.topic2, "%s Topic: [%s] Message: %s" % (self.time_stamp(),
                                                                         self.topic1, msg))
        print("%s Topic: [%s] Publish Message: [%s]" % (self.time_stamp(), self.topic2, msg))

    def on_message(self, topic, msg):
        self.arrived_msg = msg.decode("UTF-8").strip()
        print("%s Topic: [%s] Received Message: [%s]" % (self.time_stamp(),
                                                         topic.decode("UTF-8"), self.arrived_msg))
        self.link2commands()

    def wait_for_msg(self):
        try:
            while True:
                self.client.wait_msg()
        finally:
            self.client.disconnect()

    def link2commands(self):
        pass

    @staticmethod
    def time_stamp():
        t_tup = utime.localtime()
        t = "[%d-%02d-%02d %02d:%02d:%02d.%02d]" % (t_tup[0], t_tup[1], t_tup[2],
                                                    t_tup[3] + 3, t_tup[4], t_tup[5], t_tup[6])
        return t


def switch_up():
    pin_down.value(0)
    utime.sleep(0.2)
    pin_up.value(1)


def switch_down():
    pin_up.value(0)
    utime.sleep(0.2)
    pin_down.value(1)


def fliker():
    for i in range(30):
        switch_up()
        utime.sleep(0.5)
        switch_down()
        utime.sleep(0.5)


def mqtt_commands(msg):
    if msg == 'reset':
        A.pub("[Reset CMD]")
        machine.reset()
    elif msg.lower() == 'up':
        switch_up()
        A.pub("Switch CMD: [UP]")
    elif msg.lower() == 'down':
        switch_down()
        A.pub("Switch CMD: [DOWN]")
    elif msg.lower() == 'status':
        A.pub("Status CMD: UP:[%s], Down: [%s]" % (pin_up.value(), pin_down.value()))
    elif msg.lower() == 'fliker':
        fliker()
        A.pub("Fliker")


def button_switch():
    while True:
        if pin_button_up.value() == 1 and pin_button_down.value() == 0 and pin_up.value() == 0:
            switch_up()
            A.pub("Button Switch: [UP]")
        elif pin_button_up.value() == 0 and pin_button_down.value() == 1 and pin_down.value() == 0:
            switch_down()
            A.pub("Button Switch: [DOWN]")

        utime.sleep(0.2)


# ################ Def GPIOs #########################################
pin_up = machine.Pin(14, machine.Pin.OUT)
pin_down = machine.Pin(12, machine.Pin.OUT)
pin_button_up = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
pin_button_down = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)
#####################################################################

# ############### Def MQTT Communicator ##############################
SERVER = '192.168.2.113'
# SERVER = 'iot.eclipse.org'
CLIENT_ID = 'ESP32'
TOPIC1 = ['HomePi/Dvir/Windows/ESP32','HomePi/Windows/#']
TOPIC2 = 'HomePi/Dvir/Messages'  # Messages

A = MQTTCom(server=SERVER, client_id=CLIENT_ID, topic1=TOPIC1, topic2=TOPIC2)
A.link2commands = lambda: mqtt_commands(A.arrived_msg)
####################################################################

_thread.start_new_thread(A.wait_for_msg, ())
_thread.start_new_thread(button_switch, ())

sleep(1)
