
import pytest
from dbreport.dbreport import Report

def test_init():
    with pytest.raises(ValueError):
        Report('invalid/path/that/is/not/a/json/file')
