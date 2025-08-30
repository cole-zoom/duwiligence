import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

URL = os.environ.get("NEON_PASS")

def fetch_portfolios():
    """
    Fetch the list of portfolios/stock symbols to monitor from NeonDB.
    
    Returns:
        list: List of user dictionaries with their portfolios and tickers
        Format: [
            {email: {portfolio1: [ticker1, ticker2], portfolio2: [ticker1, ticker2]}},
            {email: {portfolio1: [ticker1, ticker2]}}
        ]
    """
    try:
        db_url = URL
        if not db_url:
            print("Error: NEON_PASS environment variable not set.")
            print("Please set it to your Neon database connection string.")
            return []
        
        # Connect to NeonDB using the connection string
        with psycopg.connect(db_url) as conn:
            cursor = conn.cursor()
            
            # Query to get users with their emails and portfolios with stocks
            query = """
            SELECT 
                us.email,
                p.name as portfolio_name,
                ARRAY_AGG(s.ticker) as tickers
            FROM profiles pr
            JOIN neon_auth.users_sync us ON pr.id = us.id
            LEFT JOIN portfolios p ON pr.id = p.user_id
            LEFT JOIN stocks s ON p.id = s.portfolio_id
            WHERE us.email IS NOT NULL
            GROUP BY us.email, p.name, p.id
            ORDER BY us.email, p.name;
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            
            # Organize data by user email
            user_portfolios = {}
            
            for row in results:
                # Convert tuple to dict using column names
                row_dict = dict(zip(columns, row))
                email = row_dict['email']
                portfolio_name = row_dict['portfolio_name']
                tickers = row_dict['tickers'] or []  # Handle NULL case
                
                # Remove None values from tickers list
                tickers = [ticker for ticker in tickers if ticker is not None]
                
                if email not in user_portfolios:
                    user_portfolios[email] = {}
                
                if portfolio_name:
                    user_portfolios[email][portfolio_name] = tickers
            
            # Convert to the requested format
            result = []
            for email, portfolios in user_portfolios.items():
                result.append({email: portfolios})
            
            return result
        
    except Exception as e:
        print(f"Error fetching portfolios from NeonDB: {e}")
        # Return empty list on error
        return []


if __name__ == "__main__":
    print(fetch_portfolios())