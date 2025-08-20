"""SQLAlchemy models for database tables."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, String, DECIMAL, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class RawTransaction(Base):
    """Raw transaction data as loaded from CSV."""
    
    __tablename__ = "raw_transactions"
    __table_args__ = (
        Index('idx_raw_company_id', 'company_id'),
        Index('idx_raw_created_at', 'created_at'),
        {'schema': 'raw_data'}
    )
    
    id = Column(String(64), primary_key=True)
    name = Column(String(130))
    company_id = Column(String(64))
    amount = Column(DECIMAL(16, 2))
    status = Column(String(50))
    created_at = Column(String(50))  # Raw string from CSV
    paid_at = Column(String(50))     # Raw string from CSV
    
    def __repr__(self) -> str:
        return f"<RawTransaction(id='{self.id}', company_id='{self.company_id}', amount={self.amount})>"


class Company(Base):
    """Normalized company information."""
    
    __tablename__ = "companies"
    __table_args__ = (
        Index('idx_company_name', 'company_name'),
        {'schema': 'normalized_data'}
    )
    
    company_id = Column(String(24), primary_key=True)
    company_name = Column(String(130), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    # Relationship to charges
    charges = relationship("Charge", back_populates="company")
    
    def __repr__(self) -> str:
        return f"<Company(company_id='{self.company_id}', name='{self.company_name}')>"


class Charge(Base):
    """Normalized charge/transaction information."""
    
    __tablename__ = "charges"
    __table_args__ = (
        Index('idx_charge_company_id', 'company_id'),
        Index('idx_charge_created_at', 'created_at'),
        Index('idx_charge_status', 'status'),
        Index('idx_charge_date_company', 'created_at', 'company_id'),
        {'schema': 'normalized_data'}
    )
    
    id = Column(String(24), primary_key=True)
    company_id = Column(String(24), ForeignKey('normalized_data.companies.company_id'), nullable=False)
    amount = Column(DECIMAL(16, 2), nullable=False)
    status = Column(String(30), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Relationship to company
    company = relationship("Company", back_populates="charges")
    
    def __repr__(self) -> str:
        return f"<Charge(id='{self.id}', company_id='{self.company_id}', amount={self.amount}, status='{self.status}')>"


# Note: DailyTransactionSummary is implemented as a database view, not a table
# The view is created separately in the DatabaseManager