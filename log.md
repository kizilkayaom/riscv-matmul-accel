# Jun 30, 2026

Wrote the python script for golden reference model.

## Decisions made
- **Operand format:** Q1.7 (8-bit signed, 7 fractional bits). Range: [-1.0, +127/128].
- **Product format:** Q2.14 (16-bit). Fractional bits add (7+7=14), and the total amount of bits double (8+8=16). Full 16 bits required because of two's complement asymmetry: (-128) x (-128) = +16384, which exceeds the 15-bit signed maximum of +16383.
- **Accumulator:** 32-bit signed. Overflow occurs at $N \approx 2^{17}$ products. Since this is over the 32-bit accumulator, overflow is practically eliminated.
- **Rounding:** Round-to-nearest over truncation. Since truncation produces systemic bias, round-to-nearest was selected to distribute error so they more or less cancel out one another.
- **Saturation:** Clamp to $[-2^{31}, 2^{31}-1]$ without any wrapping. Wrapping is not preferred to eliminate sign flip errors in ML inference process.

## Verification - Test Cases and Results

**Case 1**:

$$A = \begin{bmatrix} 64 \end{bmatrix}, \quad B = \begin{bmatrix} 64 \end{bmatrix}$$

$$C_{fixed} = \begin{bmatrix} 4096 \end{bmatrix}, \quad C_{float} = \begin{bmatrix} 0.25 \end{bmatrix}$$

**Case 2**:

$$A = \begin{bmatrix} -128 \end{bmatrix}, \quad B = \begin{bmatrix} -128 \end{bmatrix}$$

$$C_{fixed} = \begin{bmatrix} 16384 \end{bmatrix}, \quad C_{float} = \begin{bmatrix} 1.0 \end{bmatrix}$$

**Case 3**:

$$A = \begin{bmatrix} 64 & -128 \\ 127 & 32 \end{bmatrix}, \quad B = \begin{bmatrix} 64 & -64 \\ 127 & 32 \end{bmatrix}$$

$$C_{fixed} = \begin{bmatrix} -12160 & -8192 \\ 12192 & -7104 \end{bmatrix}, \quad C_{float} = \begin{bmatrix} -0.7422 & -0.5 \\ 0.7441 & -0.4336 \end{bmatrix}$$

# Sep 20, 2026

- Fixed PE saturation by adding a 33-bit intermediary variable to detect overflows before storing the sum in a 32-bit output register.
- Expanded the PE tests for
  - Positive and negative saturation cases
  - Overflow from positive maximum and negative minimum values
- Fixed the golden model scripts by using native Python integers in intermediate arithmetic operations and clamped the intermediary sum after each addition to prevent possible overflow before clipping.
- Improved numerical behavior by having outputs retain 14 fractional bits without any rounding.
- Connected the array test script to the golden reference models, and confirmed that
  - Expected outputs are computed automatically
  - Hardware inputs come from the same matrices
- Created a reusable matrix-test helper function that resets, drives, and checks each matrix multiplication.
- Added matrix multiplication test cases for
  - Mixed signs, positive operands, zero matrix multiplied by a nonzero matrix, minimum valued operands, mixed extreme values, and matrices with cancelling operations.
- Added a configurable randomized testing that allows the control of seed and case count. Additionally, the testing script, if happens, identifies inputs, case type, and output mismatch in case of failure.
- Tested pausing mechanism where the accumulators hold during two disabled clock edges after Cycle 0, and computation resumes correctly.
- Tested 10,000 random matrices passed for each of seeds 42 and 123, both before and after adding the pause, totaling 20,000 random cases per execution mode, with directed checks.

To run the array regression, execute these commands from `tb/` with the virtual environment active:

```sh
PYTHONPATH=.. TEST_SEED=42 NUM_CASES=10000 make
PYTHONPATH=.. TEST_SEED=123 NUM_CASES=10000 make
```
