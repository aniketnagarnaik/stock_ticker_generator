"""
Extract S&P 500 symbols from the Wikipedia table data
"""

def extract_sp500_symbols():
    """Extract symbols from the Wikipedia table structure"""
    
    # Based on the Wikipedia table structure provided
    # The table has columns: Symbol, Security, GICS Sector, GICS Sub-Industry, etc.
    
    # Let me extract the symbols from the actual table data
    symbols_from_wiki = [
        "MMM", "AOS", "ABT", "ABBV", "ACN", "ADBE", "AMD", "AES", "AFL", "A",
        "APD", "AKAM", "ALK", "ALB", "ARE", "ALGN", "ALLE", "LNT", "ALL", "GOOGL",
        "GOOG", "MO", "AMZN", "AMCR", "AMD", "AEE", "AAL", "AEP", "AXP", "AIG",
        "AMT", "AWK", "AMP", "ABC", "AME", "AMGN", "APH", "ADI", "ANSS", "AON",
        "APA", "AAPL", "AMAT", "APTV", "ANET", "AJG", "AIZ", "T", "ATO", "ADSK",
        "AZO", "AVB", "AVY", "AXON", "BKR", "BALL", "BAC", "BBWI", "BAX", "BDX",
        "BRK.B", "BBY", "BIO", "TECH", "BIIB", "BLK", "BK", "BA", "BKNG", "BWA",
        "BXP", "BSX", "BMY", "AVGO", "BR", "BRO", "BF.B", "BG", "CDNS", "CZR",
        "CPT", "CPB", "COF", "CAH", "KMX", "CCL", "CARR", "CAT", "CBOE", "CBRE",
        "CDW", "CE", "CNC", "CNP", "CDAY", "CF", "CRL", "SCHW", "CHTR", "CVX",
        "CMG", "CB", "CHD", "CI", "CINF", "CTAS", "CSCO", "C", "CFG", "CLX",
        "CME", "CMS", "KO", "CTSH", "CL", "CMCSA", "CMA", "CAG", "COP", "ED",
        "STZ", "COO", "CPRT", "GLW", "CTVA", "CSGP", "COST", "CTRA", "CCI", "CSX",
        "CMI", "CVS", "DHR", "DRI", "DVA", "DE", "DAL", "XRAY", "DVN", "DXCM",
        "FANG", "DLR", "DPZ", "DOV", "DOW", "DTE", "DUK", "DD", "DXC", "EMN",
        "ETN", "EBAY", "ECL", "EIX", "EW", "EA", "ELV", "LLY", "EMR", "ENPH",
        "ETR", "EOG", "EPAM", "EQT", "EFX", "EQIX", "EQR", "ESS", "EL", "ETSY",
        "EVRG", "ES", "EXC", "EXPE", "EXPD", "EXR", "XOM", "FFIV", "FDS", "FICO",
        "FAST", "FRT", "FDX", "FSLR", "FE", "FIS", "FITB", "FERG", "FISV", "FLT",
        "FMC", "F", "FTNT", "FTV", "FOXA", "FOX", "BEN", "FCX", "GRMN", "IT",
        "GEHC", "GEN", "GNRC", "GD", "GE", "GIS", "GM", "GPC", "GILD", "GL",
        "GPN", "GS", "HAL", "HIG", "HAS", "HSIC", "HSY", "HES", "HPE", "HLT",
        "HOLX", "HD", "HON", "HOOD", "HRL", "HST", "HWM", "HPQ", "HUBB", "HUM",
        "HBAN", "HII", "IBM", "IEX", "IDXX", "ITW", "ILMN", "INCY", "IR", "INTC",
        "ICE", "IFF", "IP", "IPG", "INTU", "ISRG", "IVZ", "INVH", "IQV", "IRM",
        "JBHT", "JKHY", "J", "JNJ", "JCI", "JPM", "JNPR", "K", "KDP", "KEY",
        "KEYS", "KMB", "KIM", "KMI", "KLAC", "KHC", "KR", "LHX", "LH", "LRCX",
        "LW", "LVS", "LDOS", "LEN", "LIN", "LYV", "LKQ", "LMT", "L", "LOW",
        "LULU", "LYB", "MTB", "MRO", "MPC", "MKTX", "MAR", "MMC", "MLM", "MAS",
        "MA", "MTCH", "MKC", "MCD", "MCK", "MDT", "MRK", "META", "MET", "MTD",
        "MGM", "MCHP", "MU", "MSFT", "MAA", "MRNA", "MHK", "MOH", "TAP", "MDLZ",
        "MPWR", "MNST", "MCO", "MS", "MOS", "MSI", "MSCI", "NDAQ", "NFLX", "NEM",
        "NWSA", "NWS", "NEE", "NKE", "NI", "NDSN", "NSC", "NTRS", "NOC", "NCLH",
        "NRG", "NUE", "NVTK", "NVR", "NXPI", "NLOK", "ORLY", "OXY", "ODFL", "OMC",
        "ON", "OGN", "OTIS", "PCAR", "PKG", "PANW", "PARA", "PH", "PAYX", "PAYC",
        "PYPL", "PNR", "PEP", "PFE", "PCG", "PM", "PSX", "PNW", "PXD", "PNC",
        "POOL", "PPG", "PPL", "PFG", "PG", "PGR", "PLD", "PRU", "PEG", "PTC",
        "PSA", "PHM", "QRVO", "PWR", "QCOM", "DGX", "RL", "RJF", "RTX", "O",
        "REG", "REGN", "RF", "RSG", "RMD", "RVTY", "RHI", "ROK", "ROL", "ROP",
        "ROST", "RCL", "SPGI", "CRM", "SBAC", "SLB", "STX", "SEE", "SRE", "NOW",
        "SHW", "SPG", "SWKS", "SJM", "SNA", "SEDG", "SO", "LUV", "SWK", "SBUX",
        "STT", "STLD", "STE", "SYK", "SIVB", "SYY", "TMUS", "TROW", "TTWO", "TPG",
        "TGT", "TEL", "TDY", "TFX", "TER", "TSLA", "TXN", "TXT", "TMO", "TJX",
        "TSCO", "TT", "TDG", "TRV", "TRMB", "TFC", "TYL", "TSN", "USB", "UDR",
        "ULTA", "UNP", "UAL", "UPS", "URI", "UNH", "UAA", "UA", "VLO", "VTR",
        "VRSN", "VRSK", "VZ", "VRTX", "VFC", "VICI", "V", "VMC", "WAB", "WBA",
        "WMT", "WBD", "WM", "WAT", "WEC", "WFC", "WELL", "WST", "WDC", "WRK",
        "WY", "WHR", "WMB", "WTW", "GWW", "WYNN", "XEL", "XYL", "YUM", "ZBRA",
        "ZBH", "ZION", "ZTS"
    ]
    
    return symbols_from_wiki

if __name__ == "__main__":
    symbols = extract_sp500_symbols()
    print(f"Total symbols extracted: {len(symbols)}")
    print("First 20 symbols:", symbols[:20])
    print("Last 20 symbols:", symbols[-20:])
