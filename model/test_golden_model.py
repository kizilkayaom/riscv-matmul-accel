import unittest
import numpy as np
from model.golden_model import model


class TestGoldenModel(unittest.TestCase):
    def test_half_times_half(self):
        A = np.array([[64]], dtype=np.int8)
        B = np.array([[64]], dtype=np.int8)
        fixed, _ = model(A, B)
        expected = np.array([[4096]], dtype=np.int32) # 64 x 64 = 4096
        np.testing.assert_array_equal(fixed, expected)

    def test_negative_times_negative(self):
        A = np.array([[-128]], dtype=np.int8)
        B = np.array([[-128]], dtype=np.int8)
        fixed, _ = model(A, B)
        expected = np.array([[16384]], dtype=np.int32) # -128 x -128 = 16384
        np.testing.assert_array_equal(fixed, expected)

    def test_mixed_sign(self):
        A = np.array([[64, -128], [127, 32]], dtype=np.int8)
        B = np.array([[64, -64], [127, 32]], dtype=np.int8)
        fixed, _ = model(A, B)
        expected = np.array(
            [[-12160, -8192], [12192, -7104]],
            dtype=np.int32,
        )
        np.testing.assert_array_equal(fixed, expected)

    def test_saturation_positive_overflow(self):
        A = np.full((1, 131072), -128, dtype=np.int8)
        B = np.full((131072, 1), -128, dtype=np.int8)
        fixed, _ = model(A, B)
        expected = np.array([[2147483647]], dtype=np.int32) # -128 x -128 x 131072 = 2147483648 clamped to 2147483647
        np.testing.assert_array_equal(fixed, expected)

    def test_saturation_negative_underflow(self):
        A = np.full((1, 140000), -128, dtype=np.int8)
        B = np.full((140000, 1), 127, dtype=np.int8)
        fixed, _ = model(A, B)
        expected = np.array([[-2147483648]], dtype=np.int32)
        np.testing.assert_array_equal(fixed, expected)

    def test_recovery_after_saturation(self):
        A = np.full((1, 131073), -128, dtype=np.int8)
        B = np.full((131073, 1), -128, dtype=np.int8)
        A[0, -1] = -3
        B[-1, 0] = 5
        fixed, _ = model(A, B)
        expected = np.array([[2147483632]], dtype=np.int32)
        np.testing.assert_array_equal(fixed, expected)
    
    def test_recovery_after_negative_saturation(self):
        A = np.full((1, 140001), -128, dtype=np.int8)
        B = np.full((140001, 1), 127, dtype=np.int8)
        A[0, -1] = 3
        B[-1, 0] = 5
        fixed, _ = model(A, B)
        expected = np.array([[-2147483633]], dtype=np.int32)
        np.testing.assert_array_equal(fixed, expected)