Write A
Write B
Write CONTROL = 1
Poll STATUS until done = 1
Read the four results


| Offset | Register | Access | Meaning |
|---|---|---|---|
| `0x00` | CONTROL | Write | Writing bit 0 as `1` with `wstrb[0]=1` requests a start |
| `0x04` | STATUS | Read | Bit 0: busy; bit 1: done |
| `0x08` | A | Read/write | Packed matrix A |
| `0x0C` | B | Read/write | Packed matrix B |
| `0x10` | C00 | Read | Signed 32-bit result |
| `0x14` | C01 | Read | Signed 32-bit result |
| `0x18` | C10 | Read | Signed 32-bit result |
| `0x1C` | C11 | Read | Signed 32-bit result |

## System address mapping

`accelerator_top` connects `bus_adapter` to `register_wrapper` and maps the accelerator into a 256-byte region:

- **Base address:** `0x40000000`.
- **Reserved range:** `0x40000000`–`0x400000FF`, inclusive.
- **Register offset:** The lowest 8 bits of the top-level 32-bit address.

For example, a write to `0x40000008` selects operand register A at offset `0x08`. The adapter forwards valid requests to the wrapper only when the full address falls within this region. Unused offsets within the region retain the wrapper's behavior: reads return zero and writes are ignored. Outside the region, top-level `ready` and `rdata` are zero, and requests cannot modify the wrapper or start an operation.

The wrapper accepts an 8-bit local register offset. `accelerator_top` exposes `valid`, `write`, `wstrb`, `addr`, `wdata`, `ready`, and `rdata`, along with clock and reset.

### SoC integration

`soc_top` connects PicoRV32 to RAM and the accelerator through `memory_system`. The accelerator connects to the CPU's native memory interface through `picorv32_accelerator`.

| Byte address range | Device |
|---|---|
| `0x00000000`–`0x00000FFF` | 4 KiB RAM for instructions and data |
| `0x40000000`–`0x400000FF` | Accelerator register region |

The register offsets above are relative to `0x40000000`. Requests outside both regions receive no acknowledgement (`mem_ready=0`), so the CPU waits for completion.

## Register behavior

- **A and B:** Reset to zero. Writes update only the bytes enabled by `wstrb`; disabled bytes retain their values. Reads return the stored value. Writes while busy prepare operands for a later operation without changing the controller's captured operands for the active operation.
- **CONTROL:** Writing bit 0 as `1` with `wstrb[0]=1` when the accelerator is available requests one operation. If either `wdata[0]` or `wstrb[0]` is zero, no operation starts. Start requests while busy are ignored and are not queued. Reads return zero. Reserved write bits are ignored.
- **STATUS:** Bit 0 reports busy and bit 1 reports done. All other bits read zero. Writes are ignored.
- **C00, C01, C10, and C11:** Reads return the corresponding controller output element. Software must wait for done before using these values as completed results. Writes are ignored.
- **Done:** Remains high until the next accepted start or reset. A start may be accepted from either IDLE or DONE.
- **Unused offsets:** Reads return zero; writes are ignored.

## Local bus handshake

- A transfer is accepted on a rising clock edge when `valid && ready` is high. `write=1` selects a write; `write=0` selects a read. The requester must provide the address, direction, write data, and strobes before that edge.
- At the wrapper, `ready` is low while reset is asserted and high otherwise. At the top level, `ready` additionally requires a valid request with an address in the accelerator region. No transfers are accepted during reset.
- Reads are combinational: `rdata` reflects the register selected by `addr`, independently of `valid` and `write`. The requester samples read data at the accepting edge.
- `wstrb[0]` enables bits `[7:0]`, `wstrb[1]` enables `[15:8]`, `wstrb[2]` enables `[23:16]`, and `wstrb[3]` enables `[31:24]` of an operand register. `wstrb=0xF` replaces all four bytes; `wstrb=0` changes nothing. Strobes do not affect reads.
- Each rising edge with `valid && ready` accepts a transfer. The requester must deassert `valid` or present the next transfer after acceptance.

## Start and status timing

An accepted CONTROL write with both `wdata[0]` and `wstrb[0]` set starts the controller on that same rising edge if it is not busy. The controller captures the stored operands on that edge. Once the edge's state updates settle, STATUS reports `busy=1` and `done=0`, clearing any previous completion indication.

CONTROL start writes accepted by the bus while the controller is busy are ignored and are not queued. When the operation completes, STATUS reports `busy=0` and `done=1`; done remains set until another accepted start or reset.
