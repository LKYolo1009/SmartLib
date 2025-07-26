import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from utils.api_client import APIClient
import textwrap

st.set_page_config(page_title="Location QR Generator", layout="wide")
st.title("📍 Location QR Generator")

def generate_location_label_image(qr_code, name, description):
    qr = qrcode.make(qr_code)
    qr = qr.resize((150, 150))
    img = Image.new("RGB", (300, 220), color="white")
    img.paste(qr, (10, 10))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((170, 10), f"Name: {name}", font=font, fill="black")
    draw.text((170, 50), f"Desc: {description[:30]}...", font=font, fill="black")
    return img

def create_location_pdf(rows):
    buffer = BytesIO()
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    label_width = page_width / 2
    label_height = page_height
    qr_size = 200

    positions = [(0, 0), (label_width, 0)]  # left and right halves
    font_large = 16
    font_medium = 14

    for i, (_, row) in enumerate(rows.iterrows()):
        if i % 2 == 0 and i != 0:  # Don't showPage() before the first label
            c.showPage()

        pos_index = i % 2
        x, y = positions[pos_index]

        # QR Code
        qr = qrcode.make(row["location_qr_code"])
        qr_buf = BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)

        qr_x = x + (label_width - qr_size) / 2
        qr_y = y + (label_height - qr_size) / 2 + 30
        c.drawImage(ImageReader(qr_buf), qr_x, qr_y, width=qr_size, height=qr_size)

        # Location Name
        text_y = qr_y - 30
        c.setFont("Helvetica-Bold", font_large)
        c.drawCentredString(x + label_width / 2, text_y, row["location_name"])

        # Multi-line Description
        c.setFont("Helvetica", font_medium)
        description = row["location_description"]
        wrapped_lines = textwrap.wrap(description, width=60)
        for j, line in enumerate(wrapped_lines):
            line_y = text_y - 25 - (j * 18)
            c.drawCentredString(x + label_width / 2, line_y, line)

    c.save()
    buffer.seek(0)
    return buffer

def show_location_qr_tab():
    @st.cache_data(ttl=600)
    def load_locations():
        try:
            url = "metadata/locations"
            data = APIClient.get_api_data(url, params={"skip": 0, "limit": 100})
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading location data: {e}")
            return pd.DataFrame()

    df = load_locations()

    if df.empty:
        st.warning("No location data available.")
        return

    st.markdown("### Step 1: Select locations to generate labels")
    select_all = st.checkbox("✅ Select All")
    df["select"] = select_all
    cols = df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("select")))
    df = df[cols]

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={"select": st.column_config.CheckboxColumn("Print", default=False)},
        disabled=["location_id", "location_name", "location_description", "location_qr_code"]
    )

    selected_locations = edited_df[edited_df["select"]]

    if not selected_locations.empty:
        st.markdown("### Step 2: Download PDF of QR Labels")
        pdf_buffer = create_location_pdf(selected_locations)
        st.download_button("📥 Download PDF Labels", pdf_buffer, file_name="location_qr_labels.pdf", mime="application/pdf")

show_location_qr_tab()
