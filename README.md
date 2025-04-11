#  Dynamo Utils

Wrapper and a set of utilities to work with data models stored in and retrieved from AWS DynamoDB.

### Dependencies

The only dependency required is `boto3`, but since the library is primarily meant for AWS Lambda functions and those
have it pre-installed, the library does not have a `requirements.txt`.

### APIs

- `db()`

```python
from dynamo import db

params = {'Table': 'myTable', 'Key': 'myKey'}
db().get_item(**params).get('Item')
```

Returns a singleton database instance. It is recommended to cache the database client between lambda invocations.

- `TypedDynamoModel` and `TypedModelWithCompositeKey`

All objects stored in DynamoDB will benefit from extending these classes:

```python
from dynamo import TypedModelWithCompositeKey


class MyModel(TypedModelWithCompositeKey):
    pass
```

Inherits basic DynamoDB read/write functionality and helps format data objects for the purpose of saving them to the
database.

- `ValidatesPresence`

Empty field checker. Useful when one wants to avoid saving an object with empty or null fields to db.

```python
from dynamo import ValidatesPresence


class MyClass(ValidatesPresence):
    def __init__(self):
        self.my_field = 'value'
        self.my_non_null_field = None

    def must_be_present(self) -> set[str]:
        return {'my_non_null_field'}


my_instance = MyClass()
my_instance.validate_completeness()  # raises EmptyValueError
```

- `Ksuid`

Fork of Python's [ksuid](https://github.com/saresend/KSUID): K-sortable UUIDs. Heavily used for sorting keys in
DynamoDb.

## Unit Testing

Tested with pytest. Install dependencies with

```shell
pip install -r tests/requirements.txt
```

and

```shell
pytest tests/unit
```

from the root.

## Integration Testing

For integration testing, one will need a DynamoDB table with a composite primary key. Here's a CloudFormation script for
it:

```yaml
MyTable:
  Type: "AWS::DynamoDB::Table"
  Properties:
    AttributeDefinitions:
      - AttributeName: PK
        AttributeType: S
      - AttributeName: SK
        AttributeType: S
    BillingMode: PAY_PER_REQUEST
    KeySchema:
      - AttributeName: PK
        KeyType: HASH
      - AttributeName: SK
        KeyType: RANGE
    TableName: "MyTableName"
```

Also, to operate on that table one will need a IAM user/role with the following permissions (CloudFormation again):

```yaml
Effect: Allow
Action:
  - "dynamodb:GetItem"
  - "dynamodb:Query"
  - "dynamodb:BatchGetItem"
  - "dynamodb:PutItem"
  - "dynamodb:UpdateItem"
  - "dynamodb:BatchWriteItem"
``` 

on that table.

The user and the table need to be saved to the env variables like this:

```shell
APP_DB=MyTableName  # as per the Cloudformation script above
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=<MY_SECRET_KEY>
AWS_DEFAULT_REGION=<MY_AWS_REGION>
```

With all that set up, run

```shell
pytest tests/integration
```

from root.

Clean after yourself with `tests/destroy_test_table.sh`
