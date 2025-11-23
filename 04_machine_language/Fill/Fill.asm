// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.

(LOOP)
    @i
    M=0

    @color
    M=-1
    //  if(R[KBD] == 0) goto SET
    @KBD
    D=M
    @SET
    D;JEQ

    // goto CHANGE
    @CHANGE
    0;JMP

(SET)
    // color = 0
    @color
    M=0

    // goto CHANGE
    @CHANGE
    0;JMP

(CHANGE)
    // if(i == 8192) goto LOOP
    @8192
    D=A
    @i
    D=D-M
    @LOOP
    D;JEQ

    // sword = &SCREEN + i
    @SCREEN
    D=A
    @i
    D=D+M
    @sword
    M=D

    // *sword = color
    @color
    D=M
    @sword
    A=M
    M=D

    // i = i +1
    @i
    M=M+1
    // goto CHANGE
    @CHANGE
    0;JMP
