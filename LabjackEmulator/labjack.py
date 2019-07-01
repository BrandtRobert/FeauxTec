import pandas as pd
from ModbusHandler import ModbusReceiver

class LabJack:

    def __init__(self, name, pins_to_registers_file, sensor_properties_file):
        self.pins = pd.read_csv(pins_to_registers_file).set_index('start_address')
        self.sensors = pd.read_csv(sensor_properties_file).set_index('reader').loc[name]
        self.name = name

    def _registers_to_pins(self, register):
        try:
            pin = self.pins.loc[register]['pin']
            return pin
        except KeyError:
            print('Start register {} is invalid'.format(register))
            return 'INVALID_START_REGISTER'

    def _pin_to_sensor(self, pin):
        return self.sensors.loc[self.sensors['pin'] == pin]

    def on_request(self, request_body):
        if request_body['function_code'] == 4:
            print('start', request_body['start_register'])
            print('count', request_body['num_registers'])
            pin = self._registers_to_pins(request_body['start_register'])
            print('pin', pin)
            sensor = self._pin_to_sensor(pin)
            print('sensor', sensor['name'][0], sensor['item_type'][0])

    def start_server(self, port):
        receiver = ModbusReceiver(port)
        receiver.start_server(self.on_request)


if __name__ == "__main__":
    s = LabJack('CB-1W.LJ-1', '../Resources/pins_to_registers.csv', '../Resources/sensor_properties.csv')
    s.start_server(8080)