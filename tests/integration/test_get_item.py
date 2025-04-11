import os

import pytest

from dynamo import TypedModelWithCompositeKey

table = os.environ.get('APP_DB')


@pytest.mark.skipif(table is None, reason='Requires database')
def test_get_item(dummy_model: TypedModelWithCompositeKey):
    dummy_model.save_as_full_item_if_not_exists(table=table)
    item = dummy_model.get_item(table=table)

    for key in ['SK', 'PK', 'StringAttribute']:
        assert key in item

    assert item['StringAttribute']['S'] == 'string'
    assert dummy_model.random_id in item['PK']['S']
    assert dummy_model.sk in item['SK']['S']
