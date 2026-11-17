// Lab 4 - Keyboard Program
// Keyboard controls screen colour

(LOOP)
@KBD
D=M

@WHITE
D;JEQ

@R2
M=-1
@DRAW
0;JMP

(WHITE)
@R2
M=0

(DRAW)
@SCREEN
D=A
@R0
M=D

@8192
D=A
@R1
M=D

(FILL)
@R1
D=M
@LOOP
D;JEQ

@R2
D=M

@R0
A=M
M=D

@R0
M=M+1

@R1
M=M-1

@FILL
0;JMP