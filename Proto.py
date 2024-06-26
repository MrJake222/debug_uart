FILL = 0x00

from ProtoError import ProtoError

import sys
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class Proto:
    def __init__(self, ser):
        self.ser = ser
        
    def addr_format(self, addr):
        return f"{addr:04x}"
        
    def value_format(self, value):
        return f"{value:02x}"
        
    def request_with_echo(self, func_name, req):
        # used when sending requests with no data to be read
        # (device should echo the request)
        # this function verifies that the echo matches what was sent
        data = bytes(req)
        self.ser.write(data)
        
        echo = self.ser.read(2)
        echo_len = len(echo)
        echo_arr = [d for d in echo]
        if echo_len < 2:
            eprint(f"\ntimeout occured, received {echo_len} / 2 bytes: {echo_arr}")
            
            raise TimeoutError(f"{func_name}: timeout")
            
        if echo != data:
            eprint(f"\n{func_name}: echo not matching")
            eprint(f"should be: {req}")
            eprint(f"is: {echo_arr}")
            
            raise ProtoError(f"{func_name}: echo not matching")
        
    # protocol functions
    def set_address_pointer_low(self, alow):
        self.request_with_echo("set_address_pointer_low", [0x01, alow])
        
    def set_address_pointer_high(self, ahigh):
        self.request_with_echo("set_address_pointer_high", [0x02, ahigh])
        
    def get_address_pointer(self):
        self.ser.write(bytes([0x03, FILL]))
        alow, ahigh = self.ser.read(2)
        return ahigh * 256 + alow
        
    def write_memory_1_byte(self, b):
        self.request_with_echo("write_memory_1_byte", [0x04, b])
        
    def read_memory_2_byte(self):
        self.ser.write(bytes([0x05, FILL]))
        return self.ser.read(2)
        
    def get_A_S(self):
        self.ser.write(bytes([0x10, FILL]))
        return self.ser.read(2)
        
    def get_X_Y(self):
        self.ser.write(bytes([0x11, FILL]))
        return self.ser.read(2)
        
    def get_IR_P(self):
        self.ser.write(bytes([0x12, FILL]))
        return self.ser.read(2)
        
    def get_PC(self):
        self.ser.write(bytes([0x13, FILL]))
        pclow, pchigh = self.ser.read(2)
        return pchigh * 256 + pclow
        
    def run_cycles(self, cycles):
        self.request_with_echo("run_cycles", [0x20, cycles])
        
    def pulse_cpu_reset(self):
        # only pulls reset down for 1 cycle
        self.request_with_echo("perform_cpu_reset", [0x21, FILL])

    def perform_cpu_reset(self):
        # takes care of reset routine
        # after this, PC is loaded with entry point address
        self.pulse_cpu_reset()
        self.run_cycles(8)
        
    def set_free_run(self, enabled):
        self.request_with_echo("set_free_run", [0x22, enabled])
    
    
    # public interface functions
    def set_address_pointer(self, a):
        self.set_address_pointer_low(a % 256)
        self.set_address_pointer_high(a // 256)
        
    def write_memory_dict(self, data_dict):
        lastaddr = -1000
        for addr, val in data_dict.items():
            if lastaddr+1 != addr:
                print(f"loading adr_ptr with ${addr:04x}")
                self.set_address_pointer(addr)
            
            #print(f"${addr:04x}  ${val:02x}")
            self.write_memory_1_byte(val)
            
            lastaddr = addr
        
    def read_memory_dict(self, addresses):
        mem_dict = {addr: -1 for addr in addresses}
        
        lastaddr = -1000
        i = 0
        while i < len(addresses):
            addr = addresses[i]
            
            if lastaddr+2 != addr:
                print(f"loading adr_ptr with ${addr:04x}")
                self.set_address_pointer(addr)
            
            val1, val2 = self.read_memory_2_byte()
            # print(f"${addr:04x}:  ${val1:02x} ${val2:02x}")
            mem_dict[addr] = val1
            mem_dict[addr+1] = val2
            
            if i+1 < len(addresses) and addr+1 == addresses[i+1]:
                i += 1
            
            lastaddr = addr
            i += 1
        
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
        

