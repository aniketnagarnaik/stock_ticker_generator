"""
DAO for stock_metrics table operations
"""

from typing import List, Dict, Optional
from database.models import StockMetrics
from .base_dao import BaseDAO


class StockMetricsDAO(BaseDAO):
    """DAO for stock_metrics table operations"""
    
    def __init__(self):
        super().__init__(StockMetrics)
    
    def get_by_symbol(self, symbol: str) -> Optional[StockMetrics]:
        """Get stock metrics by symbol"""
        try:
            return self.session.query(StockMetrics).filter(
                StockMetrics.symbol == symbol
            ).first()
        finally:
            self.session.close()
    
    def upsert_metrics(self, symbol: str, stock_id: int = None, 
                      eps_growth_qoq: float = None, eps_growth_yoy: float = None,
                      latest_quarterly_eps: float = None, rs_spy: float = None,
                      rs_sector: float = None, ema_data: Dict = None,
                      eps_history: Dict = None) -> StockMetrics:
        """Insert or update stock metrics record"""
        session = self.get_session()
        try:
            # Query within this session, don't call get_by_symbol (which closes session)
            existing_metrics = session.query(StockMetrics).filter(StockMetrics.symbol == symbol).first()
            
            if existing_metrics:
                # Update existing metrics
                if eps_growth_qoq is not None:
                    existing_metrics.eps_growth_qoq = eps_growth_qoq
                if eps_growth_yoy is not None:
                    existing_metrics.eps_growth_yoy = eps_growth_yoy
                if latest_quarterly_eps is not None:
                    existing_metrics.latest_quarterly_eps = latest_quarterly_eps
                if rs_spy is not None:
                    existing_metrics.rs_spy = rs_spy
                if rs_sector is not None:
                    existing_metrics.rs_sector = rs_sector
                if ema_data is not None:
                    existing_metrics.set_ema_data(ema_data)
                if eps_history is not None:
                    existing_metrics.set_eps_history(eps_history)
                
                session.commit()
                return existing_metrics
            else:
                # Create new metrics
                new_metrics = StockMetrics(
                    symbol=symbol,
                    stock_id=stock_id,
                    eps_growth_qoq=eps_growth_qoq,
                    eps_growth_yoy=eps_growth_yoy,
                    latest_quarterly_eps=latest_quarterly_eps,
                    rs_spy=rs_spy,
                    rs_sector=rs_sector
                )
                
                if ema_data is not None:
                    new_metrics.set_ema_data(ema_data)
                if eps_history is not None:
                    new_metrics.set_eps_history(eps_history)
                
                session.add(new_metrics)
                session.commit()
                return new_metrics
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_metrics_dict(self) -> List[Dict]:
        """Get all stock metrics as dictionaries"""
        try:
            metrics = self.session.query(StockMetrics).all()
            result = []
            
            for metric in metrics:
                metric_dict = {
                    'symbol': metric.symbol,
                    'stock_id': metric.stock_id,
                    'eps_growth_qoq': metric.eps_growth_qoq,
                    'eps_growth_yoy': metric.eps_growth_yoy,
                    'latest_quarterly_eps': metric.latest_quarterly_eps,
                    'rs_spy': metric.rs_spy,
                    'rs_sector': metric.rs_sector,
                    'ema_data': metric.get_ema_data(),
                    'eps_history': metric.get_eps_history(),
                    'last_updated': metric.last_updated
                }
                result.append(metric_dict)
            
            return result
        finally:
            self.session.close()
    
    def get_combined_stock_data(self) -> List[Dict]:
        """Get combined stock and metrics data for UI consumption"""
        try:
            from database.models import Stock
            
            # Join stocks and stock_metrics tables
            query = self.session.query(Stock, StockMetrics).outerjoin(
                StockMetrics, Stock.symbol == StockMetrics.symbol
            )
            
            result = []
            for stock, metrics in query.all():
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
                
                if metrics:
                    # Get EPS history and convert to old format
                    eps_history_raw = metrics.get_eps_history()
                    latest_quarters = []
                    eps_history_formatted = {}
                    
                    if eps_history_raw and 'data' in eps_history_raw:
                        import math
                        # Convert new format (data array) to old format (quarterly dict)
                        quarterly_dict = {}
                        for item in eps_history_raw['data']:
                            # Filter out NaN values
                            eps_value = item['eps']
                            if not (isinstance(eps_value, float) and math.isnan(eps_value)):
                                quarterly_dict[item['date']] = eps_value
                        
                        eps_history_formatted = {'quarterly': quarterly_dict}
                        
                        # Get last 4 quarters for latest_quarters
                        eps_data_sorted = sorted(eps_history_raw['data'], key=lambda x: x['date'])
                        latest_quarters = [
                            item['eps'] for item in eps_data_sorted[-4:]
                            if not (isinstance(item['eps'], float) and math.isnan(item['eps']))
                        ]
                    
                    # Format data to match old structure (nested objects)
                    # Handle NaN values for JSON serialization
                    def safe_float(value):
                        if value is None:
                            return None
                        if isinstance(value, float) and math.isnan(value):
                            return None
                        return value
                    
                    # Apply safe_float to EMA data as well
                    ema_data = metrics.get_ema_data()
                    safe_ema_data = {}
                    for key, value in ema_data.items():
                        safe_ema_data[key] = safe_float(value)
                    
                    stock_dict.update({
                        'eps_growth': {
                            'quarter_over_quarter': safe_float(metrics.eps_growth_qoq),
                            'year_over_year': safe_float(metrics.eps_growth_yoy),
                            'latest_quarters': latest_quarters
                        },
                        'relative_strength': {
                            'rs_spy': safe_float(metrics.rs_spy),
                            'rs_sector': safe_float(metrics.rs_sector)
                        },
                        'ema_data': safe_ema_data,
                        'eps_history': eps_history_formatted
                    })
                else:
                    # Add empty metrics if none exist
                    stock_dict.update({
                        'eps_growth': {
                            'quarter_over_quarter': None,
                            'year_over_year': None,
                            'latest_quarters': []
                        },
                        'relative_strength': {
                            'rs_spy': None,
                            'rs_sector': None
                        },
                        'ema_data': {},
                        'eps_history': {}
                    })
                
                result.append(stock_dict)
            
            return result
        finally:
            self.session.close()
