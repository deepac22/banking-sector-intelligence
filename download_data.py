import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from fredapi import Fred

FRED_API_KEY = "43e908d789f02ad98a5f7b28dbc665c2"

banks = [
    {'ticker': 'CM.TO', 'name': 'CIBC', 'country': 'Canada'},
    {'ticker': 'RY.TO', 'name': 'RBC', 'country': 'Canada'},
    {'ticker': 'TD.TO', 'name': 'TD Bank', 'country': 'Canada'},
    {'ticker': 'BNS.TO', 'name': 'Scotiabank', 'country': 'Canada'},
    {'ticker': 'BMO.TO', 'name': 'BMO', 'country': 'Canada'},
    {'ticker': 'NA.TO', 'name': 'National Bank', 'country': 'Canada'},
    {'ticker': 'JPM', 'name': 'JPMorgan Chase', 'country': 'USA'},
    {'ticker': 'BAC', 'name': 'Bank of America', 'country': 'USA'},
    {'ticker': 'WFC', 'name': 'Wells Fargo', 'country': 'USA'},
    {'ticker': 'GS', 'name': 'Goldman Sachs', 'country': 'USA'}
]

def get_bank_data(ticker, name, country):
    print(f"Downloading {name} ({ticker})...")
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y")
        if hist.empty:
            print(f"No data for {ticker}")
            return None
        info = stock.info
        return {
            'ticker': ticker,
            'name': name,
            'country': country,
            'prices': hist['Close'],
            'pe_ratio': info.get('trailingPE', np.nan),
            'pb_ratio': info.get('priceToBook', np.nan),
            'dividend_yield': info.get('dividendYield', np.nan) * 100 if info.get('dividendYield') else np.nan,
            'earnings_growth': info.get('earningsGrowth', np.nan) * 100 if info.get('earningsGrowth') else np.nan,
            'market_cap': info.get('marketCap', np.nan)
        }
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        return None

def create_dummy_us():
    pd.DataFrame({
        'Date': pd.date_range(start='2020-01-01', periods=1000),
        'USD_10Y': [3.5 + (i % 10) * 0.1 for i in range(1000)]
    }).to_csv('us_bond_yield.csv', index=False)

def create_dummy_cad():
    pd.DataFrame({
        'Date': pd.date_range(start='2020-01-01', periods=1000),
        'CAD_10Y': [2.5 + (i % 8) * 0.1 for i in range(1000)]
    }).to_csv('cad_bond_yield.csv', index=False)

def get_bond_yields():
    print("Downloading bond yields...")

    try:
        fred = Fred(api_key=FRED_API_KEY)
        us_bond = fred.get_series('DGS10')
        us_bond = us_bond.reset_index()
        us_bond.columns = ['Date', 'USD_10Y']
        us_bond.to_csv('us_bond_yield.csv', index=False)
        print("US 10-Year Treasury Yield saved.")
    except Exception as e:
        print(f"FRED API failed: {e}")
        create_dummy_us()

    try:
        url = "https://api.stlouisfed.org/fred/series/observations?series_id=IRLTLT01CAM156N&api_key=43e908d789f02ad98a5f7b28dbc665c2&file_type=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if observations:
                dates = []
                yields = []
                for obs in observations:
                    dates.append(obs['date'])
                    yields.append(float(obs['value']) if obs['value'] != '.' else None)
                cad_df = pd.DataFrame({
                    'Date': pd.to_datetime(dates),
                    'CAD_10Y': yields
                })
                cad_df = cad_df.dropna()
                cad_df.to_csv('cad_bond_yield.csv', index=False)
                print("Canada 10-Year Bond Yield saved from FRED.")
            else:
                print("No observations found.")
                create_dummy_cad()
        else:
            print(f"FRED Canada series returned status: {response.status_code}")
            create_dummy_cad()
    except Exception as e:
        print(f"Canada bond yield download failed: {e}")
        create_dummy_cad()

def main():
    print("Starting banking sector data download...")
    
    all_data = []
    price_data = pd.DataFrame()
    
    for bank in banks:
        data = get_bank_data(bank['ticker'], bank['name'], bank['country'])
        if data and data['prices'] is not None:
            all_data.append(data)
            price_data[bank['ticker']] = data['prices']
    
    price_data.to_csv('bank_prices_wide.csv')
    print("Bank prices saved (wide format).")
    
    # Pivot from wide to long format for Tableau
    price_data_long = price_data.reset_index()
    price_data_long = price_data_long.melt(
        id_vars=['Date'], 
        var_name='Ticker', 
        value_name='Price'
    )
    price_data_long.to_csv('bank_prices_long.csv', index=False)
    print("Bank prices saved (long format) for Tableau.")
    
    returns = price_data.pct_change().dropna()
    
    metrics = []
    for data in all_data:
        ticker = data['ticker']
        name = data['name']
        country = data['country']
        
        if ticker not in returns.columns:
            continue
        
        annual_return = returns[ticker].mean() * 252 * 100
        annual_vol = returns[ticker].std() * np.sqrt(252) * 100
        sharpe = annual_return / annual_vol if annual_vol != 0 else 0
        
        latest_price = data['prices'].iloc[-1]
        high_52w = data['prices'].max()
        pct_from_high = ((latest_price - high_52w) / high_52w) * 100
        
        metrics.append({
            'Bank': name,
            'Ticker': ticker,
            'Country': country,
            'Latest_Price': round(latest_price, 2),
            'Annual_Return': round(annual_return, 2),
            'Volatility': round(annual_vol, 2),
            'Sharpe_Ratio': round(sharpe, 2),
            'P/E': round(data['pe_ratio'], 2) if not np.isnan(data['pe_ratio']) else np.nan,
            'P/B': round(data['pb_ratio'], 2) if not np.isnan(data['pb_ratio']) else np.nan,
            'Dividend_Yield': round(data['dividend_yield'], 2) if not np.isnan(data['dividend_yield']) else np.nan,
            'Earnings_Growth': round(data['earnings_growth'], 2) if not np.isnan(data['earnings_growth']) else np.nan,
            'Market_Cap_B': round(data['market_cap'] / 1e9, 2) if not np.isnan(data['market_cap']) else np.nan,
            'Pct_From_High': round(pct_from_high, 2)
        })
    
    metrics_df = pd.DataFrame(metrics)
    metrics_df = metrics_df.sort_values(['Country', 'Annual_Return'], ascending=[True, False])
    metrics_df.to_csv('bank_metrics.csv', index=False)
    print("Metrics saved.")
    
    corr_matrix = returns.corr().round(2)
    corr_matrix.to_csv('bank_correlation.csv', index=False)
    print("Correlation matrix saved.")
    
    print("\n===== Banking Sector Summary =====")
    print(metrics_df.to_string(index=False))
    
    get_bond_yields()
    
    print("Done.")
    print("\nFiles generated for Tableau:")
    print("1. bank_prices_long.csv - Use this for price charts (Date, Ticker, Price)")
    print("2. bank_metrics.csv - Use this for metrics (Ticker, Annual_Return, Volatility, etc.)")
    print("3. bank_correlation.csv - Use this for the correlation heatmap")

if __name__ == "__main__":
    main()