from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ReadStatus(Base):
    __tablename__ = 'read_status'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    read_status = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class GeneralChatMessage(Base):
    __tablename__ = 'general_chat_message'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender = Column(String(64), nullable=False)

class TacticsChatMessage(Base):
    __tablename__ = 'tactics_chat_message'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender = Column(String(64), nullable=False)
    read_status = Column(Boolean, default=False)

class ArenaChatMessage(Base):
    __tablename__ = 'arena_chat_message'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender = Column(String(64), nullable=False)
    name = Column(String(64), nullable=False)
    arena_id = Column(Integer, nullable=False)
    read_status = Column(Boolean, default=False)
