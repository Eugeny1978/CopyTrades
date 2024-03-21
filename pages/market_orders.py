import streamlit as st
from data_base.path_to_base import DATABASE
from manual_market_orders import Accounts, style_amount, style_cost

# В терминале набрать: streamlit run interface.py

coins = ('Liquid', 'Shit')

# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
cols = st.columns([8, 1])
with cols[0]:
    st.header('Создание Рыночных Ордеров Клиенту', anchor=False, divider='red')
with cols[1]:
    type_coins = st.selectbox('Coins:', index=0, options=coins)

accounts = Accounts(DATABASE, type_coins)

account = st.selectbox('Client', index=0, options=accounts.data.keys())
rate = accounts.get_rate(account)
connect = accounts.connect_account(account)
balance = accounts.get_balance(connect)
cost_balance = accounts.get_cost_balance(balance)
sum_cost = accounts.get_sum_cost_balance(cost_balance)
orders = accounts.get_orders(connect)

tab_info, tab_order = st.tabs(['Account Information', 'Market Order'])

with tab_info:
    st.markdown(f"{'#' * 5} Trade Rate: {rate}")
    colA, colB = st.columns([2.3, 1])
    with colA:
        st.markdown(':red[SPOT Balance:]')
        st.dataframe(balance.style.pipe(style_amount), use_container_width=True)
        st.markdown(f':red[COST Balance: | {sum_cost} USDT |]')
        st.dataframe(cost_balance.style.pipe(style_cost), use_container_width=True) #
    with colB:
        st.markdown(':red[Active ORDERS:]')
        st.dataframe(orders, use_container_width=True)
with tab_order:
    with st.form('order', clear_on_submit=True, border=False):
        col_symbol, col_side, col_amount, col_cost, col_button = st.columns(5)
        with col_symbol:
            symbol = st.selectbox('Symbol:', index=None, options=accounts.symbols, placeholder="Choose Symbol")
        with col_side:
            side = st.selectbox('SIDE:', index=None, options=('sell', 'buy'), placeholder="Choose Side")
        with col_amount:
            amount = st.number_input('Amount:', min_value=0.0, value=None, format='%f', placeholder="Set Amount or Cost USDT") # format='%.6f'
        with col_cost:
            cost = st.number_input('Cost USDT:', min_value=10.0, value=None, format='%f', placeholder="Set Amount or Cost USDT") # format='%.6f'
        with col_button:
            # st.markdown('Click after filling in the fields')
            # st.caption('---')
            button = st.form_submit_button('Создать Market Order', use_container_width=True)
            if symbol and side and (cost or amount):
                if amount: volume = f"Amount: {amount}"
                else: volume = f"Cost USDT: {cost}"
                order_message = f"Рыночный Ордер: {symbol} | {side.upper()} | {volume}"
                try:
                    # ttt = 55/0 # для тестов проверил выполнение исключения
                    accounts.create_market_order(connect, symbol, side, amount, cost)
                    st.markdown(f":green[Был создан {order_message}]")
                except:
                    st.markdown(f":red[Сбой Соединения с API Биржи. Не удалось создать {order_message}]")
            else:
                st.markdown(':red[Заполните Все Необходимые Поля, иначе при нажатии Кнопки "Создать Market Order" запрос на биржу отправлен не будет]')
        st.markdown(':red[После ввода значений не нажимайте Enter - сработает обновление страницы!]')