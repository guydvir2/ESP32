import machine
import utime
from umqtt.simple import MQTTClient

def start_mqtt(client_id, server):
    client = MQTTClient()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(server)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


MQTT_SERVER = '192.168.2.113' 
MQTT_SERVER = "iot.eclipse.org"
TOPIC = '/HomePi/Dvir/Windows/test'
CLIENT_ID = 'ESP32'

relayPin = machine.Pin(13,machine.Pin.OUT)
client = MQTTClient(CLIENT_ID, MQTT_SERVER)
client.on_message = on_message
client.on_connect = on_connect
client.connect()   # Connect to MQTT broker
client.publish(TOPIC,'Im ON')
#start_mqtt(CLIENT_ID, MQTT_SERVER)

