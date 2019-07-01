import socket
from typing import Callable
from ModbusHandler import ModbusDecoder


class ModbusReceiver:

    def __init__(self, port):
        self.port = port

    @staticmethod
    def _dissect_packet(packet_data):
        function_code = packet_data[0]
        switch = {
            1: ModbusDecoder.read_coils,
            2: ModbusDecoder.read_discrete_inputs,
            3: ModbusDecoder.read_holding_registers,
            4: ModbusDecoder.read_input_registers,
            5: ModbusDecoder.write_single_coil,
            6: ModbusDecoder.write_single_holding_register,
            15: ModbusDecoder.write_multiple_coils,
            16: ModbusDecoder.write_multiple_holding_registers
        }
        function = switch.get(function_code, ModbusDecoder.invalid_function_code)
        return function(packet_data)

    def start_server(self, request_handler: Callable):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # s.bind((socket.gethostname(), self.port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', self.port))
            s.listen(5)
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
