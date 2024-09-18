import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_js_eval import streamlit_js_eval

#########################################################################

# 各地方厚生局から毎月公開される施設基準申請状況のExcelからデータを集計し

# 施設基準の類似施設を抽出する

#########################################################################


# セッション状態からデータを取得（今回はpickleファイルからロード）
one_hot_table = pd.read_pickle('/home/shisetsubm/dev/one_hot_table.pkl')

# 病床数のカラム
bed_columns = ['その他', '一般', '一般（特例）', '介護', '感染', '特定', '療養', '精神', '結核']

# 除外したいラベルのリスト
excluded_labels = ['都道府県コード', '都道府県名', '区分', '医療機関番号', '併設医療機関番号', '医療機関記号番号',
                   '医療機関名称', '医療機関所在地（郵便番号）', '医療機関所在地（住所）', '電話番号', 'FAX番号', '登録日', '病床数']

# 比較に使用するカラムを選択
comparison_columns = [col for col in one_hot_table.columns if col not in excluded_labels + bed_columns]
# # bed_columnsのどれかに1以上の値がある行だけを残す
# one_hot_table = one_hot_table[(one_hot_table[bed_columns] > 0).any(axis=1)]

# 各施設の '施設基準取得数' を作成
# one_hot_table['施設基準取得数'] = (one_hot_table[comparison_columns] >= 1).sum(axis=1)

# 都道府県名カラムからユニークなリストを作成
prefectures = one_hot_table['都道府県名'].unique().tolist()

st.set_page_config(
    page_title="ShisetsuKijunDB", 
    layout="wide", 
    initial_sidebar_state="auto", 
    menu_items={
        'Get Help': 'https://www.google.com',
        'Report a bug': "https://www.google.com",
        'About': """
        # 施設基準データベースアプリ
        """
    })

st.markdown("## 施設基準ベンチマーク検索")

########################[ sidebar ]########################

st.sidebar.write(' :sunglasses: ※※※　:red[検索条件入力]　※※※  :sunglasses:')

# 都道府県名選択 #####################################################
selected_prefecture_mei = st.sidebar.selectbox(
    "都道府県名を選択", prefectures, index=None, placeholder="プルダウンから選択", help='都道府県名の一部を入力すると候補が絞られます。'
)

# 施設名選択 #####################################################
shisetsu_list = one_hot_table[one_hot_table['都道府県名'] == selected_prefecture_mei]['医療機関名称'].tolist()
selected_shisetsu_mei = st.sidebar.selectbox(
    "施設名を選択", shisetsu_list, index=None, placeholder="プルダウンから選択", help='施設名の一部を入力すると候補が絞られます。'
)

# 施設名が選択されていない場合、実行を停止
if not selected_shisetsu_mei:
    st.warning("施設名が選択されていません。施設名を選択してください。")
    st.stop()

# ターゲット施設のデータを取得
selected_shisetsh_data = one_hot_table[
    (one_hot_table['医療機関名称'] == selected_shisetsu_mei) & 
    (one_hot_table['都道府県名'] == selected_prefecture_mei)
]

# 病床数のフィルタリング関数
def filter_by_bed_category(df, target_record, bed_columns, lower_ratio, upper_ratio):
    if target_record.empty:
        st.warning("ターゲット施設のデータが見つかりませんでした。")
        return pd.DataFrame()  # 空のデータフレームを返す

    if isinstance(target_record, pd.DataFrame):
        target_record = target_record.iloc[0]

    target_bed_values = target_record[bed_columns]
    non_zero_columns = [col for col in bed_columns if target_bed_values[col] > 0]

    conditions = []
    for col in non_zero_columns:
        target_value = target_bed_values[col]
        lower_bound = target_value * lower_ratio
        upper_bound = target_value * upper_ratio
        condition = (df[col] >= lower_bound) & (df[col] <= upper_bound)
        conditions.append(condition)

    if conditions:
        final_condition = pd.concat(conditions, axis=1).all(axis=1)
        df_filtered = df[final_condition]
    else:
        df_filtered = df.copy()

    return df_filtered

# コサイン類似度フィルタリング関数
def filter_by_cosine_similarity(df, target_record, bed_columns, threshold_similarity):
    if target_record.empty:
        st.warning("ターゲット施設のデータが見つかりませんでした。")
        return pd.DataFrame()  # 空のデータフレームを返す

    if isinstance(target_record, pd.DataFrame):
        target_record = target_record.iloc[0]

    target_bed_values = target_record[bed_columns].values.reshape(1, -1)
    df_bed_values = df[bed_columns].values
    similarities = cosine_similarity(target_bed_values, df_bed_values)[0]
    df_filtered = df[similarities >= threshold_similarity]

    return df_filtered

# サイドバーで範囲を指定
lower_ratio = st.sidebar.number_input("病床数適合率の下限％", value=50, min_value=0, max_value=100) / 100
upper_ratio = st.sidebar.number_input("病床数適合率の上限％", value=150, min_value=100, max_value=200) / 100

# コサイン類似度の閾値を設定
threshold_similarity = st.sidebar.slider("病症種構成類似度の閾値", 0.0, 1.0, 0.8)

# match_rateの下限値を設定
threshold_match_rate = st.sidebar.number_input("施設基準数の適合率の下限％", value=75) / 100

# ターゲット施設のデータが空かどうか確認
if selected_shisetsh_data.empty:
    st.error("選択した施設のデータが存在しません。別の施設を選択してください。")
    st.stop()

# 1. 病床区分別にフィルターをかける
df_filtered_beds = filter_by_bed_category(one_hot_table, selected_shisetsh_data, bed_columns, lower_ratio, upper_ratio)

# 2. 病床フィルタリング後のデータにコサイン類似度フィルターをかける
if df_filtered_beds.empty:
    st.error("病床数フィルタでデータが見つかりませんでした。条件を見直してください。")
    st.stop()

df_filtered_cosine = filter_by_cosine_similarity(df_filtered_beds, selected_shisetsh_data, bed_columns, threshold_similarity)

# コサイン類似度フィルタ結果が空の場合の処理
if df_filtered_cosine.empty:
    st.error("コサイン類似度フィルタでデータが見つかりませんでした。条件を見直してください。")
    st.stop()

# 値が0でない比較対象カラムを選択
target_positive_columns = [col for col in comparison_columns if (selected_shisetsh_data[col] > 0).any()]

# 比較対象のカラムでフィルター後のデータフレームを作成
df_reduced = df_filtered_cosine[target_positive_columns]

# 各レコードとの一致数をカウントし、適合率を計算
def calculate_match_rate(row):
    matched_count = sum(row[col] == selected_shisetsh_data.iloc[0][col] for col in target_positive_columns)
    match_rate = matched_count / len(target_positive_columns) if len(target_positive_columns) > 0 else 0
    return matched_count, match_rate

# 各レコードに対して一致数と適合率を計算
df_filtered_cosine[['施設基準適合数', '施設基準適合率（％）']] = df_reduced.apply(calculate_match_rate, axis=1, result_type='expand')

# 適合率を100倍にして小数点1桁に丸める
df_filtered_cosine['施設基準適合率（％）'] = (df_filtered_cosine['施設基準適合率（％）'] * 100).round(1)

# 閾値以上の適合率を持つデータを抽出
df_filtered_cosine = df_filtered_cosine[df_filtered_cosine['施設基準適合率（％）'] >= threshold_match_rate * 100]

# matched_count (施設基準適合数) と match_rate (施設基準適合率) を7列目と8列目に挿入
cols = df_filtered_cosine.columns.tolist()
cols.insert(7, cols.pop(cols.index('施設基準適合数')))
cols.insert(8, cols.pop(cols.index('施設基準適合率（％）')))
# '施設基準取得数' を 9 列目に挿入
cols.insert(9, cols.pop(cols.index('施設基準取得数')))

# 新しい列順にデータフレームを並べ替える
df_filtered_cosine = df_filtered_cosine[cols]

st.write('＊＊＊＊＊＊')
st.write('横並び版')
st.write('＊＊＊＊＊＊')

# 結果の表示
st.write('## 条件マッチ施設数', len(df_filtered_cosine))
# 結果の表示（データフレーム）
st.dataframe(df_filtered_cosine.sort_values('施設基準適合率（％）', ascending=False).reset_index(drop=True))

st.write('＊＊＊＊＊＊')
st.write('縦並び版')
st.write('＊＊＊＊＊＊')

# 結果の表示（データフレーム）
st.dataframe(df_filtered_cosine.sort_values('施設基準適合率（％）', ascending=False).reset_index(drop=True).T)

if st.button("ページ全体リセット", key="reset0"):
    streamlit_js_eval(js_expressions="parent.window.location.reload()")

if st.sidebar.button("ページ全体リセット", key="reset1"):
    streamlit_js_eval(js_expressions="parent.window.location.reload()")
