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
    """Transform date into milliseconds since Unix Epoch """
    dt = datetime.combine(date_value, datetime.min.time())
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000)


def change_interval_for_pandas(interval):
    return interval[1:] + interval[0].upper().replace('M', 'T')


def interval_detalization(date_from, date_to):
    """Setting detalization level to get enough data for dashboard"""
    if date_to - date_from > timedelta(days=120):
        return 'd1'
    elif date_to - date_from > timedelta(days=30):
        return 'h6'
    elif date_to - date_from > timedelta(days=5):
        return 'h1'
    else:
        return 'm15'


def prepare_data(data, interval):
    """Correct dtypes and filling gaps for showing with default streamlit bar_chart"""
    df = pd.DataFrame(data)
    df['PRICE'] = df['priceUsd'].astype(float)
    df['TIME'] = pd.to_datetime(df['date'])

    dr = pd.date_range(start=df['TIME'].min(),
                       end=df['TIME'].max(),
                       freq=interval,
                       name='TIME')
    df = df.drop(columns=['priceUsd', 'time', 'date'])
    df = df.set_index("TIME").reindex(dr).ffill().bfill().reset_index()
    return df


def get_history_data(assets):
    """Prepare request to get history data from COINCAP, and convert it to streamlit bar_chart"""
    coin_id = get_id_from_coin_symbol(assets=assets, symbol=st.session_state['coin_symbol'])

    date_from = timestamp(st.session_state['date_from'])
    date_to = timestamp(st.session_state['date_to'])
    interval = interval_detalization(st.session_state['date_from'], st.session_state['date_to'])

    request_url = f'{URL}/{coin_id}/history'
    parameters = {
        'interval': interval,
        'start': date_from,
        'end': date_to,
    }

    response = get_request(url=request_url, params=parameters)

    return prepare_data(data=response['data'],
                        interval=change_interval_for_pandas(interval))


@st.cache
def get_assets_df():
    return pd.DataFrame(get_request(url=URL)['data'])


def main():
    assets_df = get_assets_df()

    today = date.today()
    minimum_available_date = years_ago(years=11,
                                       from_date=today+timedelta(days=1))

    if 'date_from' not in st.session_state:
        st.session_state['date_from'] = today - timedelta(weeks=40)
    if 'date_to' not in st.session_state:
        st.session_state['date_to'] = today

    st.sidebar.selectbox(
        label='Select an asset',
        key='coin_symbol',
        options=assets_df['symbol'])

    sidebar_col1, sidebar_col2 = st.sidebar.columns(2)

    sidebar_col1.date_input(
        label="Date from",
        key='date_from',
        value=st.session_state['date_from'],
        min_value=minimum_available_date,
        max_value=st.session_state['date_to'] - timedelta(days=1)
    )

    sidebar_col2.date_input(
        label="Date to",
        key='date_to',
        value=st.session_state['date_to'],
        min_value=st.session_state['date_from'] + timedelta(days=1),
        max_value=today)

    st.bar_chart(
        data=get_history_data(assets=assets_df),
        x='TIME',
        y='PRICE')


if __name__ == "__main__":
    main()
