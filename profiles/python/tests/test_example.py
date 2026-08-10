from coregraft_example import hello


def test_hello() -> None:
    assert "coregraft-example" in hello()
