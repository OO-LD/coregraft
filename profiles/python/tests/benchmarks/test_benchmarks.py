"""Performance benchmarks; run with `make bench`, never with the unit tests."""

from coregraft_example import hello


def test_hello_benchmark(benchmark) -> None:
    result = benchmark(hello)
    assert result
