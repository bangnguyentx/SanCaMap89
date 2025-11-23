from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, Float, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class ForcedActionStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"

class PayoutStatus(enum.Enum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    balance = Column(BigInteger, default=0)  # Stored in smallest unit (e.g., cents)
    client_seed = Column(String(64))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    round_id = Column(String(255), nullable=False)
    bet_type = Column(String(50), nullable=False)  # 'small', 'big', 'even', 'odd', 'specific'
    amount = Column(BigInteger, nullable=False)
    digits = Column(String(6))  # For specific bets
    created_at = Column(DateTime, default=func.now())

class ProvableSeed(Base):
    __tablename__ = "provable_seeds"

    id = Column(Integer, primary_key=True)
    round_id = Column(String(255), unique=True, nullable=False)
    commitment = Column(String(64), nullable=False)  # SHA256 of server_seed
    encrypted_seed = Column(Text, nullable=False)  # Encrypted server_seed
    revealed_seed_hash = Column(String(64))  # SHA256 of revealed seed for verification
    revealed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    period_tag = Column(String(50))  # e.g., "daily_2024-01-01"
    drand_round = Column(String(50))
    client_seed_allowed = Column(Boolean, default=True)

class ForcedAction(Base):
    __tablename__ = "forced_actions"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    requested_by = Column(BigInteger, nullable=False)  # Telegram user ID
    forced_value = Column(String(20))  # 'small', 'big', 'even', 'odd'
    requested_at = Column(DateTime, default=func.now())
    confirmations = Column(JSON)  # List of {"admin_id": 123, "confirmed_at": "..."}
    required_confirmations = Column(Integer, default=2)
    status = Column(String(20), default=ForcedActionStatus.PENDING.value)
    applied_round = Column(String(255))
    audit_ref = Column(String(100))

class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True)
    tx_ref = Column(String(36), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(BigInteger, nullable=False)
    round_id = Column(String(255))
    status = Column(String(20), default=PayoutStatus.PENDING.value)
    attempts = Column(Integer, default=0)
    last_error = Column(Text)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor_id = Column(BigInteger, nullable=False)  # Telegram user ID or 'system'
    action = Column(String(100), nullable=False)
    target = Column(String(100))  # user_id, round_id, etc.
    meta = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class Pot(Base):
    __tablename__ = "pot"

    id = Column(Integer, primary_key=True)
    balance = Column(BigInteger, default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
