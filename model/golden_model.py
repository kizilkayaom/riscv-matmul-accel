""" 
Golden reference model for a fixed-point matrix-multiply accelerator

Specs:
- Operands: 8-bit signed integers represented in the Q1.7 notation (range: [-1.0, +127/128])
- Products: 16-bit signed integer in Q2.14 notation
- Accumulator: 32-bit signed (overflow bound (N): ~2^17 products)
- Rounding: Round to nearest (add 1 if MSB of discarded bits is set)
- Saturation protocol: Clamp the values to the represented range of [-2^31, 2^31-1], and do not wrap
- Error characterization: Float path provision

"""
import numpy as np
import numpy.typing as npt

def model(in1: npt.NDArray[np.int8], in2: npt.NDArray[np.int8]) -> tuple[npt.NDArray[np.int32], npt.NDArray[np.float64]]:
    if (np.size(in1, 1) != np.size(in2, 0)):
        raise Exception("Matrix dimension mismatch: Model aborted.") 

    C = np.zeros((np.size(in1, 0), np.size(in2, 1)), dtype="int32")

    for i in range(len(in1)):
        for j in range(in2.shape[1]):
            y = np.int32(0)
            for k in range(in1.shape[1]):
                y += np.int16(in1[i][k]) * np.int16(in2[k][j])
                y = np.clip(y, -(2**31), 2**31 - 1)
            C[i][j] = np.int32(y)
    
    float_path = np.matmul(np.float64(in1) / 128, np.float64(in2) / 128)
    return (C, float_path)

# Case 1: 0.5 × 0.5
a3 = np.array([[64, -128],
               [127, 32]], dtype=np.int8)
b3 = np.array([[64, -64],
               [127, 32]], dtype=np.int8)
fixed, floating = model(a3, b3)
print("Case 3 - fixed:", fixed, "float:", floating)