#!/usr/bin/env python3

import requests
import json

def test_extract_endpoint():
    """
    Test the /extract endpoint by sending sample financial newsletter emails
    """
    
    # The URL for your local Flask app
    url = "http://localhost:8082/extract"
    
    # Sample financial newsletter emails
    test_data = {
        "emails": [
            {
                "subject": "Bloomberg Markets Close - Tech Stocks Rally",
                "date": "2025-01-20T21:30:00.000Z",
                "from": "Bloomberg Markets <newsletters@bloomberg.com>",
                "body": """Markets closed higher today with technology stocks leading the rally. The Nasdaq Composite gained 2.3% while the S&P 500 rose 1.8%. Key drivers included strong earnings from major tech companies and renewed optimism about AI investments. 

Key highlights:
- NVIDIA (NVDA) surged 5.2% on data center demand
- Apple (AAPL) gained 3.1% ahead of quarterly results
- Microsoft (MSFT) rose 2.8% on cloud growth prospects
- Tesla (TSLA) jumped 4.5% on delivery beat expectations

The VIX volatility index fell to 18.2, indicating reduced market anxiety. Bond yields remained stable with the 10-year Treasury at 4.32%.

Looking ahead, investors await Fed commentary and more earnings reports this week."""
            },
            {
                "subject": "Financial Times: Central Bank Policies Drive Market Momentum",
                "date": "2025-01-20T18:45:12.000Z",
                "from": "Financial Times <noreply@ft.com>",
                "body": """Central bank policies continue to shape global market dynamics as investors digest the latest monetary policy signals. The Federal Reserve's dovish stance has provided tailwinds for risk assets, while European markets showed mixed performance.

Market Analysis:
- US Dollar weakened against major currencies
- Gold prices reached new monthly highs at $2,045/oz
- Energy sector outperformed on crude oil strength
- Banking stocks rallied on interest rate expectations

Sector Performance:
- Technology: +2.1%
- Energy: +1.9% 
- Financials: +1.7%
- Healthcare: +0.8%
- Utilities: -0.3%

Key stocks to watch: JPMorgan Chase (JPM), ExxonMobil (XOM), Alphabet (GOOGL), and Johnson & Johnson (JNJ) all reporting this week.

The market's resilience suggests continued bullish sentiment despite geopolitical uncertainties."""
            },
            {
                "subject": "WSJ Morning Brief: Earnings Season Kicks Into High Gear",
                "date": "2025-01-20T13:15:30.000Z",
                "from": "Wall Street Journal <newsletters@wsj.com>",
                "body": """Earnings season accelerates this week with major corporations reporting quarterly results. Analyst expectations remain elevated as companies navigate economic headwinds and shifting consumer behavior.

Earnings Preview:
- Netflix (NFLX) reports after market close today
- Johnson & Johnson (JNJ) before market open Tuesday
- Tesla (TSLA) Wednesday after close
- Intel (INTC) Thursday after close

Economic Data This Week:
- Existing Home Sales (Tuesday)
- Weekly Jobless Claims (Thursday)
- PMI Manufacturing Flash (Friday)

Market sentiment remains cautiously optimistic despite inflation concerns. The recent rally in growth stocks has been supported by better-than-expected corporate guidance and signs of economic resilience.

Commodities Update:
- Crude oil: $78.45/barrel (+1.2%)
- Natural gas: $2.89/MMBtu (-0.8%)
- Copper: $4.12/pound (+0.5%)

Currency markets show USD weakness continuing as investors position for potential Fed policy shifts."""
            }
        ]
    }
    
    try:
        print("Sending request to /extract endpoint...")
        print(f"URL: {url}")
        print(f"Number of emails: {len(test_data['emails'])}")
        print("-" * 50)
        
        # Send the POST request
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS: Request sent successfully!")
            print("The emails have been queued for processing.")
        else:
            print(f"\n❌ ERROR: Request failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the server.")
        print("Make sure your Flask app is running on localhost:8082")
        print("Run: python main.py")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out.")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("🚀 Testing Duwiligence /extract endpoint")
    print("=" * 50)
    test_extract_endpoint()
