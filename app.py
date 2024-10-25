import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# CSS personalizzato per colori e stile
st.markdown(
    """
    <style>
    /* Colore di sfondo e testo della pagina */
    .main {
        background-color: rgb(255, 255, 255);
        color: #FFFFFF;
    }

    /* Stile titolo */
    h1 {
        color: #4A5568;
        text-align: center;
        font-family: sans-serif;
        font-weight: bold;
    }

    /* Stile dei pulsanti non selezionati */
    .stButton > button {
        color: #FF6B6B;
        border: 2px solid #FF6B6B;
        background-color: transparent;
        font-weight: bold;
        width: 100%;
    }

    /* Colore del pulsante selezionato */
    .stButton > button.selected {
        background-color: #FF6B6B;
        color: white;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Titolo
st.markdown("<h1>SCOPRI IL FUTURO! 😉</h1>", unsafe_allow_html=True)

# Inizializzazione dello stato per la selezione della sezione
if "sezione_selezionata" not in st.session_state:
    st.session_state["sezione_selezionata"] = "Formazione"  # Default

# Funzione per controllare se il pulsante è selezionato
def is_selected(sezione):
    return "selected" if st.session_state["sezione_selezionata"] == sezione else ""

# Pulsanti per selezione tra formazione e documenti
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Formazione", key="formazione_btn"):
        st.session_state["sezione_selezionata"] = "Formazione"
with col2:
    if st.button("Documenti", key="documenti_btn"):
        st.session_state["sezione_selezionata"] = "Documenti"

sezione_corrente = st.session_state["sezione_selezionata"]

# Caricamento file e selettore anno
file_caricato = st.file_uploader(
    f"Carica il file {sezione_corrente.lower()} da filtrare",
    type="xlsx",
    key=f"file_uploader_{sezione_corrente}",
    label_visibility="collapsed",
)

# Selettore per l'anno di riferimento
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Pulsante per generare file
if st.button("GENERA FILE", key=f"genera_file_button_{sezione_corrente}"):
    if file_caricato:
        if sezione_corrente == "Formazione":
            st.write("Elaborazione del file di formazione...")
            # Codice per elaborare file di formazione
        elif sezione_corrente == "Documenti":
            st.write("Elaborazione del file di documenti...")
            # Codice per elaborare file di documenti
    else:
        st.error("Carica un file prima di generare.")
