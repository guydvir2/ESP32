import json
import os


class JSONconfig:
    def __init__(self, filename):
        self.filename = filename
        self.def_values = {}
        self.data_from_file = None
        self.read_file()

    def read_file(self):
        if self.filename in os.listdir():
            with open(self.filename, 'r') as f:
                self.data_from_file = json.load(f)
        else:
            self.create_default_file()

    def create_def_vals(self):
        self.def_values = {"client_ID": 'ESP32_1',
                           "client_topic": 'HomePi/Dvir/my_device',
                           "out_topic": 'HomePi/Dvir/Messages',
                           "pin_in1": 22, "pin_in2": 19, "pin_out1": 23, "pin_out2": 18,
                           "static_ip": None,
                           "server": '192.168.2.200', "user": "guy", "password": "kupelu9e"}
        self.def_values["listen_topics"] = [self.def_values["client_topic"], 'HomePi/Dvir/Windows/All']

    def create_default_file(self):
        self.create_def_vals()
        self.write2file(self.def_values)

    def write2file(self, dict):
        with open(self.filename, 'w') as f:
            json.dump(dict, f)

    def update_value(self, key, value):
        self.read_file()
        self.data_from_file[key] = value
        self.write2file(self.data_from_file)


if __name__ == "__main__":
    name = "kRoomWindow"
    create_config_files = JSONconfig('config.froom')
    create_config_files.update_value("client_ID", name)
    create_config_files.update_value("client_topic", 'HomePi/Dvir/Windows/' + name)
