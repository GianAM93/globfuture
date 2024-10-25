# Importa le librerie necessarie
import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# Funzione per impostare lo stile della pagina
def set_page_style(bg_color, font_family='Arial'):
    st.markdown(
        f"""
        <style>
        .main {{
            background-color: {bg_color};
            font-family: {font_family};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Logo e titolo con font personalizzato
st.markdown(
    """
    <style>
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .title {
        font-size: 36px;
        text-align: center;
    }
    </style>
    <div class="logo-container">
        <img src="LOGO_URL" width="150">
    </div>
    <h1 class="title">Gestione Corsi e Scadenze</h1>
    """,
    unsafe_allow_html=True
)

# Funzione per processare i dati
def processa_corsi(file_corsi, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento):
    # Processamento dati per corsi...
    pass  # sostituisci con il codice esistente

def processa_documenti(file_documenti, df_mappa_documenti, df_periodo_documenti, anno_riferimento):
    # Processamento dati per documenti...
    pass  # sostituisci con il codice esistente

# Funzione per convertire DataFrame in Excel
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Funzione per dividere il DataFrame per GruppoCorso e salvarlo in un file Excel
def save_groups_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for gruppo, group_data in df.groupby('GruppoCorso'):
            group_data.drop(columns=['Localita', 'CodATECO', 'GruppoCorso'], inplace=True)
            group_data.to_excel(writer, sheet_name=gruppo[:31], index=False)
    return output.getvalue()

# Inizializza il tipo di file selezionato
file_type = st.session_state.get("file_type", None)

# Colori per le modalità
bg_colors = {"formazione": "#d1e7ff", "documenti": "#ffe6cc", "generazione": "#d4edda"}
set_page_style(bg_color=bg_colors["formazione"] if file_type == "formazione" else bg_colors["documenti"])

# Pulsanti per selezionare "Formazione" o "Documenti"
col1, col2 = st.columns(2)
with col1:
    if st.button("Formazione"):
        st.session_state["file_type"] = "formazione"
        set_page_style(bg_color=bg_colors["formazione"])
with col2:
    if st.button("Documenti"):
        st.session_state["file_type"] = "documenti"
        set_page_style(bg_color=bg_colors["documenti"])

# Caricamento del file e altre impostazioni in base alla selezione
if st.session_state["file_type"] == "formazione":
    # Caricamento file e impostazioni per la formazione
    file_corsi = st.file_uploader("Carica il file dei corsi (Corsi_yyyy.xlsx)", type="xlsx")
    # (Carica i file di mappatura per Formazione)
    # Quando si preme il pulsante "Genera File" e il file è caricato, mostra un feedback colorato
    if st.button("Genera File"):
        if file_corsi:
            set_page_style(bg_color=bg_colors["generazione"])
            # Chiama le funzioni di processamento e scarica i file
            # ...
        else:
            st.error("Carica il file dei corsi.")

elif st.session_state["file_type"] == "documenti":
    # Caricamento file e impostazioni per i documenti
    file_documenti = st.file_uploader("Carica il file dei documenti (Documenti_yyyy.xlsx)", type="xlsx")
    # (Carica i file di mappatura per Documenti)
    # Quando si preme il pulsante "Genera File" e il file è caricato, mostra un feedback colorato
    if st.button("Genera File"):
        if file_documenti:
            set_page_style(bg_color=bg_colors["generazione"])
            # Chiama le funzioni di processamento e scarica i file
            # ...
        else:
            st.error("Carica il file dei documenti.")
