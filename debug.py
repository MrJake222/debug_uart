#!/usr/bin/env python3

import os
import sys
import serial
import argparse
from intelhex import IntelHex
from Proto import Proto, ProtoError

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def get_args():
    
    p = argparse.ArgumentParser(
        description="Interface the FPGA 6502 via UART\nActions:\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    p.add_argument("-p", "--port", help="serial port to use", required=False, default="/dev/ttyUSB0")
    p.add_argument("-b", "--baudrate", help="baud of serial", required=False, default=115200, metavar="BAUD")
    p.add_argument("-t", "--timeout", help="timeout of serial port [seconds]", required=False, default=1, metavar="T", type=float)

    subp = p.add_subparsers(required=True, dest="action")
    
    write = subp.add_parser("write", description="write a program into memory")
    write.add_argument("-o", "--org", help="origin, where to write the program (hex)", required=False, type=lambda x: int(x, 16))
    write.add_argument("-i", "--ihex", help="hex file to write", required=False)
    write.add_argument("-b", "--bin", help="bin file to write", required=False)
    write.add_argument("-m", "--mem", help="raw memory data to write (hex)", required=False, nargs ="*", type=lambda x: int(x, 16))
    write.add_argument("-v", "--verify", help="verify the program after upload", required=False, default=False, action='store_true')
    
    read = subp.add_parser("read", description="read data from memory")
    read.add_argument("-o", "--org", help="origin, where start a read (hex)", required=True, type=lambda x: int(x, 16))
    read.add_argument("-n", "--num", help="number of bytes to read", required=True, type=int)
    
    status = subp.add_parser("status", description="check CPU registers")
    
    run = subp.add_parser("run", description="start the processor for given number of cycles")
    run.add_argument("clks", help="clocks to run", type=int)
    
    reset = subp.add_parser("reset", description="reset the processor")
    
    #p.description="Interface the FPGA 6502 via UART\n\nActions:"
    for name, parser in subp.choices.items():
        p.description += f"{name: >10}  {parser.description}\n"
    
    return p, p.parse_args()


p, args = get_args()
prot = Proto(serial.Serial(args.port, args.baudrate, timeout=args.timeout))

try:
    if args.action == "write":
        if args.ihex:
            print(f"loading IntelHex data from {os.path.basename(args.ihex)}")
            
            ih = IntelHex(args.ihex)
            data_dict = ih.todict()
        
        elif args.bin:
            if not args.org:
                p.error("-o/--org required with binary data")
                
            print(f"loading binary data from {os.path.basename(args.bin)} at {args.org:04x}")
            data_dict = {}
            addr = args.org
            with open(args.bin, "rb") as f:
                while True:
                    data = f.read(1)
                    if not data:
                        break
                    
                    data_dict[addr] = data[0]
                    addr += 1
            
        elif args.mem:
            if not args.org:
                p.error("-o/--org required with raw memory")
                
            print(f"loading raw memory data data from command line at {args.org:04x}")
            data_dict = {}
            addr = args.org
            for data in args.mem:
                data_dict[addr] = data
                addr += 1
                
        else:
            p.error("no data to write, provide one of --ihex/--bin/--mem")
                
                
        lastaddr = -1
        for addr, val in data_dict.items():
            if lastaddr+1 != addr:
                print(f"loading adr_ptr with ${addr:04x}")
                prot.set_address_pointer(addr)
            
            print(f"${addr:04x}  ${val:02x}")
            prot.write_memory_1_byte(val)
            
            lastaddr = addr
        
        if args.verify:
            print("verifying data")
            mem_dict = prot.read_memory_dict(data_dict.keys())
            for addr, val in data_dict.items():
                if mem_dict[addr] != val:
                    eprint(f"verify error: first error at ${addr:04x}: should be ${val:02x}, is ${mem_dict[addr]:02x}")
                    sys.exit(1)
            
            print("OK.")


    if args.action == "read":
        lastaddr = -1
        for i in range(0, args.num, 2):
            addr = args.org + i
            
            if lastaddr+2 != addr:
                print(f"loading adr_ptr with ${addr:04x}")
                prot.set_address_pointer(addr)
            
            val1, val2 = prot.read_memory_2_byte()
            print(f"${addr:04x}:  ${val1:02x} ${val2:02x}")
            
            lastaddr = addr
        
        
    if args.action == "status":
        A, S = prot.get_A_S()
        X, Y = prot.get_X_Y()
        IR, P = prot.get_IR_P()
        PC = prot.get_PC()
        
        print(f"A     ${A:02x}")
        print(f"X     ${X:02x}")
        print(f"Y     ${Y:02x}")
        print(f"S     ${S:02x}")
        print(f"IR    ${IR:02x}")
        print(f"P     ${P:02x}")
        print(f"PC  ${PC:04x}")


    if args.action == "run":
        prot.run_cycles(args.clks)
        
        PC = prot.get_PC()
        print(f"run for {args.clks} cycles, PC: ${PC:04x}")


    if args.action == "reset":
        prot.perform_cpu_reset()
        
        PC = prot.get_PC()
        print(f"performed reset, PC: ${PC:04x}")
        
except ProtoError:
    eprint(f"\n{sys.argv[0]}: protocol error occurred")
    sys.exit(3)
        
except TimeoutError:
    eprint(f"\n{sys.argv[0]}: timeout occurred")
    sys.exit(3)
