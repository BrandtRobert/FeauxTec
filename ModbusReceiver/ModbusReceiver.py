import socket
from typing import Callable


class ModbusReceiver:

    def __init__(self, port):
        self.port = port

    def _read_coils(self, data):
        data = data[1:]
        is_error = False

        start_coil = (data[0] << 8) | (data[1])
        num_coils = (data[2] << 8) | (data[3])

        if start_coil < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)
            # return is_error,
        elif num_coils < 0:
            is_error = True
            return is_error, self._invalid_data_value(data)
        else:
            return is_error, {
                'start_coil': start_coil,
                'num_coils': num_coils
            }

    def _read_discrete_inputs(self, data):
        data = data[1:]
        is_error = False

        start_input = (data[0] << 8) | (data[1])
        num_inputs = (data[2] << 8) | (data[3])

        if start_input < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)
            # return is_error,
        elif num_inputs < 0:
            is_error = True
            return is_error, self._invalid_data_value(data)
        else:
            return is_error, {
                'start_discrete_input': start_input,
                'num_discrete_inputs': num_inputs
            }

    def _read_holding_registers(self, data):
        data = data[1:]
        is_error = False

        start_register = (data[0] << 8) | (data[1])
        num_registers = (data[2] << 8) | (data[3])

        if start_register < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)
            # return is_error,
        elif num_registers < 0:
            is_error = True
            return is_error, self._invalid_data_value(data)
        else:
            return is_error, {
                'start_holding_register': start_register,
                'num_holding_registers': num_registers
            }

    def _read_input_registers(self, data):
        data = data[1:]
        is_error = False

        start_register = (data[0] << 8) | (data[1])
        num_registers = (data[2] << 8) | (data[3])

        if start_register < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)
            # return is_error,
        elif num_registers < 0:
            is_error = True
            return is_error, self._invalid_data_value(data)
        else:
            return is_error, {
                'start_register': start_register,
                'num_registers': num_registers
            }

    def _write_single_coil(self, data):
        data = data[1:]
        is_error = False

        coil_address = (data[0] << 8) | (data[1])
        value_to_write = (data[2] << 8) | (data[3])

        if coil_address < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)

        switch = None
        if value_to_write == 0:
            switch = 'off'
        elif value_to_write == 0xFF00:
            switch = 'on'
        else:
            is_error = True
            return is_error, self._invalid_data_value(data)

        return is_error, {
            'coil_address': coil_address,
            'switch': switch
        }

    def _write_single_holding_register(self, data):
        is_error = False
        data = data[1:]
        register_address = (data[0] << 8) | (data[1])
        value_to_write = (data[2] << 8) | (data[3])

        if register_address < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)
        elif value_to_write < 0:
            is_error = True
            return is_error, self._invalid_data_value(data)

        return is_error, {
            'register_address': register_address,
            'value_to_write': value_to_write
        }

    def _write_multiple_coils(self, data):
        data = data[1:]
        is_error = False

        first_coil = (data[0] << 8) | (data[1])
        num_coils_to_write = (data[2] << 8) | (data[3])
        num_bytes_of_coils = data[4]
        coil_values = data[5:5 + num_bytes_of_coils]

        if first_coil < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)

        for val in coil_values:
            if val < 0:
                return is_error, self._invalid_data_value(data)

        return is_error, {
            'start_coil': first_coil,
            'coil_values': coil_values,
            'num_coils': num_coils_to_write
        }

    def _write_multiple_holding_registers(self, data):
        data = data[1:]
        is_error = False

        first_register = (data[0] << 8) | (data[1])
        num_regs_to_write = (data[2] << 8) | (data[3])
        num_bytes_of_registers = data[4]
        print(data[5:])
        register_values = [0] * (num_bytes_of_registers // 2)
        # Each register value is 16 bits, decode every 2 bytes of data into one 16 bit value
        for i in range(0, num_bytes_of_registers // 2):
            idx = 5 + i*2
            register_values[i] = (data[idx] << 8) | (data[idx + 1])

        if first_register < 0:
            is_error = True
            return is_error, self._invalid_register_addr(data)

        for val in register_values:
            if val < 0:
                return is_error, self._invalid_data_value(data)

        return is_error, {
            'start_register': first_register,
            'register_values': register_values,
            'num_registers': num_regs_to_write
        }

    @staticmethod
    def _invalid_function_code(data):
        code = data[0]
        is_error = True
        response_code = 0x80 | code
        error_code = 0x01
        response = (response_code << 8) | error_code
        return is_error, response.to_bytes(2, byteorder='big')

    @staticmethod
    def _invalid_register_addr(data):
        function_code = data[0]
        error_code = 0x02
        return (((function_code | 0x80) << 8) | error_code).to_bytes(2, byteorder='big')

    @staticmethod
    def _invalid_data_value(data):
        function_code = data[0]
        error_code = 0x03
        return (((function_code | 0x80) << 8) | error_code).to_bytes(2, byteorder='big')

    def _dissect_packet(self, packet_data):
        function_code = packet_data[0]
        switch = {
            1: self._read_coils,
            2: self._read_discrete_inputs,
            3: self._read_holding_registers,
            4: self._read_input_registers,
            5: self._write_single_coil,
            6: self._write_single_holding_register,
            15: self._write_multiple_coils,
            16: self._write_multiple_holding_registers
        }
        function = switch.get(function_code, self._invalid_function_code)
        return function(packet_data)

    def start_server(self, request_handler: Callable):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.bind((socket.gethostname(), self.port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', self.port))
            s.listen()
            print('Starting server at {}:{}'.format(socket.gethostname(), self.port))
            while True:
                connection, address = s.accept()
                with connection:
                    print('Connected by {}'.format(address))
                    header = connection.recv(7)
                    # Modbus length is in bytes 4 & 5 of the header according to spec (pg 25)
                    # https://www.prosoft-technology.com/kb/assets/intro_modbustcp.pdf
                    length = (header[4] << 8) | (header[5])
                    data = connection.recv(length)
                    is_error, dissection = self._dissect_packet(data)
                    if is_error:
                        print("Error function code")
                        connection.sendall(dissection)
                        connection.close()
                        continue
                    else:
                        dissection['type'] = 'request'
                        dissection['function_code'] = data[0]
                        request_handler(dissection)
                        # response = request_handler(dissection)
                        # connection.sendall(response)
                        connection.close()


if __name__ == '__main__':
    m = ModbusReceiver(8080)

    def handler(msg):
        print(msg)
    m.start_server(handler)
