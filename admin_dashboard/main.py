import streamlit as st

pages = [
    st.Page("pages/dashboard.py", title="📊 Dashboard"),
    st.Page("pages/qr_label_generator.py", title="🏷️ QR Label Generator"),
]

pg = st.navigation(pages)
pg.run()