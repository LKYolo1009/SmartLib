import streamlit as st
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from utils.api_client import APIClient


st.set_page_config(page_title="QR Label Generator", layout="wide")
st.title("🏷️ QR Code Label Generator")

def generate_label_image(uid, title, call_number, isbn):
    qr = qrcode.make(uid)
    qr = qr.resize((150, 150))
    img = Image.new("RGB", (300, 220), color="white")
    img.paste(qr, (10, 10))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((170, 10), f"Title: {title}", font=font, fill="black")
    draw.text((170, 50), f"Call No: {call_number}", font=font, fill="black")
    if isbn:
        draw.text((170, 90), f"ISBN: {isbn}", font=font, fill="black")
    return img


def create_pdf(rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    label_width = 180
    label_height = 140
    x_start = 40
    y_start = 700
    x, y = x_start, y_start
    count = 0

    for _, row in rows.iterrows():
        uid = row["qr_code"]
        title = row["title"]
        call_number = row["call_number"]
        isbn = row["isbn"] if pd.notna(row["isbn"]) else ""
        qr = qrcode.make(uid)
        qr_buf = BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        c.drawImage(ImageReader(qr_buf), x, y, width=60, height=60)
        text_x = x + 65
        text_y = y + 40
        c.setFont("Helvetica", 8)
        c.drawString(text_x, text_y, f"Title: {title[:40]}")
        c.drawString(text_x, text_y - 12, f"Call No: {call_number}")
        if isbn:
            c.drawString(text_x, text_y - 24, f"ISBN: {isbn}")
        x += label_width
        count += 1
        if count % 3 == 0:
            x = x_start
            y -= label_height
        if count % 15 == 0:
            c.showPage()
            x, y = x_start, y_start

    c.save()
    buffer.seek(0)
    return buffer


def show_qr_label_tab():

    @st.cache_data(ttl=600)
    def load_books_from_api():
        try:
            data = APIClient.get_book_copy_labels()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error loading book data: {e}")
            return pd.DataFrame()

    df = load_books_from_api()

    if df.empty:
        st.warning("No book data available.")
        return

    st.markdown("### Step 1: Select books to generate labels")
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
        disabled=["qr_code", "title", "call_number", "isbn"]
    )

    selected_books = edited_df[edited_df["select"]]

    if not selected_books.empty:
        st.markdown("### Step 2: Download the PDF")
        pdf_buffer = create_pdf(selected_books)
        st.download_button("📥 Download PDF Labels", pdf_buffer, file_name="qr_labels.pdf", mime="application/pdf")

show_qr_label_tab()