# Golden model and numerical error analysis

## Purpose

The golden model specifies the accelerator's integer multiplication, accumulation, and saturation behavior. RTL outputs are expected to match this model bit-for-bit for the same encoded inputs.

The numerical experiment measures the effect of converting original floating-point inputs into Q1.7. It compares the scaled model result against matrix multiplication of the original floats. Differences here describe numerical approximation error; they do not imply a mismatch between the RTL and its arithmetic specification.

## Files

| File | Purpose |
|---|---|
| [golden_model.py](golden_model.py) | Fixed-point matrix multiplication with saturation after each addition. |
| [test_golden_model.py](test_golden_model.py) | Seven tests covering pinned results, saturation, and recovery. |
| [error_analysis.py](error_analysis.py) | Input quantization and numerical comparisons against original floating-point matrices. |

## Arithmetic and quantization

Each operand is a signed 8-bit integer in `[-128, 127]` representing its integer value divided by 128. The Q1.7 real range is therefore `[-1, 127/128]`, with a step of `1/128`. For example, integer `64` represents `0.5`; positive `1.0` cannot be represented exactly.

The experiment quantizes floats by multiplying by 128, rounding to nearest even with `np.rint`, clamping to `[-128, 127]`, and only then converting to `int8`. This input conversion leaves the original floating-point matrices unchanged.

Products have 14 fractional bits. The model computes intermediate sums using Python integers and clamps after every addition to the signed 32-bit range `[-2147483648, 2147483647]`. It stores the final result as `int32`. Saturation does not lock the accumulator at a limit, as an opposite-sign product can move it back into range.

Outputs retain 14 fractional bits and are divided by 16,384 for comparison in real units. No output rounding or requantization is performed. The model's separate floating-point return value starts from already-quantized inputs, so this experiment instead uses the original `A @ B` as its reference.

## Experiment setup

| Setting | Value |
|---|---|
| Matrix dimensions | 2×2 for both inputs |
| Matrix pairs per amplitude | 1,000 |
| Input distribution | Uniform in `[-amplitude, amplitude)` |
| Amplitudes | 0.25, 0.5, 1.0, 1.5 |
| Random seed | 42, restarted for each amplitude |
| Output elements per amplitude | 4,000 |
| Input elements per amplitude | 8,000 |
| Reference | `A @ B` using the original floating-point inputs |
| Compared result | Golden-model integer output divided by 16,384 |

## Metrics

All output-error metrics aggregate the 4,000 output elements at each amplitude:

- **Mean absolute error:** average absolute difference across all output elements.
- **Maximum absolute error:** largest observed absolute difference.
- **Normalized RMSE:** RMS error divided by the RMS magnitude of the reference outputs, aggregated across the entire experiment.
- **Input clipping percentage:** percentage of rounded, scaled input elements outside `[-128, 127]` before clamping.

For reference outputs `R` and absolute errors `E`, normalized RMSE is `sqrt(mean(E**2)) / sqrt(mean(R**2))`. It measures error relative to the reference signal's RMS magnitude, rather than averaging per-element relative errors. If the reference RMS is zero, the script reports `NaN`.

The script prints normalized RMSE as a ratio; the table below expresses it as a percentage. Clipping counts input elements from both matrices, giving a denominator of 8,000 per amplitude.

## Results

Results reproduced on September 27, 2026. Absolute errors are rounded to six decimal places and percentages to three decimal places.

| Amplitude | Mean absolute error | Maximum absolute error | Normalized RMSE (%) | Inputs clipped (%) |
|---|---|---|---|---|
| 0.25 | 0.000523 | 0.002507 | 2.271 | 0.000 |
| 0.5 | 0.001014 | 0.004941 | 1.100 | 0.000 |
| 1.0 | 0.002080 | 0.010036 | 0.563 | 0.275 |
| 1.5 | 0.205460 | 1.674488 | 31.245 | 33.450 |

Clipped input counts were respectively 0, 0, 22, and 2,676 out of 8,000. All seven standalone golden-model tests also passed.

## Interpretation and limitations

Amplitude 0.25 has the smallest absolute error, but also produces smaller reference outputs. The quantization step stays fixed at `1/128`, so smaller signals use fewer available operand levels. Normalizing by reference RMS reveals that the relative error decreases as amplitude increases from 0.25 to 1.0, despite the increase in absolute error.

Amplitude 1.0 has the lowest normalized RMSE among these four settings: approximately 0.563%, with 0.275% of inputs requiring clipping. At amplitude 1.5, 33.45% of inputs require clipping, and normalized RMSE rises to approximately 31.245%.

These results do not establish a universal optimal scale. They cover one seed, uniformly distributed inputs, 2×2 matrices, and four amplitudes. Restarting the generator with the same seed uses corresponding samples scaled to each amplitude. Other distributions and application requirements can change the preferred scale. Maximum errors are observed sample maxima, and not necessarily the theoretical bounds.

Input clipping is separate from accumulator saturation. These 2×2 products contain only two terms per output and cannot saturate the 32-bit accumulator. The standalone model tests exercise accumulator saturation with long dot products.

These numerical measurements use the software model, and they are not measurements of RTL mismatches or hardware performance.

## Reproduce

Run from the repository root with the project's virtual environment active.

Run the model tests:

```sh
python -m unittest discover -s model -p 'test_*.py'
```

Run the numerical experiment:

```sh
python -m model.error_analysis
```

The experiment settings are currently specified in `error_analysis.py`; the script does not accept any command-line options.
