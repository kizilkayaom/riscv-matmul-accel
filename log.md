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