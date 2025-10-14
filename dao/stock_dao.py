"""
DAO for stocks table operations
"""

from typing import List, Dict, Optional
from database.models import Stock
from .base_dao import BaseDAO


class StockDAO(BaseDAO):
    """DAO for stocks table operations"""
    
    def __init__(self):
        super().__init__(Stock)
    
    def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol"""
        try:
            return self.session.query(Stock).filter(
                Stock.symbol == symbol
            ).first()
        finally:
            self.session.close()
    
    def get_all_stocks_dict(self) -> List[Dict]:
        """Get all stocks as dictionaries for UI consumption"""
        try:
            stocks = self.session.query(Stock).all()
            result = []
            
            for stock in stocks:
                stock_dict = {
                    'symbol': stock.symbol,
                    'company_name': stock.company_name,
                    'market_cap': stock.market_cap,
                    'price': stock.current_price,
                    'sector': stock.sector,
                    'industry': stock.industry,
                    'last_updated': stock.last_updated,
                    'created_at': stock.created_at
                }
                result.append(stock_dict)
            
            return result
        finally:
            self.session.close()
    
    def upsert_stock(self, symbol: str, company_name: str, sector: str = None, 
                    industry: str = None, market_cap: int = None, 
                    current_price: float = None) -> Stock:
        """Insert or update stock record"""
        session = self.get_session()
        try:
            # Query within this session, don't call get_by_symbol (which closes session)
            existing_stock = session.query(Stock).filter(Stock.symbol == symbol).first()
            
            if existing_stock:
                # Update existing stock
                if company_name:
                    existing_stock.company_name = company_name
                if sector:
                    existing_stock.sector = sector
                if industry:
                    existing_stock.industry = industry
                if market_cap is not None:
                    existing_stock.market_cap = market_cap
                if current_price is not None:
                    existing_stock.current_price = current_price
                
                session.commit()
                return existing_stock
            else:
                # Create new stock
                new_stock = Stock(
                    symbol=symbol,
                    company_name=company_name,
                    sector=sector,
                    industry=industry,
                    market_cap=market_cap,
                    current_price=current_price
                )
                session.add(new_stock)
                session.commit()
                return new_stock
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_stocks_by_sector(self, sector: str) -> List[Stock]:
        """Get all stocks in a specific sector"""
        try:
            return self.session.query(Stock).filter(
                Stock.sector == sector
            ).all()
        finally:
            self.session.close()
    
    def get_stock_count(self) -> int:
        """Get total number of stocks"""
        try:
            return self.session.query(Stock).count()
        finally:
            self.session.close()
