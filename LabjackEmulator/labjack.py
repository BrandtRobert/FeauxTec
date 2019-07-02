import pandas as pd
from ModbusHandler import ModbusReceiver
from METECModel import PnIDModel
from typing import Dict


class LabJack:

    def __init__(self, name, pins_to_registers_file, sensor_properties_file, physical_model):
        self.pins = pd.read_csv(pins_to_registers_file).set_index('start_address')
        # Filter out DIO pins because they are duplicates
        self.pins = self.pins.loc[self.pins['pin'].str.contains('DIO[0-9]+$', regex=True) == False]
        # Only get sensors for this labjack reader
        self.sensors = pd.read_csv(sensor_properties_file).set_index('reader').loc[name]
        self.name = name

    '''
        Converts a register address to a pin on the labjack.
        Using a mapping defined in the pins_to_registers file.
        This file must have at least columns 'pin' and 'start_address'
        https://labjack.com/support/datasheets/t-series/communication/modbus-map
            Example: address: 0 --> pin: AIN0
            Example: address: 2016 --> pin: CIO0 (DIO0 removed because of ambiguity) 
    '''
    def _registers_to_pins(self, register):
        try:
            pin = self.pins.loc[register]['pin']
            return pin
        except KeyError:
            print('Start register {} is invalid'.format(register))
            return 'INVALID_START_REGISTER'

    '''
        Converts a pin on the labjack to the sensor, or device it's connected to.
        Uses a mapping defined in the sensor_properties file. This file must at least
        contain columns 'pin', 'name' for the name of the sensor/device, and 'reader' for the name
        of the labjack reading and modifying that device.
            Example: pin: AIN0 --> device: CB-1W.PT-1 (pressure transducer 1)
            Example: pin: CIO0 --> device: CB-1W.EV-14 (electronic vale 14)
    '''
    def _pin_to_sensor(self, pin):
        return self.sensors.loc[self.sensors['pin'] == pin]

    '''
        Handles decoded Modbus requests and takes action based on requested methods.
        TCP/IP communicates are handled in ModbusHandler.ModbusReceiver, this function is a callback
        that is passed to the ModbusReceiver so that it can take action on decoded Modbus messages.
            Supported function codes:
                1: read_coils                   5: write_single_coil
                2: read_discrete_inputs         6: write_single_holding_register
                3: read_holding registers       7: write_multiple_coils
                4: reading_input_registers      8: write_multiple_holding_registers
        Should return a message that can be sent back to the client, this message can be encoded with the 
        ModbusHandler.ModbusEncoder
    '''
    def on_request(self, request_body) -> Dict:
        pin = self._registers_to_pins(request_body['address'])
        sensor = self._pin_to_sensor(pin)
        # We use '_' instead of '-' in the physical model as '-' gets confused in mathematical interpretations
        lookup_name = sensor['name'][0].replace('-', '_')
        print(model.get_node_component(lookup_name))

    '''
        Starts the modbus receiving server and sends on_request function as a callback.
        Server can be stopped with  
    '''
    def start_server(self, port):
        receiver = ModbusReceiver(port)
        receiver.start_server(self.on_request)


if __name__ == "__main__":
    model = PnIDModel('../Resources/volumes_CB_1W.json')
    s = LabJack('CB-1W.LJ-1', '../Resources/pins_to_registers.csv', '../Resources/sensor_properties.csv', model)
    s.start_server(8080)