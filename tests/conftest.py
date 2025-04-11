from typing import Dict, Any
from uuid import uuid4

import pytest
from dynamo import TypedModelWithCompositeKey


class MyTestModel(TypedModelWithCompositeKey):

    def __init__(self, item_id):
        self.id = item_id
        self.random_id = f'{uuid4()}'

    def _to_item(self) -> Dict[str, Any]:
        return {
            'PK': self.pk,
            'SK': self.sk,
            'StringAttribute': 'string',
        }

    @classmethod
    def from_item(cls, record: dict):
        pass

    @property
    def type(self) -> str:
        return 'dynamo-test-model'

    @property
    def pk(self) -> str:
        return f'{self.type}#{self.id}#{self.random_id}'

    @property
    def sk(self) -> str:
        return f'{self.type}#SK'


@pytest.fixture
def dummy_model() -> MyTestModel:
    return MyTestModel('123')
