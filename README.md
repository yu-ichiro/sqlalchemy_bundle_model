# sqlalchemy_bundle_model
An extension to SQLAlchemy to treat aggregated columns and clauses as Models

# installation

```
$ pip install sqlalchemy-bundle-model
```

# usage

```
>>> from sqlalchemy import Column, BigInteger, Text, ForeignKey
>>> from sqlalchemy.orm import declarative_base, relationship, sessionmaker
>>> from sqlalchemy.engine import create_engine
>>> from sqlalchemy_bundle_model import BundleModel, col
>>> DeclarativeBase = declarative_base()
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
...     def join(_query):
...         return _query.join(User.group)
...
>>> engine = create_engine("sqlite://")
>>> DeclarativeBase.metadata.create_all(bind=engine)
>>> session_cls = sessionmaker(bind=engine)
>>> session = session_cls()
>>> user = User(id=1, name="John Doe")
>>> group = Group(id=1, name="A")
>>> user.group = group
>>> session.add(user)
>>> session.commit()
>>> query = session.query(GroupUser)
>>> query = GroupUser.join(query)
>>> result = query.first()
>>> result.group_name == "A"
```
