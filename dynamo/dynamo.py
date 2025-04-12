from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Iterable

from .client import db
from .ksuid import Ksuid

_types = {
    str: 'S',
    set: 'SS',
    dict: 'M',
    bool: 'BOOL',
    type(None): 'NULL',
    bytes: 'B',
    int: 'N',
    float: 'N',
    list: 'L',
}


def set_type(value: set) -> str:
    if all(map(lambda v: isinstance(v, int) or isinstance(v, float), value)):
        return 'NS'
    if all(map(lambda v: isinstance(v, str), value)):
        return 'SS'
    if all(map(lambda v: isinstance(v, bytes), value)):
        return 'BS'
    raise TypeError


class DynamoModel(ABC):

    @staticmethod
    def dynamo_type(value: Any) -> str:
        """
        :param value: arbitrary value
        :raises TypeError if type is not supported by DynamoDb
        :return: DynamoDb type of `value`
        """
        value_type = type(value)
        cls = _types.get(value_type)

        if cls:

            if cls == 'SS':
                return set_type(value)
            else:
                return cls

        raise TypeError

    @abstractmethod
    def _to_item(self) -> Dict[str, Any]:
        """
        DynamoDB representation of the object.

        Should be formatted as:

        .. code-block:: python

        {
            'myStrAttr': 'myValue',
            'myIntAttr': 5,
        }

        ::

        Then calling `to_item`
        returns

        .. code-block:: python

        {
            'myStrAttr': {'S': 'myValue'},
            'myIntAttr': {'S': 5},
        }

        which is DynamoDB write-ready.

        :return: map of attribute names to their values to be saved to the db
        """
        raise NotImplementedError

    def to_item(self, exclude_nulls=False) -> Dict[str, Dict[str, Any]]:
        """
        Public converter of the object to a DynamoDB data structure.

        Looks like

        .. code-block:: python

        {
            'myStrAttr': {'S': 'myValue'},
            'myIntAttr': {'N': 5},
        }

        :param exclude_nulls: if the final representation should exclude item attributes that are None
        :return: DynamoDB data structure

        """

        def condition(value):
            return value is not None if exclude_nulls else True

        return {
            key: {
                self.dynamo_type(value): str(value)
                if (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
                else value
            }
            for key, value
            in self._to_item().items() if condition(value)
        }

    def to_non_null_item(self) -> Dict[str, Any]:
        """
        Same as `to_item` but with null attributes removed.
        :return: DynamoDb data structure
        """
        return self.to_item(exclude_nulls=True)

    @classmethod
    @abstractmethod
    def from_item(cls, record: dict):
        """
        Constructor from DynamoDB item data structure,

        :param record: DynamoDB item
        :return: instance of self
        """
        raise NotImplementedError


class Typed(ABC):
    """
    Interface that forces the class to have a `type` getter.
    With single-table design in DynamoDB all data models should have a `type` attribute.
    """

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotImplementedError

    @property
    def item_type(self) -> dict:
        return {'type': self.type}


class WithPartitionKey(ABC):
    """
    Interface that forces the class to have a `PK` getter.
    """

    @property
    @abstractmethod
    def pk(self) -> str:
        raise NotImplementedError

    @property
    def item_pk(self) -> dict:
        return {'PK': self.pk}


class WithSortingKey(ABC):
    """
    Interface that forces the class to have a `SK` getter.
    """

    @property
    @abstractmethod
    def sk(self) -> str:
        raise NotImplementedError

    @property
    def item_sk(self) -> dict:
        return {'SK': self.sk}


class TypedDynamoModel(DynamoModel, Typed, ABC):
    """
    Base class for models stored in DynamoDB
    """
    pass


class WithSortableId(ABC):
    @property
    @abstractmethod
    def id(self) -> Ksuid:
        raise NotImplementedError

    @property
    def created(self) -> datetime:
        return self.id.datetime


class Expires(ABC):
    """
    Interface that exposes an DynamoDB attribute `scheduledForDeletionAt`
    which is used conventionally to signal DynamoDB when this item should be removed from the table.

    TTL is how many days this item gets to live.
    """

    @property
    @abstractmethod
    def ttl(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def created(self) -> datetime:
        raise NotImplementedError

    @property
    def _scheduled_for_deletion_at(self) -> datetime:
        return self.created + timedelta(days=self.ttl)

    @property
    def scheduled_for_deletion_at(self) -> dict[str, int]:
        return {'scheduledForDeletionAt': int(self._scheduled_for_deletion_at.timestamp())}


class TypedModelWithCompositeKey(TypedDynamoModel, WithPartitionKey, WithSortingKey, ABC):
    """
    Base class for models with composite primary keys.
    For all the specific DynamoDB APIs consult boto3 documentation.

    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
    """

    @property
    def item_primary_key(self) -> dict[str, str]:
        return self.item_pk | self.item_sk

    @property
    def primary_key(self) -> Dict[str, Dict]:
        return {k: {DynamoModel.dynamo_type(v): v} for k, v in self.item_primary_key.items()}

    def all_attributes(self) -> Dict[str, Dict]:
        return {key: value for key, value in self.to_item().items() if key not in ['PK', 'SK']}

    def _save_attributes(self, *, table: str, attrs: Iterable[str]) -> dict:
        to_update = {key: value for key, value in self.all_attributes().items() if key in attrs}
        return db().update_item(
            TableName=table,
            Key=self.primary_key,
            UpdateExpression=f'SET {", ".join(f"#{key} = :{key}" for key in to_update)}',
            ExpressionAttributeNames={
                f'#{key}': key for key in to_update
            },
            ExpressionAttributeValues={
                f':{key}': value for key, value in to_update.items()
            },
            ReturnValues="ALL_NEW"
        )

    @staticmethod
    def _save_event(*, table: str, item: dict, condition: str = None) -> dict:
        args = {
            'TableName': table,
            'Item': item,
        }
        if condition:
            args['ConditionExpression'] = condition
        return args

    def save_full_item_event(self, *, table: str, condition: str = None) -> dict:
        return self._save_event(table=table, item=self.to_item(), condition=condition)

    def save_non_null_item_event(self, *, table: str, condition: str = None) -> dict:
        return self._save_event(table=table, item=self.to_non_null_item(), condition=condition)

    @staticmethod
    def _save(*, table: str, item: dict, condition: str = None) -> dict:
        args = TypedModelWithCompositeKey._save_event(table=table, item=item, condition=condition)
        return db().put_item(**args)

    def save_as_full_item(self, *, table: str, condition: str = None) -> dict:
        return self._save(table=table, item=self.to_item(), condition=condition)

    def save_as_non_null_item(self, *, table: str, condition: str = None) -> dict:
        return self._save(table=table, item=self.to_non_null_item(), condition=condition)

    def save_as_full_item_if_not_exists(self, *, table: str) -> dict:
        return self._save(table=table, item=self.to_item(), condition='attribute_not_exists(PK)')

    def save_as_non_null_item_if_not_exists(self, *, table: str) -> dict:
        return self._save(table=table, item=self.to_non_null_item(), condition='attribute_not_exists(PK)')

    def save_attributes(self, *, table: str, attrs: Iterable[str]) -> dict:
        return self._save_attributes(table=table, attrs=attrs)

    def save_single_attribute(self, *, table: str, attr_name: str) -> dict:
        return self._save_attributes(table=table, attrs=[attr_name])

    def save_all_attributes(self, *, table: str) -> dict:
        attrs = self.all_attributes().keys()
        return self._save_attributes(table=table, attrs=attrs)

    def get_item(self, *, table: str, attrs: Iterable[str] = None):
        params = dict(
            TableName=table,
            Key=self.primary_key,
        )

        if attrs:
            params['ProjectionExpression'] = ', '.join(f'#{each}' for each in attrs)
            params['ExpressionAttributeNames'] = {f'#{each}': each for each in attrs}

        return db().get_item(**params).get('Item')


class TypedModelWithSortableKey(TypedModelWithCompositeKey, WithSortableId, ABC):
    """
    Same as TypedModelWithCompositeKey, but the sorting key will have to actually be
    lexicographically sortable. This interface will make the host override its id method
    that returns a KSUID tht will be used as the sorting key.
    """
    pass


class EmptyValueError(ValueError):
    """
    Raised by ValidatesPresence instances.
    """
    pass


class ValidatesPresence(ABC):
    """
    Interface that checks if some mandatory fields of self are not None or not empty.
    :raises: a EmptyValueError if any are
    """

    @property
    @abstractmethod
    def must_be_present(self) -> set[str]:
        """
        :return: List of attribute names that must not be null
        """
        raise NotImplementedError

    def _validate_against_null(self):
        for each in self.must_be_present:
            try:
                if getattr(self, each) is None:
                    raise EmptyValueError(f'{each} must not be null')
            except AttributeError:
                raise EmptyValueError(f'{self.__class__.__name__} must have {each} attribute')

    def _validate_against_empty(self):
        for each in self.must_be_present:
            try:
                att = getattr(self, each)
                # how to handle 0 and 0.0?
                if not isinstance(att, bool) and not bool(att):
                    raise EmptyValueError(f'{each} must not be empty')
            except AttributeError:
                raise EmptyValueError(f'{self.__class__.__name__} must have {each} attribute')

    def validate_completeness(self):
        self._validate_against_null()
        self._validate_against_empty()
