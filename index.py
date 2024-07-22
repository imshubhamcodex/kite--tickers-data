import datetime
import pandas as pd
from dateutil.tz import tzoffset

from colorama import init, Fore, Back, Style
from invoker import (
    prepare_data,
    login_with_enctoken,
    get_instruments_list,
    get_historical_dataset
)
from utilities import findIToken
from logger import printing
print = printing


def main():
    # Login data fetch
    user_id, password, enctoken = prepare_data()

    # Trying login
    kite = login_with_enctoken(enctoken)

    print(Back.GREEN + "Hi", kite.profile()["user_shortname"],", successfully logged in." + Style.RESET_ALL)
    print(" ")

    # Fetching instruments list
    i_list = get_instruments_list(kite)

    ticker = input("Enter instrument name: ")
    iToken = findIToken(ticker, i_list)
    # iToken = "341249" 

    if not iToken:
        print("Invalid iToken")
        print("Exiting")
        return
    
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=1*360)
    interval = "3minute"

    print(f"\n{iToken} -- Downloading data...\n")
    historical_data = get_historical_dataset(kite, iToken, start_date, end_date, interval)
    # for record in historical_data[::-1]:
    #     print(record)

    df = pd.DataFrame(historical_data)
    df['5_EMA'] = df['close'].ewm(span=5, adjust=False).mean()
    # print(df)


    # 5EMA start here  
    # Add columns for trade details
    df['test_candle_index'] = None
    df['trigger_candle_index'] = None
    df['sl'] = None
    df['tp'] = None

    # Iterate through the dataframe
    for i in range(len(df) - 1):
        if df['low'].iloc[i] > df['5_EMA'].iloc[i]:  # Test candle condition
            if df['low'].iloc[i + 1] < df['low'].iloc[i]:  # Trigger candle condition
                sl = df['high'].iloc[i]  # Stop Loss
                tp = df['low'].iloc[i] - 5 * abs(df['low'].iloc[i] - sl)  # Take Profit

                df.at[i, 'test_candle_index'] = i  # Log trade details
                df.at[i, 'trigger_candle_index'] = i + 1
                df.at[i, 'sl'] = sl
                df.at[i, 'tp'] = tp

    # Display trades
    trades_df = df.dropna(subset=['test_candle_index'])
    # print(trades_df)

    win_count = 0
    loss_count = 0
    win_df = []
    loss_df = []

    point_gain = 0
    point_loss = 0

    # Iterate through trades and print corresponding rows
    for i in range(len(trades_df)):
        index = int(trades_df.iloc[i]['test_candle_index'])
        is_success = validate_trade(df, index)

        if(is_success):
            win_count += 1
            win_df.append(df.iloc[index])
            point_gain += abs(df['low'].iloc[index] - df['tp'].iloc[index])
        else:
            loss_count += 1
            loss_df.append(df.iloc[index])
            point_loss += abs(df['sl'].iloc[index] - df['low'].iloc[index])
    
    print(f"Win:{win_count}, Loss:{loss_count}")
    print(f"Point won:{point_gain}, Point Lost:{point_loss}")

    print("\nLoss Dataset:\n")
    for record in loss_df:
        print(record)
        print("-----------------------------------------------------------------")

    print("\nWin Dataset:\n")
    for record in win_df:
        print(record)
        print("-----------------------------------------------------------------")

    



def validate_trade(df, index):
    tp = df['tp'].iloc[index]
    sl = df['sl'].iloc[index]

    is_success = True
    for itr_index in range(index + 1, len(df)):
        if(df['high'].iloc[itr_index] > sl):
            is_success = False
            break
        elif(df['low'].iloc[itr_index] < tp):
            is_success = True
            break
    
    return is_success


    







if __name__ == "__main__":
    init()  # For colorama

    print(Back.RED)
    print("Designed by Shubham @https://github.com/imshubhamcodex/Kite")
    print(Style.RESET_ALL)

    main()
