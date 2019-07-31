from pymodbus.client.sync import ModbusTcpClient
from pymodbus.register_read_message import ReadInputRegistersResponse
from time import sleep
from threading import Thread
import struct


def config_thermocouple(client: ModbusTcpClient, name, AIN='AIN0'):
    # cfg = {
    #     AIN + "_EF_INDEX": 24,
    #     AIN + "_EF_CONFIG_A": 2,
    #     AIN + "_EF_CONFIG_B": 60052,
    #     AIN + "_EF_CONFIG_D": 1.0,
    #     AIN + "_EF_CONFIG_E": 0.0
    # }

    cfg = {
        8198: 24,
        9298: 2,
        9598: 60052,
        10198: 1.0,
        10498: 0.0
    }

    for addr, val in cfg.items():
        ba = bytearray(struct.pack(">f", val))
        print(name, ba)
        client.write_registers(addr, [int.from_bytes(ba[:2], 'big'), int.from_bytes(ba[2:], 'big')])
        print(name, _convert_to_32_float(int.from_bytes(ba[:2], 'big'), int.from_bytes(ba[2:], 'big')))


def _convert_to_32_float(register1, register2) -> float:
    # Pad hex with 0's
    reg1_hex = hex(register1)[2:]
    if len(reg1_hex) < 4:
        reg1_hex = reg1_hex + ('0' * (4 - len(reg1_hex)))
    reg2_hex = hex(register2)[2:]
    if len(reg2_hex) < 4:
        reg2_hex = reg2_hex + ('0' * (4 - len(reg2_hex)))
    import struct
    hex_bytes = reg1_hex + reg2_hex
    f = struct.unpack('!f', bytes.fromhex(hex_bytes))
    return f[0]


def load_test_client(client: ModbusTcpClient, name: str):
    results_dict = {}
    config_thermocouple(client, name, AIN='AIN0')
    while True:
        results_dict[60000] = client.read_input_registers(60000, 2)
        results_dict[2800] = client.read_input_registers(2800, 2)
        results_dict[0] = client.read_input_registers(0, 2)
        resp = results_dict[60000]
        data = _convert_to_32_float(resp.registers[0], resp.registers[1])
        print('{}: "read version id" trans: {}, unit: {}, registers: {}'
              .format(name, resp.transaction_id, resp.unit_id, data))
        resp = results_dict[2800]
        data = hex(resp.registers[0]) + hex(resp.registers[1])[2:]
        print('{}: "DIO" trans: {}, unit: {}, registers: {}'
              .format(name, resp.transaction_id, resp.unit_id, data))
        resp = results_dict[0]
        data = _convert_to_32_float(resp.registers[0], resp.registers[1])
        print('{}: "read AIN0" trans: {}, unit: {}, registers: {}'
              .format(name, resp.transaction_id, resp.unit_id, data))
        sleep(.500)


if __name__ == "__main__":
    client_501 = ModbusTcpClient(host='Brandt.local', port=501)
    client_502 = ModbusTcpClient(host='Brandt.local', port=502)
    thread_501 = Thread(target=load_test_client, args=(client_501, '501'), daemon=True, name='501')
    thread_502 = Thread(target=load_test_client, args=(client_502, '502'), daemon=True, name='502')
    thread_501.start()
    thread_502.start()
    sleep(500)
