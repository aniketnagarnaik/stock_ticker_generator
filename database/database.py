"""
Database connection and setup
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base

class DatabaseManager:
    """Manages database connection and operations"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _get_database_url(self):
        """Get database URL - SQLite for local development, PostgreSQL for production"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            # Use SQLite for local development
            sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'stocks.db')
            database_url = f"sqlite:///{sqlite_path}"
            print(f"Using local SQLite database: {sqlite_path}")
        return database_url
    
    def _setup_database(self):
        """Setup database connection and create tables"""
        database_url = self._get_database_url()
        
        # Create engine (SQLite or PostgreSQL)
        if database_url.startswith('sqlite'):
            self.engine = create_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                connect_args={"check_same_thread": False}  # SQLite specific
            )
            db_type = "SQLite"
        else:
            self.engine = create_engine(
                database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=300     # Recycle connections every 5 minutes
            )
            db_type = "PostgreSQL"
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )
        
        print(f"Database initialized: {db_type}")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self):
        """Close current session"""
        self.SessionLocal.remove()
    
    def get_all_stocks(self):
        """Get all stocks with their metrics"""
        from database.models import Stock
        from sqlalchemy.orm import joinedload
        session = self.get_session()
        try:
            stocks = session.query(Stock).options(
                joinedload(Stock.metrics)
            ).all()
            
            # Convert to dictionary format for compatibility with existing frontend
            result = []
            for stock in stocks:
                stock_dict = {
                    'symbol': stock.symbol,
                    'company_name': stock.company_name,
                    'market_cap': stock.market_cap,
                    'price': stock.current_price,
                    'sector': stock.sector,
                    'industry': stock.industry,
                    'eps': stock.eps,
                    'eps_growth': {
                        'quarter_over_quarter': stock.metrics[0].eps_growth_qoq if stock.metrics else None,
                        'year_over_year': stock.metrics[0].eps_growth_yoy if stock.metrics else None,
                        'latest_quarters': [v for k, v in sorted(stock.metrics[0].get_eps_history().get('quarterly', {}).items())][-4:] if stock.metrics else []
                    },
                    'eps_history': stock.metrics[0].get_eps_history() if stock.metrics else {},
                    'relative_strength': {
                        'rs_spy': stock.metrics[0].rs_spy if stock.metrics else None,
                        'rs_sector': stock.metrics[0].rs_sector if stock.metrics else None
                    },
                    'ema_data': stock.metrics[0].get_ema_data() if stock.metrics else {}
                }
                result.append(stock_dict)
            
            return result
            
        finally:
            session.close()
    
    def get_stock_count(self):
        """Get total number of stocks in database"""
        from database.models import Stock
        session = self.get_session()
        try:
            return session.query(Stock).count()
        finally:
            session.close()
    
    def get_last_refresh_time(self):
        """Get timestamp of last successful refresh"""
        from database.models import RefreshLog
        session = self.get_session()
        try:
            last_refresh = session.query(RefreshLog).filter(
                RefreshLog.status == 'completed'
            ).order_by(RefreshLog.completed_at.desc()).first()
            
            return last_refresh.completed_at if last_refresh else None
            
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()
