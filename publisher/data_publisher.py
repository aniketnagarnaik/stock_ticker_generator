"""
Data publisher for storing stock data in database
"""

from typing import List, Dict, Tuple
from database.database import db_manager
from database.models import Stock, StockMetrics, RefreshLog
from publisher.yahoo_client import YahooFinanceClient

class DataPublisher:
    """Publishes stock data to database"""
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
    
    def publish_all_stocks(self) -> Tuple[bool, int, int]:
        """
        Fetch all stock data and publish to database
        Returns: (success, successful_count, failed_count)
        """
        # Create refresh log entry
        session = db_manager.get_session()
        try:
            refresh_log = RefreshLog(status='running')
            session.add(refresh_log)
            session.commit()
            log_id = refresh_log.id
            
            print(f"🔄 Starting data refresh (Log ID: {log_id})...")
            
            # Fetch fresh data from Yahoo Finance (use test data for initial deployment)
            fresh_data = self.yahoo_client.get_all_stocks(use_test_data=True)
            
            if not fresh_data:
                refresh_log.mark_completed(0, 0, "Failed to fetch data from Yahoo Finance")
                session.commit()
                return False, 0, 0
            
            # Publish data to database
            successful_count = 0
            failed_count = 0
            
            for stock_data in fresh_data:
                try:
                    self._publish_single_stock(session, stock_data)
                    successful_count += 1
                except Exception as e:
                    print(f"❌ Failed to publish {stock_data.get('symbol', 'unknown')}: {e}")
                    failed_count += 1
            
            # Mark refresh as completed
            refresh_log.mark_completed(successful_count, failed_count)
            session.commit()
            
            print(f"✅ Data refresh completed: {successful_count} successful, {failed_count} failed")
            return True, successful_count, failed_count
            
        except Exception as e:
            print(f"❌ Data refresh failed: {e}")
            if 'refresh_log' in locals():
                refresh_log.mark_completed(0, 0, str(e))
                session.commit()
            return False, 0, 0
        finally:
            session.close()
    
    def _publish_single_stock(self, session, stock_data: Dict):
        """Publish a single stock's data to database"""
        symbol = stock_data['symbol']
        
        # Check if stock exists
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            # Create new stock
            stock = Stock(
                symbol=symbol,
                company_name=stock_data['company_name'],
                sector=stock_data.get('sector'),
                industry=stock_data.get('industry'),
                market_cap=stock_data.get('market_cap'),
                current_price=stock_data.get('price'),
                eps=stock_data.get('eps')
            )
            session.add(stock)
        else:
            # Update existing stock
            stock.company_name = stock_data['company_name']
            stock.sector = stock_data.get('sector')
            stock.industry = stock_data.get('industry')
            stock.market_cap = stock_data.get('market_cap')
            stock.current_price = stock_data.get('price')
            stock.eps = stock_data.get('eps')
            stock.last_updated = stock_data.get('last_updated')
        
        # Commit stock changes
        session.commit()
        
        # Handle metrics
        self._publish_stock_metrics(session, stock, stock_data)
    
    def _publish_stock_metrics(self, session, stock: Stock, stock_data: Dict):
        """Publish stock metrics to database"""
        symbol = stock.symbol
        
        # Check if metrics exist
        metrics = session.query(StockMetrics).filter(StockMetrics.symbol == symbol).first()
        
        if not metrics:
            # Create new metrics
            metrics = StockMetrics(symbol=symbol, stock_id=stock.id)
            session.add(metrics)
        
        # Update EPS growth data
        eps_growth = stock_data.get('eps_growth', {})
        metrics.eps_growth_qoq = eps_growth.get('quarter_over_quarter')
        metrics.eps_growth_yoy = eps_growth.get('year_over_year')
        
        # Update relative strength data
        rs_data = stock_data.get('relative_strength', {})
        metrics.rs_spy = rs_data.get('rs_spy')
        metrics.rs_sector = rs_data.get('rs_sector')
        
        # Update EMA data
        ema_data = stock_data.get('ema_data', {})
        if ema_data:
            metrics.set_ema_data(ema_data)
        
        # Update EPS history
        eps_history = stock_data.get('eps_history', {})
        if eps_history:
            metrics.set_eps_history(eps_history)
        
        metrics.last_updated = stock_data.get('last_updated')
        
        session.commit()
    
    def get_refresh_status(self) -> Dict:
        """Get status of last refresh operation"""
        session = db_manager.get_session()
        try:
            last_refresh = session.query(RefreshLog).order_by(
                RefreshLog.started_at.desc()
            ).first()
            
            if not last_refresh:
                return {
                    'status': 'never_run',
                    'last_run': None,
                    'stocks_processed': 0,
                    'duration_seconds': 0
                }
            
            return {
                'status': last_refresh.status,
                'last_run': last_refresh.started_at,
                'completed_at': last_refresh.completed_at,
                'stocks_processed': last_refresh.stocks_successful + last_refresh.stocks_failed,
                'stocks_successful': last_refresh.stocks_successful,
                'stocks_failed': last_refresh.stocks_failed,
                'duration_seconds': last_refresh.duration_seconds,
                'error_message': last_refresh.error_message
            }
            
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        session = db_manager.get_session()
        try:
            total_stocks = session.query(Stock).count()
            total_metrics = session.query(StockMetrics).count()
            last_stock_update = session.query(Stock.last_updated).order_by(
                Stock.last_updated.desc()
            ).first()
            
            return {
                'total_stocks': total_stocks,
                'total_metrics': total_metrics,
                'last_stock_update': last_stock_update[0] if last_stock_update else None
            }
            
        finally:
            session.close()
