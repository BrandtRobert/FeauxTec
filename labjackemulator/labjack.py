import pandas as pd
from modbushandler import ModbusReceiver
import modbushandler.modbusencoder as encoder
import modbushandler.modbusdecoder as decoder
from metecmodel import PnIDModel
from metecmodel import Component
from typing import Dict


class LabJack:

    # https://labjack.com/support/software/api/modbus/protocol-details
    # They only use holding register protocols
    DEVICE_FUNCTION_CODES = [3, 4, 6, 16]
    ENDIANNESS = 'BIG'

    def __init__(self, name, pins_to_registers_file, sensor_properties_file, physical_model):
        self.pins = pd.read_csv(pins_to_registers_file).set_index('start_address')
        # Filter out DIO pins because they are duplicates, this is a temporary solution
        self.pins = self.pins.loc[self.pins['pin'].str.contains('DIO[0-9]+$', regex=True) == False]
        # Only get sensors for this labjack reader
        self.sensors = pd.read_csv(sensor_properties_file).set_index('reader').loc[name]
        self.name = name
        self.model = physical_model

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
        Given a pin, search the modbus map for the next pin. Sometimes the addressing can get
        weird with the different 8, 16, and 32 bit data types. This method helps clear that up.
    '''
    def _get_next_pin(self, pin):
        return self.pins.loc[self.pins['pin'] == pin]['next_pin']

    '''
        Look up the component in the model using the pin and referencing the sensor properties file.
    '''
    def _get_component_from_pin(self, pin):
        sensor = self._pin_to_sensor(pin)
        # We use '_' instead of '-' in the physical model as '-' gets confused in mathematical interpretations
        if len(sensor) == 0:
            return None
        lookup_name = sensor['name'][0].replace('-', '_')
        return self.model.get_node_component(lookup_name)

    @staticmethod
    def _read_from_component(component) -> int:
        if 'reading' in component.data.keys():
            reading = component.data['reading']
            if 'offset' in component.data.keys():
                reading = reading - component.data['offset']
            if 'slope' in component.data.keys():
                reading = reading / component.data['slope']
        elif 'electronic-valve' in component.get_type():
            reading = 1 if component.current_state is 'open' else 0
        else:
            reading = 0
        return reading

    def _write_to_component(self, component, value_to_set) -> Component:
        # transfer values to model spec
        if 'electronic-valve' in component.get_type():
            value_to_set = 'open' if value_to_set != 0 else 'closed'
            self.model.change_node_state(component.get_full_name(), value_to_set)
        else:
            if 'slope' in component.data.keys():
                value_to_set = value_to_set * component.data['slope']
            if 'offset' in component.data.keys():
                value_to_set = value_to_set + component.data['offset']
            component.data['reading'] = value_to_set
        return component

    '''
        We are mapping physical commands to our virtual model. Our model is in different about whether
        a component holds a 32 bit or 16 bit reading. However, we are simulating a labjack with 16bit memory 
        words so we have to account for the fact that floats and 32 bit ints take up two registers.
    '''
    def _convert_register_count_to_pin_count(self, start_register, count):
        pin_count = 0
        current_pin_record = self.pins.loc[start_register]
        while count > 0:
            data_type = current_pin_record['data_type']
            if '32' in data_type:
                count = count - 2
            else:
                count = count - 1
            current_pin_record = self._get_next_pin(current_pin_record['next_pin'])
            pin_count = pin_count + 1
        return pin_count

    '''
        Handles decoded Modbus requests and takes action based on requested methods.
        TCP/IP communicates are handled in modbushandler.ModbusReceiver, this function is a callback
        that is passed to the ModbusReceiver so that it can take action on decoded Modbus messages.
            Supported function codes:
                1: read_coils                   5: write_single_coil
                2: read_discrete_inputs         6: write_single_holding_register
                3: read_holding registers       7: write_multiple_coils
                4: reading_input_registers      8: write_multiple_holding_registers
        Should return a message that can be sent back to the client, this message can be encoded with the 
        modbushandler.ModbusEncoder
    '''
    def on_request(self, request) -> Dict:
        request_body = request['body']
        request_header = request['header']
        pin = self._registers_to_pins(request_body['address'])
        component = self._get_component_from_pin(pin)

        # read one register
        if request_header['function_code'] == 4:
            # rn if the reading is a 32 bit value then this is gonna break i believe
            reading = self._read_from_component(component)
            data_type = self.pins.loc[self.pins['pin'] == pin]['data_type'][0]
            return encoder.respond_read_registers(request_header, [(reading, data_type)], self.ENDIANNESS)
        # write one register
        elif request_header['function_code'] == 6:
            value_to_set = request_body['value']
            self._write_to_component(component, value_to_set)
            num_registers_written = 1
            return encoder.respond_write_registers(request_header, request_body['address'], num_registers_written)
        # write multiple
        elif request_header['function_code'] == 16:
            current_component = component
            current_pin = pin
            values = request_body['values']
            pin_count = self._convert_register_count_to_pin_count(request_body['address'], request_body['count'])
            for i in range(pin_count):
                value_to_set = values[i]
                self._write_to_component(current_component, value_to_set)
                current_pin = self._get_next_pin(current_pin)
                current_component = self._get_component_from_pin(current_pin)
            return encoder.respond_write_registers(request_header, request_body['address'], request_body['count'])
        # read multiple
        elif request_header['function_code'] == 3:
            current_component = component
            current_pin = pin
            values = []
            pin_count = self._convert_register_count_to_pin_count(request_body['address'], request_body['count'])
            for i in range(pin_count):
                current_dtype = self.pins.loc[self.pins['pin'] == current_pin]['data_type'][0]
                values.append((self._read_from_component(current_component), current_dtype))
                current_pin = self._get_next_pin(current_pin)[0]
                current_component = self._get_component_from_pin(current_pin)
            return encoder.respond_read_registers(request_header, values, self.ENDIANNESS)
        else:
            return decoder.invalid_function_code([request_header['function_code']])[1]


    '''
        Starts the modbus receiving server and sends on_request function as a callback.
        Server can be stopped with  
    '''
    def start_server(self, port):
        receiver = ModbusReceiver(port)
        receiver.start_server(self.on_request)


if __name__ == "__main__":
    m = PnIDModel('../Resources/volumes_CB_1W.json', 50, {'ambient_temperature': 75})
    s = LabJack('CB-1W.LJ-1', '../Resources/pins_to_registers.csv', '../Resources/sensor_properties.csv', m)
    s.start_server(502)
