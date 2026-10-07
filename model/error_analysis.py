# Measure Q1.7 quantization error against floating-point multiplication.

import numpy as np

from model.golden_model import model

OPERAND_SCALE = 128
OUTPUT_SCALE = OPERAND_SCALE ** 2
MIN_OPERAND = -128
MAX_OPERAND = 127


def quantize_q1_7(values):
    values = np.asarray(values, dtype=np.float64) * OPERAND_SCALE
    values = np.rint(values)
    values = np.clip(values, MIN_OPERAND, MAX_OPERAND)
    return values.astype(np.int8)


def count_clipped_inputs(values):
    rounded = np.rint(np.asarray(values, dtype=np.float64) * OPERAND_SCALE)
    return np.count_nonzero((rounded < MIN_OPERAND) | (rounded > MAX_OPERAND))


def compare_matmul(A, B):
    reference = A @ B
    fixed, _ = model(quantize_q1_7(A), quantize_q1_7(B))
    actual = fixed / OUTPUT_SCALE
    error = np.abs(actual - reference)
    return reference, actual, error


def print_example():
    A = np.array([[0.1, -0.3], [0.7, 0.2]])
    B = np.array([[0.4, 0.6], [-0.2, 0.9]])
    reference, actual, error = compare_matmul(A, B)

    print("Reference:\n", reference)
    print("Quantized result:\n", actual)
    print("Absolute error:\n", error)
    print("Mean absolute error:", error.mean())
    print("Maximum absolute error:", error.max())


def run_experiment(amplitude=1.0, num_cases=1000, seed=42):
    rng = np.random.default_rng(seed)
    errors = []
    references = []
    clipped_count = 0
    input_count = 0

    for _ in range(num_cases):
        A = rng.uniform(-amplitude, amplitude, size=(2, 2))
        B = rng.uniform(-amplitude, amplitude, size=(2, 2))

        for values in (A, B):
            clipped_count += count_clipped_inputs(values)
            input_count += values.size

        reference, _, error = compare_matmul(A, B)
        references.append(reference)
        errors.append(error)

    errors = np.stack(errors)
    references = np.stack(references)

    rmse = np.sqrt(np.mean(errors**2))
    reference_rms = np.sqrt(np.mean(references**2))
    normalized_rmse = rmse / reference_rms if reference_rms > 0 else np.nan

    print(
        f"Random experiment: {num_cases} pairs, {errors.size} outputs, "
        f"seed={seed}, amplitude={amplitude}"
    )
    print("Mean absolute error:", errors.mean())
    print("Maximum absolute error:", errors.max())
    print("Clipped input elements:", clipped_count, "/", input_count)
    print("Input clipping percentage:", 100 * clipped_count / input_count)
    print("Normalized RMSE:", normalized_rmse)


if __name__ == "__main__":
    print_example()
    print()
    for amplitude in (0.25, 0.5, 1.0, 1.5):
        print()
        run_experiment(amplitude=amplitude)
