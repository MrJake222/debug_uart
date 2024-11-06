from ProtoError import ProtoError

import struct
from collections import defaultdict

import sys
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

I_ADR_PTR_SET = 0x01
I_ADR_PTR_GET = 0x03
I_MEM_WR      = 0x04
I_MEM_RD      = 0x05
I_CPU_RUN_CYC = 0x20
I_CPU_RESET   = 0x21
I_CPU_FREERUN = 0x22
OK = 0x01

class Proto32:
    def __init__(self, ser):
        self.ser = ser
        self.batch_reset()
        
    def batch_reset(self):
        self.bmode = False
        self.bdata = bytes()
        self.brsp_len = 0
        
    def addr_format(self, addr):
        return f"{addr:08x}"
        
    def value_format(self, value):
        return f"{value:02x}"
        
    def request(self, func_name, req, rsp_len, rsp_check=None):
        # used when sending requests (all kind)
        # reads exactly rsp_len bytes (less -> timeout error)
        # is rsp_check is not Null, verifies by equality
        # ( with auto bytes conversion)
        data = bytes(req)
        
        if self.bmode:
            self.bdata += data
            self.brsp_len += rsp_len
            return bytes()
        
        self.ser.write(data)
        echo = self.ser.read(rsp_len)
        
        echo_len = len(echo)
        echo_arr = [d for d in echo]
        if echo_len != rsp_len:
            eprint(f"\ntimeout occured, received {echo_len} / {rsp_len} bytes: {echo_arr}")
            
            raise TimeoutError(f"{func_name}: timeout")
            
        if rsp_check is not None and echo != bytes(rsp_check):
            eprint(f"\n{func_name}: ack not matching")
            eprint(f"should be: {rsp_check}")
            eprint(f"is: {echo_arr}")
            
            raise ProtoError(f"{func_name}: ack not matching")
        
        return echo
    
    def request_with_ack(self, func_name, req):
        # pass to request, expecting 1 byte reply: OK (0x01)
        return self.request(func_name, req, 1, [OK])
    
    def batch(self):
        # Batch mode, requests accumulate in memory
        # execute and response collection in flush()
        # below protocol functions stay the same and
        # can be used in request generation as usual
        # (of course except their return values)
        self.bmode = True
        
    def flush(self):
        self.ser.write(self.bdata)
        echo = self.ser.read(self.brsp_len)
        if len(echo) != self.brsp_len:
            eprint(f"\nbatch flush: response length not matching")
            eprint(f"should be: {self.brsp_len}, is: {len(echo)}")
            raise ProtoError(f"batch flush: response length not matching")
        self.batch_reset()
        return echo
    
    # protocol functions
    def set_address_pointer(self, addr):
        self.request_with_ack("set_address_pointer", bytes([I_ADR_PTR_SET]) + struct.pack("<L", addr))
        
    def get_address_pointer(self):
        addr = self.request("get_address_pointer", [I_ADR_PTR_GET], 4)
        return struct.unpack("<L", addr)
        
    def write_memory_4_byte(self, b):
        self.request_with_ack("write_memory_4_byte", [I_MEM_WR]+b)
        
    def read_memory_4_byte(self):
        data = self.request("read_memory_4_byte", [I_MEM_RD], 4)
        return data
        
    def run_cycles(self, cycles):
        self.request_with_ack("run_cycles", [I_CPU_RUN_CYC, cycles])
        
    def pulse_cpu_reset(self):
        # only pulls reset down for 1 cycle
        self.request_with_ack("perform_cpu_reset", [I_CPU_RESET])

    def perform_cpu_reset(self):
        # takes care of reset routine
        # after this, PC is loaded with entry point address
        self.pulse_cpu_reset()
        self.run_cycles(8)
        
    def set_free_run(self, enabled):
        self.request_with_ack("set_free_run", [I_CPU_FREERUN, enabled])
    
    
    # public interface functions
    def write_memory_dict(self, data_dict):
        
        data_dict32 = defaultdict(lambda: [0]*4)
        for adr, val in data_dict.items():
            adr32 = adr & ~0x3
            data_dict32[adr32][adr%4] = val
        
        # self.batch()
        
        lastaddr = -1000
        for addr in sorted(data_dict32.keys()):
            val = data_dict32[addr]
            if lastaddr+4 != addr:
                print(f"loading adr_ptr with ${addr:08x}")
                self.set_address_pointer(addr)
            
            # print(f"${addr:08x}  ${val}")
            self.write_memory_4_byte(val)
            
            lastaddr = addr
            
        # self.flush()
        
    def read_memory_dict(self, addresses):
        # zero 4 least significant (and with negated 32'b11)
        # dict for uniqueness, make sorted list
        addresses32 = {x&~0x3 for x in addresses}
        addresses32 = sorted(addresses32)
        
        rsp = bytes()
        # self.batch()
        
        lastaddr = -1000
        for addr in addresses32:
            
            if lastaddr+4 != addr:
                # rsp += self.flush()
                print(f"loading adr_ptr with ${addr:08x}")
                self.set_address_pointer(addr)
                # self.batch()
            
            ret = self.read_memory_4_byte()
            rsp += ret
            
            lastaddr = addr
            
        # rsp += self.flush()
        print("read rsp len:", len(rsp))
        
        mem_dict = {}
        for addr, val in zip(addresses, rsp):
            mem_dict[addr] = val
        
        return mem_dict
    
    def print_status(self):
        raise NotImplementedError()
        

