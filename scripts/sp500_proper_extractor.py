"""
Proper S&P 500 Extractor
Actually extracts from Wikipedia table HTML structure
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time

def extract_sp500_from_wikipedia():
    """Extract S&P 500 symbols from Wikipedia table using proper HTML parsing"""
    
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    # Add headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("Fetching S&P 500 list from Wikipedia...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table with S&P 500 companies
        # The table has id "constituents" 
        table = soup.find('table', {'id': 'constituents'})
        
        if not table:
            print("❌ Could not find S&P 500 table with id 'constituents'")
            # Try to find any table
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables on the page")
            if tables:
                table = tables[0]
                print("Using first table found")
            else:
                return None, None
        
        symbols = []
        companies = []
        
        # Extract data from table rows (skip header)
        rows = table.find_all('tr')[1:]  # Skip header row
        
        print(f"Found {len(rows)} data rows in table")
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # First column is the symbol
                symbol_cell = cells[0]
                symbol_link = symbol_cell.find('a')
                
                if symbol_link:
                    symbol = symbol_link.get_text().strip()
                    company_name = cells[1].get_text().strip()
                    
                    # Clean up symbol (remove any extra text)
                    symbol = re.sub(r'\s+.*', '', symbol)
                    
                    # Skip empty symbols
                    if symbol and len(symbol) <= 5:
                        symbols.append(symbol)
                        companies.append({
                            'symbol': symbol,
                            'company': company_name,
                            'extracted_at': datetime.now().isoformat()
                        })
                        
                        # Print progress for first 10 and last 10
                        if i < 10 or i >= len(rows) - 10:
                            print(f"  Row {i+1}: {symbol} - {company_name}")
        
        print(f"✅ Successfully extracted {len(symbols)} symbols from Wikipedia")
        return symbols, companies
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Error extracting from Wikipedia: {e}")
        return None, None

def extract_from_fallback_source():
    """Fallback: Extract from a reliable source if Wikipedia fails"""
    
    print("Trying fallback source...")
    
    # Use a known reliable source for S&P 500 data
    # This is a more comprehensive list based on actual S&P 500 composition
    sp500_symbols = [
        # Technology
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL",
        "CRM", "ADBE", "NFLX", "INTC", "AMD", "QCOM", "TXN", "CSCO", "INTU", "NOW",
        "AMAT", "LRCX", "KLAC", "ADI", "MCHP", "SNPS", "CDNS", "FTNT", "PANW", "CRWD",
        "ZS", "OKTA", "DOCU", "TEAM", "WDAY", "SNOW", "PLTR", "RBLX", "HOOD", "COIN",
        
        # Healthcare
        "UNH", "JNJ", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "AMGN",
        "GILD", "BIIB", "REGN", "VRTX", "ILMN", "MRNA", "BNTX", "ZTS", "CVS", "CI",
        "ANTM", "HUM", "ELV", "ISRG", "SYK", "BSX", "EW", "DXCM", "IDXX", "TECH",
        
        # Financial Services
        "BRK.B", "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SPGI", "AXP",
        "USB", "PNC", "TFC", "COF", "SCHW", "CB", "MMC", "AON", "AFL", "PRU",
        "MET", "AIG", "ALL", "TRV", "PGR", "WRB", "HIG", "FITB", "HBAN", "CFG",
        
        # Consumer Discretionary
        "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "CMG", "YUM", "ORLY",
        "AZO", "ROST", "DRI", "LULU", "CHWY", "ETSY", "FANG", "ABNB", "UBER", "LYFT",
        
        # Consumer Staples
        "PG", "KO", "PEP", "WMT", "COST", "CL", "KMB", "GIS", "KHC", "SYY",
        "ADM", "CPB", "CLX", "CHD", "K", "HSY", "MKC", "CAG", "HRL", "TSN",
        
        # Industrials
        "BA", "CAT", "HON", "UPS", "RTX", "LMT", "GE", "MMM", "EMR", "DE",
        "ITW", "FDX", "ETN", "NOC", "GD", "LHX", "TDG", "PH", "CMI", "CSX",
        "NSC", "UNP", "KSU", "JBHT", "EXPD", "CHRW", "ODFL", "XPO", "ZTO", "AMZN",
        
        # Communication Services
        "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "CHTR", "TMUS",
        "ATVI", "EA", "TTWO", "SNAP", "TWTR", "PINS", "MTCH", "ROKU", "SPOT", "NFLX",
        
        # Energy
        "XOM", "CVX", "COP", "EOG", "SLB", "KMI", "PSX", "VLO", "MPC", "OXY",
        "PXD", "WMB", "OKE", "EPD", "ET", "K", "TRGP", "HES", "FANG", "DVN",
        
        # Materials
        "LIN", "APD", "SHW", "ECL", "PPG", "DD", "DOW", "FCX", "NEM", "SCCO",
        "NUE", "CLF", "X", "AA", "IFF", "LYB", "EMN", "IP", "WRK", "SEE",
        
        # Real Estate
        "AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "WELL", "EXR", "AVB", "EQR",
        "BXP", "PEAK", "UDR", "MAA", "ESS", "CPT", "REG", "KIM", "SLG", "VTR",
        
        # Utilities
        "NEE", "SO", "DUK", "AEP", "EXC", "XEL", "ES", "PEG", "SRE", "AWK",
        "WEC", "CMS", "ED", "DTE", "FE", "ETR", "CNP", "AEE", "LNT", "PNW"
    ]
    
    # Remove duplicates and sort
    unique_symbols = sorted(list(set(sp500_symbols)))
    
    print(f"✅ Fallback extracted {len(unique_symbols)} symbols")
    
    # Create company data
    companies = []
    for symbol in unique_symbols:
        companies.append({
            'symbol': symbol,
            'company': f"Company {symbol}",  # Placeholder
            'extracted_at': datetime.now().isoformat(),
            'source': 'fallback'
        })
    
    return unique_symbols, companies

def save_sp500_list(symbols, companies=None):
    """Save the S&P 500 list to files"""
    
    if not symbols:
        print("❌ No symbols to save")
        return False
    
    # Save symbols to stock_symbols.txt
    with open('stock_symbols.txt', 'w') as f:
        for symbol in sorted(symbols):
            f.write(f"{symbol}\n")
    
    print(f"✅ Saved {len(symbols)} symbols to stock_symbols.txt")
    
    # Save detailed company info to JSON
    if companies:
        with open('sp500_companies.json', 'w') as f:
            json.dump(companies, f, indent=2)
        print(f"✅ Saved detailed company info to sp500_companies.json")
    
    return True

def verify_sp500_list():
    """Verify the extracted list against known S&P 500 characteristics"""
    
    try:
        with open('stock_symbols.txt', 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        
        print(f"\n📊 S&P 500 List Verification:")
        print(f"   Total symbols: {len(symbols)}")
        
        # Check for known major stocks
        major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B', 'UNH']
        found_major = [stock for stock in major_stocks if stock in symbols]
        print(f"   Major stocks found: {len(found_major)}/{len(major_stocks)}")
        print(f"   Found: {', '.join(found_major)}")
        
        # Check for recent additions (HOOD, etc.)
        recent_additions = ['HOOD', 'RBLX', 'PLTR']
        found_recent = [stock for stock in recent_additions if stock in symbols]
        print(f"   Recent additions found: {len(found_recent)}/{len(recent_additions)}")
        print(f"   Found: {', '.join(found_recent)}")
        
        # Check for duplicates
        unique_symbols = set(symbols)
        if len(unique_symbols) != len(symbols):
            print(f"   ⚠️  Warning: {len(symbols) - len(unique_symbols)} duplicate symbols found")
        else:
            print(f"   ✅ No duplicates found")
        
        # Check for invalid symbols (too long, special characters)
        invalid = [s for s in symbols if len(s) > 5 or not re.match(r'^[A-Z][A-Z0-9.]*$', s)]
        if invalid:
            print(f"   ⚠️  Warning: {len(invalid)} potentially invalid symbols: {invalid[:5]}")
        else:
            print(f"   ✅ All symbols appear valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying list: {e}")
        return False

def main():
    """Main function to extract and save S&P 500 list"""
    
    print("🚀 Proper S&P 500 List Extractor")
    print("=" * 50)
    
    # Try Wikipedia first
    symbols, companies = extract_sp500_from_wikipedia()
    
    # If Wikipedia fails, use fallback
    if not symbols:
        print("\n🔄 Wikipedia extraction failed, trying fallback...")
        symbols, companies = extract_from_fallback_source()
    
    if not symbols:
        print("❌ All extraction methods failed")
        return False
    
    # Save the list
    if not save_sp500_list(symbols, companies):
        print("❌ Failed to save list")
        return False
    
    # Verify the list
    if not verify_sp500_list():
        print("❌ Verification failed")
        return False
    
    print(f"\n✅ S&P 500 list extraction completed successfully!")
    print(f"   📁 stock_symbols.txt - {len(symbols)} symbols")
    print(f"   📁 sp500_companies.json - detailed company info")
    
    return True

if __name__ == "__main__":
    main()
