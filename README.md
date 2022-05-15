# How does code execution work?

## From C to Assembly

Begin with a hello world program in C:

*hello.c*
```C
int main(void) {
	prinf("hello world\n");
	return 0;
}
```

Compile this C file to Assembly:

```bash
gcc -S -fverbose-asm -O2 hello.c
```

**Files:**
- *hello.c*: C source file
- *hello.s*: gcc compiled assembly file


## From Assembly to hex and binary

Let's look at an example .S file that prints hello world.
This is a handwritten assembly file (.S -> capital S) as the compiled one by gcc has tons of stuff that is not necessary for illustration.

*hello.S*
```
; hello.s
extern printf     ; declare external C function
section .data
  msg     db  "hello, world",0
  fmtstr  db  "This is the str: %s",10,0  ; format string
section .bss
section .text
  global main
main:
  push  rbp
  mov   rbp,rsp
  mov   rdi, fmtstr     ; 1st argument for printf
  mov   rsi, msg        ; 2nd argument for printf
  mov   rax, 0
  call  printf          ; call the function
  mov   rsp,rbp
  pop   rbp
  mov   rax, 60         ; 60 = exit
  mov   rdi, 0          ; 0 = success and exit
  syscall               ; quit
```

Let's create a corresponding `Makefile` and make sure to use tabs as indentation:

*Makefile*
```Makefile
# Makefile for hello.S
hello: hello.o
	gcc -o hello hello.o -no-pie
hello.o: hello.S
	nasm -f elf64 -g -F dwarf hello.S -l hello.lst
```

Compile `hello.s` via `make`-command.
The output is as follows:

```txt
$ ls
hello  hello.c  hello.lst  hello.o  hello.s  hello.S  Makefile
```

**Files:**
- *hello*: executable file
- *hello.lst*: file with corresponding machine code to assembly code
- *hello.o*: binary output
- *hello.S*: handwritten assembly file
- *Makefile*: Makefile for compiling


The first column (not the line numbers) are the addresses of the commands.
The second column is the corresponding machine code of the assembly code on the right.

*hello.lst*
```lst
     1                                  ; hello.s
     2                                  extern  printf      ; declare the function as external
     3                                  section .data
     4 00000000 68656C6C6F2C20776F-       msg     db  "hello, world",0
     4 00000009 726C6400           
     5 0000000D 54686973206973206F-       fmtstr  db  "This is our string: %s",10,0 ; format string
     5 00000016 757220737472696E67-
     5 0000001F 3A2025730A00       
     6                                  section .bss
     7                                  section .text
     8                                    global main
     9                                  main:
    10 00000000 55                        push    rbp
    11 00000001 4889E5                    mov     rbp,rsp
    12 00000004 48BF-                     mov     rdi, fmtstr         ; 1st argument for printf
    12 00000006 [0D00000000000000] 
    13 0000000E 48BE-                     mov     rsi, msg            ; 2nd argument for printf
    13 00000010 [0000000000000000] 
    14 00000018 B800000000                mov     rax, 0
    15 0000001D E8(00000000)              call    printf              ; call the function
    16 00000022 4889EC                    mov     rsp,rbp
    17 00000025 5D                        pop     rbp
    18 00000026 B83C000000                mov     rax, 60             ; 60 = exit
    19 0000002B BF00000000                mov     rdi, 0              ; 0 = success and exit code
    20 00000030 0F05                      syscall                     ; quit
```


This next binary file is the program that is executed.
It can be viewed either in binary or hexadecimal.
This is just a snippet of the whole file. The displayed part is the actual program in hex, hence the same statements as the machine code above.

**Note:** Two digits in hex represent one byte. The bytes are however swapped for every block. This means it is a little-endian system:

*hello.o*
```txt
$ hexdump hello.o | less

...

00004c0 6568 6c6c 2c6f 7720 726f 646c 5400 6968
00004d0 2073 7369 6f20 7275 7320 7274 6e69 3a67
00004e0 2520 0a73 0000 0000 0000 0000 0000 0000
00004f0 4855 e589 bf48 0000 0000 0000 0000 be48
0000500 0000 0000 0000 0000 00b8 0000 e800 0000
0000510 0000 8948 5dec 3cb8 0000 bf00 0000 0000
0000520 050f 0000 0000 0000 0000 0000 0000 0000

...

```

In binary the commands are again in the correct order.
This is again just a part of the whole `hello.o`. 

*hello.o*
```txt
$ xxd -b hello.o | less

...

000004bc: 00000000 00000000 00000000 00000000 01101000 01100101  ....he
000004c2: 01101100 01101100 01101111 00101100 00100000 01110111  llo, w
000004c8: 01101111 01110010 01101100 01100100 00000000 01010100  orld.T
000004ce: 01101000 01101001 01110011 00100000 01101001 01110011  his is
000004d4: 00100000 01101111 01110101 01110010 00100000 01110011   our s
000004da: 01110100 01110010 01101001 01101110 01100111 00111010  tring:
000004e0: 00100000 00100101 01110011 00001010 00000000 00000000   %s...
000004e6: 00000000 00000000 00000000 00000000 00000000 00000000  ......
000004ec: 00000000 00000000 00000000 00000000 01010101 01001000  ....UH
000004f2: 10001001 11100101 01001000 10111111 00000000 00000000  ..H...
000004f8: 00000000 00000000 00000000 00000000 00000000 00000000  ......
000004fe: 01001000 10111110 00000000 00000000 00000000 00000000  H.....
00000504: 00000000 00000000 00000000 00000000 10111000 00000000  ......
0000050a: 00000000 00000000 00000000 11101000 00000000 00000000  ......
00000510: 00000000 00000000 01001000 10001001 11101100 01011101  ..H..]
00000516: 10111000 00111100 00000000 00000000 00000000 10111111  .<....
0000051c: 00000000 00000000 00000000 00000000 00001111 00000101  ......

...

```

You can check that the bytes are actually exactly the same (the bytes are swapped) with following command.

```bash
# first two bytes of program
$ printf '%x\n' "$((2#0110100001100101))"
6865
```

While this code above is the real program in hex and binary, it also appears in a similar form in the executable file.
In `hello` however the program is slightly adapted and not executed 1:1 as shown above.
