import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime, timedelta

URL = 'http://api.coincap.io/v2/assets'


def get_request(url, params=None):
    return requests.get(url=url, params=params).json()


def get_id_from_coin_symbol(assets, symbol):
    return assets[assets['symbol'] == symbol]['id'].values[0]


def years_ago(years, from_date=None):
    if from_date is None:
        from_date = datetime.now()
    try:
        return from_date.replace(year=from_date.year - years)
    except ValueError:
        # Must be 2/29
        return from_date.replace(month=2, day=28,
                                 year=from_date.year-years)


def timestamp(date_value):
    dt = datetime.combine(date_value, datetime.min.time())
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000)


def interval_detalization(date_from, date_to):
    if date_to - date_from > timedelta(days=120):
        return 'd1'
    elif date_to - date_from > timedelta(days=50):
        return 'h6'
    elif date_to - date_from > timedelta(days=5):
        return 'h1'
    else:
        return 'm15'


def prepare_data(data):
    df = pd.DataFrame(data)
    result = pd.DataFrame()
    result['PRICE'] = df['priceUsd'].astype(float)
    result['TIME'] = pd.to_datetime(df['date'])
    return result


def get_actual_data(assets):
    coin_id = get_id_from_coin_symbol(assets=assets, symbol=st.session_state['coin_symbol'])
    date_from = timestamp(st.session_state['date_from'])
    date_to = timestamp(st.session_state['date_to'])
    request_url = f'{URL}/{coin_id}/history'
    interval = interval_detalization(st.session_state['date_from'], st.session_state['date_to'])
    parameters = {
        'interval': interval,
        'start': date_from,
        'end': date_to,
    }
    grouped_data = prepare_data(get_request(url=request_url, params=parameters)['data'])
    return grouped_data


def main():
    @st.cache
    def get_assets_df():
        return pd.DataFrame(get_request(url=URL)['data'])

    today = date.today()

    if 'date_from' not in st.session_state:
        st.session_state['date_from'] = today - timedelta(weeks=1)
    if 'date_to' not in st.session_state:
        st.session_state['date_to'] = today

    assets_df = get_assets_df()

    st.sidebar.selectbox(
        label='Select an asset',
        key='coin_symbol',
        options=assets_df['symbol'])

    scol1, scol2 = st.sidebar.columns(2)

    minimum_available_date=years_ago(years=11,
                                     from_date=today+timedelta(days=1))

    scol1.date_input(
        label="Date from",
        key='date_from',
        value=st.session_state['date_from'],
        min_value=minimum_available_date,
        max_value=st.session_state['date_to'] - timedelta(days=1)
    )

    scol2.date_input(
        label="Date to",
        key='date_to',
        value=st.session_state['date_to'],
        min_value=st.session_state['date_from'] + timedelta(days=1),
        max_value=today)

    grouped_data = get_actual_data(assets=assets_df)
    st.bar_chart(grouped_data, y='PRICE', x='TIME')

if __name__ == "__main__":
    main()
