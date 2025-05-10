import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText

# --- Load kredensial dari .env atau Streamlit Secrets ---
load_dotenv()
SENDER_EMAIL = os.getenv("EMAIL_SENDER", st.secrets.get("EMAIL_SENDER", ""))
EMAIL_PASS = os.getenv("EMAIL_PASSWORD", st.secrets.get("EMAIL_PASSWORD", ""))

# --- Fungsi kirim email ---
def send_email(subject, message, receiver_email):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_PASS)
        smtp.send_message(msg)

# --- Streamlit UI ---
st.title("📈 Analisis Sederhana Saham & Crypto + Notifikasi Email")

symbols = st.text_input("Simbol saham/crypto (pisahkan koma)", "AAPL,TSLA,BTC-USD")
email = st.text_input("Email kamu (opsional)", "")
start_date = st.date_input("Tanggal mulai", pd.to_datetime("2023-01-01"))
max_date = pd.to_datetime("today") - pd.Timedelta(days=1)
end_date = st.date_input("Tanggal akhir", value=max_date, max_value=max_date)

if st.button("🔍 Analisis Sekarang"):
    symbols = [s.strip().upper() for s in symbols.split(",")]
    for symbol in symbols:
        st.subheader(f"📊 {symbol}")

        try:
            data = yf.download(symbol, start=start_date, end=end_date)
        except Exception as e:
            st.error(f"❌ Gagal mengambil data untuk {symbol}: {e}")
            continue

        if data.empty or 'Close' not in data.columns:
            st.warning(f"⚠️ Data untuk {symbol} kosong atau tidak valid.")
            continue

        # Plot harga penutupan
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(data['Close'], label='Harga Penutupan', color='blue')
        ax.set_title(f"Harga Penutupan {symbol}")
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Harga")
        ax.legend()
        st.pyplot(fig)

        # Deteksi pergerakan harga dengan validasi panjang data
        try:
            latest = data['Close'].iloc[-1]
            if len(data['Close']) >= 2:
                prev = data['Close'].iloc[-2]
                if latest > prev:
                    direction = "⬆️ Naik"
                elif latest < prev:
                    direction = "⬇️ Turun"
                else:
                    direction = "⏸ Stabil"
            else:
                direction = "🔹 Data terlalu sedikit untuk analisis"
        except Exception:
            st.warning(f"⚠️ Tidak bisa membaca harga penutupan terakhir untuk {symbol}")
            continue

        st.markdown(f"**Harga Terakhir:** ${latest:.2f}")
        st.markdown(f"**Pergerakan:** {direction}")

        # Notifikasi email
        if email and "Data terlalu sedikit" not in direction:
            subject = f"[{symbol}] Update Harga"
            message = f"Harga terakhir {symbol}: ${latest:.2f}\nPergerakan: {direction}"
            try:
                send_email(subject, message, email)
                st.success(f"📧 Email dikirim ke {email}")
            except Exception as e:
                st.error(f"❌ Gagal mengirim email: {e}")
