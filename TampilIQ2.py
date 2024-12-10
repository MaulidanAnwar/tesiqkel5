import streamlit as st
import numpy as np
import pickle
import pandas as pd
import sqlite3
import uuid  # Untuk membuat UUID unik

# Mengubah layout 
st.set_page_config(page_title="Prediksi IQ & Outcome", layout="wide", page_icon="🧠")

background_url = "https://raw.githubusercontent.com/MaulidanAnwar/Final-Project-Group-5/8a14423da65459d56047b014e582f7146e1cf042/top-view-keyboard-desk-with-notebook-succulent-plant.jpg"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("{background_url}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Load the train model dan scaler
classifier = pickle.load(open('Klasifikasi.sav', 'rb'))
regresi_nilai = pickle.load(open('NilaiIQ.sav', 'rb'))
scaler = pickle.load(open('scaler.sav', 'rb'))

# Generate UUID unik untuk perangkat
if "device_id" not in st.session_state:
    st.session_state["device_id"] = str(uuid.uuid4())

device_id = st.session_state["device_id"]

# Buat koneksi ke SQLite
conn = sqlite3.connect('test_data_prediksi_iq.db')
c = conn.cursor()

# Buat tabel jika belum ada
c.execute('''
CREATE TABLE IF NOT EXISTS prediksi_iq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    nilai_iq INTEGER,
    kategori TEXT,
    device_id TEXT
)
''')

# Fungsi untuk mengambil riwayat dari database
def get_history(device_id):
    c.execute('SELECT * FROM prediksi_iq WHERE device_id = ?', (device_id,))
    return c.fetchall()

# Sidebar untuk riwayat dan hapus data
st.sidebar.markdown("---")  # Pembatas
st.sidebar.markdown("## 📑 Riwayat Data")
with st.sidebar.expander("Lihat Riwayat Prediksi IQ"):
    # Ambil data riwayat dari database
    data = get_history(device_id)

    # Jika ada data, tampilkan dalam dataframe
    if data:
        df = pd.DataFrame(data, columns=["ID", "Nama", "Nilai IQ", "Kategori", "Device ID"])
        st.dataframe(df.drop(columns=["Device ID"]))  # Sembunyikan kolom Device ID dari pengguna

        # Download tombol untuk database sebagai CSV
        csv = df.drop(columns=["Device ID"]).to_csv(index=False)
        st.download_button(
            label="📄 Unduh Hasil sebagai CSV",
            data=csv,
            file_name="Hasil_Prediksi_IQ.csv",
            mime="text/csv"
        )
    else:
        st.info("Belum ada riwayat prediksi yang tersimpan untuk perangkat ini.")

# Tombol hapus riwayat di sidebar
if st.sidebar.button("🗑️ Hapus Riwayat Data"):
    # Menghapus data hanya untuk UUID perangkat ini
    c.execute('DELETE FROM prediksi_iq WHERE device_id = ?', (device_id,))
    conn.commit()
    st.experimental_rerun()  # Jalankan ulang aplikasi untuk menampilkan pembaruan

# Judul Aplikasi
st.markdown("<h1 style='text-align: center; color: blue;'>🧠 Aplikasi Prediksi Nilai IQ dan Outcome</h1>", unsafe_allow_html=True)

# Input dari pengguna 
st.markdown("<h3 style='text-align: center;'>Masukkan Nama dan Skor Mentah Anda di bawah ini:</h3>", unsafe_allow_html=True)

# Input nama pengguna
nama = st.text_input("👤 Nama Anda:")

# Input data pengguna
input_data = st.number_input("⚖️ Skor Mentah (X):", min_value=0, max_value=100, step=1)

# Button untuk menghitung hasil
if st.button("🔍 Hitung Hasil"):
    if nama and input_data:
        # Proses input data
        input_data_as_numpy_array = np.array(input_data).reshape(1, -1)

        # Normalisasi data input
        std_data = scaler.transform(input_data_as_numpy_array)

        # Prediksi Nilai IQ
        prediksi_iq = regresi_nilai.predict(std_data)
        prediksi_iq = round(prediksi_iq[0])

        # Prediksi Outcome
        prediction = classifier.predict(std_data)
        if prediction[0] == 1:
            kategori = "Di bawah rata-rata"
        elif prediction[0] == 2:
            kategori = "Rata-rata"
        else:
            kategori = "Di atas rata-rata"

        # Menyimpan data ke SQLite
        c.execute('''
            INSERT INTO prediksi_iq (nama, nilai_iq, kategori, device_id) 
            VALUES (?, ?, ?, ?)
        ''', (nama, prediksi_iq, kategori, device_id))
        conn.commit()

        # Menampilkan hasil prediksi
        st.markdown("---")
        st.markdown("<h2 style='text-align: center; color: green;'>📊 Hasil Prediksi</h2>", unsafe_allow_html=True)
        st.success(f"**Hai {nama}**")
        st.success(f"**Nilai IQ Anda: {prediksi_iq}**")
        if kategori == "Di bawah rata-rata":
            st.warning(f"Kategori Anda: **{kategori}**")
        elif kategori == "Rata-rata":
            st.info(f"Kategori Anda: **{kategori}**")
        else:
            st.success(f"Kategori Anda: **{kategori}**")
    else:
        st.warning("Harap masukkan Nama dan Skor Mentah untuk melihat hasil prediksi.")

# Tutup koneksi ke SQLite
conn.close()

# Tampilan tambahan di bawah
st.markdown("<p style='text-align: center; font-weight: bold; color: black;'>Ingin mengulang prediksi? Masukkan skor baru dan klik tombol di atas!</p>", unsafe_allow_html=True)
