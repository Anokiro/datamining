import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime


Base = declarative_base()

tag_post = Table(
    "tag_post",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id")),
)


class Post(Base):
    __tablename__ = "post"
    url = Column(String, nullable=False, unique=True)
    image_url = Column(String, nullable=False)
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    publication_date = Column(DateTime)
    author_id = Column(Integer, ForeignKey("author.id"))
    author = relationship("Author")
    tags = relationship("Tag", secondary=tag_post)
    comments = relationship("Comment")


class Author(Base):
    __tablename__ = "author"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    posts = relationship("Post")


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    posts = relationship("Post", secondary=tag_post)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    text_of_comment = Column(String)
    created_at = Column(DateTime, nullable=False)
    author_id = Column(Integer, ForeignKey("author.id"))
    author = relationship("Author")
    post_id = Column(Integer, ForeignKey("post.id"))

    def __init__(self, **kwargs):
        self.id = kwargs["id"]
        self.parent_id = kwargs["parent_id"]
        self.text_of_comment = kwargs["body"]
        self.created_at = datetime.datetime.fromisoformat(kwargs["created_at"])
        self.author = kwargs["author"]