from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Nassau Candy | Profitability Intelligence', page_icon='📊', layout='wide')

FACTORIES = {
    "Lot's O' Nuts": (32.881893, -111.768036),
    "Wicked Choccy's": (32.076176, -81.088371),
    'Sugar Shack': (48.11914, -96.18115),
    'Secret Factory': (41.446333, -90.565487),
    'The Other Factory': (35.1175, -89.971107),
}
PRODUCT_FACTORY = {
    'Wonka Bar - Nutty Crunch Surprise': "Lot's O' Nuts",
    'Wonka Bar - Fudge Mallows': "Lot's O' Nuts",
    'Wonka Bar -Scrumdiddlyumptious': "Lot's O' Nuts",
    'Wonka Bar - Scrumdiddlyumptious': "Lot's O' Nuts",
    'Wonka Bar - Milk Chocolate': "Wicked Choccy's",
    'Wonka Bar - Triple Dazzle Caramel': "Wicked Choccy's",
    'Laffy Taffy': 'Sugar Shack', 'SweeTARTS': 'Sugar Shack', 'Nerds': 'Sugar Shack',
    'Fun Dip': 'Sugar Shack', 'Fizzy Lifting Drinks': 'Sugar Shack',
    'Everlasting Gobstopper': 'Secret Factory', 'Hair Toffee': 'The Other Factory',
    'Lickable Wallpaper': 'Secret Factory', 'Wonka Gum': 'Secret Factory', 'Kazookles': 'Secret Factory'
}
REQUIRED = ['Row ID','Order ID','Order Date','Ship Date','Ship Mode','Customer ID','Country/Region','City','State/Province','Postal Code','Division','Region','Product ID','Product Name','Sales','Units','Gross Profit','Cost']

@st.cache_data(show_spinner=False)
def load_data(file_bytes, file_name):
    import io
    if file_name.lower().endswith(('.xlsx','.xls')):
        raw = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raw = pd.read_csv(io.BytesIO(file_bytes))
    return raw

def clean_data(raw):
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise ValueError('Missing required columns: ' + ', '.join(missing_cols))
    for c in ['Product Name','Division','Region','State/Province','Ship Mode']:
        df[c] = df[c].astype('string').str.strip().str.replace(r'\s+', ' ', regex=True)
    for c in ['Order Date','Ship Date']:
        df[c] = pd.to_datetime(df[c], dayfirst=True, errors='coerce')
    for c in ['Sales','Units','Gross Profit','Cost']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    report = {
        'rows_input': len(df), 'duplicate_row_ids': int(df['Row ID'].duplicated().sum()),
        'missing_values': int(df[REQUIRED].isna().sum().sum()),
        'invalid_dates': int(df['Order Date'].isna().sum() + df['Ship Date'].isna().sum()),
        'nonpositive_sales': int((df['Sales'] <= 0).sum()),
        'nonpositive_units': int((df['Units'] <= 0).sum()),
        'negative_cost': int((df['Cost'] < 0).sum()),
        'profit_cost_mismatch': int(((df['Gross Profit'] - (df['Sales'] - df['Cost'])).abs() > 0.02).sum()),
    }
    # Keep raw records visible in QA metrics; analysis excludes rows with missing key numeric/date values or invalid denominators.
    df['Data Issue'] = ''
    conditions = [
        (df['Sales'].isna() | (df['Sales'] <= 0), 'Missing/nonpositive sales'),
        (df['Units'].isna() | (df['Units'] <= 0), 'Missing/nonpositive units'),
        (df['Cost'].isna() | (df['Cost'] < 0), 'Missing/negative cost'),
        (df['Gross Profit'].isna(), 'Missing gross profit'),
        (df['Order Date'].isna(), 'Invalid order date'),
    ]
    for mask, label in conditions:
        df.loc[mask, 'Data Issue'] = df.loc[mask, 'Data Issue'].apply(lambda x: (x + '; ' if x else '') + label)
    report['flagged_rows'] = int((df['Data Issue'] != '').sum())
    analysis = df[(df['Data Issue'] == '')].copy()
    analysis['Gross Margin %'] = np.where(analysis['Sales'] != 0, analysis['Gross Profit'] / analysis['Sales'] * 100, np.nan)
    analysis['Profit per Unit'] = np.where(analysis['Units'] != 0, analysis['Gross Profit'] / analysis['Units'], np.nan)
    analysis['Ship Processing Days'] = (analysis['Ship Date'] - analysis['Order Date']).dt.days
    analysis['Factory'] = analysis['Product Name'].map(PRODUCT_FACTORY)
    return df, analysis, report

def money(v): return f'${v:,.2f}'
def pct(v): return f'{v:,.2f}%'

st.markdown('''<style>
.stApp {background: #f4f7fb;} [data-testid="stSidebar"] {background:#101c34;}
[data-testid="stSidebar"] * {color:#f3f6fb !important;}
.block-container {padding-top:1.5rem; padding-bottom:2rem;}
.kicker {color:#0d9488; font-weight:700; letter-spacing:.08em; font-size:.78rem;}
.main-title {font-size:2.1rem; font-weight:800; color:#14213d; line-height:1.15;}
.subtle {color:#5b6577;}
</style>''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## 🍬 Nassau Candy')
    st.caption('Profitability Intelligence')
    uploaded = st.file_uploader('Upload order dataset', type=['csv','xlsx','xls'])
    default_path = Path(__file__).with_name('dataset.csv')
    if uploaded is not None:
        raw = load_data(uploaded.getvalue(), uploaded.name)
        source_name = uploaded.name
    elif default_path.exists():
        raw = load_data(default_path.read_bytes(), default_path.name)
        source_name = default_path.name
    else:
        raw = None
        source_name = 'No dataset'
    st.divider()
    page = st.radio('Dashboard modules', ['Executive Overview','Product Profitability','Division Performance','Cost & Margin Diagnostics','Profit Concentration','Factory Insights','Data Quality & Export'])

if raw is None:
    st.warning('Upload a CSV or Excel file to begin.')
    st.stop()
try:
    all_rows, df, qa = clean_data(raw)
except Exception as e:
    st.error(str(e)); st.stop()

st.markdown('<div class="kicker">BUSINESS INTELLIGENCE / LIVE FILTERED ANALYTICS</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Nassau Candy Profitability Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Understand what sells, what earns, and where margin risk is hiding.</div>', unsafe_allow_html=True)
st.caption(f'Source: {source_name} · {len(all_rows):,} source rows · Refreshed: {pd.Timestamp.now().strftime("%d %b %Y, %H:%M")}')

# Global filters
with st.container(border=True):
    f1, f2, f3, f4 = st.columns([1.4,1,1.1,1.3])
    valid_dates = df['Order Date'].dropna()
    min_date = valid_dates.min().date() if len(valid_dates) else pd.Timestamp('2020-01-01').date()
    max_date = valid_dates.max().date() if len(valid_dates) else pd.Timestamp.now().date()
    with f1:
        date_range = st.date_input('Order date range', value=(min_date,max_date), min_value=min_date, max_value=max_date)
    with f2:
        divisions = sorted(df['Division'].dropna().unique().tolist())
        chosen_div = st.multiselect('Division', divisions, default=divisions)
    with f3:
        regions = sorted(df['Region'].dropna().unique().tolist())
        chosen_region = st.multiselect('Region', regions, default=regions)
    with f4:
        margin_threshold = st.slider('Margin risk threshold (%)', min_value=0, max_value=80, value=40, step=5)
search = st.text_input('🔎 Search product name or product ID', placeholder='e.g., Wonka Bar or CHO-MIL')

filtered = df.copy()
if isinstance(date_range, (tuple,list)) and len(date_range)==2:
    filtered = filtered[filtered['Order Date'].dt.date.between(date_range[0], date_range[1])]
if chosen_div: filtered = filtered[filtered['Division'].isin(chosen_div)]
else: filtered = filtered.iloc[0:0]
if chosen_region: filtered = filtered[filtered['Region'].isin(chosen_region)]
else: filtered = filtered.iloc[0:0]
if search.strip():
    q=search.strip().casefold()
    filtered=filtered[filtered['Product Name'].str.casefold().str.contains(q,na=False) | filtered['Product ID'].astype(str).str.casefold().str.contains(q,na=False)]
if filtered.empty:
    st.warning('No valid rows match these filters. Adjust the date range, division, region, or product search.')
    st.stop()

sales=filtered['Sales'].sum(); profit=filtered['Gross Profit'].sum(); cost=filtered['Cost'].sum(); units=filtered['Units'].sum()
margin=profit/sales*100 if sales else np.nan
prod = filtered.groupby(['Product ID','Product Name','Division'], dropna=False).agg(Sales=('Sales','sum'), Cost=('Cost','sum'), Profit=('Gross Profit','sum'), Units=('Units','sum'), Orders=('Order ID','nunique')).reset_index()
prod['Gross Margin %']=np.where(prod['Sales']!=0,prod['Profit']/prod['Sales']*100,np.nan)
prod['Profit per Unit']=np.where(prod['Units']!=0,prod['Profit']/prod['Units'],np.nan)
prod['Revenue Contribution %']=np.where(sales!=0,prod['Sales']/sales*100,np.nan)
prod['Profit Contribution %']=np.where(profit!=0,prod['Profit']/profit*100,np.nan)
# Margin volatility is the standard deviation of monthly product-level margins; requires at least two valid months.
monthly_product = filtered.assign(Month=filtered['Order Date'].dt.to_period('M').astype(str)).groupby(['Product ID','Product Name','Division','Month']).agg(MonthSales=('Sales','sum'), MonthProfit=('Gross Profit','sum')).reset_index()
monthly_product['Month Margin %'] = np.where(monthly_product['MonthSales'] != 0, monthly_product['MonthProfit'] / monthly_product['MonthSales'] * 100, np.nan)
volatility = monthly_product.groupby(['Product ID','Product Name','Division'])['Month Margin %'].std().rename('Margin Volatility (pp)').reset_index()
prod = prod.merge(volatility, on=['Product ID','Product Name','Division'], how='left')
prod['Margin Risk']=(prod['Gross Margin %'] < margin_threshold) | (prod['Profit'] < 0)

if page == 'Executive Overview':
    cols=st.columns(5)
    for c,label,value in zip(cols,['Revenue','Gross Profit','Gross Margin','Cost','Units Sold'],[money(sales),money(profit),pct(margin),money(cost),f'{units:,.0f}']): c.metric(label,value)
    st.subheader('Performance at a glance')
    c1,c2=st.columns(2)
    with c1:
        trend=filtered.groupby(filtered['Order Date'].dt.to_period('M').astype(str)).agg(Sales=('Sales','sum'),Profit=('Gross Profit','sum')).reset_index(names='Month')
        long=trend.melt('Month',var_name='Metric',value_name='Amount')
        st.plotly_chart(px.line(long,x='Month',y='Amount',color='Metric',markers=True,title='Monthly revenue and gross profit'),use_container_width=True)
    with c2:
        div=filtered.groupby('Division').agg(Sales=('Sales','sum'),Profit=('Gross Profit','sum')).reset_index()
        st.plotly_chart(px.bar(div,x='Division',y=['Sales','Profit'],barmode='group',title='Revenue vs gross profit by division'),use_container_width=True)
    a,b=st.columns(2)
    with a:
        st.markdown('#### Top products by gross profit')
        st.dataframe(prod.sort_values('Profit',ascending=False)[['Product Name','Division','Sales','Profit','Gross Margin %']].head(7),hide_index=True,use_container_width=True)
    with b:
        st.markdown('#### Margin risk products')
        risk=prod[prod['Margin Risk']].sort_values(['Sales','Gross Margin %'],ascending=[False,True])
        st.dataframe(risk[['Product Name','Division','Sales','Profit','Gross Margin %']].head(7),hide_index=True,use_container_width=True)
    st.info('Margin risk is a screening flag based on the selected threshold or negative profit; review product volume and business context before acting.')

elif page == 'Product Profitability':
    st.subheader('Product-level profitability leaderboard')
    rank_by=st.selectbox('Rank products by',['Gross Profit','Gross Margin %','Sales','Profit per Unit','Revenue Contribution %'])
    show=prod.sort_values(rank_by,ascending=False)
    st.plotly_chart(px.bar(show.head(15).sort_values(rank_by),x=rank_by,y='Product Name',color='Division',orientation='h',title=f'Top products by {rank_by}'),use_container_width=True)
    st.dataframe(show[['Product ID','Product Name','Division','Sales','Cost','Profit','Gross Margin %','Profit per Unit','Revenue Contribution %','Profit Contribution %','Margin Volatility (pp)','Units','Orders']].style.format({'Sales':'${:,.2f}','Cost':'${:,.2f}','Profit':'${:,.2f}','Gross Margin %':'{:.2f}%','Profit per Unit':'${:,.2f}','Revenue Contribution %':'{:.2f}%','Profit Contribution %':'{:.2f}%','Margin Volatility (pp)':'{:.2f}'}),hide_index=True,use_container_width=True)
    st.download_button('Download product leaderboard CSV',show.to_csv(index=False).encode('utf-8'),file_name='product_profitability.csv',mime='text/csv')
    st.markdown('#### Product portfolio matrix')
    st.plotly_chart(px.scatter(prod,x='Sales',y='Gross Margin %',size='Profit',color='Division',hover_name='Product Name',hover_data=['Profit','Units','Profit per Unit'],title='Sales vs gross margin (bubble size = gross profit)'),use_container_width=True)

elif page == 'Division Performance':
    st.subheader('Division performance')
    div=filtered.groupby('Division').agg(Sales=('Sales','sum'),Cost=('Cost','sum'),Profit=('Gross Profit','sum'),Units=('Units','sum'),Products=('Product Name','nunique')).reset_index()
    div['Gross Margin %']=div['Profit']/div['Sales']*100
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(px.bar(div,x='Division',y=['Sales','Profit'],barmode='group',title='Revenue and gross profit'),use_container_width=True)
    with c2: st.plotly_chart(px.bar(div,x='Division',y='Gross Margin %',color='Gross Margin %',title='Weighted gross margin by division'),use_container_width=True)
    st.dataframe(div.sort_values('Profit',ascending=False).style.format({'Sales':'${:,.2f}','Cost':'${:,.2f}','Profit':'${:,.2f}','Gross Margin %':'{:.2f}%'}),hide_index=True,use_container_width=True)
    st.plotly_chart(px.box(filtered,x='Division',y='Gross Margin %',points='outliers',title='Order-level margin distribution by division'),use_container_width=True)

elif page == 'Cost & Margin Diagnostics':
    st.subheader('Cost structure and margin risk')
    c1,c2=st.columns(2)
    with c1: st.plotly_chart(px.scatter(prod,x='Sales',y='Cost',size='Profit',color='Division',hover_name='Product Name',title='Product cost vs sales'),use_container_width=True)
    with c2: st.plotly_chart(px.scatter(prod,x='Sales',y='Gross Margin %',size='Profit',color='Margin Risk',hover_name='Product Name',hover_data=['Cost','Profit','Units'],title='Sales vs margin risk'),use_container_width=True)
    risk=prod.copy()
    risk['Risk Reason']=np.select([risk['Profit']<0,risk['Gross Margin %']<margin_threshold],['Negative gross profit',f'Margin below {margin_threshold}%'],'No threshold breach')
    risk=risk[risk['Margin Risk']].sort_values('Sales',ascending=False)
    st.markdown(f'#### Products flagged for review ({len(risk)})')
    st.dataframe(risk[['Product Name','Division','Sales','Cost','Profit','Gross Margin %','Risk Reason']],hide_index=True,use_container_width=True)
    st.caption('Suggested review: investigate pricing, cost inputs, discounts, and product strategy. This dashboard identifies signals; it cannot prove their cause.')

elif page == 'Profit Concentration':
    st.subheader('Pareto and dependency analysis')
    mode=st.radio('Analyze concentration by',['Revenue','Gross Profit'],horizontal=True)
    metric='Sales' if mode=='Revenue' else 'Profit'
    pareto=prod.sort_values(metric,ascending=False).copy()
    total=pareto[metric].sum()
    if total <= 0:
        st.warning(f'{mode} total is zero or negative; standard cumulative 80% Pareto interpretation is not meaningful for this selection.')
    else:
        pareto['Contribution %']=pareto[metric]/total*100
        pareto['Cumulative %']=pareto['Contribution %'].cumsum()
        reach=(pareto['Cumulative %']>=80).to_numpy().nonzero()[0]
        n=int(reach[0]+1) if len(reach) else len(pareto)
        st.metric(f'Products needed to reach 80% of {mode.lower()}',f'{n} / {len(pareto)}',f'{n/len(pareto)*100:.1f}% of products')
        fig=go.Figure()
        fig.add_bar(x=pareto['Product Name'],y=pareto[metric],name=mode)
        fig.add_scatter(x=pareto['Product Name'],y=pareto['Cumulative %'],name='Cumulative contribution %',yaxis='y2',mode='lines+markers')
        fig.update_layout(title=f'{mode} Pareto analysis',xaxis_title='Product',yaxis_title=mode,yaxis2=dict(title='Cumulative %',overlaying='y',side='right',range=[0,105]),xaxis_tickangle=-45)
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(pareto[['Product Name',metric,'Contribution %','Cumulative %']].style.format({metric:'${:,.2f}','Contribution %':'{:.2f}%','Cumulative %':'{:.2f}%'}),hide_index=True,use_container_width=True)
    geo=filtered.groupby('Region').agg(Sales=('Sales','sum'),Profit=('Gross Profit','sum')).reset_index()
    st.plotly_chart(px.bar(geo,x='Region',y=['Sales','Profit'],barmode='group',title='Regional revenue and profit concentration'),use_container_width=True)
    st.caption('Regional totals are sales/profit concentration indicators, not evidence of congestion or delivery bottlenecks.')

elif page == 'Factory Insights':
    st.subheader('Factory and product association insights')
    factory_rows=filtered[filtered['Factory'].notna()].copy()
    unmatched=filtered[filtered['Factory'].isna()]['Product Name'].drop_duplicates().tolist()
    if factory_rows.empty:
        st.warning('No products in the current selection match the supplied factory mapping.')
    else:
        agg=factory_rows.groupby('Factory').agg(Sales=('Sales','sum'),Cost=('Cost','sum'),Profit=('Gross Profit','sum'),Units=('Units','sum'),Products=('Product Name','nunique')).reset_index()
        agg['Gross Margin %']=agg['Profit']/agg['Sales']*100
        coords=pd.DataFrame([{'Factory':n,'latitude':v[0],'longitude':v[1]} for n,v in FACTORIES.items()])
        agg=coords.merge(agg,on='Factory',how='left').fillna({'Sales':0,'Cost':0,'Profit':0,'Units':0,'Products':0,'Gross Margin %':0})
        st.map(agg.rename(columns={'latitude':'lat','longitude':'lon'}),latitude='lat',longitude='lon',size='Sales')
        st.plotly_chart(px.bar(agg,x='Factory',y=['Sales','Profit'],barmode='group',title='Mapped product performance by associated factory'),use_container_width=True)
        st.dataframe(agg[['Factory','latitude','longitude','Products','Sales','Cost','Profit','Gross Margin %','Units']].style.format({'Sales':'${:,.2f}','Cost':'${:,.2f}','Profit':'${:,.2f}','Gross Margin %':'{:.2f}%'}),hide_index=True,use_container_width=True)
        st.markdown('#### Products included in factory mapping')
        st.dataframe(factory_rows.groupby(['Factory','Division','Product Name']).agg(Sales=('Sales','sum'),Profit=('Gross Profit','sum'),Units=('Units','sum')).reset_index(),hide_index=True,use_container_width=True)
    if unmatched: st.warning('Unmapped product names in current filtered data: ' + ', '.join(unmatched))
    st.info('Factory results are based on the provided product-to-factory correlation. The dataset does not contain an order-level factory or physical shipment route, so this is an association analysis, not verified shipment provenance.')

else:
    st.subheader('Data quality and export')
    st.markdown('#### Validation summary')
    qcols=st.columns(4)
    items=[('Input rows',qa['rows_input']),('Duplicate Row IDs',qa['duplicate_row_ids']),('Missing values',qa['missing_values']),('Flagged rows',qa['flagged_rows']),('Invalid date values',qa['invalid_dates']),('Sales ≤ 0',qa['nonpositive_sales']),('Units ≤ 0',qa['nonpositive_units']),('Profit/cost mismatches',qa['profit_cost_mismatch'])]
    for i,(label,value) in enumerate(items): qcols[i%4].metric(label,f'{value:,}')
    st.caption('A profit/cost mismatch means Gross Profit differs from Sales minus Cost by more than $0.02. Flagged rows are excluded from analysis but remain available in the raw-quality export.')
    st.markdown('#### Rows flagged during cleaning')
    flagged=all_rows[all_rows['Data Issue']!='']
    st.dataframe(flagged,hide_index=True,use_container_width=True)
    st.download_button('Download flagged rows CSV',flagged.to_csv(index=False).encode('utf-8'),file_name='data_quality_flags.csv',mime='text/csv')
    st.download_button('Download currently filtered data CSV',filtered.to_csv(index=False).encode('utf-8'),file_name='filtered_orders.csv',mime='text/csv')
    st.download_button('Download current product metrics CSV',prod.to_csv(index=False).encode('utf-8'),file_name='filtered_product_metrics.csv',mime='text/csv')
    st.markdown('#### Method notes')
    st.write('- Analytics update when filters or the uploaded dataset change.')
    st.write('- Product and division margins use aggregated profit divided by aggregated sales.')
    st.write('- Missing or invalid core numeric/date records are flagged and excluded from analysis; source rows are retained for review.')
    st.write('- Ship Date values should be checked before using shipping lead-time metrics. This dataset contains dates later than the Order Date range by an unusually large interval, so no delivery-efficiency claims are made.')

st.divider()
st.caption('Nassau Candy Profitability Intelligence · Assignment prototype · Analytical findings are descriptive and depend on the selected filters and supplied data.')
