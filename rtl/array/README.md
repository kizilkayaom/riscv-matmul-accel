# Controller Interface and Verification Pipeline

A request is accepted on a rising clock edge when `start=1` in IDLE or DONE and reset is inactive. Both matrices are captured at that edge, so later changes to the input ports do not affect the active operation. Requests while busy are ignored and are not queued.

Pulse `start` for one clock cycle. It is level-sensitive: holding it high through completion causes another operation on the next rising edge in DONE.

After completion, the `done` signal remains high, and the results stay stable until another accepted request is received, or the state is reset.

The reset is active-high and asynchronous. It aborts the current operation, clears saved operands and array results, and returns the controller to IDLE with `busy=0` and `done=0`.

The implemented schedule includes one CLEAR cycle followed by four computation steps (STEP0–STEP3), including the final drain step. `busy` is high throughout these states. The `done` signal becomes high five clock periods after the edge accepting `start`, once the final array update settles. The currently implemented tests enforce a 10-cycle completion timeout, so they do not explicitly assert exact five-cycle latency.

## Ports and packing

| Port | Direction | Width | Purpose |
|---|---|---|---|
| `clk` | Input | 1 | Rising-edge clock. |
| `reset` | Input | 1 | Active-high asynchronous reset. |
| `start` | Input | 1 | Request a multiplication. |
| `a_matrix`, `b_matrix` | Input | 32 each | Packed operand matrices. |
| `busy` | Output | 1 | High during CLEAR and STEP0–STEP3. |
| `done` | Output | 1 | High in DONE; indicates valid results. |
| `out` | Output | 128 | Four packed result elements. |

Each input element is a signed 8-bit Q1.7 integer. Each output element is a signed 32-bit integer with 14 fractional bits. Divide the signed integer value by 16,384 to obtain its real value. Interpret each packed element separately as a two's-complement signed integer.

| Matrix element | Input bits (`a_matrix`, `b_matrix`) | Output bits (`out`) |
|---|---|---|
| `[0,0]` | `[7:0]` | `[31:0]` |
| `[0,1]` | `[15:8]` | `[63:32]` |
| `[1,0]` | `[23:16]` | `[95:64]` |
| `[1,1]` | `[31:24]` | `[127:96]` |

The outputs contain partial sums during computation and should be read as completed results only when `done=1`.

## Verification

The three controller tests cover initial reset, operand capture despite changing external inputs, rejection of an extra start pulse while busy, completion and result hold, restart without external reset, reset interruption and recovery, and consecutive randomized operations.

Seeds `42` and `123` each passed all three tests, including 10,000 random controller operations per seed: 20,000 random multiplications and 80,000 output comparisons against the golden model in total. Random operations use one initial external reset and exercise automatic clearing between requests.

## Run the tests

From the repository root:

```sh
source .venv/bin/activate
cd tb
```

Run the controller suite with each seed:

```sh
PYTHONPATH=.. TEST_SEED=42 NUM_CASES=10000 make \
    TOPLEVEL=controller COCOTB_TEST_MODULES=test_controller \
    SIM_BUILD=sim_build_controller

PYTHONPATH=.. TEST_SEED=123 NUM_CASES=10000 make \
    TOPLEVEL=controller COCOTB_TEST_MODULES=test_controller \
    SIM_BUILD=sim_build_controller
```

`TEST_SEED` and `NUM_CASES` are environment variables used to configure the random test. Their defaults are `42` and `100`, respectively.
