from benchmark.experiment import extract_number,equal_numeric,ARCHS
from benchmark.providers import generate
import pytest

def test_answer_parser():
    assert extract_number('ANSWER: 1,234')=='1234'
    assert extract_number('ANSWER: -4.5')=='-4.5'
    assert extract_number('no answer') is None

def test_numeric_comparison():
    assert equal_numeric('2.0','2')
    assert not equal_numeric(None,'2')

def test_four_architectures():
    assert len(ARCHS)==4

def test_unknown_provider():
    with pytest.raises(ValueError):generate('unknown','any','system','prompt')
