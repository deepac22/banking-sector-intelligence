import pandas as pd
import numpy as np
from datetime import datetime
import os

def generate_insights():
    df = pd.read_csv('bank_metrics.csv')
    
    insights = []
    insights.append(f"Banking Sector Report - {datetime.now().strftime('%B %d, %Y')}")
    insights.append("=" * 50)
    
    best_return = df.loc[df['Annual_Return'].idxmax()]
    insights.append(f"Best Performer: {best_return['Bank']} ({best_return['Annual_Return']}%)")
    
    best_dividend = df.loc[df['Dividend_Yield'].idxmax()]
    insights.append(f"Highest Dividend Yield: {best_dividend['Bank']} ({best_dividend['Dividend_Yield']}%)")
    
    best_sharpe = df.loc[df['Sharpe_Ratio'].idxmax()]
    insights.append(f"Best Risk/Reward: {best_sharpe['Bank']} (Sharpe: {best_sharpe['Sharpe_Ratio']})")
    
    df_pe = df.dropna(subset=['P/E'])
    if not df_pe.empty:
        lowest_pe = df_pe.loc[df_pe['P/E'].idxmin()]
        insights.append(f"Most Undervalued (P/E): {lowest_pe['Bank']} (P/E: {lowest_pe['P/E']})")
    
    country_stats = df.groupby('Country')['Annual_Return'].mean().round(2)
    insights.append(f"Country Average Returns: Canada ({country_stats.get('Canada', 0)}%) vs USA ({country_stats.get('USA', 0)}%)")
    
    avg_vol = df['Volatility'].mean()
    avg_return = df['Annual_Return'].mean()
    sentiment = "Bullish" if avg_return > 5 else "Neutral" if avg_return > 0 else "Bearish"
    insights.append(f"Sector Sentiment: {sentiment} (Avg Return: {avg_return:.2f}%)")
    
    insights.append("")
    insights.append("=" * 50)
    insights.append("SECTOR SUMMARY")
    insights.append(f"Best Performer: {best_return['Bank']} ({best_return['Annual_Return']}%)")
    insights.append(f"Worst Performer: {df.loc[df['Annual_Return'].idxmin()]['Bank']} ({df.loc[df['Annual_Return'].idxmin()]['Annual_Return']}%)")
    insights.append(f"Highest Yield: {best_dividend['Bank']} ({best_dividend['Dividend_Yield']}%)")
    
    with open('bank_insights.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(insights))
    
    print("Insights generated and saved to bank_insights.txt")
    return '\n'.join(insights)

if __name__ == "__main__":
    generate_insights()