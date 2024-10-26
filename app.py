import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter
import os

# Page configuration
st.set_page_config(
    page_title="Scopri il Futuro!",
    page_icon="🔮",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
        .main-container {
            max-width: 768px;
            padding: 32px;
            margin: auto;
        }
        /* Altri stili personalizzati */
        .title-text {
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 32px;
            background: linear-gradient(45deg, #FF4B4B, #FF8080);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle-text {
            font-size: 18px;
            color: #666666;
            text-align: center;
            margin-bottom: 32px;
        }
        .stButton button {
            padding: 12px 24px;
            border-radius: 8px;
            height: 48px;
            margin-right: 16px;
            background-color: #FF4B4B;
            color: white;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            background-color: #FF2B4B;
        }
        .stFileUploader {
            width: 100%;
            border: 4px dashed #cccccc;
            border-radius: 8px;
            padding: 32px;
            text-align: center;
        }
        .stFileUploader label div {
            font-size: 48px;
        }
        .stNumberInput input {
            width: 192px;
            height: 48px;
            border-radius: 8px;
            padding: 8px;
            text-align: center;
        }
        .generate-button button {
            padding: 16px 32px;
            font-size: 18px;
            border-radius: 8px;
            height: 56px;
        }
    </style>
""", unsafe_allow_html=True)

# Percorso della cartella dei file di supporto
data_folder = ".data"

# Funzione per caricare i file e gestire errori
def carica_file_excel(nome_file):
    percorso_file = os.path.join(data_folder, nome_file)
    try:
        return pd.read_excel(percorso_file)
    except FileNotFoundError:
        st.error(f"Errore: il file '{nome_file}' non è stato trovato nella cartella '{data_folder}'.")

# Caricamento dei file di supporto con nomi corretti
df_ateco = carica_file_excel("AziendeAteco.xlsx")
df_aggiornamento = carica_file_excel("Corso_Aggiornamento.xlsx")
df_mappa_corsi = carica_file_excel("MappaCorsi.xlsx")
df_periodo_gruppi = carica_file_excel("PeriodoGruppi.xlsx")
df_mappa_documenti = carica_file_excel("MappaDocumenti.xlsx")
df_periodo_documenti = carica_file_excel("PeriodicitaDocumenti.xlsx")

# Controllo che i DataFrame siano stati caricati
if any(df is None for df in [df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, df_mappa_documenti, df_periodo_documenti]):
    st.stop()  # Interrompe l'applicazione se manca un file

# Funzione di elaborazione aggiornata per generare i due file
@st.cache_data
def processa_corsi(file_corsi, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento):
    df_corsi = pd.read_excel(file_corsi)
    df_corsi_cleaned = df_corsi[['TipoCorso', 'DataCorso', 'RagioneSociale', 'Dipendente', 'Localita']]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Merge con df_ateco e mappatura dei corsi
    df_corsi_ateco = pd.merge(df_corsi_cleaned, df_ateco, how='left', on='RagioneSociale')
    df_corsi_mappati = pd.merge(df_corsi_ateco, df_mappa_corsi, how='left', on='TipoCorso')
    settore_edile = df_corsi_mappati['CodATECO'].str.startswith(('41', '42', '43'))
    df_corsi_mappati.loc[settore_edile & df_corsi_mappati['GruppoCorso'].str.contains('Specifica', case=False), 'GruppoCorso'] = 'SpecificaEdile'
    df_corsi_completo = pd.merge(df_corsi_mappati, df_periodo_gruppi, how='left', on='GruppoCorso')
    
    # Creazione del primo file (senza PeriodicitaCorso e AnnoScadenza)
    df_corsi_completo['AnnoScadenza'] = df_corsi_completo['DataCorso'].apply(lambda x: x.year) + df_corsi_completo['PeriodicitaCorso']
    df_finale_1 = df_corsi_completo[df_corsi_completo['AnnoScadenza'] == anno_riferimento].drop(columns=['PeriodicitaCorso', 'AnnoScadenza'])

    # Creazione del secondo file con più pagine per GruppoCorso (filtrato)
    file_buffer = BytesIO()
    with pd.ExcelWriter(file_buffer, engine='xlsxwriter') as writer:
        for gruppo, gruppo_df in df_corsi_completo.groupby("GruppoCorso"):
            gruppo_df_filtered = gruppo_df.drop(columns=['TipoCorso', 'Localita', 'CodATECO', 'GruppoCorso', 'PeriodicitaCorso', 'AnnoScadenza'])
            gruppo_df_filtered.to_excel(writer, sheet_name=gruppo[:31], index=False)  # Excel ha limite di 31 caratteri per nome pagina
    
    progress_bar.progress(100)
    status_text.text("Elaborazione completata!")
    
    return df_finale_1, file_buffer.getvalue()

# Funzione per convertire il primo DataFrame in un file Excel
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Pulsante per generare il file
st.markdown('<div class="section-box">', unsafe_allow_html=True)
if st.button("🚀 GENERA FILE", use_container_width=True):
    if file_caricato:
        try:
            with st.spinner('Elaborazione in corso...'):
                if st.session_state["sezione_selezionata"] == "Formazione":
                    df_finale_1, file_buffer_paginated = processa_corsi(file_caricato, df_ateco, df_aggiornamento, 
                                                                        df_mappa_corsi, df_periodo_gruppi, anno_riferimento)
                    
                    # Primo file senza colonne PeriodicitaCorso e AnnoScadenza
                    excel_finale_1 = convert_df_to_excel(df_finale_1)
                    st.success('Elaborazione completata con successo!')
                    st.download_button(
                        "📥 Scarica file formazione (senza PeriodicitaCorso e AnnoScadenza)",
                        data=excel_finale_1,
                        file_name=f'Corsi_scadenza_{anno_riferimento}_completo.xlsx',
                        mime='application/vnd.ms-excel'
                    )
                    
                    # Secondo file con più pagine
                    st.download_button(
                        "📥 Scarica file formazione diviso per GruppoCorso",
                        data=file_buffer_paginated,
                        file_name=f'Corsi_scadenza_{anno_riferimento}_per_GruppoCorso.xlsx',
                        mime='application/vnd.ms-excel'
                    )
                else:
                    # Inserire l'elaborazione per documenti
                    pass
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione: {str(e)}")
    else:
        st.warning("⚠️ Carica un file valido per generare l'output.")
st.markdown('</div>', unsafe_allow_html=True)
