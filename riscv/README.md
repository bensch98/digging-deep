# RISC-V

## How to install RISC-V toolchain

Helpful repos:
- [riscv-collab/riscv-gnu-toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain)
- [riscv-software-src/riscv-tests](https://github.com/riscv-software-src/riscv-tests)

Toolchain can be installed like this:

```bash
git clone https://github.com/riscv/riscv-gnu-toolchain
cd riscv-gnu-toolchain
sudo apt-get install autoconf automake autotools-dev curl python3 python3-pip libmpc-dev libmpfr-dev libgmp-dev gawk build-essential bison flex texinfo gperf libtool patchutils bc zlib1g-dev libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev
sudo mkdir /opt/riscv
```

For an installation targeting Linux (cross-compiler, riscv64-unknown-linux-gcc) run:
```bash
./configure --prefix=/opt/riscv
sudo make -j
```

For `riscv64-unknown-elf`:

```bash
./configure --prefix=/opt/riscv
sudo make -j
```

Now tests can be compiled according to [riscv-software-src/riscv-tests](https://github.com/riscv-software-src/riscv-tests).
