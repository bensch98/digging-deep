# Makefile for hello.S
hello: hello.o
	gcc -o hello hello.o -no-pie
hello.o: hello.S
	nasm -f elf64 -g -F dwarf hello.S -l hello.lst
