import streamlit as st

pages = [
    st.Page("pages/dashboard.py", title="📊 Dashboard"),
    st.Page("pages/book_qr_generator.py", title="🏷️ Book QR Generator"),
    st.Page("pages/location_qr_generator.py", title="📍 Location QR Generator"),
]

pg = st.navigation(pages)
pg.run()