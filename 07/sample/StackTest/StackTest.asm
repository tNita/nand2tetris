// CommandType.C_PUSH constant 17 
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 17 
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_0
D;JEQ
@SP
A=M-1
M=0
@COMP_END_0
0;JMP
(COMP_TRUE_0)
@SP
A=M-1
M=-1
(COMP_END_0)
// CommandType.C_PUSH constant 17 
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 16 
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_1
D;JEQ
@SP
A=M-1
M=0
@COMP_END_1
0;JMP
(COMP_TRUE_1)
@SP
A=M-1
M=-1
(COMP_END_1)
// CommandType.C_PUSH constant 16 
@16
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 17 
@17
D=A
@SP
A=M
M=D
@SP
M=M+1
// eq 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_2
D;JEQ
@SP
A=M-1
M=0
@COMP_END_2
0;JMP
(COMP_TRUE_2)
@SP
A=M-1
M=-1
(COMP_END_2)
// CommandType.C_PUSH constant 892 
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 891 
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_3
D;JLT
@SP
A=M-1
M=0
@COMP_END_3
0;JMP
(COMP_TRUE_3)
@SP
A=M-1
M=-1
(COMP_END_3)
// CommandType.C_PUSH constant 891 
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 892 
@892
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_4
D;JLT
@SP
A=M-1
M=0
@COMP_END_4
0;JMP
(COMP_TRUE_4)
@SP
A=M-1
M=-1
(COMP_END_4)
// CommandType.C_PUSH constant 891 
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 891 
@891
D=A
@SP
A=M
M=D
@SP
M=M+1
// lt 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_5
D;JLT
@SP
A=M-1
M=0
@COMP_END_5
0;JMP
(COMP_TRUE_5)
@SP
A=M-1
M=-1
(COMP_END_5)
// CommandType.C_PUSH constant 32767 
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 32766 
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_6
D;JGT
@SP
A=M-1
M=0
@COMP_END_6
0;JMP
(COMP_TRUE_6)
@SP
A=M-1
M=-1
(COMP_END_6)
// CommandType.C_PUSH constant 32766 
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 32767 
@32767
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_7
D;JGT
@SP
A=M-1
M=0
@COMP_END_7
0;JMP
(COMP_TRUE_7)
@SP
A=M-1
M=-1
(COMP_END_7)
// CommandType.C_PUSH constant 32766 
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 32766 
@32766
D=A
@SP
A=M
M=D
@SP
M=M+1
// gt 
@SP
AM=M-1
D=M
A=A-1
D=M-D
@COMP_TRUE_8
D;JGT
@SP
A=M-1
M=0
@COMP_END_8
0;JMP
(COMP_TRUE_8)
@SP
A=M-1
M=-1
(COMP_END_8)
// CommandType.C_PUSH constant 57 
@57
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 31 
@31
D=A
@SP
A=M
M=D
@SP
M=M+1
// CommandType.C_PUSH constant 53 
@53
D=A
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
// CommandType.C_PUSH constant 112 
@112
D=A
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
// neg 
@SP
A=M-1
M=-M
// and 
@SP
AM=M-1
D=M
A=A-1
M=D&M
// CommandType.C_PUSH constant 82 
@82
D=A
@SP
A=M
M=D
@SP
M=M+1
// or 
@SP
AM=M-1
D=M
A=A-1
M=D|M
// not 
@SP
A=M-1
M=!M
(END)
@END
0;JMP
