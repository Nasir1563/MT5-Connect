from flask import Flask, request, render_template, jsonify
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import chardet
from io import StringIO

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure your Supabase URL and key from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_data(df, symbol, timeframe):
    expected_columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'extra']
    df.columns = expected_columns[:len(df.columns)]
    df['symbol'] = symbol
    df['timeframe'] = timeframe
    data_to_insert = df.to_dict(orient='records')
    response = supabase.table('EURUSD').insert(data_to_insert).execute()
    if response.status_code != 201:
        print(f"Error inserting data: {response}")
        return False, response
    else:
        print("Data uploaded successfully")
        return True, "Data uploaded successfully"

def fetch_chart_data(timeframe):
    if timeframe == 'all':
        response = supabase.table('EURUSD').select("*").execute()
    else:
        response = supabase.table('EURUSD').select("*").eq('timeframe', str(timeframe)).execute()
    
    if response.status_code != 200:
        print(f"Error fetching data: {response}")
        return None
    else:
        return response.data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chart')
def chart():
    return render_template('chart.html')

@app.route('/get_chart_data', methods=['GET'])
def get_chart_data():
    timeframe = request.args.get('timeframe')
    data = fetch_chart_data(timeframe)
    if data is None:
        return jsonify({'error': 'Failed to fetch data'})
    df = pd.DataFrame(data)
    return jsonify({
        'time': df['time'].tolist(),
        'open': df['open'].tolist(),
        'high': df['high'].tolist(),
        'low': df['low'].tolist(),
        'close': df['close'].tolist()
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    symbol = request.form['symbol']
    timeframe = request.form['timeframe']
    
    if file and symbol and timeframe:
        try:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            df = pd.read_csv(StringIO(raw_data.decode(encoding)), delimiter=',', header=None)
        except UnicodeDecodeError:
            return "Error: File encoding is not supported. Please upload a valid CSV file."
        except Exception as e:
            return f"Error: {str(e)}"
        
        success, message = insert_data(df, symbol, timeframe)
        if success:
            return "Data uploaded successfully"
        else:
            return f"Error: {message}"

    return "Invalid data or missing parameters"

if __name__ == '__main__':
    app.run(debug=True)
