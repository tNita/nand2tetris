## 各memory領域へのpush pop
- push
    - 各領域の特定のアドレスの値をDに入れた上でDのものをスタックマシンにpush
- pop
    - スタックマシンpopしてDに入れた上で各領域の特定のアドレスの値を更新
    - 更新するアドレスはR13二一時退避

## push
@SP, A=M, M=D, @SP, M=M+1

## pop
@SP, M=M-1, @SP, A=M, D=M

## 各領域のアドレスの値→Dまで
### localとか
#### push
```asm
// iの値をDに入れる
@{i}
D=A
// D = RAM[base+i]
@LCL
A=M
D=D+M
A=D
D=M
// Dをpush
@SP, A=M, M=D, @SP, M=M+1
```

#### pop

先に書き込み先のaddrをR13に退避
```asm
// R13 = base + i
@i, D=A, @LCL, A=M, D=D+M, @R13, M=D

// D = RAM[--SP]
@SP
AM=M-1
D=M

// M[base+i] = D
@R13, A=M, M=D
```

## arithmetic

### add
```
@SP
AM=M-1
D=M
A=A-1
M=D+M // *SP-1 = x + y
```

## eq
