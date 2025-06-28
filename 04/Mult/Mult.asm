// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.

// TODO: run auto test after fix https://github.com/nand2tetris/web-ide/issues/565

    // result=0
    @r
    M=0
    // i=R[1]
    @R1
    D=M
    @i
    M=D

(LOOP)
    // if(i == 0) goto STOP
    @i
    D=M
    @STOP
    D;JEQ

    // result = result + R[0]
    @r
    D=M
    @R0
    D=D+M
    @r
    M=D

    // i = i-1
    @i
    M=M-1

    @LOOP
    0;JMP

(STOP) 
    // R[2] = result
    @r
    D=M
    @R2
    M=D
(END)
    @END
    0;JMP