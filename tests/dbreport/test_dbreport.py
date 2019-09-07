
import pytest
# from pytest_mock import mock
import mock
from pytest_mock import mocker
from dbreport.dbreport import Report

@mock.path('dbreport.dbreport.Report.parse')
def test_parse(mock_parse):


def test_init():

    with pytest.raises(TypeError):
        Report('invalid/path/that/is/not/a/json/file')



def test_something():
    pytest.fail()


def test_parse():
    pass
