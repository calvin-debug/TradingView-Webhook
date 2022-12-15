import json
import math
import os
import requests
from datetime import datetime
from binance.client import Client
from binance.enums import *
from flask_login import current_user
from app.models import User
from app.encryption import dec_data


# Function to get ticker(s) price(s)
def get_ticker_price(tickers: list) -> dict:
    # Creating the query for getting the ticker prices
    ticker_query = str(tickers).replace(" ", "").replace("'", '"')

    # Sending request
    prices = json.loads(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbols={ticker_query}").text)
    
    # Creating a dictionary with the ticker prices
    return_prices = {}
    try:
        for price in prices:
            return_prices[price["symbol"]] = float(price["price"])
    except:
        pass

    return return_prices



# Creating order data - how much was actually processed and how much was aquired
def create_order_data(data: dict) -> dict:
    shares = float(data["executedQty"])
    spent = float(data["cummulativeQuoteQty"])

    order_data = {
        "shares": shares,
        "spent": spent
    }

    return order_data


# Splitting the ticker name as base currency and ticker name
def split_ticker(ticker_name: str):
    # Ticker data - name and basecurrency separated
    try:
        name = get_tickers()[ticker_name].split("/")[0]
        base = get_tickers()[ticker_name].split("/")[1]
    except Exception as e:
        return e        

    return name, base


# Converting the log to readable time
def convert_log(amount: int=0) -> dict:
    """
    Converting the log to only include the last x amount of log entries.
    """
    user_id = current_user.user_id

    # User directory path
    user_dir_path = get_user_dir_path(user_id)

    # Opening the log file
    with open(f"{user_dir_path}/log.json", 'r') as file:
        data = json.load(file)
    
    if amount == 0:

        data.reverse()

        # Converting time
        for date in data:
            raw_date = date["date"]
            value = datetime.fromtimestamp(raw_date)
            date["date"] = {
                "date": f"{value:%d/%m/%Y}",
                "time": f"{value:%H:%M:%S}"
            }

        return data

    else:

        # Spliced data
        spliced_data = data[-amount:]

        spliced_data.reverse()

        # Converting time
        for date in spliced_data:
            raw_date = date["date"]
            value = datetime.fromtimestamp(raw_date)
            date["date"] = {
                "date": f"{value:%d/%m/%Y}",
                "time": f"{value:%H:%M:%S}"
            }

        return spliced_data


# Getting the list of currently traded tickers
def get_traded_tickers(user_id: str) -> list:
    """
    Get a list of all the tickers the user has previously traded.
    """
    user_dir_path = get_user_dir_path(user_id)
    return list(os.listdir(f"{user_dir_path}/tickers"))


# Creating a file with the specified ticker (used if traded ticker is new for user)
def create_ticker_file(user_id: str, ticker_name: str) -> None:
    """
    Creating a file for the incoming ticker file.
    """
    user_dir_path = get_user_dir_path(user_id)
    ticker_data = []
    with open(f"{user_dir_path}/tickers/{ticker_name}.json", "w") as file:
        json.dump(ticker_data, file)


# Creating data for the trade
def create_trade_data(profit: float) -> dict:
    """
    Creating data for the current trade based on the profit that the trade accumulated.
    """
    
    time = get_time()
    return {
        "date": time,
        "profit": profit
    }


# Get the current time
def get_time() -> datetime:
    return datetime.timestamp(datetime.now())


# Getting the rank to round the buy/sell order to certain decimal
def get_rank(value: float) -> int:
    """
    Converts a decimal number to reflect the maximum
    shown precision in that number (eg. 0.00010 -> 4)
    """
    for i in range(8):
        result = value * pow(10, i)
        if result == 1:
            return i


# Rounding value down
def round_down(number: float, decimals: int) -> float:
    """
    Rounding a value down to the given decimal index.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor


# See what trades the user currently has going on
def get_open_trades(user_id: str) -> list:
    # User directory
    user_dir_path = get_user_dir_path(user_id)

    # Get list of active trades
    file_list = os.listdir(f"{user_dir_path}/active")

    # Creating the list to store ticker data in
    open_ticker_data = []

    # List of tickers
    ticker_list = []
    for ticker in file_list:
        ticker_list.append(ticker[:-5])
    
    prices = get_ticker_price(ticker_list)

    # Looping over the list of files
    for file in file_list:
        # Name of the ticker from the file name, removing ".json" from the end
        ticker_name = file[:-5]

        # Creating the ticker data
        ticker_data = {
            "ticker": ticker_name
        }

        # Getting the contents of the file
        with open(f"{user_dir_path}/active/{file}", 'r') as ticker_file:
            data = json.load(ticker_file)

        # Adding values to the ticker data object
        ticker_data["entries"] = data["entries"]
        ticker_data["shares"] = data["shares"]
        ticker_data["spent"] = data["spent"]
        try:
            ticker_data["avg_price"] = data["spent"] / data["shares"]
        except:
            ticker_data["avg_price"] = 0
        # Get asset price
        price = prices[ticker_name]
        ticker_data["total_value"] = round(data["shares"] * price, 1)
        ticker_data["profit"] = round(ticker_data["total_value"] - ticker_data["spent"], 1)

        # Create the client
        client = create_client(user_id)
        name = get_tickers()[ticker_name].split("/")[0]
        ticker_name_stripped = ticker_name.replace("/", "")

        ticker_data["name"] = name
        ticker_data["icon"] = f"static/icons/tickers/{name}.png"

        # # Checking how much the client has of the asset
        # with open(f"{get_user_dir_path(user_id)}/active/{ticker_name_stripped}.json") as file:
        #     actual_shares = json.load(file)["shares"]
        
        # min_value = float(client.get_symbol_info(ticker_name)["filters"][1]["minQty"])
        # min_value_strip = float(('%f' % min_value).rstrip('0').rstrip('.'))


        # # Is the current trade valid
        # if actual_shares - ticker_data["shares"] > min_value_strip * 5:
        #     ticker_data["valid_trade"] = False
        # else:
        
        ticker_data["valid_trade"] = True

        # Appending the object to the ticker list
        open_ticker_data.append(ticker_data)

    return open_ticker_data


# Creating a client
def create_client(user_id: str) -> Client:
    try:
        user = User.query.filter_by(user_id=user_id).first() 
        api = user.api
        enc_secret = user.secret
        exchange = user.exchange
        # secret = dec_data(enc_secret)
        secret = enc_secret


        if exchange == 'bin':
            client = Client(api, secret)
        if exchange == 'binus':
            client = Client(api, secret, tld="us")
        return client
    except Exception as e:
        return "Error getting credentials"


# Getting paths of user-specific files
def get_user_dir_path(user_id: str) -> str:
    # Returing the paths to the current user folder
    return f"{os.getcwd()}/app/users/{user_id}"


# See user data
def see_user_data(user_id: str) -> dict:
    with open(f"{get_user_dir_path(user_id)}/data.json", 'r') as file:
        data = json.load(file)
    return data

def write_user_data(user_id: str, new_data: dict) -> None:
    with open(f"{get_user_dir_path(user_id)}/data.json", 'w') as file:
        json.dump(new_data, file)




# Log trade to user
def create_log_entry(user_id, message):
    # Current time
    time = get_time()

    # Creating the log entry
    log_entry = {
        "date": time,
        "message": message
    }


    # Open the user_data file again and dump the "data" contents to it
    with open(f"{get_user_dir_path(user_id)}/log.json", "r") as file:
        data = list(json.load(file))
    
    with open(f"{get_user_dir_path(user_id)}/log.json", "w") as file:
        data.append(log_entry)
        json.dump(data, file)


# Get ticker list
def get_tickers() -> dict:
    current = os.getcwd()
    with open(f"{current}/app/binance_tickers.json", "r") as file:
        data = json.load(file)
    return data




# Function to create data
def create_data(user_id: str) -> None:
    """
    Creating necessary data for the registered user.
    """
    # Getting the current WD
    current_dir = os.getcwd()

    # Creating the requied directories
    os.mkdir(f"{current_dir}/app/users/{user_id}")
    os.mkdir(f"{current_dir}/app/users/{user_id}/active")
    os.mkdir(f"{current_dir}/app/users/{user_id}/tickers")

    # User directory path
    user_dir_path = get_user_dir_path(user_id) 

    # Creating both the log and user data file
    data = {"max_open": 0, "disabled": False}
    with open(f"{user_dir_path}/data.json", "w") as file:
        json.dump(data, file)

    with open(f"{user_dir_path}/log.json", "w") as file:
        json.dump([], file)

    return



# Function to process the incoming signal
def process_signal(side, ticker_name, user_id):
    """
    Processes the incoming webhook signal based on whether
    it is a buy or a sell signal.
    """
    # Define the user
    user = User.query.filter_by(user_id=user_id).first()
    
    # User directory path
    user_dir_path = get_user_dir_path(user_id)

    # Loading data from the user data file
    ticker_data = get_open_trades(user_id)
    
    # Defining user variables
    max_open = user.max_open
    
    # Creating the open list
    open_list = []
    for ticker in ticker_data:
        open_list.append(ticker["ticker"])

    # Checking whether the requested ticker is in the supported list
    try:
        # Ticker data - name and basecurrency separated
        name = split_ticker(ticker_name)[0]
        base = split_ticker(ticker_name)[1]
    except Exception as e:
        return create_log_entry(user_id, f"Invalid ticker name {ticker_name}")

    # Order size
    qty = user.size

    # If the message side is buy
    if side == "buy":
        # If length of list is less than max, validate
        if ticker_name not in open_list and len(open_list) < max_open:
            
            # 1. send order & get order response
            order_response = send_order(user_id, side, ticker_name, qty)

            # If the response is not a dictionary, then there was an error with the order
            if not isinstance(order_response, dict):
                return create_log_entry(user_id, f"Failed to {side} {ticker_name}: {order_response}")
            
            # 2. create object with trade data
            order_data = create_order_data(order_response)

            trade_data = {
                "entries": 1,
                "spent": order_data["spent"],
                "shares": order_data["shares"]
            }

            # 3. create a file with the format "{ticker_name}.json"
            # 4. put trade object inside the file with json.dump()
            with open(f"{user_dir_path}/active/{ticker_name}.json", 'w') as file:
                json.dump(trade_data, file)

            return create_log_entry(user_id, f'Bought {round(order_data["spent"], 1)} {base} of {name}')

        # If value is already in the list, validate
        elif ticker_name in open_list:
            
            #Order response
            order_response = send_order(user_id, side, ticker_name, qty)
            
            if not isinstance(order_response, dict):
                return create_log_entry(user_id, f"Failed to {side} {ticker_name}")

            order_data = create_order_data(order_response)

            # Data for the currently open trade
            with open(f"{user_dir_path}/active/{ticker_name}.json", 'r') as file:
                open_trade = json.load(file)
            
            # Updating the values
            open_trade["entries"] += 1
            open_trade["shares"] += order_data["shares"]
            open_trade["spent"] += order_data["spent"]

            with open(f"{user_dir_path}/active/{ticker_name}.json", 'w') as file:
                json.dump(open_trade, file)
            
            return create_log_entry(user_id, f'Bought {round(order_data["spent"], 1)} of {ticker_name}')



    if side == "sell":
        # Invaldiate if the ticker is not in the list
        if ticker_name not in open_list:
            return
        
        # Getting the order response
        order_response = send_order(user_id, side, ticker_name, qty)
        
        # If the order response is not an error
        if not isinstance(order_response, dict):
            # Removing the ticker listing
            os.remove(f"{user_dir_path}/active/{ticker_name}.json")

            return create_log_entry(user_id, f"Removed {ticker_name} from open list")

        # Removing the ticker listing
        os.remove(f"{user_dir_path}/active/{ticker_name}.json")
        
        # Creating order data
        order_data = create_order_data(order_response)

        # Get the current trade
        current_trade = next(item for item in ticker_data if item["ticker"] == ticker_name)
        profit = current_trade["profit"]
        
        # Get a list of the previously traded tickers
        user_tickers = get_traded_tickers(user_id)

        # Determining whether there is a listing for that ticker already
        value = ""
        try:
            list(filter(lambda x: ticker_name in x, user_tickers))[0]
        except:
            create_ticker_file(user_id, ticker_name)
        
        
        with open(f"{user_dir_path}/tickers/{ticker_name}.json", "r") as file:
            trade_ticker_data = json.load(file)
        
        trade_ticker_data.append(create_trade_data(profit))

        with open(f"{user_dir_path}/tickers/{ticker_name}.json", "w") as file:
            json.dump(trade_ticker_data, file)

        # Actual profit
        exec_profit = round(float(order_response["cummulativeQuoteQty"]) - current_trade['spent'], 1)

        return create_log_entry(user_id, 
            f"Sold {round(order_data['spent'], 1)} {base} of {name} ({(f'{exec_profit}$' if exec_profit <= 0 else f'+{exec_profit}$') if current_trade['valid_trade'] else 'Na'})")
        
        
# Function to send the order
def send_order(user_id, side, ticker_id, qty):
    # Get user credentials
    try:
        client = create_client(user_id)
    except Exception as e:
        create_log_entry(user_id, "Could not validate API keys")
        return e

    # Ticker data - name and basecurrency separated
    name = split_ticker(ticker_id)[0]
    base = split_ticker(ticker_id)[1]

    # Getting the maximum rank
    min_value = float(client.get_symbol_info(ticker_id)['filters'][1]['minQty'])
    min_value_strip = ('%f' % min_value).rstrip('0').rstrip('.')
    rank = get_rank(float(min_value_strip))

    # Getting price data
    price = get_ticker_price([ticker_id])

    # If message is entry alert
    if side == 'buy':
        # If coin is UP or DOWN coin, then it has to be handled differently
        if "UP" in ticker_id or "DOWN" in ticker_id:
            # Calculating the order size
            order_size = round_down(qty / price, rank)

    if side == 'sell':
        # Order size
        order_size = round_down((float(client.get_asset_balance(name)['free'])), rank)

    order_data = ""

    try:
        # Create the order
        if (side == 'sell') or ('UP' in ticker_id or 'DOWN' in ticker_id):
            order_data = client.create_order(symbol=ticker_id, side=side.upper(), type=ORDER_TYPE_MARKET, quantity=order_size)
        else:
            order_data = client.create_order(symbol=ticker_id, side=side.upper(), type=ORDER_TYPE_MARKET, quoteOrderQty=qty)
        
        # Returning response from sent order
        return order_data

    except Exception as e:
        return e


# Function to handle the message
def handle_alert(data):
    user_id = data["id"]
    side = data["side"]
    ticker = data["ticker"]
    process_signal(side, ticker, user_id)

    

    

