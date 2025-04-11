import os

import pytest

from dynamo import TypedModelWithCompositeKey, db

table = os.environ.get('APP_DB')


@pytest.mark.skipif(table is None, reason='Requires database')
def test_save(dummy_model: TypedModelWithCompositeKey):
    dummy_model.save_as_full_item_if_not_exists(table=table)
    item = db().get_item(
        TableName=table,
        Key={
            'PK': {'S': dummy_model.pk},
            'SK': {'S': dummy_model.sk},
        }
    )['Item']

    assert dummy_model.random_id in item['PK']['S']
    assert dummy_model.sk in item['SK']['S']
    assert item['StringAttribute']['S'] == 'string'
