# Extracted verbatim from notebooks/la_permit_analysis.ipynb (final cell). Runs as a Streamlit in Snowflake app; requires the course Snowflake database.
# LA Building Permits Dashboard - Complete Analysis
# Interactive Streamlit App covering all 5 analyses

import streamlit as st
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session

# Get Snowflake session
session = get_active_session()
session.sql("USE ROLE TRAINING_ROLE").collect() 
session.sql("USE DATABASE LA_PERMIT_DATA").collect()
session.sql("USE SCHEMA PUBLIC").collect()

# ============================================================================
# LOAD AND CLEAN DATA
# ============================================================================
@st.cache_data
def load_data():
    records = session.table("PERMIT_RECORDS").to_pandas()
    census_tracts = session.table("CENSUS_TRACTS").to_pandas()
    contractors = session.table("MASTER_LICENSE").to_pandas()
    
    for col in ["ISSUE_DATE", "STATUS_DATE"]:
        records[col] = pd.to_datetime(records[col], errors="coerce")
    
    records["VALUATION"] = pd.to_numeric(
        records["VALUATION"].astype(str).str.replace("$", "").str.replace(",", ""),
        errors="coerce"
    )
    
    records["year"] = records["ISSUE_DATE"].dt.year
    records["month"] = records["ISSUE_DATE"].dt.month
    records["month_year"] = records["ISSUE_DATE"].dt.to_period('M').astype(str)
    
    records = records[(records["year"] >= 2020) & (records["year"] <= 2024)].copy()
    
    return records, census_tracts, contractors

with st.spinner("Loading data from Snowflake..."):
    records, census_tracts, contractors = load_data()

# ============================================================================
# DASHBOARD HEADER
# ============================================================================
st.title("🏗️ LA Building Permits Dashboard (2020-2024)")
st.markdown("### Understanding LA's Construction Landscape: Where, What, How Much, and Who")
st.markdown("*Comprehensive analysis covering temporal trends, geographic patterns, work types, valuations, and contractor landscape*")
st.markdown("---")

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
st.sidebar.header("🔍 Filters")

years = sorted(records['year'].dropna().unique())
selected_years = st.sidebar.multiselect(
    "Select Years",
    options=years,
    default=years
)

permit_types = ['All'] + sorted(records['PERMIT_TYPE'].dropna().unique().tolist())
selected_permit_type = st.sidebar.selectbox(
    "Permit Type",
    options=permit_types
)

zip_codes = ['All'] + sorted(records['ZIP_CODE'].dropna().astype(str).unique().tolist())
selected_zip = st.sidebar.selectbox(
    "ZIP Code",
    options=zip_codes
)

min_val, max_val = st.sidebar.slider(
    "Valuation Range ($)",
    min_value=0,
    max_value=int(records['VALUATION'].quantile(0.99)),
    value=(0, int(records['VALUATION'].quantile(0.95))),
    step=10000,
    format="$%d"
)

# Apply filters
if len(selected_years) > 0:
    filtered_data = records[records['year'].isin(selected_years)].copy()
else:
    filtered_data = records.copy()

if selected_permit_type != 'All':
    filtered_data = filtered_data[filtered_data['PERMIT_TYPE'] == selected_permit_type]

if selected_zip != 'All':
    filtered_data = filtered_data[filtered_data['ZIP_CODE'].astype(str) == selected_zip]

filtered_data = filtered_data[
    (filtered_data['VALUATION'] >= min_val) & 
    (filtered_data['VALUATION'] <= max_val)
].copy()

# Recreate month_year column after filtering
filtered_data['month_year'] = filtered_data['ISSUE_DATE'].dt.to_period('M').astype(str)

# ============================================================================
# SIDEBAR METRICS
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Filtered Data Summary")
st.sidebar.metric("Total Permits", f"{len(filtered_data):,}")
st.sidebar.metric("Total Valuation", f"${filtered_data['VALUATION'].sum()/1e9:.2f}B")
st.sidebar.metric("Avg Valuation", f"${filtered_data['VALUATION'].mean():,.0f}")
st.sidebar.metric("Median Valuation", f"${filtered_data['VALUATION'].median():,.0f}")

# ============================================================================
# KEY METRICS CARDS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📋 Total Permits",
        value=f"{len(filtered_data):,}"
    )

with col2:
    st.metric(
        label="💰 Total Investment",
        value=f"${filtered_data['VALUATION'].sum()/1e9:.2f}B"
    )

with col3:
    st.metric(
        label="📍 Unique ZIP Codes",
        value=f"{filtered_data['ZIP_CODE'].nunique():,}"
    )

with col4:
    st.metric(
        label="👷 Unique Contractors",
        value=f"{filtered_data['LICENSE_NUM'].nunique():,}"
    )

st.markdown("---")

# ============================================================================
# ANALYSIS 1: TRENDS OVER TIME
# ============================================================================
st.header("📈 Analysis 1: Building Permit Trends (2020-2024)")
st.markdown("*Setting the temporal context - understanding WHEN construction activity occurs*")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Total Permits Issued per Year")
    permits_by_year = filtered_data.groupby('year').size().reset_index(name='count')
    st.bar_chart(permits_by_year.set_index('year')['count'])
    
    # Show year-over-year change
    if len(permits_by_year) > 1:
        pct_change = ((permits_by_year['count'].iloc[-1] - permits_by_year['count'].iloc[0]) / permits_by_year['count'].iloc[0]) * 100
        st.info(f"📊 Change from {permits_by_year['year'].iloc[0]} to {permits_by_year['year'].iloc[-1]}: {pct_change:+.1f}%")

with col2:
    st.subheader("Top 5 Permit Types - Trends Over Time")
    top_5_types = filtered_data['PERMIT_TYPE'].value_counts().head(5).index
    trend_data = filtered_data[filtered_data['PERMIT_TYPE'].isin(top_5_types)].groupby(['year', 'PERMIT_TYPE']).size().unstack(fill_value=0)
    st.line_chart(trend_data)

# Monthly trends
st.subheader("Monthly Permit Activity Trend")
monthly_data = filtered_data.groupby('month_year').size().reset_index(name='count')
st.line_chart(monthly_data.set_index('month_year')['count'])

# Valuation by year
col1, col2 = st.columns(2)
with col1:
    st.subheader("Total Valuation by Year")
    valuation_by_year = filtered_data.groupby('year')['VALUATION'].sum().reset_index()
    valuation_by_year['VALUATION_B'] = valuation_by_year['VALUATION'] / 1e9
    st.bar_chart(valuation_by_year.set_index('year')['VALUATION_B'])

with col2:
    st.subheader("Year-by-Year Summary")
    summary_by_year = filtered_data.groupby('year').agg({
        'PCIS_PERMIT_NUM': 'count',
        'VALUATION': ['sum', 'mean', 'median']
    }).round(0)
    summary_by_year.columns = ['Permits', 'Total Val ($)', 'Avg Val ($)', 'Median Val ($)']
    summary_by_year['Total Val ($)'] = summary_by_year['Total Val ($)'].apply(lambda x: f"${x/1e9:.2f}B")
    summary_by_year['Avg Val ($)'] = summary_by_year['Avg Val ($)'].apply(lambda x: f"${x:,.0f}")
    summary_by_year['Median Val ($)'] = summary_by_year['Median Val ($)'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(summary_by_year, use_container_width=True)

st.markdown("---")

# ============================================================================
# ANALYSIS 2: GEOGRAPHIC DISTRIBUTION
# ============================================================================
st.header("🗺️ Analysis 2: Geographic Distribution - Most Active ZIP Codes")
st.markdown("*Understanding WHERE construction activity concentrates in LA*")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 15 ZIP Codes by Number of Permits")
    top_zips_count = filtered_data['ZIP_CODE'].value_counts().head(15).reset_index()
    top_zips_count.columns = ['ZIP_CODE', 'Count']
    st.bar_chart(top_zips_count.set_index('ZIP_CODE')['Count'])
    
    # Show top 5 in table
    st.markdown("**Top 5 ZIP Codes:**")
    st.dataframe(top_zips_count.head(5), hide_index=True, use_container_width=True)

with col2:
    st.subheader("Top 15 ZIP Codes by Total Project Valuation")
    top_zips_val = filtered_data.groupby('ZIP_CODE')['VALUATION'].sum().sort_values(ascending=False).head(15).reset_index()
    top_zips_val['VALUATION_M'] = top_zips_val['VALUATION'] / 1e6
    st.bar_chart(top_zips_val.set_index('ZIP_CODE')['VALUATION_M'])
    
    # Show top 5 in table
    st.markdown("**Top 5 by Valuation:**")
    top_5_val_display = top_zips_val.head(5)[['ZIP_CODE', 'VALUATION']].copy()
    top_5_val_display['VALUATION'] = top_5_val_display['VALUATION'].apply(lambda x: f"${x/1e6:.1f}M")
    top_5_val_display.columns = ['ZIP Code', 'Total Valuation']
    st.dataframe(top_5_val_display, hide_index=True, use_container_width=True)

# Geographic concentration insight
total_permits = len(filtered_data)
top_15_permits = top_zips_count['Count'].sum()
concentration_pct = (top_15_permits / total_permits) * 100 if total_permits > 0 else 0
st.info(f"🎯 **Geographic Concentration**: Top 15 ZIP codes account for {concentration_pct:.1f}% of all permits")

# Map visualization
st.subheader("Permit Locations Map")
if 'LATITUDE_LONGITUDE' in filtered_data.columns:
    coords_data = filtered_data['LATITUDE_LONGITUDE'].dropna()
    if len(coords_data) > 0:
        coords = coords_data.str.extract(r'\(([-\d.]+) ([-\d.]+)\)')
        coords.columns = ['lon', 'lat']
        coords = coords.astype(float).dropna()
        
        if len(coords) > 0:
            st.map(coords.head(5000))
        else:
            st.info("No valid coordinates available for mapping")
    else:
        st.info("No coordinate data available")
else:
    st.info("Coordinate data not available in dataset")

st.markdown("---")

# ============================================================================
# ANALYSIS 3: PERMIT TYPES - WHAT TYPES OF WORK
# ============================================================================
st.header("🔧 Analysis 3: What Types of Work Are People Doing?")
st.markdown("*Understanding the nature of construction activity - repairs, additions, new construction*")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Permit Types")
    top_permit_types = filtered_data['PERMIT_TYPE'].value_counts().head(10).reset_index()
    top_permit_types.columns = ['Permit Type', 'Count']
    top_permit_types['Percentage'] = (top_permit_types['Count'] / len(filtered_data) * 100).round(1)
    
    st.bar_chart(top_permit_types.set_index('Permit Type')['Count'])
    
    # Show percentage breakdown
    st.markdown("**Distribution:**")
    display_types = top_permit_types.copy()
    display_types['Percentage'] = display_types['Percentage'].apply(lambda x: f"{x}%")
    st.dataframe(display_types, hide_index=True, use_container_width=True)

with col2:
    st.subheader("Permit Categories Distribution")
    if 'PERMIT_CATEGORY' in filtered_data.columns:
        permit_cat = filtered_data['PERMIT_CATEGORY'].value_counts().head(8).reset_index()
        permit_cat.columns = ['Category', 'Count']
        st.bar_chart(permit_cat.set_index('Category')['Count'])
    else:
        st.info("Permit category data not available")

# Key insights
most_common = filtered_data['PERMIT_TYPE'].mode()[0] if len(filtered_data) > 0 else "N/A"
most_common_count = filtered_data['PERMIT_TYPE'].value_counts().iloc[0] if len(filtered_data) > 0 else 0
most_common_pct = (most_common_count / len(filtered_data) * 100) if len(filtered_data) > 0 else 0

st.info(f"📌 **Most Common Permit Type**: {most_common} ({most_common_count:,} permits, {most_common_pct:.1f}% of total)")

# Permit type by year
st.subheader("How Permit Types Have Changed Over Time")
top_types_for_trend = filtered_data['PERMIT_TYPE'].value_counts().head(5).index
trend_by_type = filtered_data[filtered_data['PERMIT_TYPE'].isin(top_types_for_trend)].groupby(['year', 'PERMIT_TYPE']).size().unstack(fill_value=0)
st.line_chart(trend_by_type)

st.markdown("---")

# ============================================================================
# ANALYSIS 4: PROJECT VALUATION ANALYSIS
# ============================================================================
st.header("💵 Analysis 4: Project Size and Investment Analysis")
st.markdown("*Understanding HOW MUCH people invest in construction projects*")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Mean Valuation", f"${filtered_data['VALUATION'].mean():,.0f}")
with col2:
    st.metric("Median Valuation", f"${filtered_data['VALUATION'].median():,.0f}")
with col3:
    st.metric("Total Investment", f"${filtered_data['VALUATION'].sum()/1e9:.2f}B")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Project Valuation Distribution")
    bins = [0, 5000, 10000, 25000, 50000, 100000, 500000, float('inf')]
    labels = ['<$5K', '$5K-10K', '$10K-25K', '$25K-50K', '$50K-100K', '$100K-500K', '>$500K']
    filtered_data['val_bin'] = pd.cut(filtered_data['VALUATION'], bins=bins, labels=labels)
    val_dist = filtered_data['val_bin'].value_counts().sort_index()
    st.bar_chart(val_dist)
    
    # Show percentage breakdown
    val_dist_pct = (val_dist / val_dist.sum() * 100).round(1)
    dist_df = pd.DataFrame({
        'Range': val_dist.index,
        'Count': val_dist.values,
        'Percentage': val_dist_pct.values
    })
    dist_df['Percentage'] = dist_df['Percentage'].apply(lambda x: f"{x}%")
    st.dataframe(dist_df, hide_index=True, use_container_width=True)

with col2:
    st.subheader("Valuation Statistics")
    stats_df = pd.DataFrame({
        'Metric': ['Mean', 'Median', '25th Percentile', '75th Percentile', '90th Percentile', 'Max'],
        'Value': [
            f"${filtered_data['VALUATION'].mean():,.0f}",
            f"${filtered_data['VALUATION'].median():,.0f}",
            f"${filtered_data['VALUATION'].quantile(0.25):,.0f}",
            f"${filtered_data['VALUATION'].quantile(0.75):,.0f}",
            f"${filtered_data['VALUATION'].quantile(0.90):,.0f}",
            f"${filtered_data['VALUATION'].max():,.0f}"
        ]
    })
    st.dataframe(stats_df, hide_index=True, use_container_width=True)
    
    # High-value projects insight
    high_value_count = len(filtered_data[filtered_data['VALUATION'] > 500000])
    high_value_pct = (high_value_count / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
    st.info(f"💎 **High-Value Projects (>$500K)**: {high_value_count:,} permits ({high_value_pct:.1f}%)")

st.subheader("Median Project Valuation by Permit Type (Top 10)")
top_types = filtered_data['PERMIT_TYPE'].value_counts().head(10).index
val_by_type = filtered_data[filtered_data['PERMIT_TYPE'].isin(top_types)].groupby('PERMIT_TYPE')['VALUATION'].median().sort_values(ascending=False)
st.bar_chart(val_by_type)

# Show table
val_by_type_df = val_by_type.reset_index()
val_by_type_df.columns = ['Permit Type', 'Median Valuation']
val_by_type_df['Median Valuation'] = val_by_type_df['Median Valuation'].apply(lambda x: f"${x:,.0f}")
st.dataframe(val_by_type_df, hide_index=True, use_container_width=True)

st.markdown("---")

# ============================================================================
# ANALYSIS 5: CONTRACTOR ANALYSIS
# ============================================================================
st.header("👷 Analysis 5: Most Active Contractors")
st.markdown("*Understanding WHO executes LA's construction projects*")

# Merge contractor info
top_15_licenses = filtered_data['LICENSE_NUM'].value_counts().head(15)
top_15_df = pd.DataFrame({
    'LICENSE_NUM': top_15_licenses.index,
    'Permit_Count': top_15_licenses.values
})

# Merge with contractor names
contractors_merged = top_15_df.merge(
    contractors[['LICENSE_NO', 'BUSINESS_NAME', 'CITY', 'PRIMARY_STATUS']],
    left_on='LICENSE_NUM',
    right_on='LICENSE_NO',
    how='left'
)
contractors_merged['BUSINESS_NAME'] = contractors_merged['BUSINESS_NAME'].fillna('Unknown/Not Listed')

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 15 Contractors by Number of Permits")
    display_contractors = contractors_merged[['BUSINESS_NAME', 'CITY', 'Permit_Count']].copy()
    display_contractors.columns = ['Business Name', 'City', 'Permit Count']
    st.dataframe(display_contractors, hide_index=True, use_container_width=True)
    
    # Show chart
    chart_data = contractors_merged[['BUSINESS_NAME', 'Permit_Count']].set_index('BUSINESS_NAME')
    st.bar_chart(chart_data)

with col2:
    st.subheader("Top 15 Contractors by Total Project Valuation")
    top_contractors_val = filtered_data.groupby('LICENSE_NUM')['VALUATION'].sum().sort_values(ascending=False).head(15).reset_index()
    
    # Merge with contractor names
    contractors_val_merged = top_contractors_val.merge(
        contractors[['LICENSE_NO', 'BUSINESS_NAME', 'CITY']],
        left_on='LICENSE_NUM',
        right_on='LICENSE_NO',
        how='left'
    )
    contractors_val_merged['BUSINESS_NAME'] = contractors_val_merged['BUSINESS_NAME'].fillna('Unknown/Not Listed')
    
    display_val = contractors_val_merged[['BUSINESS_NAME', 'CITY', 'VALUATION']].copy()
    display_val['VALUATION'] = display_val['VALUATION'].apply(lambda x: f"${x/1e6:.2f}M")
    display_val.columns = ['Business Name', 'City', 'Total Valuation']
    st.dataframe(display_val, hide_index=True, use_container_width=True)
    
    # Show chart
    chart_val = contractors_val_merged[['BUSINESS_NAME', 'VALUATION']].copy()
    chart_val['VALUATION_M'] = chart_val['VALUATION'] / 1e6
    chart_val = chart_val.set_index('BUSINESS_NAME')['VALUATION_M']
    st.bar_chart(chart_val)

# Contractor concentration metrics
total_contractors = filtered_data['LICENSE_NUM'].nunique()
top_15_count = top_15_df['Permit_Count'].sum()
top_15_pct = (top_15_count / len(filtered_data) * 100) if len(filtered_data) > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Contractors", f"{total_contractors:,}")
with col2:
    st.metric("Top 15 Permit Share", f"{top_15_pct:.1f}%")
with col3:
    permits_with_license = len(filtered_data[filtered_data['LICENSE_NUM'].notna()])
    license_coverage = (permits_with_license / len(filtered_data) * 100) if len(filtered_data) > 0 else 0
    st.metric("Permits with License", f"{license_coverage:.1f}%")

st.info(f"🏢 **Market Concentration**: Top 15 contractors handle {top_15_pct:.1f}% of permits, indicating a {'highly concentrated' if top_15_pct > 25 else 'fragmented'} contractor landscape")

st.markdown("---")

# ============================================================================
# SECTION 6: DETAILED DATA EXPLORER
# ============================================================================
st.header("📊 Detailed Permit Data Explorer")

st.write(f"Showing {min(1000, len(filtered_data)):,} of {len(filtered_data):,} permits")

display_cols = [
    'PCIS_PERMIT_NUM', 'ISSUE_DATE', 'STATUS', 'PERMIT_TYPE', 
    'VALUATION', 'ZIP_CODE', 'ADDRESS_START', 'STREET_NAME',
    'AI_DESCRIPTION', 'LICENSE_NUM'
]

display_cols = [col for col in display_cols if col in filtered_data.columns]

st.dataframe(
    filtered_data[display_cols].head(1000).sort_values('ISSUE_DATE', ascending=False),
    use_container_width=True,
    hide_index=True
)

csv = filtered_data[display_cols].to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name="la_permits_filtered.csv",
    mime="text/csv"
)

# ============================================================================
# FOOTER WITH INSIGHTS
# ============================================================================
st.markdown("---")
st.markdown("### 🔑 Key Insights from All 5 Analyses")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.markdown("""
    **1. Temporal Trends (Analysis 1)**
    - Construction activity showed growth from 2020-2022
    - Most permit types peaked in 2022
    - 2023 data suggests market changes
    
    **2. Geographic Patterns (Analysis 2)**
    - Top 15 ZIP codes dominate permit activity
    - High permit count ≠ high valuation (different patterns)
    - Construction is geographically concentrated
    
    **3. Work Types (Analysis 3)**
    - Alteration/Repair work is most common
    - New construction is a small fraction
    - Electrical and Fire Sprinkler work is significant
    """)

with insights_col2:
    st.markdown("""
    **4. Investment Patterns (Analysis 4)**
    - Most projects are under $25K (small repairs/upgrades)
    - Small percentage of projects are >$500K
    - Valuation varies dramatically by permit type
    
    **5. Contractor Landscape (Analysis 5)**
    - Thousands of contractors compete in LA
    - Energy companies dominate permit counts
    - Market is relatively fragmented
    - Top contractors specialize by project type/size
    """)

st.markdown("---")
st.markdown("""
    **Data Source:** LA City Building Permits (2020-2024)  
    **Dashboard created with:** Streamlit + Snowflake  
    **Analysis Framework:** Temporal → Geographic → Work Type → Valuation → Contractors
""")