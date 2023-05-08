#!/usr/bin/env python3

from Test import Test
from Proto import Proto
import serial
import sys

tests = []

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
    
    
tests.append(Test("flag carry set",
    """
      .org $8000
      sec
    """, 1+2,
    "B(P, 0)=1"))
tests.append(Test("flag carry reset",
    """
      .org $8000
      clc
    """, 1+2,
    "B(P, 0)=0"))


tests.append(Test("ALU adc imm",
    """
      .org $8000
      lda #$10
      clc
      adc #$5
    """, 1+2*3,
    "A=15")) 
tests.append(Test("ALU adc abs",
    """
      .org $8000
      lda #$10
      sta $0200
      lda #$25
      clc
      adc $0200
    """, 1+(4+2)*2+2,
    "A=35"))
    
tests.append(Test("index increments",
    """
      .org $8000
      ldx #$30
      inx
      inx
      ldy #$20
      iny
      iny
    """, 1+2*6,
    "X=32", "Y=22"))

tests.append(Test("ALU sbc imm",
    """
      .org $8000
      lda #$10
      sec
      sbc #$5
    """, 1+2*3,
    "A=0b"))
tests.append(Test("ALU sbc abs",
    """
      .org $8000
      lda #$5
      sta $0200
      lda #$30
      sec
      sbc $0200
    """, 1+(4+2)*2+2,
    "A=2b"))

tests.append(Test("ALU ora imm",
    """
      .org $8000
      lda #$10
      ora #$5
    """, 1+2*2,
    "A=15"))
tests.append(Test("ALU ora abs",
    """
      .org $8000
      lda #$4
      sta $0200
      lda #$38
      ora $0200
    """, 1+(4+2)*2,
    "A=3c"))

tests.append(Test("ALU and imm",
    """
      .org $8000
      lda #$10
      and #$5
    """, 1+2*2,
    "A=0"))
tests.append(Test("ALU and abs",
    """
      .org $8000
      lda #$1c
      sta $0200
      lda #$38
      and $0200
    """, 1+(4+2)*2,
    "A=18"))
    
tests.append(Test("ALU eor imm",
    """
      .org $8000
      lda #$10
      eor #$15
    """, 1+2*2,
    "A=5"))
tests.append(Test("ALU eor abs",
    """
      .org $8000
      lda #$1c
      sta $0200
      lda #$38
      eor $0200
    """, 1+(4+2)*2,
    "A=24"))
    
    
    
tests.append(Test("ALU dec abs",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      dec $0200
      sec
      dec $0200
    """, 1+2+4+(2+6)*2,
    "MEM(0200)=3"))
tests.append(Test("ALU dec abs,X",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      sec
      dec $0200, X
      sec
      dec $0200, X
    """, 1+2+4+2+(2+6)*2,
    "MEM(0202)=3"))
    
tests.append(Test("ALU inc abs",
    """
      .org $8000
      lda #$5
      sta $0200
      clc
      inc $0200
      clc
      inc $0200
    """, 1+2+4+(2+6)*2,
    "MEM(0200)=7"))
tests.append(Test("ALU inc abs,X",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      inc $0200, X
      clc
      inc $0200, X
      clc
    """, 1+2+4+2+(2+6)*2,
    "MEM(0202)=7"))
    
tests.append(Test("ALU asl abs c=1",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      asl $0200
    """, 1+2+4+2+6*1,
    "MEM(0200)=A"))
tests.append(Test("ALU asl abs,X c=0",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      clc
      asl $0200, X
    """, 1+2+4+2+2+6*1,
    "MEM(0202)=A"))
tests.append(Test("ALU asl A",
    """
      .org $8000
      lda #$5
      asl A
    """, 1+2+2,
    "A=A"))
    
tests.append(Test("ALU rol abs c=1",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      rol $0200
    """, 1+2+4+2+6*1,
    "MEM(0200)=B"))
tests.append(Test("ALU rol abs,X c=0",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      clc
      rol $0200, X
    """, 1+2+4+2+2+6*1,
    "MEM(0202)=A"))
tests.append(Test("ALU rol A",
    """
      .org $8000
      lda #$5
      rol A
    """, 1+2+2,
    "A=A"))
    
tests.append(Test("ALU lsr abs c=1",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      lsr $0200
    """, 1+2+4+2+6*1,
    "MEM(0200)=2"))
tests.append(Test("ALU lsr abs,X c=0",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      clc
      lsr $0200, X
    """, 1+2+4+2+2+6*1,
    "MEM(0202)=2"))
tests.append(Test("ALU lsr A",
    """
      .org $8000
      lda #$5
      lsr A
    """, 1+2+2,
    "A=2"))
    
tests.append(Test("ALU ror abs c=1",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      ror $0200
    """, 1+2+4+2+6*1,
    "MEM(0200)=82"))
tests.append(Test("ALU ror abs,X c=0",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      clc
      ror $0200, X
    """, 1+2+4+2+2+6*1,
    "MEM(0202)=2"))
tests.append(Test("ALU ror A + next",
    """
      .org $8000
      lda #$5
      ror A
      ldx #$88
    """, 1+2+2+2,
    "A=2", "X=88"))



tests.append(Test("abs x/y read",
    """
      .org $8000
      lda #$5
      sta $0202
      lda #$A
      ldx #0
      sta $0203
      ldx #2
      lda $0200, X
      ldy #3
      ldx $0200, Y
    """, 1+2+(2+4)*4,
    "A=5", "X=A"))
tests.append(Test("abs x/y write",
    """
      .org $8000
      ldx #$2
      ldy #$3
      lda #$50
      sta $0200, X
      lda #$A0
      sta $0200, Y
    """, 1+2*3+4+2+4,
    "M(0202)=50", "M(0203)=A0"))


tests.append(Test("stack pha",
	"""
	  .org $8000
	  ldx #$FF
	  txs
	  lda #$50
	  pha
	  lda #$A0
	  pha
	""", 1+2*3+3+2+3,
	"M(01FF)=50", "M(01FE)=A0")) 
tests.append(Test("stack pla",
	"""
	  .org $8000
	  ldx #$FF
	  txs
	  lda #$50
	  pha
	  lda #$A0
	  pla
	""", 1+2*3+3+2+4,
	"A=50")) 
# TODO php plp

tests.append(Test("jmp",
	"""
	  .org $8000
	  ldx #0
	.loop:
	  inx
	  jmp .loop
	""", 1+2+(2+3)*10,
	"X=0A")) 


tests.append(Test("flag neg reset",
	"""
	  .org $8000
	  lda #20
      sbc #15
	""", 1+2*2,
	"B(P, 7)=0"))
tests.append(Test("flag neg set",
	"""
	  .org $8000
	  lda #20
      sbc #30
	""", 1+2*2,
	"B(P, 7)=1"))

tests.append(Test("flag ov set1",
	"""
	  .org $8000
	  lda #80
      adc #80
	""", 1+2*2,
	"B(P, 6)=1"))
tests.append(Test("flag ov reset1",
	"""
	  .org $8000
	  lda #20
      sbc #30
	""", 1+2*2,
	"B(P, 6)=0"))
tests.append(Test("flag ov set2",
    """
      .org $8000
      lda #20
      sbc #130
    """, 1+2*2,
    "B(P, 6)=1"))
tests.append(Test("flag ov reset2",
	"""
	  .org $8000
	  lda #20
      sbc #15
	""", 1+2*2,
	"B(P, 6)=0"))
    
tests.append(Test("flag carry set",
	"""
	  .org $8000
	  lda #120
      adc #150
	""", 1+2*2,
	"B(P, 0)=1"))
tests.append(Test("flag carry reset",
	"""
	  .org $8000
	  lda #20
      sec
      adc #20
	""", 1+2*3,
	"B(P, 0)=0"))

tests.append(Test("flag zero set",
	"""
	  .org $8000
	  lda #20
      cmp #20
	""", 1+2*2,
	"B(P, 1)=1"))
tests.append(Test("flag zero reset",
	"""
	  .org $8000
	  lda #20
      cmp #19
	""", 1+2*2,
	"B(P, 1)=0"))


tests = []
tests.append(Test("branch plus",
	"""
	  .org $8000
      ldx #10
    .loop:
      dex
      bpl .loop
    n:
      jmp n
	""", 1+2+(2+3)*20,
	"X=FF"))
tests.append(Test("branch minus",
	"""
	  .org $8000
      ldx #$fe
    .loop:
      inx
      bmi .loop
    n:
      jmp n
	""", 1+2+(2+3)*20,
	"X=0"))
tests.append(Test("branch ov clear",
	"""
	  .org $8000
      ldx #120
    .loop:
      inx
      bvc .loop
    n:
      jmp n
	""", 1+2+(2+3)*20,
	"X=80"))
tests.append(Test("branch ov set",
	"""
	  .org $8000
      ldx #127
    .loop:
      inx
      bvs .loop
    n:
      jmp n
	""", 1+2+(2+3)*20,
	"X=81"))
tests.append(Test("branch carry clear",
	"""
	  .org $8000
      ldx #250
    .loop:
      inx
      bcc .loop
    n:
      jmp n
	""", 1+2+(2+3)*20,
	"X=0"))
tests.append(Test("branch carry set",
	"""
	  .org $8000
      ldx #255
    .loop:
      clc
      inx
      bcs .loop
    n:
      jmp n
	""", 1+2+(2+2+3)*20,
	"X=1"))
tests.append(Test("branch not eq",
	"""
	  .org $8000
      ldx #$50
      clc
    .loop:
      inx
      cpx #$5A
      bne .loop
    n:
      jmp n
	""", 1+2+2+(2+2+3)*20,
	"X=5A"))
tests.append(Test("branch eq",
	"""
	  .org $8000
      ldx #$50
    .loop:
      clc
      inx
      cpx #$51
      beq .loop
    n:
      jmp n
	""", 1+2+(2+2+2+3)*20,
	"X=52"))



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
    
