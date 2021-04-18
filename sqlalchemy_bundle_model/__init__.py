"""
An extension to SQLAlchemy to treat aggregated columns and clauses as Models

>>> class User(DeclarativeBase):
...     __tablename__ = "users"
...     id = Column(BigInteger, primary_key=True)
...     name = Column(Text, nullable=False)
...     group_id = Column(ForeignKey("groups.id"), nullable=False)
...
...     group = relationship("Group")
...
>>> class Group(DeclarativeBase):
...     __tablename__ = "groups"
...     id = Column(BigInteger, primary_key=True)
...     name = Column(Text, nullable=False)
...
>>> class GroupUser(BundleModel):
...     id = col(int, User.id)
...     name = col(str, User.name)
...     group_name = col(str, Group.name)
...
...     @staticmethod
...     def join(_query: Query):
...         return _query.join(User.group)
...
>>> session = session_cls()
>>> query = session.query(GroupUser)
>>> query = GroupUser.join(query)
>>> result = query.first()
>>> result.group_name is not None
"""

__copyright__ = "Copyright (C) 2021 Yuichiro Smith"
__version__ = "0.1.0"
__license__ = "Apache License 2.0"
__author__ = "Yuichiro Smith <contact@yu-smith.com>"
__url__ = "https://github.com/yu-ichiro/sqlalchemy_bundle_model"
__status__ = "beta"
__date__ = "2021/04/18"

from collections import OrderedDict
from typing import Type, Union, Any, TypeVar, NamedTuple, Dict

from sqlalchemy.orm import Bundle
from sqlalchemy.sql.elements import Label, _textual_label_reference
from sqlalchemy.sql.operators import Operators

T = TypeVar('T')


class Alias(Label):
    def __init__(self, element, name=None, type_=None):
        super().__init__(name, element, type_)

    @property
    def ref(self):
        val = _textual_label_reference(self.name)
        return val

    def value_at(self, row):
        return getattr(row, self.name)


class BundleMeta(Bundle, type):
    single_entity = True

    def __init__(cls, name, bases, namespace):
        cls.__attrs: Dict[str, Alias] = {}
        _namespace = OrderedDict()
        for base in bases:
            _namespace.update(base.__dict__)
        _namespace.update(namespace)
        namespace = _namespace
        for attr_key, attr_value in namespace.items():
            if isinstance(attr_value, Operators) and hasattr(attr_value, '_label'):
                cls.__attrs[attr_key] = namespace[attr_key] = Alias(attr_value, attr_key)
            if isinstance(attr_value, Alias):
                cls.__attrs[attr_key] = namespace[attr_key] = attr_value
        super().__init__(name, *cls.__attrs.values())
        namespace.update(cls.__dict__)
        namespace.update(cls.__attrs)
        for key, value in namespace.items():
            try:
                setattr(cls, key, value)
            except:  # noqa
                pass
            if hasattr(value, '__set_name__'):
                value.__set_name__(cls, key)  # noqa
        setattr(cls, '__name__', name)
        setattr(cls, 'name', name)

    @property
    def aliases(cls):
        return cls.__attrs

    @property
    def _select_iterable(self):
        return self,


class BundleModel(metaclass=BundleMeta):
    """
    A model that can aggregate columns and clauses from different tables and treat it like a orm model
    """
    auto_process_row = True

    @classmethod
    def create_row_processor(cls, query, procs, labels):
        """Produce the "row processing" function for this :class:`.Bundle`.

        May be overridden by subclasses.

        .. seealso::

            :ref:`bundles` - includes an example of subclassing.

        """
        super_proc = Bundle.create_row_processor(cls, query, procs, labels)  # noqa
        result_cls = BundleResult(cls)

        def proc(row):
            result = result_cls(*super_proc(row))
            if not cls.auto_process_row:
                return result
            return cls.process_result(result)

        return proc

    @classmethod
    def process_result(cls, result):
        return result

    @classmethod
    def generate(cls: Type[T], **kwargs) -> Type[T]:
        return BundleMeta(cls.__name__, (cls,), kwargs)  # noqa


def bundle(class_: Type[T]) -> Type[T]:
    """
    a utility function to copy fields from another model

    >>> class User(Base):
    ...     __tablename__ = "users"
    ...     id = Column(BigInteger, primary_key=True)
    ...     name = Column(Text, nullable=False)
    ...     group_id = Column(ForeignKey("groups.id"), nullable=False)
    ...
    ...     group = relationship("Group")
    ...
    >>> class A(bundle(User)):
    ...     name = col(str, Group.name)
    >>> A.name is not None and A.id is not None
    True

    :param class_: model
    :return:
    """
    namespace = OrderedDict()
    for attr in dir(class_):
        if not attr.startswith('_') and attr != 'metadata':
            attr_object = getattr(class_, attr)
            namespace[attr] = attr_object
    return BundleMeta(class_.__name__, (), namespace)  # noqa


class BundleResult(type(NamedTuple), type):
    def __new__(mcs, bundle_cls: BundleMeta):
        annotations = {}
        for name, alias in bundle_cls.aliases.items():
            try:
                annotations[name] = alias.type.python_type
            except NotImplementedError:
                annotations[name] = Any
        return super().__new__(mcs, bundle_cls.__name__, (), {
            '__annotations__': annotations,
            '__table__': bundle_cls,
        })


def col(_type: Type[T], column: Operators) -> Union[T, Alias]:
    return column  # type: Any


# utility type (it's not being used because pycharm doesn't support it)
Col = Union[T, Alias]
