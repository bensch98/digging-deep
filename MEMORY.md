# Memory

The memory is structured as following:

![memory layout](./img/memory_layout.png)

- The stack grows downwards into lower addresses (into .bss direction)
- The heap grows into higher addresses and is dynamically allocated during runtime. It is whatever is free between the stack and .bss
