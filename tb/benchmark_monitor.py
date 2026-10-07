# Validate benchmark markers, result writes, and cycle counts.

class BenchmarkMonitor:
    def __init__(self, expected, case_id):
        self.expected = {0x700 + 4 * i: int(value) & 0xFFFFFFFF for i, value in enumerate(expected)}
        self.case_id = case_id
        self.start_cycle = None
        self.end_cycle = None
        self.results = set()

    def accept_write(self, cycle, address, data, strobes):
        prefix = f"{self.case_id}: cycle {cycle}, address 0x{address:08X}"
        if address == 0x7F8:
            raise AssertionError(f"{prefix}: firmware error 0x{data:08X}")
        if address in (0x7F0, 0x7F4):
            assert strobes == 0xF and data == 1, f"{prefix}: invalid marker data/strobes"
            if address == 0x7F0:
                assert self.start_cycle is None, f"{prefix}: duplicate start marker"
                self.start_cycle = cycle
            else:
                assert self.start_cycle is not None, f"{prefix}: end before start"
                assert self.end_cycle is None, f"{prefix}: duplicate end marker"
                assert self.results == set(self.expected), f"{prefix}: missing result writes"
                assert cycle > self.start_cycle, f"{prefix}: invalid timing interval"
                self.end_cycle = cycle
        elif 0x700 <= address < 0x710:
            assert self.start_cycle is not None and self.end_cycle is None, f"{prefix}: result outside markers"
            assert address in self.expected, f"{prefix}: unaligned result"
            assert address not in self.results, f"{prefix}: duplicate result"
            assert strobes == 0xF, f"{prefix}: partial result write"
            assert data == self.expected[address], f"{prefix}: incorrect result 0x{data:08X}"
            self.results.add(address)

    @property
    def elapsed_cycles(self):
        assert self.start_cycle is not None and self.end_cycle is not None, f"{self.case_id}: incomplete benchmark"
        return self.end_cycle - self.start_cycle
