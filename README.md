# Debug UART interface

## Scripting
- `debug.py` -- Main file, run `./debug.py [write read status run reset] -h` for help,
- `Proto.py` -- default, 8bit protocol implementation,
- `Proto32.py` -- 32bit protocol implementation,
- `Test.py` -- Test class, runs 6502 assembler and tests the register/memory values,
- `test.py` -- 6520 tests,
- `upload.sh` -- `write` + `reset` commands for `debug.py`, pass hex file as argument. May need to add `--d32` to run in 32bit mode.

### Usage
`debug.py` has following options:
- `-h` -- shows help,
- `-p PORT` -- serial port, default: `/dev/ttyUSB0`,
- `-b BAUD` -- serial baud, default: `115200`,
- `-t T` -- timeout in seconds, default: `1`,
- `--d32` -- switches from 8bit protocol (default) to 32bit version
- action

Actions:

#### `write`
Writes bytes (from file or from cmd) to memory.
- `-h` -- shows help,
- `-i` -- Intel Hex file to upload,
- `-b` -- binary file to upload,
- `-m` -- accepts hex octets separated by space as consecutive bytes (Little Endian, eg. `00 f a bb` will write `000f0abb` into memory)
- `-o ORG` -- starting address as hex, only required with `-b` and `-m`,
- `-v` -- verify after write.

#### `read`
Reads bytes from memory and displays it.
- `-h` -- shows help,
- `-o ORG` -- starting address as hex,
- `-n NUM` -- number of bytes to read.

#### `status`
(8bit only) Reads 6502 registers.

#### `run`
Starts/stops the processor.
- `-h` -- shows help,
- `-c CLKS` -- start CPU, stop after `CLKS` clock cycles,
- `-f` -- freerun, run indefinitely,
- `-n` -- disable freerun.

#### `reset`
Resets the processor.
- `-h` -- shows help,
- `--pc` -- (8bit only) perform reset routine (run `8` clock cycles after reset, 6502 CPU reads PC from `FFFC`)

## Protocol docs
- `docs/instruction set.ods` -- 8bit protocol docs
- `docs/instruction set 32.ods` -- 32bit protocol docs
