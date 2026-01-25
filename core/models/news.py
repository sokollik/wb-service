from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.sql import func

from core.models.base import Base
from core.models.enums import NewsCategory, NewsStatus


class NewsOrm(Base):
    __tablename__ = "news"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    short_description = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    author_id = Column(
        BigInteger, ForeignKey("employee.eid"), nullable=False, index=True
    )

    is_pinned = Column(Boolean, default=False, index=True)
    mandatory_ack = Column(Boolean, default=False)

    status = Column(Enum(NewsStatus), nullable=False, default=NewsStatus.DRAFT)

    published_at = Column(DateTime, server_default=func.now(), index=True)
    expires_at = Column(DateTime, nullable=True)
    views_count = Column(BigInteger, default=0)


class NewsToCategoryOrm(Base):
    __tablename__ = "news_to_category"
    news_id = Column(
        BigInteger, ForeignKey("news.id", ondelete="CASCADE"), primary_key=True
    )
    category_id = Column(
        BigInteger,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )


class CategoryOrm(Base):
    __tablename__ = "categories"
    id = Column(BigInteger, primary_key=True)
    name = Column(Enum(NewsCategory), nullable=False, index=True)


class UserFollowedCategoryOrm(Base):
    __tablename__ = "user_followed_categories"
    user_eid = Column(BigInteger, ForeignKey("employee.eid"), primary_key=True)
    category_id = Column(
        BigInteger,
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    )


class TagOrm(Base):
    __tablename__ = "tags"
    id = Column(BigInteger, primary_key=True)
    name = Column(String, unique=True, index=True)


class NewsTagOrm(Base):
    __tablename__ = "news_tags"
    news_id = Column(
        BigInteger, ForeignKey("news.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(
        BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class NewsToFileOrm(Base):
    __tablename__ = "news_to_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    news_id = Column(
        BigInteger,
        ForeignKey("news.id", ondelete="CASCADE"),
        primary_key=True,
    )
    file_id = Column(
        BigInteger,
        ForeignKey("file.id", ondelete="CASCADE"),
        primary_key=True,
    )


class CommentOrm(Base):
    __tablename__ = "comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(
        BigInteger,
        ForeignKey("news.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(BigInteger, ForeignKey("employee.eid"), nullable=False)
    parent_id = Column(
        BigInteger,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    is_edited = Column(Boolean, default=False)


class CommentToFileOrm(Base):
    __tablename__ = "comments_to_files"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    comment_id = Column(
        BigInteger,
        ForeignKey("comments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    file_id = Column(
        BigInteger,
        ForeignKey("file.id", ondelete="CASCADE"),
        primary_key=True,
    )


class NewsLikeOrm(Base):
    __tablename__ = "news_likes"
    user_id = Column(BigInteger, ForeignKey("employee.eid"), primary_key=True)
    news_id = Column(
        BigInteger, ForeignKey("news.id", ondelete="CASCADE"), primary_key=True
    )


class CommentLikeOrm(Base):
    __tablename__ = "comments_likes"
    user_id = Column(BigInteger, ForeignKey("employee.eid"), primary_key=True)
    comment_id = Column(
        BigInteger,
        ForeignKey("comments.id", ondelete="CASCADE"),
        primary_key=True,
    )


class MentionOrm(Base):
    __tablename__ = "mentions"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    comment_id = Column(
        BigInteger,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False,
    )
    mentioned_user_id = Column(
        BigInteger, ForeignKey("employee.eid"), nullable=False
    )
