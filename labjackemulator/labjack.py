import pandas as pd
from modbushandler import ModbusReceiver
import modbushandler.modbusencoder as encoder
import modbushandler.modbusdecoder as decoder
from metecmodel import Model, StatisticsCollector
from interfaces import ComponentBaseClass
import re
import socket
from logger import Logger
import random


class LabJack:

    # https://labjack.com/support/software/api/modbus/protocol-details
    # They only use holding register protocols
    DEVICE_FUNCTION_CODES = [3, 4, 6, 16]
    ENDIANNESS = 'BIG'

    def __init__(self, name, pins_to_registers_file, sensor_properties_file, physical_model, port,
                 localhost=True, socket_type=socket.SOCK_STREAM, noise_factor=0):
        self.pins = pd.read_csv(pins_to_registers_file).set_index('start_address')
        self.pins['data'] = 0
        self.pins.loc['pin' == 'HARDWARE_VERSION', 'data'] = 1.35
        # Only get sensors for this labjack reader
        self.sensors = pd.read_csv(sensor_properties_file).set_index('reader').loc[name]
        self.name = name
        self.model = physical_model
        self.receiver = ModbusReceiver(port, localhost=localhost, device_function_codes=self.DEVICE_FUNCTION_CODES,
                                       socket_type=socket_type)
        self.logger = Logger('LabjackLogger-{}'.format(port), '../logger/logs/labjack_log.txt')
        self.port = port
        self.logger.info('Labjack created at port {}'.format(port))
        self.noise_factor = noise_factor
        StatisticsCollector.increment_number_of_devices()

    @staticmethod
    def _DIO_to_ALT(dio_name) -> str:
        # get DIO number
        num = re.compile('.[A-Za-z]*([0-9]+)').search(dio_name).group(1)
        num = int(num)
        if 0 <= num <= 7:
            return 'FIO' + str(num)
        if 8 <= num <= 15:
            return 'EIO' + str(num % 8)
        if 16 <= num <= 19:
            return 'CIO' + str(num % 16)
        if 20 <= num <= 22:
            return 'MIO' + str(num % 20)


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
            pin = self.pins.loc[register, 'pin']
            if type(pin).__name__ == 'Series':
                return pin.values[-1]
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
        pin = self.pins.loc[self.pins['pin'] == pin]['next_pin'].values[0]
        if 'DIO' in pin:
            return self._DIO_to_ALT(pin)
        else:
            return pin

    def _get_next_register(self, register):
        pin = self._registers_to_pins(register)
        next_pin = self._get_next_pin(pin)
        next_register = self.pins[self.pins['pin'] == next_pin].index[0]
        return next_register

    '''
        Look up the component in the model using the pin and referencing the sensor properties file.
    '''
    def _get_component_from_pin(self, pin) -> ComponentBaseClass:
        sensor = self._pin_to_sensor(pin)
        if len(sensor) == 0:
            return None
        lookup_name = sensor['name'][0]
        return self.model.get_component(lookup_name)

    def _read_from_sensor(self, component: ComponentBaseClass) -> int:
        comp_type = component.get_type()
        self.logger.debug('LJ:{} Attempting read from component type {}'.format(self.port, component.get_type()))
        if component.get_type() not in ['PressureTransducer', 'Thermocouple', 'FlowMeter']:
            raise Exception('Cannot read from non-sensor components')
        if component.get_type() == 'FlowMeter':
            self.logger.debug('Calculating flows and setting meters')
            self.model.calculate_flows(component.get_prefix()) # add component attribute for it's parent gashouse
        self.logger.debug('LJ:{} {} reading {}'.format(self.port, comp_type, component.get_reading()))
        noised_reading = component.get_reading_voltage() + \
            (component.get_reading_voltage() * random.uniform(-self.noise_factor, self.noise_factor))
        self.logger.info('LJ:{} {} reading noised in volts {}'.format(self.port, comp_type, noised_reading))
        return noised_reading

    def _write_to_component(self, component: ComponentBaseClass, value_to_set) -> ComponentBaseClass:
        # transfer values to model spec
        if component.get_type() == 'ElectricValve' or component.get_type() == 'ThreeWayElectricValve':
            value_to_set = 'open' if value_to_set == 0 else 'closed'
            self.model.set_valve(component.get_full_name(), value_to_set)
            self.logger.info('LJ:{} Write {} to component {}'.format(self.port, value_to_set, component))
        else:
            raise Exception('Cannot write to {} type components'.format(component.get_type()))
        return component

    '''
        We are mapping physical commands to our virtual model. Our model is in different about whether
        a component holds a 32 bit or 16 bit reading. However, we are simulating a labjack with 16bit memory 
        words so we have to account for the fact that floats and 32 bit ints take up two registers.
    '''
    def _convert_register_count_to_pin_count(self, start_register, count):
        pin_count = 0
        # use the indexing to jump over DIO pins when counting
        current_pin_record = self.pins.loc[start_register]
        if type(current_pin_record).__name__ == 'DataFrame':
            current_pin_record = self.pins.loc[start_register][-1:].squeeze()
        current_pin = current_pin_record['pin']
        while count > 0:
            data_type = current_pin_record['data_type']
            if '32' in data_type:
                count = count - 2
            else:
                count = count - 1
            pin_count = pin_count + 1
            current_pin = self._get_next_pin(current_pin)
            current_pin_record = self.pins.loc[self.pins['pin'] == current_pin][-1:].T.squeeze()
        return pin_count

    def _DIO_state_request(self, request_header):
        # Use next pin as a work around to having to convert every DIO pin
        pins = self.pins.loc[self.pins['pin'].str.contains('DIO[0-9]+$')]['next_pin'].values
        bit_str = 0xFFFFFFFF
        for idx, pin in enumerate(pins):
            component = self._get_component_from_pin(pin)
            if component and 'ElectricValve' in component.get_type():
                if component.get_reading() == 'open' or component.get_reading() == 'b':
                    bit_str = bit_str ^ 0x1 << idx
        self.logger.info('LJ:{} DIO state request returning {}'.format(self.port, bin(bit_str)))
        return encoder.respond_read_registers(request_header, [(bit_str, 'UINT32')], self.ENDIANNESS)

    def _read_write_register(self, register_address, write_value=None):
        # self.logger.debug('Request at address {}'.format(register_address))
        pin = self._registers_to_pins(register_address)
        # EF_READ is used to read without setting the mode, just read from whatever virtual_pin corresponds
        if 'EF_READ_A' in pin and write_value is None:
            pin = pin.split('_')[0]
        component = self._get_component_from_pin(pin)
        data_type = self.pins.loc[register_address, 'data_type']
        if type(data_type).__name__ == 'Series':
            data_type = data_type.values[0]
        if component:
            if write_value is not None:
                return self._write_to_component(component, write_value), data_type
            else:
                return self._read_from_sensor(component), data_type
        else:
            if write_value is not None:
                self.pins.loc[register_address, 'data'] = write_value
                self.logger.debug('LJ:{} Writing to non-component register {} value now {}'
                                  .format(self.port, register_address, self.pins.loc[register_address, 'data']))
                return write_value, data_type
            else:
                self.logger.debug('LJ:{} Read from non component register {} value {}'
                                  .format(self.port, register_address, self.pins.loc[register_address, 'data']))
                return self.pins.loc[register_address, 'data'], data_type

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
    def on_request(self, request):
        request_body = request['body']
        request_header = request['header']

        # if request_body['address'] == 60000:
        #     self.logger.info('Request for hardware version returning 0')
        #     return encoder.respond_read_registers(request_header, [(0, 'FLOAT32')], self.ENDIANNESS)

        pin = self._registers_to_pins(request_body['address'])
        if re.compile('.*_STATE$').match(pin):
            return self._DIO_state_request(request_header)
        try:
            # read one register
            if request_header['function_code'] == 4:
                reading, data_type = self._read_write_register(request_body['address'])
                return encoder.respond_read_registers(request_header, [(reading, data_type)], self.ENDIANNESS)
            # write one register
            elif request_header['function_code'] == 6:
                self._read_write_register(request_body['address'], request_body['value'])
                num_registers_written = 1
                return encoder.respond_write_registers(request_header, request_body['address'], num_registers_written)
            # write multiple
            elif request_header['function_code'] == 16:
                current_register = request_body['address']
                values = request_body['values']
                pin_count = self._convert_register_count_to_pin_count(request_body['address'], request_body['count'])
                for i in range(pin_count):
                    value_to_set = values[i]
                    self._read_write_register(current_register, value_to_set)
                    current_register = self._get_next_register(current_register)
                return encoder.respond_write_registers(request_header, request_body['address'], request_body['count'])
            # read multiple
            elif request_header['function_code'] == 3:
                current_register = request_body['address']
                values = []
                pin_count = self._convert_register_count_to_pin_count(request_body['address'], request_body['count'])
                for i in range(pin_count):
                    reading, current_dtype = self._read_write_register(current_register)
                    values.append((reading, current_dtype))
                    current_register = self._get_next_register(current_register)
                return encoder.respond_read_registers(request_header, values, self.ENDIANNESS)
            else:
                return decoder.invalid_function_code([request_header['function_code']])[1]
        except Exception as e:
            print('Exception occurred:\n{}'.format(e))
            raise e
            # error responses possible?
            # return decoder.invalid_function_code([request_header['function_code']])[1]

    '''
        Starts the modbus receiving server and sends on_request function as a callback.
        Server can be stopped with  
    '''
    def start_server(self):
        self.receiver.start_server(self.on_request)

    def stop_server(self):
        self.receiver.stop_server()


if __name__ == "__main__":
    m = Model('../Resources/sensor_properties.csv', '../Resources/GSH-1-volumes.json')
    s = LabJack('CB-1W.LJ-1', '../Resources/pins_to_registers.csv', '../Resources/sensor_properties.csv', m, 502)
    s.start_server()
