import streamlit as st

conn = st.experimental_connection("snowpark")
df = conn.query("select current_warehouse()")
st.write(df)