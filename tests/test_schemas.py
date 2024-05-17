import pytest

from tests.dataset import candles_math


def test_candle_add():
    c1, c2 = candles_math[0][0][1], candles_math[0][1][1]
    c = c1 + c2
    assert round(c.open, 2) == 524.41
    assert round(c.high, 2) == 532.51
    assert round(c.low, 2) == 518.8
    assert round(c.close, 2) == 524.03
    assert c.volume == 92761000
    assert c.dt == c1.dt


def test_candle_multiply():
    c1, c2 = candles_math[0][0][1], candles_math[0][1][1]
    c = c1 * c2
    assert round(c.open, 2) == 68484.96
    assert round(c.high, 2) == 70585.3
    assert round(c.low, 2) == 67010.8
    assert round(c.close, 2) == 68373.47
    assert c.volume == 92761000
    assert c.dt == c1.dt


def test_candle_sub():
    c1, c2 = candles_math[0][0][1], candles_math[0][1][1]
    c = c1 - c2
    assert round(c.open, 2) == 32.65
    assert round(c.high, 2) == 35.01
    assert round(c.low, 2) == 33.32
    assert round(c.close, 2) == 33.37
    assert c.volume == 92761000
    assert c.dt == c1.dt


def test_candle_division():
    c1, c2 = candles_math[0][0][1], candles_math[0][1][1]
    c = c1 / c2
    assert round(c.open, 2) == 1.13
    assert round(c.high, 2) == 1.14
    assert round(c.low, 2) == 1.14
    assert round(c.close, 2) == 1.14
    assert c.volume == 92761000
    assert c.dt == c1.dt


@pytest.mark.parametrize("candles_1,candles_2,results", candles_math)
def test_candle_add(candles_1, candles_2, results):
    for method, expected in results:
        func = getattr(candles_1, method.__name__)
        candles = func(candles_2)

        assert len(candles) == len(expected)
        for c_v, c_e in zip(candles, expected):
            assert round(c_v.close, 2) == round(c_e.close, 2)
            assert round(c_v.open, 2) == round(c_e.open, 2)
            assert round(c_v.high, 2) == round(c_e.high, 2)
            assert round(c_v.low, 2) == round(c_e.low, 2)
            assert c_v.volume == c_e.volume
            assert c_v.dt == c_e.dt
