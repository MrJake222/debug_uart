#!/usr/bin/env python3

import os
import sys
import time
import serial
import argparse
from intelhex import IntelHex
from Proto import Proto
from Proto32 import Proto32
from ProtoError import ProtoError

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
    p.add_argument("--d32", help="use dbgu32 version", required=False, default=False, action='store_true')

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
    
    run = subp.add_parser("run", description="start the processor")
    run_grp = run.add_mutually_exclusive_group(required=True)
    run_grp.add_argument("-c", "--clks", help="finite number of clocks to run", type=int)
    run_grp.add_argument("-f", "--freerun", help="free run mode enabled", action='store_true')
    run_grp.add_argument("-n", "--no-freerun", help="free run mode enabled", dest='feature', action='store_false')
    
    reset = subp.add_parser("reset", description="reset the processor")
    reset.add_argument("--pc", help="perform reset routine and read PC (disables freerun)", required=False, default=False, action='store_true')
    
    #p.description="Interface the FPGA 6502 via UART\n\nActions:"
    for name, parser in subp.choices.items():
        p.description += f"{name: >10}  {parser.description}\n"
    
    return p, p.parse_args()


p, args = get_args()
ser = serial.Serial(args.port, args.baudrate, timeout=args.timeout)
if args.d32:
    prot = Proto32(ser)
else:
    prot = Proto(ser)

try:
    if args.action == "write":
        data_dict = {}
        
        if args.ihex:
            print(f"loading IntelHex data from {os.path.basename(args.ihex)}")
            
            ih = IntelHex(args.ihex)
            for addr in ih.addresses():
                data_dict[addr] = ih[addr]
        
        elif args.bin:
            if args.org is None:
                p.error("-o/--org required with binary data")
                
            print(f"loading binary data from {os.path.basename(args.bin)} at {args.org:04x}")
            addr = args.org
            with open(args.bin, "rb") as f:
                while True:
                    data = f.read(1)
                    if not data:
                        break
                    
                    data_dict[addr] = data[0]
                    addr += 1
            
        elif args.mem:
            if args.org is None:
                p.error("-o/--org required with raw memory")
                
            print(f"loading raw memory data data from command line at {args.org:04x}")
            addr = args.org
            for data in args.mem:
                data_dict[addr] = data
                addr += 1
                
        else:
            p.error("no data to write, provide one of --ihex/--bin/--mem")
                
        print()
        print("writing data")
        t1 = time.time()
                
        prot.write_memory_dict(data_dict)
            
        t2 = time.time()
        print(f"OK {t2-t1:.2f}s")
                
        if args.verify:
            print()
            print("verifying data")
            t1 = time.time()
            
            mem_dict = prot.read_memory_dict(data_dict.keys())
            for addr, val in data_dict.items():
                # print(mem_dict[addr], val)
                if mem_dict[addr] != val:
                    eprint(f"verify error: first error at ${prot.addr_format(addr)}: " \
                           f"should be ${val:02x}, is ${prot.value_format(mem_dict[addr])}")
                    sys.exit(1)
            
            t2 = time.time()
            print(f"OK {t2-t1:.2f}s")


    if args.action == "read":
        addresses = [args.org + i for i in range(args.num)]
        mem_dict = prot.read_memory_dict(addresses)
        
        for i, addr in enumerate(addresses):
            if i % 8 == 0:
                print(f"\n${prot.addr_format(addr)}:  ", end="")
            print(f"{prot.value_format(mem_dict[addr])} ", end="")
        print()
        print()
        
        
    if args.action == "status":
        prot.print_status()


    if args.action == "run":
        if args.clks:
            prot.run_cycles(args.clks)
            
            PC = prot.get_PC()
            print(f"run for {args.clks} cycles, PC: ${PC:04x}")
        
        if args.freerun is not None:
            en = 1 if args.freerun else 0
            prot.set_free_run(en)
            print(f"set freerun to {en}")


    if args.action == "reset":
        if args.pc:
            prot.perform_cpu_reset()
            PC = prot.get_PC()
            print(f"performed reset, PC: ${PC:04x}")
        else:
            # only pulse
            prot.pulse_cpu_reset()
        
except ProtoError:
    eprint(f"\n{sys.argv[0]}: protocol error occurred")
    sys.exit(3)
        
except TimeoutError:
    eprint(f"\n{sys.argv[0]}: timeout occurred")
    sys.exit(3)
