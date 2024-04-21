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
    """, 2*3,
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
    """, (2+4)*3,
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
    """, (2+4+4)*3,
    "A=22", "X=20", "Y=21"))

tests.append(Test("transfers A->",
    """
      .org $8000
      lda #$5
      ldx #$6
      ldy #$7
      tax
      tay
    """, 2*5,
    "X=5", "Y=5"))
tests.append(Test("transfers X->",
    """
      .org $8000
      ldx #$8
      lda #$9      
      txa
      txs
    """, 2*4,
    "A=8", "S=8"))
tests.append(Test("transfers S->",
    """
      .org $8000
      ldx #$9
      txs
      ldx #$10
      tsx
    """, 2*4,
    "X=9"))
tests.append(Test("transfers Y->",
    """
      .org $8000
      ldy #$10
      lda #$11
      tya
    """, 2*3,
    "A=10"))
    
    
tests.append(Test("flag carry set",
    """
      .org $8000
      sec
    """, 2,
    "B(P, 0)=1"))
tests.append(Test("flag carry reset",
    """
      .org $8000
      clc
    """, 2,
    "B(P, 0)=0"))


tests.append(Test("ALU adc imm",
    """
      .org $8000
      lda #$10
      clc
      adc #$5
    """, 2*3,
    "A=15")) 
tests.append(Test("ALU adc abs",
    """
      .org $8000
      lda #$10
      sta $0200
      lda #$25
      clc
      adc $0200
    """, (4+2)*2+2,
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
    """, 2*6,
    "X=32", "Y=22"))

tests.append(Test("ALU sbc imm",
    """
      .org $8000
      lda #$10
      sec
      sbc #$5
    """, 2*3,
    "A=0b"))
tests.append(Test("ALU sbc abs",
    """
      .org $8000
      lda #$5
      sta $0200
      lda #$30
      sec
      sbc $0200
    """, (4+2)*2+2,
    "A=2b"))

tests.append(Test("ALU ora imm",
    """
      .org $8000
      lda #$10
      ora #$5
    """, 2*2,
    "A=15"))
tests.append(Test("ALU ora abs",
    """
      .org $8000
      lda #$4
      sta $0200
      lda #$38
      ora $0200
    """, (4+2)*2,
    "A=3c"))

tests.append(Test("ALU and imm",
    """
      .org $8000
      lda #$10
      and #$5
    """, 2*2,
    "A=0"))
tests.append(Test("ALU and abs",
    """
      .org $8000
      lda #$1c
      sta $0200
      lda #$38
      and $0200
    """, (4+2)*2,
    "A=18"))
    
tests.append(Test("ALU eor imm",
    """
      .org $8000
      lda #$10
      eor #$15
    """, 2*2,
    "A=5"))
tests.append(Test("ALU eor abs",
    """
      .org $8000
      lda #$1c
      sta $0200
      lda #$38
      eor $0200
    """, (4+2)*2,
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
    """, 2+4+(2+6)*2,
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
    """, 2+4+2+(2+6)*2,
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
    """, 2+4+(2+6)*2,
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
    """, 2+4+2+(2+6)*2,
    "MEM(0202)=7"))

tests.append(Test("ALU asl abs c=1",
    """
      .org $8000
      lda #$85
      sta $0200
      sec
      asl $0200
    """, 2+4+2+6*1,
    "MEM(0200)=A", "B(P, 0)=1")) # P,0 -- carry out
tests.append(Test("ALU asl abs,X c=0",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      clc
      asl $0200, X
    """, 2+4+2+2+6*1,
    "MEM(0202)=A", "B(P, 0)=0"))
tests.append(Test("ALU asl A",
    """
      .org $8000
      lda #$85
      asl A
    """, 2+2,
    "A=A", "B(P, 0)=1"))
    
tests.append(Test("ALU rol abs c=1",
    """
      .org $8000
      lda #$85
      sta $0200
      sec
      rol $0200
    """, 2+4+2+6*1,
    "MEM(0200)=B", "B(P, 0)=1"))
tests.append(Test("ALU rol abs,X c=0",
    """
      .org $8000
      lda #$5
      sta $0202
      ldx #2
      clc
      rol $0200, X
    """, 2+4+2+2+6*1,
    "MEM(0202)=A", "B(P, 0)=0"))
tests.append(Test("ALU rol A",
    """
      .org $8000
      lda #$85
      clc
      rol A
    """, 2*3,
    "A=A", "B(P, 0)=1"))
    
tests.append(Test("ALU lsr abs c=1",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      lsr $0200
    """, 2+4+2+6*1,
    "MEM(0200)=2", "B(P, 0)=1"))
tests.append(Test("ALU lsr abs,X c=0",
    """
      .org $8000
      lda #$4
      sta $0202
      ldx #2
      clc
      lsr $0200, X
    """, 2+4+2+2+6*1,
    "MEM(0202)=2", "B(P, 0)=0"))
tests.append(Test("ALU lsr A",
    """
      .org $8000
      lda #$5
      lsr A
    """, 2+2,
    "A=2", "B(P, 0)=1"))
    
tests.append(Test("ALU ror abs c=1",
    """
      .org $8000
      lda #$5
      sta $0200
      sec
      ror $0200
    """, 2+4+2+6*1,
    "MEM(0200)=82", "B(P, 0)=1"))
tests.append(Test("ALU ror abs,X c=0",
    """
      .org $8000
      lda #$4
      sta $0202
      ldx #2
      clc
      ror $0200, X
    """, 2+4+2+2+6*1,
    "MEM(0202)=2", "B(P, 0)=0"))
tests.append(Test("ALU ror A + next",
    """
      .org $8000
      lda #$5
      clc
      ror A
      ldx #$88
    """, 2*4,
    "A=2", "B(P, 0)=1", "X=88"))



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
    """, 2+(2+4)*4,
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
    """, 2*3+4+2+4,
    "M(0202)=50", "M(0203)=A0"))
tests.append(Test("abs x/y page overf",
    """
      .org $8000
      ldx #$50
      lda #$AA
      sta $02F0, X
    """, 2*2+5,
    "M(0340)=AA"))


tests.append(Test("stack pha",
	"""
	  .org $8000
	  ldx #$FF
	  txs
	  lda #$50
	  pha
	  lda #$A0
	  pha
	""", 2*3+3+2+3,
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
	""", 2*3+3+2+4,
	"A=50")) 
# TODO php plp

tests.append(Test("jmp",
	"""
	  .org $8000
	  ldx #0
	.loop:
	  inx
	  jmp .loop
	""", 2+(2+3)*10,
	"X=0A")) 


tests.append(Test("flag neg reset",
	"""
	  .org $8000
	  lda #20
      sbc #15
	""", 2*2,
	"B(P, 7)=0"))
tests.append(Test("flag neg set",
	"""
	  .org $8000
	  lda #20
      sbc #30
	""", 2*2,
	"B(P, 7)=1"))

tests.append(Test("flag ov set1",
	"""
	  .org $8000
	  lda #80
      adc #80
	""", 2*2,
	"B(P, 6)=1"))
tests.append(Test("flag ov reset1",
	"""
	  .org $8000
	  lda #20
      sbc #30
	""", 2*2,
	"B(P, 6)=0"))
tests.append(Test("flag ov set2",
    """
      .org $8000
      lda #20
      sbc #130
    """, 2*2,
    "B(P, 6)=1"))
tests.append(Test("flag ov reset2",
	"""
	  .org $8000
	  lda #20
      sbc #15
	""", 2*2,
	"B(P, 6)=0"))
    
tests.append(Test("flag carry set",
	"""
	  .org $8000
	  lda #120
      adc #150
	""", 2*2,
	"B(P, 0)=1"))
tests.append(Test("flag carry reset",
	"""
	  .org $8000
	  lda #20
      sec
      adc #20
	""", 2*3,
	"B(P, 0)=0"))

tests.append(Test("flag zero set cmp",
	"""
	  .org $8000
	  lda #20
      cmp #20
	""", 2*2,
	"B(P, 1)=1"))
tests.append(Test("flag zero reset cmp",
	"""
	  .org $8000
	  lda #20
      cmp #19
	""", 2*2,
	"B(P, 1)=0"))
tests.append(Test("flag zero/carry set inx",
	"""
	  .org $8000
	  ldx #$ff
      inx
	""", 2*2,
	"B(P, 1)=1", "B(P, 0)=1"))
tests.append(Test("flag zero/carry set iny",
	"""
	  .org $8000
	  ldy #$ff
      iny
	""", 2*2,
	"B(P, 1)=1", "B(P, 0)=1"))
tests.append(Test("flag zero/neg lda",
	"""
	  .org $8000
	  ldy #$ff
      iny
      lda #$90
	""", 2*3,
	"B(P, 7)=1", "B(P, 1)=0"))
tests.append(Test("flag zero/neg lda 2",
	"""
	  .org $8000
	  ldx #7F
      inx
      lda #0
	""", 2*3,
	"B(P, 7)=0", "B(P, 1)=1"))
tests.append(Test("carry chain",
	"""
ADR=$00
	  .org $8000
      lda #$C0
      sta ADR
      lda #$50
      sta ADR+1
      
      clc
      lda ADR
      adc #64
      sta ADR
      lda ADR+1
      adc #0
      sta ADR+1
	""", (2+3)*2+2+(3+2+3)*2,
	"M(00)=0", "M(01)=51"))
tests.append(Test("carry iny",
	"""
ADR=$00
	  .org $8000
      ldy #0
      sec
      iny
	""", 2*3,
	"Y=1"))

tests.append(Test("branch plus",
	"""
	  .org $8000
      ldx #10
    .loop:
      dex
      bpl .loop
    n:
      jmp n
	""", 2+(2+3)*20,
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
	""", 2+(2+3)*20,
	"X=0"))
tests.append(Test("branch ov clear",
	"""
	  .org $8000
      lda #120
      clc
    .loop:
      adc #1
      bvc .loop
    n:
      jmp n
	""", 2*2+(2+3)*20,
	"A=80"))
tests.append(Test("branch ov set",
	"""
	  .org $8000
      lda #127
      clc
    .loop:
      adc #1
      bvs .loop
    n:
      jmp n
	""", 2*2+(2+3)*20,
	"A=81"))
tests.append(Test("branch carry clear",
	"""
	  .org $8000
      lda #250
      clc
    .loop:
      adc #1
      bcc .loop
    n:
      jmp n
	""", 2*2+(2+3)*20,
	"A=0"))
tests.append(Test("branch carry set",
	"""
	  .org $8000
      lda #255
    .loop:
        clc
      adc #1
      bcs .loop
    n:
      jmp n
	""", 2+(2+2+3)*20,
	"A=1"))
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
	""", 2+2+(2+2+3)*20,
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
	""", 2+(2+2+2+3)*20,
	"X=52"))
    
tests.append(Test("branch page overf",
	"""
	  .org $8000
      clc
      jmp test
    
    .org $80F0
    test:
      clc
      bcc $8150
	""", 3+2+4,
	"PC=8150"))
tests.append(Test("branch page underf",
	"""
	  .org $8000
      clc
      jmp test
    
    .org $8110
    test:
      clc
      bcc $80F0
	""", 3+2+4,
	"PC=80F0"))


tests.append(Test("sta zpg",
	"""
	  .org $8000
      lda #$15
      sta $00
	""", 2+3,
	"M(00)=15"))
tests.append(Test("lda zpg",
	"""
	  .org $8000
      lda #$15
      sta $00
      ldx $00
	""", 2+3+3,
	"X=15"))
tests.append(Test("adc zpg",
	"""
	  .org $8000
      lda #$15
      sta $00
      lda #$05
      clc
      adc $00
	""", 2+3+2+2+3,
	"A=1A"))
tests.append(Test("asl zpg",
	"""
	  .org $8000
      lda #$28
      sta $00
      asl $00
	""", 2+3+5,
	"M(00)=50"))

tests.append(Test("sta ind, y",
	"""
	  .org $8000
      lda #$15
      sta $00
      lda #$02
      sta $01
      
      lda #$AA
      ldy #$05
      sta ($00), y
	""", (2+3)*2+2*2+6,
	"M(00)=15", "M(01)=02", "M(021A)=AA"))
tests.append(Test("sta ind, y page overf",
	"""
	  .org $8000
      lda #$F0
      sta $00
      lda #$02
      sta $01
      
      lda #$AA
      ldy #$51
      sta ($00), y
	""", (2+3)*2+2*2+7,
	"M(0341)=AA"))

tests.append(Test("jsr",
	"""
	  .org $8000
      ldx #$FF
      txs
      lda #0
      jsr test
      lda #$5
    test:
      ldy #6
      rts
	""", 2*3+6+2,
	"A=0", "Y=6"))
tests.append(Test("jsr2",
	"""
	  .org $8000
      ldx #$FF
      txs
      lda #0
      jsr test
      lda #$5
    test:
      ldy #6
      rts
	""", 2*3+(6+2)*2,
	"A=5"))

tests.append(Test("abs ind",
	"""
	  .org $8000
      jmp (test)
      lda #$20
      lda #$20
	real_test:
	  lda #$10
    test:
      .word real_test
	""", 6+2,
	"A=10"))
tests.append(Test("zpg x,ind",
	"""
	  .org $8000
	  lda #$66
	  sta $45
	  lda #$03
	  sta $46
      lda #$30
      ldx #$5
      sta ($40, x)
      clc
      lda #$40
      adc ($40, x)
	""", (2+3)*2+2+6+2+2+2+6,
	"A=70", "M(366)=30"))
tests.append(Test("zpg,x",
	"""
	  .org $8000
      lda #$20
      ldx #$10
      sta $50, x
      clc
      lda #$10
      adc $50, x
	""", 4+4+2+2+4,
	"A=30", "M(60)=20"))
tests.append(Test("zpg,y",
	"""
	  .org $8000
      lda #$20
      ldy #$80
      sta $50, y
      clc
      lda #$50
      adc $50, y
	""", 4+4+2+2+4,
	"A=70", "M(D0)=20"))
tests.append(Test("zpg,x rmw",
	"""
	  .org $8000
      lda #$33
      ldx #$10
      sta $50, x
      asl $50, x
	""", 2+2+6+6,
	"M(60)=66"))
tests.append(Test("php/plp",
	"""
	  .org $8000
	  ldx #$FF
      txs
      clc
      lda #$80
      php
	  sta $00
	  adc $00
	  plp
	""", 2*3+3+2+3*2+4,
	"B(P, 0)=0"))

tests.append(Test("bit load m7",
	"""
	  .org $8000
	  lda #$80
	  sta $20
	  lda #$70 ; reset neg
	  bit $20
	""", 2+3+2+3,
	"B(P, 7)=1"))
tests.append(Test("bit load m6",
	"""
	  .org $8000
	  lda #$70
	  sta $20
	  clv
	  bit $20
	""", 2+3+2+3,
	"B(P, 6)=1"))
tests.append(Test("bit load zero",
	"""
	  .org $8000
	  lda #$07
	  sta $20
	  lda #$08
	  bit $20
	""", 2+3+2+3,
	"B(P, 1)=1"))
tests.append(Test("bit load not zero",
	"""
	  .org $8000
	  lda #$0F
	  sta $20
	  lda #$08
	  ldx #0 ; set zero
	  bit $20
	""", 2+3+2+2+3,
	"B(P, 1)=0"))
	
#tests = []
tests.append(Test("sbc carry clear",
	"""
	  .org $8000
	  sec
	  lda #5
	  sbc #10
	""", 2*3,
	"B(P, 0)=0"))

tests.append(Test("sbc carry set",
        """
          .org $8000
          clc
          lda #5
          sbc #4
        """, 2*3,
        "B(P, 0)=1"))

tests.append(Test("wdc dea",
        """
          .org $8000
          lda #5
          dea
        """, 2*2,
        "A=4"))
        
tests.append(Test("wdc ina",
        """
          .org $8000
          lda #2
          ina
        """, 2*2,
        "A=3"))

import sys

if len(sys.argv) != 3:
    print("Usage:", sys.argv[0], "[serial port] [baud]")
    exit(1)
    
serial_path = sys.argv[1]
serial_baud = int(sys.argv[2])

prot = Proto(serial.Serial(serial_path, serial_baud))

passed = 0
for test in tests:
    test.compile()
    test.upload(serial_path, serial_baud)
    test.run(prot)
    r = test.verify(prot)
    if r == 0:
        passed += 1

if passed == len(tests):
    print(f"all tests passed. count={len(tests)}")
else:
    print(f"{len(tests) - passed} tests failed. count={len(tests)}")
    
