import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta
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
st.title("📊 Analisis Saham & Crypto + Notifikasi Email")

symbols = st.text_input("Simbol saham/crypto (pisahkan koma)", "AAPL,TSLA,BTC-USD")
email = st.text_input("Email kamu (opsional untuk notifikasi)", "")
start_date = st.date_input("Tanggal mulai", pd.to_datetime("2023-01-01"))
end_date = st.date_input("Tanggal akhir", pd.to_datetime("2025-01-01"))

if st.button("🔍 Analisis Sekarang"):
    symbols = [sym.strip().upper() for sym in symbols.split(",")]
    for symbol in symbols:
        st.subheader(f"📈 {symbol}")
        data = yf.download(symbol, start=start_date, end=end_date)

        # Validasi data
        if data is None or data.empty or 'Close' not in data.columns:
            st.warning(f"⚠️ Tidak ada data valid untuk {symbol}. Coba simbol atau tanggal lain.")
            continue

        data = data[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        data['Close'] = pd.to_numeric(data['Close'], errors='coerce')

        if data['Close'].isnull().all():
            st.warning(f"⚠️ Semua nilai 'Close' untuk {symbol} kosong atau tidak valid.")
            continue

        # Hitung indikator teknikal
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        data['RSI'] = ta.momentum.RSIIndicator(close=data['Close']).rsi()
        data['MACD'] = ta.trend.macd_diff(data['Close'])

        bb = ta.volatility.BollingerBands(close=data['Close'])
        data['BB_upper'] = bb.bollinger_hband()
        data['BB_lower'] = bb.bollinger_lband()

        # Visualisasi chart
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(data['Close'], label='Harga', color='black')
        ax.plot(data['SMA20'], label='SMA20')
        ax.plot(data['SMA50'], label='SMA50')
        ax.plot(data['BB_upper'], linestyle='--', color='gray', alpha=0.5)
        ax.plot(data['BB_lower'], linestyle='--', color='gray', alpha=0.5)
        ax.set_title(f"{symbol} Chart")
        ax.legend()
        st.pyplot(fig)

        # Analisis sinyal
        latest = data.iloc[-1]
        signal = "⏸ Normal"
        if latest['SMA20'] > latest['SMA50']:
            signal = "🟢 BUY (Golden Cross)"
        elif latest['SMA20'] < latest['SMA50']:
            signal = "🔴 SELL (Death Cross)"

        rsi_status = "Normal"
        if latest['RSI'] > 70:
            rsi_status = "⚠️ Overbought"
        elif latest['RSI'] < 30:
            rsi_status = "✅ Oversold"

        st.markdown(f"**Sinyal:** {signal}")
        st.markdown(f"**RSI:** {latest['RSI']:.2f} ({rsi_status})")
        st.markdown(f"**MACD:** {latest['MACD']:.2f}")

        # Kirim email jika diminta
        if email and ("BUY" in signal or "SELL" in signal):
            subject = f"[{symbol}] {signal}"
            message = f"Harga: {latest['Close']:.2f}\nRSI: {latest['RSI']:.2f} ({rsi_status})\nSinyal: {signal}"
            try:
                send_email(subject, message, email)
                st.success(f"📧 Email notifikasi dikirim ke {email}")
            except Exception as e:
                st.error(f"Gagal mengirim email: {e}")
