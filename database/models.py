"""
SQLAlchemy models for stock ticker application
"""

from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Stock(Base):
    """Stock basic information"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(BigInteger)  # Store as big integer for large market caps
    current_price = Column(Float)
    eps = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to metrics
    metrics = relationship("StockMetrics", back_populates="stock")

class StockMetrics(Base):
    """Stock metrics and calculated values"""
    __tablename__ = 'stock_metrics'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    
    # Relationship to stock
    stock = relationship("Stock", back_populates="metrics")
    
    # EPS Growth
    eps_growth_qoq = Column(Float)  # Quarter over quarter
    eps_growth_yoy = Column(Float)  # Year over year
    latest_quarterly_eps = Column(Float)
    
    # Relative Strength
    rs_spy = Column(Float)
    rs_sector = Column(Float)
    
    # EMAs (stored as JSON for flexibility)
    ema_data = Column(Text)  # JSON string
    
    # EPS History (stored as JSON)
    eps_history = Column(Text)  # JSON string
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def get_ema_data(self):
        """Parse EMA data from JSON string"""
        if self.ema_data:
            try:
                return json.loads(self.ema_data)
            except:
                return {}
        return {}
    
    def set_ema_data(self, ema_dict):
        """Store EMA data as JSON string"""
        self.ema_data = json.dumps(ema_dict)
    
    def get_eps_history(self):
        """Parse EPS history from JSON string"""
        if self.eps_history:
            try:
                return json.loads(self.eps_history)
            except:
                return {}
        return {}
    
    def set_eps_history(self, eps_dict):
        """Store EPS history as JSON string"""
        self.eps_history = json.dumps(eps_dict)

class RefreshLog(Base):
    """Log of data refresh operations"""
    __tablename__ = 'refresh_logs'
    
    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(20))  # 'running', 'completed', 'failed'
    stocks_processed = Column(Integer, default=0)
    stocks_successful = Column(Integer, default=0)
    stocks_failed = Column(Integer, default=0)
    error_message = Column(Text)
    duration_seconds = Column(Float)
    
    def mark_completed(self, successful_count, failed_count, error_msg=None):
        """Mark refresh as completed"""
        self.completed_at = datetime.utcnow()
        self.status = 'completed' if not error_msg else 'failed'
        self.stocks_successful = successful_count
        self.stocks_failed = failed_count
        self.error_message = error_msg
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
