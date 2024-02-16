import streamlit as st
import pandas.io.sql as sqlio
import altair as alt
import folium
from streamlit_folium import st_folium
from db import get_db_conn  # Assuming get_db_conn is correctly importing from db.py

# Initialize the app and title
st.title("Seattle Events")

# Database connection
conn = get_db_conn()

# Fetch distinct values for dropdown filters
categories = sqlio.read_sql_query("SELECT DISTINCT category FROM events", conn)
locations = sqlio.read_sql_query("SELECT DISTINCT location FROM events", conn)

# Category Filter Dropdown
category_choice = st.selectbox('Choose a category', ['All'] + sorted(categories['category'].tolist()))

# Location Filter
location_choice = st.selectbox('Choose a location', ['All'] + sorted(locations['location'].tolist()))

# Date Range Selector
date_range = st.date_input("Choose the date range", [])

# Construct the SQL query based on filters
sql_query = "SELECT * FROM events"
conditions = []

if category_choice != 'All':
    conditions.append(f"category = '{category_choice}'")

if location_choice != 'All':
    conditions.append(f"location = '{location_choice}'")

if date_range:
    start_date, end_date = date_range[0], date_range[-1]
    conditions.append(f"date BETWEEN '{start_date}' AND '{end_date}'")

if conditions:
    sql_query += " WHERE " + " AND ".join(conditions)

# Fetch events with location data
sql_query_with_location = sql_query.replace("*", "title, location, latitude, longitude")

df = sqlio.read_sql_query(sql_query, conn)
st.write("Filtered Events:", df)

# Initialize the map
m = folium.Map(location=[47.6062, -122.3321], zoom_start=12)

# Add markers for each event
for index, row in df.iterrows():
    folium.Marker(
        [row['latitude'], row['longitude']],
        popup=f"{row['title']} - {row['location']}",
    ).add_to(m)

# Display the map
st_folium(m, width=725, height=500)

# Original visualization (assuming this is for event categories)
df = sqlio.read_sql_query("SELECT * FROM events", conn)
st.altair_chart(
    alt.Chart(df).mark_bar().encode(
        x="count()", 
        y=alt.Y("category", sort='-x')
    ).interactive(),
    use_container_width=True,
)


# Second chart: Number of events per month
query_month = """
SELECT EXTRACT(MONTH FROM date) AS month, COUNT(*) AS event_count
FROM events
GROUP BY month
ORDER BY month;
"""
df_month = sqlio.read_sql_query(query_month, conn)
st.altair_chart(
    alt.Chart(df_month).mark_bar().encode(
        x=alt.X('month:N', title='Month'),
        y=alt.Y('event_count:Q', title='Number of Events')
    ).properties(title="Number of Events per Month"),
    use_container_width=True
)

# Third chart: Number of events by day of the week
query_day = """
SELECT EXTRACT(DOW FROM date) AS day_of_week, COUNT(*) AS event_count
FROM events
GROUP BY day_of_week
ORDER BY day_of_week;
"""
df_day = sqlio.read_sql_query(query_day, conn)
days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
df_day['day_of_week'] = df_day['day_of_week'].apply(lambda x: days[int(x)])

st.altair_chart(
    alt.Chart(df_day).mark_bar().encode(
        x=alt.X('day_of_week:N', title='Day of the Week'),
        y=alt.Y('event_count:Q', title='Number of Events')
    ).properties(title="Number of Events by Day of the Week"),
    use_container_width=True
)
