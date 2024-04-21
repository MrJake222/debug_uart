import subprocess

# all numbers hex
class Test:
    """
    name: test name (informative)
    code: code for assembler
    cycles: how many cycles to run
    *tests: list of tests (strings), see verify() for docs
    """
    def __init__(self, name, code, cycles, *tests):
        self.name = name
        self.code = code
        self.cycles = cycles
        
        self.tests = {}
        for test in tests:
            what, should_be = test.split("=")
            should_be = int(should_be, 16)
            self.tests[what] = should_be
        
        self.asm = ".tmp.s"
        self.pgm = ".tmp.hex"

    def compile(self):
        with open(self.asm, "w") as f:
            f.write(self.code)
        
        p = subprocess.run([
            "vasm6502_oldstyle", "-dotdir", "-esc", "-wdc02",
            "-Fihex", self.asm,
            "-o", self.pgm
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if p.returncode != 0:
            print(f"vasm errored")
            print(p.stderr.decode())
            raise ValueError("vasm error")
    
    def upload(self, serial_path, serial_baud):
        p = subprocess.run([
            "./debug.py",
            "-p", serial_path, "-b", str(serial_baud),
            "write",
            "-i", self.pgm,
            "-v"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if p.returncode == 0:
            # write reset vector
            p = subprocess.run([
                "./debug.py",
                "-p", serial_path, "-b", str(serial_baud),
                "write",
                "-o", "FFFC",
                "--mem", "00", "80",
                "-v"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if p.returncode == 0:
                return
        
        print(f"debug.py errored")
        print(p.stderr.decode())
        subprocess.run([
            "./debug.py",
            "-p", serial_path, "-b", str(serial_baud),
            "read",
            "-o", "8000",
            "-n", "32"
        ])
        raise ValueError("debug.py error")

    def run(self, prot):
        prot.perform_cpu_reset()
        # reset routine handled in reset
        prot.run_cycles(self.cycles + 1)
        # perform one extra cycle for any writebacks to finish
    
    """
    Test case
    format: <what>=<hex number>
    <what>: see Proto::get(<what>)
    """
    def verify(self, prot):
        ok = True
        
        for what, should_be in self.tests.items():
            val = prot.get(what)
            if val != should_be:
                print(f"error in test {self.name}: {what} should be ${should_be:02x}, is ${val:02x}")
                ok = False
                
        if not ok:
            return -1
        
        print(f"test {self.name:20} OK.")
        return 0
