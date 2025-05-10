import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText

# --- Load kredensial dari .env atau secrets ---
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
st.title("💹 Analisis Harga Crypto + Notifikasi Email")

symbols = st.text_input("Masukkan simbol crypto (contoh: BTC-USD, ETH-USD)", "BTC-USD,ETH-USD")
email = st.text_input("Email kamu (opsional)", "")
start_date = st.date_input("Tanggal mulai", pd.to_datetime("2023-01-01"))
max_date = pd.to_datetime("today") - pd.Timedelta(days=1)
end_date = st.date_input("Tanggal akhir", value=max_date, max_value=max_date)

if st.button("🔍 Analisis Sekarang"):
    symbols = [s.strip().upper() for s in symbols.split(",")]
    for symbol in symbols:
        st.subheader(f"📈 {symbol}")

        # Validasi hanya simbol crypto (akhiran -USD)
        if not symbol.endswith("-USD"):
            st.warning(f"⚠️ {symbol} bukan simbol crypto valid (harus diakhiri -USD).")
            continue

        try:
            data = yf.download(symbol, start=start_date, end=end_date)
        except Exception as e:
            st.error(f"❌ Gagal mengambil data untuk {symbol}: {e}")
            continue

        if data.empty or 'Close' not in data.columns:
            st.warning(f"⚠️ Data kosong atau tidak valid untuk {symbol}.")
            continue

        # Visualisasi harga
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(data['Close'], label='Harga Penutupan', color='blue')
        ax.set_title(f"Harga Penutupan {symbol}")
        ax.set_xlabel("Tanggal")
        ax.set_ylabel("Harga (USD)")
        ax.legend()
        st.pyplot(fig)

        # Deteksi pergerakan
        clean_close = data['Close'].dropna()
        if clean_close.empty:
            st.warning(f"⚠️ Tidak ada data harga valid untuk {symbol}.")
            continue

        try:
            latest = float(clean_close.iloc[-1])
            if len(clean_close) >= 2:
                prev = float(clean_close.iloc[-2])
                if latest > prev:
                    direction = "⬆️ Naik"
                elif latest < prev:
                    direction = "⬇️ Turun"
                else:
                    direction = "⏸ Stabil"

                change_pct = ((latest - prev) / prev) * 100
                if change_pct > 2:
                    rekomendasi = "🔼 BUY — Harga naik >2%, potensi tren naik"
                elif change_pct < -2:
                    rekomendasi = "🔽 SELL — Harga turun >2%, waspadai koreksi"
                else:
                    rekomendasi = "⏸ HOLD — Perubahan <2%, belum signifikan"
                
            else:
                direction = "🔹 Data terlalu sedikit untuk analisis"
                rekomendasi = "ℹ️ Tidak cukup data untuk rekomendasi"
        except Exception as e:
            st.warning(f"⚠️ Gagal membaca harga penutupan untuk {symbol}: {e}")
            continue

        st.markdown(f"**Harga Terakhir:** ${latest:.2f}")
        st.markdown(f"**Pergerakan:** {direction}")
        st.markdown(f"**Rekomendasi:** {rekomendasi}")


        # Kirim email jika diperlukan
        if email and "Data terlalu sedikit" not in direction:
            subject = f"[{symbol}] {direction}"
            message = f"Harga terakhir {symbol}: ${latest:.2f}\nStatus: {direction}"
            try:
                send_email(subject, message, email)
                st.success(f"📧 Notifikasi dikirim ke {email}")
            except Exception as e:
                st.error(f"❌ Gagal kirim email: {e}")
