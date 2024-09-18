import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="ShisetsuKijunDB", 
    # page_icon=image, 
    layout="wide", 
    initial_sidebar_state="auto", 
    menu_items={
         'Get Help': 'https://www.google.com',
         'Report a bug': "https://www.google.com",
         'About': """
         # 施設基準検索アプリ
         """
     })

# st.set_page_config(
#     page_title="購買DB",
#     page_icon="👋",
# )

# st.sidebar.write("サイドバー")
# st.page_link("pages/01_page_1.py", label="Page 1", icon="1️⃣")
st.markdown("# 施設基準データベースシステム")

st.markdown("### :red[左のサイドバーから機能を選択してください。]" )

# one_hot_table = pd.read_pickle('./data/one_hot_table.pkl')
# one_hot_table_csv = pd.read_csv('./data/one_hot_table.csv')
# st.markdown(one_hot_table_csv['一般'])
# st.markdown(one_hot_table['一般'])


# # セッション状態にデータを保存
# if 'one_hot_table' not in st.session_state:
#     st.session_state.one_hot_table = one_hot_table

# # トップページの表示
# st.write("トップページ")
# st.dataframe(st.session_state.one_hot_table)
