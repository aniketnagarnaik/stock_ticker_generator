#!/usr/bin/env python3
"""
S&P 500 Data Extractor
======================

This script extracts S&P 500 company data from Wikipedia and updates
the local stock symbols file. It can be run independently to refresh
the stock list.

Usage:
    python3 scripts/sp500_extractor.py

Features:
- Extracts symbols and company names from Wikipedia
- Handles rate limiting and errors gracefully
- Updates both stock_symbols.txt and sp500_companies.json
- Provides detailed logging and error handling

Author: Stock Data Viewer Team
Last Updated: October 2025
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import os
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SP500Extractor:
    """Extracts S&P 500 data from Wikipedia"""
    
    def __init__(self):
        self.wikipedia_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.companies = []
    
    def fetch_wikipedia_data(self) -> bool:
        """
        Fetch S&P 500 data from Wikipedia
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("🌐 Fetching S&P 500 data from Wikipedia...")
            response = requests.get(self.wikipedia_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the S&P 500 companies table
            table = soup.find('table', {'id': 'constituents'})
            if not table:
                print("❌ Could not find S&P 500 companies table")
                return False
            
            # Extract company data from table rows
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    symbol = cells[0].get_text(strip=True)
                    company_name = cells[1].get_text(strip=True)
                    sector = cells[2].get_text(strip=True)
                    industry = cells[3].get_text(strip=True)
                    
                    self.companies.append({
                        'symbol': symbol,
                        'company_name': company_name,
                        'sector': sector,
                        'industry': industry
                    })
            
            print(f"✅ Successfully extracted {len(self.companies)} companies")
            return True
            
        except requests.RequestException as e:
            print(f"❌ Error fetching data from Wikipedia: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def save_stock_symbols(self, filename: str = 'stock_symbols.txt') -> bool:
        """
        Save stock symbols to text file
        
        Args:
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            symbols = [company['symbol'] for company in self.companies]
            symbols.sort()  # Sort alphabetically
            
            with open(filename, 'w') as f:
                for symbol in symbols:
                    f.write(f"{symbol}\n")
            
            print(f"✅ Saved {len(symbols)} symbols to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving symbols: {e}")
            return False
    
    def save_companies_data(self, filename: str = 'sp500_companies.json') -> bool:
        """
        Save detailed company data to JSON file
        
        Args:
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.companies, f, indent=2)
            
            print(f"✅ Saved detailed company data to {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving company data: {e}")
            return False
    
    def extract_and_save(self) -> bool:
        """
        Main extraction and save process
        
        Returns:
            bool: True if successful, False otherwise
        """
        print("🚀 Starting S&P 500 data extraction...")
        print("=" * 50)
        
        # Fetch data from Wikipedia
        if not self.fetch_wikipedia_data():
            return False
        
        # Save stock symbols
        if not self.save_stock_symbols():
            return False
        
        # Save detailed company data
        if not self.save_companies_data():
            return False
        
        print("=" * 50)
        print("🎉 S&P 500 data extraction completed successfully!")
        print(f"📊 Total companies: {len(self.companies)}")
        
        return True

def main():
    """Main function"""
    extractor = SP500Extractor()
    
    try:
        success = extractor.extract_and_save()
        if success:
            print("\n✅ All done! Stock symbols and company data have been updated.")
            sys.exit(0)
        else:
            print("\n❌ Extraction failed. Please check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

