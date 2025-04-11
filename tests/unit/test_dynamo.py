import pytest
from contextlib import nullcontext as does_not_raise
from dynamo import DynamoModel


@pytest.mark.parametrize(
    "value, expectation",
    [
        ('Username', 'S'),
        (1, 'N'),
        (1.2, 'N'),
        (True, 'BOOL'),
        (None, 'NULL'),
        ([], 'L'),
        ([1, 2], 'L'),
        ({}, 'M'),
        ({1: 2}, 'M'),
        (b'', 'B'),
        (b'123', 'B'),
        ({1, 2}, 'NS'),
        ({1, 2.2}, 'NS'),
        ({1.2, 2}, 'NS'),
        ({1}, 'NS'),
        ({1.2}, 'NS'),
        ({'a', 'b'}, 'SS'),
        ({'a'}, 'SS'),
        ({b'a', b'b'}, 'BS'),
        ({b'a'}, 'BS'),
    ],
)
def test_dynamo_type(value, expectation):
    assert DynamoModel.dynamo_type(value) == expectation


class WrongDynamoType:
    pass


_error = pytest.raises(TypeError)


@pytest.mark.parametrize(
    "value, expectation",
    [
        ('Username', does_not_raise()),
        (WrongDynamoType(), _error),
        (WrongDynamoType, _error),
        ({'1'}, does_not_raise()),
        ({'1', 2}, _error),
        ({2, True}, does_not_raise()),
    ],
)
def test_negative_dynamo_type(value, expectation):
    with expectation:
        assert isinstance(DynamoModel.dynamo_type(value), str)
