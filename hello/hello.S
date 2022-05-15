; hello.S
extern  printf      ; declare the function as external
section .data
  msg     db  "hello, world",0
  fmtstr  db  "This is our string: %s",10,0 ; format string
section .bss
section .text
  global main
main:
  push    rbp
  mov     rbp,rsp
  mov     rdi, fmtstr         ; 1st argument for printf
  mov     rsi, msg            ; 2nd argument for printf
  mov     rax, 0
  call    printf              ; call the function
  mov     rsp,rbp
  pop     rbp
  mov     rax, 60             ; 60 = exit
  mov     rdi, 0              ; 0 = success and exit code
  syscall                     ; quit
