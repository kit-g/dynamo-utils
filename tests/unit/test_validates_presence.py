from typing import Set

import pytest
from contextlib import nullcontext as does_not_raise
from dynamo import ValidatesPresence, EmptyValueError

_error = pytest.raises(EmptyValueError)


class NullableFieldsType(ValidatesPresence):

    @property
    def must_be_present(self) -> Set[str]:
        return {'a', 'b', 'c'}

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.mark.parametrize(
    "value, expectation",
    [
        (NullableFieldsType(), _error),
        (NullableFieldsType(a='1', b='2'), _error),
        (NullableFieldsType(a='1', c='2'), _error),
        (NullableFieldsType(b='1', c='2'), _error),
        (NullableFieldsType(a='', b='2', c='3'), _error),
        (NullableFieldsType(a='1', b='', c='3'), _error),
        (NullableFieldsType(a='1', b='2', c=''), _error),
        (NullableFieldsType(a='1', b=None, c='3'), _error),
        (NullableFieldsType(a='1', b='2', c=[]), _error),
        (NullableFieldsType(a='1', b=[], c='3'), _error),
        (NullableFieldsType(a=[], b='2', c='3'), _error),
        (NullableFieldsType(a='1', b='2', c={}), _error),
        (NullableFieldsType(a='1', b={}, c='3'), _error),
        (NullableFieldsType(a={}, b='2', c='3'), _error),
        (NullableFieldsType(a=0, b='2', c='3'), _error),
        (NullableFieldsType(a='1', b=0, c='3'), _error),
        (NullableFieldsType(a='1', b='2', c=0), _error),
        (NullableFieldsType(a='1', b='None', c=None), _error),
        (NullableFieldsType(a=None, b='2', c='3'), _error),
        (NullableFieldsType(a=False, b=None, c=1, d='4'), _error),
        (NullableFieldsType(a=False, b=False, c=1, d=None), does_not_raise()),
        (NullableFieldsType(a='1', b='2', c='3'), does_not_raise()),
        (NullableFieldsType(a='1', b='2', c='3', d='4'), does_not_raise()),
        (NullableFieldsType(a=1, b='2', c='3', d='4'), does_not_raise()),
        (NullableFieldsType(a=1, b=[1], c='3', d='4'), does_not_raise()),
        (NullableFieldsType(a=1, b=[1], c={3}, d='4'), does_not_raise()),
        (NullableFieldsType(a=False, b=True, c=1, d='4'), does_not_raise()),
    ],
)
def test_validates_presence(value, expectation):
    with expectation:
        assert value.validate_completeness() is None
