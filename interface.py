import streamlit as st

# В терминале набрать: streamlit run interface.py



# ЛОГИКА СТРАНИЦЫ

st.set_page_config(layout="wide") # Вся страница вместо узкой центральной колонки
st.header('Купить или Продать по Рынку', anchor=False, divider='red')

account = st.selectbox('Account:', index=None, options=accounts.acc_names, placeholder="Choose an account name", key='account') # , on_change=

