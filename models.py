from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """Sample Users table"""
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name       = Column(String(100), nullable=False)
    email      = Column(String(150), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<User id={self.id} name={self.name}>"


class Product(Base):
    """Sample Products table"""
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name        = Column(String(200), nullable=False)
    price       = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Product id={self.id} name={self.name} price={self.price}>"


class ChatHistory(Base):
    """
    AI Chat history store karne ke liye table.
    conversation_id se ek session ki poori history track hoti hai.
    """
    __tablename__ = "chat_history"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(String(100), index=True, nullable=False)
    user_message    = Column(Text, nullable=False)
    ai_response     = Column(Text, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ChatHistory id={self.id} conv={self.conversation_id}>"
