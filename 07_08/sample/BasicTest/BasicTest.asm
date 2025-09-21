// CommandType.C_PUSH constant 10 
@10
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_POP local 0 
@0
D=A
@LCL
D=D+M
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// CommandType.C_PUSH constant 21 
@21
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 22 
@22
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_POP argument 2 
@2
D=A
@ARG
D=D+M
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// CommandType.C_POP argument 1 
@1
D=A
@ARG
D=D+M
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// CommandType.C_PUSH constant 36 
@36
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_POP this 6 
@6
D=A
@THIS
D=D+M
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// CommandType.C_PUSH constant 42 
@42
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 45 
@45
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_POP that 5 
@5
D=A
@THAT
D=D+M
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// CommandType.C_POP that 2 
@2
D=A
@THAT
D=D+M
@R13
M=D
@SP
AM=M-1
D=M
@R13
A=M
M=D
// CommandType.C_PUSH constant 510 
@510
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_POP temp 6 
@SP
AM=M-1
D=M
@11
M=D
// CommandType.C_PUSH local 0 
@0
D=A
@LCL
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH that 5 
@5
D=A
@THAT
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// add 
@SP
AM=M-1
D=M
A=A-1
M=D+M
// CommandType.C_PUSH argument 1 
@1
D=A
@ARG
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// sub 
@SP
AM=M-1
D=M
A=A-1
M=M-D
// CommandType.C_PUSH this 6 
@6
D=A
@THIS
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH this 6 
@6
D=A
@THIS
A=D+M
D=M
@SP
A=M
M=D
@SP
M=M+1
// add 
@SP
AM=M-1
D=M
A=A-1
M=D+M
// sub 
@SP
AM=M-1
D=M
A=A-1
M=M-D
// CommandType.C_PUSH temp 6 
@11
D=M
@SP
A=M
M=D
@SP
M=M+1
// add 
@SP
AM=M-1
D=M
A=A-1
M=D+M
(END)
@END
0;JMP
