import streamlit as st
from data_base.path_to_base import DATABASE
from manual_market_orders import Accounts, style_amount, style_cost

# В терминале набрать: streamlit run interface.py


coins = ('Liquid', 'Shit')
help_tabs = """Вы можете прокручивать вкладки различнымси способами:
1) Удерживайте SHIFT при использовании прокрутки и наведении курсора мыши на вкладки.
2) Используйте клавиши со стрелками для навигации по вкладкам после выбора одной из них."""

# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
cols = st.columns([8, 1])
with cols[0]:
    st.header('Аккаунты Клиентов', anchor=False, divider='red', help=help_tabs)
with cols[1]:
    type_coins = st.selectbox('Coins:', index=0, options=coins)

accounts = Accounts(DATABASE, type_coins)
tab_names = [name.split(' ')[0] for name in accounts.data.keys()]
tabs = st.tabs(tab_names)

for tab, account in zip(tabs, accounts.data.keys()):
    with tab:
        rate = accounts.get_rate(account)
        connect = accounts.connect_account(account)
        balance = accounts.get_balance(connect)
        cost_balance = accounts.get_cost_balance(balance)
        sum_cost = accounts.get_sum_cost_balance(cost_balance)
        orders = accounts.get_orders(connect)

        st.markdown(f"{'#'*5} {account}     |     Trade Rate: {rate}")

        colA, colB = st.columns([2.3, 1])
        with colA:
            st.markdown(':red[SPOT Balance:]')
            st.dataframe(balance.style.pipe(style_amount), use_container_width=True)
            st.markdown(f':red[COST Balance: | {sum_cost} USDT |]')
            st.dataframe(cost_balance.style.pipe(style_cost), use_container_width=True) #
        with colB:
            st.markdown(':red[Active ORDERS:]')
            st.dataframe(orders, use_container_width=True)


# words1 = [f'word {i}' for i in range(50)]
# words2 = [f'word {i}' for i in range(50,100)]
# tabs1 = st.tabs(words1)
# tabs2 = st.tabs(words2)
# for tab, word in zip(tabs1, words1):
#     with tab:
#         st.write(word)
# for tab, word in zip(tabs2, words2):
#     with tab:
#         st.write(word)





# account = st.selectbox('Account:', index=None, options=accounts.acc_names, placeholder="Choose an account name", key='account') # , on_change=

