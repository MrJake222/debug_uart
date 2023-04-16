#!/usr/bin/env python3

from Test import Test
from Proto import Proto
import serial
import sys

tests = []

# memory write by dgbu sometimes fails
# or writes garbage (fe, ff, etc.)

# make every command send confirmation after it finishes
# ex. after cpu finishes execution

tests.append(Test("load imm A/X/Y",
    """
      .org $8000
      lda #$20
      ldx #$21
      ldy #$22
    """, 1+2*3,
    "A=20", "X=21", "Y=22"))

tests.append(Test("store abs A/X/Y",
    """
      .org $8000
      lda #$20
      ldx #$21
      ldy #$22
      sta $0200
      stx $0201
      sty $0202
    """, 1+(2+4)*3,
    "M(0200)=20", "M(0201)=21", "M(0202)=22"))
    
tests.append(Test("load abs A/X/Y",
    """
      .org $8000
      lda #$20
      ldx #$21
      ldy #$22
      sta $0200
      stx $0201
      sty $0202
      lda $0202
      ldx $0200
      ldy $0201
    """, 1+(2+4+4)*3,
    "A=22", "X=20", "Y=21"))

tests.append(Test("transfers A->",
    """
      .org $8000
      lda #$5
      ldx #$6
      ldy #$7
      tax
      tay
    """, 1+2*5,
    "X=5", "Y=5"))
    
tests.append(Test("transfers X->",
    """
      .org $8000
      ldx #$8
      lda #$9      
      txa
      txs
    """, 1+2*4,
    "A=8", "S=8"))
    
tests.append(Test("transfers S->",
    """
      .org $8000
      ldx #$9
      txs
      ldx #$10
      tsx
    """, 1+2*4,
    "X=9"))
    
tests.append(Test("transfers Y->",
    """
      .org $8000
      ldy #$10
      lda #$11
      tya
    """, 1+2*3,
    "A=10"))

prot = Proto(serial.Serial("/dev/ttyUSB0", 115200))

for test in tests:
    test.compile()
    test.upload(prot)
    test.run(prot)
    r = test.verify(prot)
    if r != 0:
        sys.exit(1)
else:
    print(f"all tests passed. count={len(tests)}")
    
