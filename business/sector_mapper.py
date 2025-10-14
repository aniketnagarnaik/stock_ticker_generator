"""
Business logic for sector-to-ETF mapping
"""


class SectorMapper:
    """Maps stock sectors to appropriate sector ETFs for RS calculations"""
    
    def __init__(self):
        # Map sectors to their corresponding ETFs
        self.sector_etf_map = {
            'Technology': 'XLK',
            'Healthcare': 'XLV', 
            'Financial Services': 'XLF',
            'Consumer Discretionary': 'XLY',
            'Consumer Staples': 'XLP',
            'Energy': 'XLE',
            'Industrials': 'XLI',
            'Materials': 'XLB',
            'Real Estate': 'XLRE',
            'Utilities': 'XLU',
            'Communication Services': 'XLC'
        }
    
    def get_sector_etf(self, sector: str) -> str:
        """
        Get the appropriate sector ETF for a given sector
        
        Args:
            sector: Stock sector (e.g., 'Technology', 'Healthcare')
            
        Returns:
            ETF symbol (e.g., 'XLK', 'XLV') or None if no mapping exists
        """
        return self.sector_etf_map.get(sector)
    
    def get_all_sector_etfs(self) -> list:
        """Get list of all sector ETFs"""
        return list(self.sector_etf_map.values())
    
    def add_sector_mapping(self, sector: str, etf: str) -> None:
        """Add a new sector-to-ETF mapping"""
        self.sector_etf_map[sector] = etf
    
    def is_valid_sector(self, sector: str) -> bool:
        """Check if sector has a corresponding ETF mapping"""
        return sector in self.sector_etf_map
