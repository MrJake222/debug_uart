from ProtoError import ProtoError

import struct
from collections import defaultdict

import sys
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class Proto32:
    def __init__(self, ser):
        self.ser = ser
        
    def addr_format(self, addr):
        return f"{addr:08x}"
        
    def value_format(self, value):
        return f"{value:02x}"
        
    def request_with_ack(self, func_name, req):
        # used when sending requests with no data to be read
        # (device should respond with ack, byte 01)
        # this function verifies the ack
        data = bytes(req)
        self.ser.write(data)
        
        echo = self.ser.read(1)
        echo_len = len(echo)
        echo_arr = [d for d in echo]
        if echo_len < 1:
            eprint(f"\ntimeout occured, received {echo_len} / 2 bytes: {echo_arr}")
            
            raise TimeoutError(f"{func_name}: timeout")
            
        if echo[0] != 0x01:
            eprint(f"\n{func_name}: ack not matching")
            eprint(f"should be: [1]")
            eprint(f"is: {echo_arr}")
            
            raise ProtoError(f"{func_name}: ack not matching")
        
    # protocol functions
    def set_address_pointer(self, addr):
        self.request_with_ack("set_address_pointer", bytes([0x01]) + struct.pack("<L", addr))
        
    def get_address_pointer(self):
        self.ser.write(bytes([0x03]))
        addr = self.ser.read(4)
        return struct.unpack("<L", addr)
        
    def get_address_pointer(self):
        self.ser.write(bytes([0x03, FILL]))
        alow, ahigh = self.ser.read(2)
        return ahigh * 256 + alow
        
    def write_memory_4_byte(self, b):
        self.request_with_ack("write_memory_4_byte", [0x04]+b)
        
    def read_memory_4_byte(self):
        self.ser.write(bytes([0x05]))
        return self.ser.read(4)
        
    def run_cycles(self, cycles):
        self.request_with_ack("run_cycles", [0x20, cycles])
        
    def pulse_cpu_reset(self):
        # only pulls reset down for 1 cycle
        self.request_with_ack("perform_cpu_reset", [0x21])

    def perform_cpu_reset(self):
        # takes care of reset routine
        # after this, PC is loaded with entry point address
        self.pulse_cpu_reset()
        self.run_cycles(8)
        
    def set_free_run(self, enabled):
        self.request_with_ack("set_free_run", [0x22, enabled])
    
    
    # public interface functions
    def write_memory_dict(self, data_dict):
        
        data_dict32 = defaultdict(lambda: [0]*4)
        for adr, val in data_dict.items():
            adr32 = adr & ~0x3
            data_dict32[adr32][adr%4] = val
                    
        lastaddr = -1000
        for addr in sorted(data_dict32.keys()):
            val = data_dict32[addr]
            if lastaddr+4 != addr:
                print(f"loading adr_ptr with ${addr:08x}")
                self.set_address_pointer(addr)
            
            # print(f"${addr:08x}  ${val}")
            self.write_memory_4_byte(val)
            
            lastaddr = addr
        
    def read_memory_dict(self, addresses):
        mem_dict = {addr: -1 for addr in addresses}

        # zero 4 least significant (and with negated 32'b11)
        addresses = {x&~0x3 for x in addresses}
        
        lastaddr = -1000
        for addr in sorted(addresses):
            if lastaddr+4 != addr:
                print(f"loading adr_ptr with ${addr:08x}")
                self.set_address_pointer(addr)
            
            vals = self.read_memory_4_byte()
            for i in range(4):
                mem_dict[addr + i] = vals[i]
            
            # print(f"${addr:08x}:  ${vals}")
            
            lastaddr = addr
        
        return mem_dict
    
    def print_status(self):
        A, S  = self.get_A_S()
        X, Y  = self.get_X_Y()
        IR, P = self.get_IR_P()
        PC    = self.get_PC()
        
        print(f"A     ${A:02x}")
        print(f"X     ${X:02x}")
        print(f"Y     ${Y:02x}")
        print(f"S     ${S:02x}")
        print(f"IR    ${IR:02x}")
        print(f"P     ${P:02x}")
        print(f"PC  ${PC:04x}")
    
    """
    Get a value
    name can be:
        register A X Y S IR P PC -- read register value
        M(<hex addr>) -- read memory value at <hex addr>
        B(<register>, <bit>) -- read <register> <bit> value
    """
    def get(self, name):
        if name == "A":
            return self.get_A_S()[0]
        if name == "X":
            return self.get_X_Y()[0]
        if name == "Y":
            return self.get_X_Y()[1]
        if name == "S":
            return self.get_A_S()[1]
        
        if name == "IR":
            return self.get_IR_P()[0]
        if name == "P":
            return self.get_IR_P()[1]
        if name == "PC":
            return self.get_PC()
            
        if name.startswith("M"):
            addr = int(name.split("(")[1].split(")")[0], 16)
            self.set_address_pointer(addr)
            return self.read_memory_2_byte()[0]
        
        if name.startswith("B"):
            reg, bit = name.split("(")[1].split(")")[0].split(",")
            val = self.get(reg.strip())
            bit = int(bit.strip())
            return (val >> bit) & 0x01
            
        raise ValueError("no such field")
        

