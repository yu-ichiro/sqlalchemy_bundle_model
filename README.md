# sqlalchemy_bundle_model
An extension to SQLAlchemy to treat aggregated columns and clauses as Models

# usage

```
>>> from sqlalchemy_bundle_model import BundleModel
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

```