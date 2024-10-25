import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# CSS personalizzato per colori e stile
st.markdown(
    """
    <style>
    /* Colore di sfondo e testo della pagina */
    body {
        background-color: white;
        color: #4A5568;
    }

    /* Stile titolo */
    h1 {
        color: #4A5568;
        text-align: center;
        font-family: sans-serif;
        font-weight: bold;
    }

    /* Stile dei pulsanti non cliccati */
    .stButton > button {
        color: #FF6B6B;
        border: 2px solid #FF6B6B;
        background-color: transparent;
        font-weight: bold;
        width: 100%;
    }

    /* Stile dei pulsanti cliccati */
    .stButton > button[selected] {
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

# Pulsanti per selezione tra formazione e documenti
col1, col2 = st.columns([1, 1])

with col1:
    formazione_clicked = st.button("Formazione", key="formazione_btn")
with col2:
    documenti_clicked = st.button("Documenti", key="documenti_btn")

# Imposta lo stato del pulsante selezionato
if "sezione_selezionata" not in st.session_state:
    st.session_state["sezione_selezionata"] = "Formazione"  # Default

if formazione_clicked:
    st.session_state["sezione_selezionata"] = "Formazione"
elif documenti_clicked:
    st.session_state["sezione_selezionata"] = "Documenti"

sezione_corrente = st.session_state["sezione_selezionata"]

# Rimuovi la linea di separazione e aumenta l’altezza dell’area di caricamento
file_caricato = st.file_uploader(
    f"Carica il file {sezione_corrente.lower()} da filtrare",
    type="xlsx",
    key=f"file_uploader_{sezione_corrente}",  # Chiave unica per ciascuna sezione
    label_visibility="collapsed",
)

# Selettore per l'anno di riferimento
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Pulsante genera file centrato
st.markdown("<div style='display: flex; justify-content: center; margin-top: 20px;'>", unsafe_allow_html=True)
if st.button("GENERA FILE", key="genera_file_button"):
    if file_caricato:
        if sezione_corrente == "Formazione":
            st.write("Elaborazione del file di formazione...")
        elif sezione_corrente == "Documenti":
            st.write("Elaborazione del file di documenti...")
    else:
        st.error("Carica un file prima di generare.")
st.markdown("</div>", unsafe_allow_html=True)

# Determina la sezione corrente in base al pulsante cliccato
sezione_corrente = st.session_state["sezione_selezionata"]

# Caricamento file e selezione anno senza linea separatrice
file_caricato = st.file_uploader(f"Carica il file {sezione_corrente.lower()} da filtrare", type="xlsx", key="file_uploader", label_visibility="collapsed")

# Funzione per processare i dati dei corsi
def processa_corsi(file_corsi, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento):
    df_corsi = pd.read_excel(file_corsi)
    df_corsi_cleaned = df_corsi[['TipoCorso', 'DataCorso', 'RagioneSociale', 'Dipendente', 'Localita']]
    df_corsi_ateco = pd.merge(df_corsi_cleaned, df_ateco, how='left', on='RagioneSociale')
    df_corsi_mappati = pd.merge(df_corsi_ateco, df_mappa_corsi, how='left', on='TipoCorso')
    df_corsi_mappati['CodATECO'] = df_corsi_mappati['CodATECO'].astype(str)
    settore_edile = df_corsi_mappati['CodATECO'].str.startswith(('41', '42', '43'))
    df_corsi_mappati.loc[settore_edile & df_corsi_mappati['GruppoCorso'].str.contains('Specifica', case=False), 'GruppoCorso'] = 'SpecificaEdile'
    df_corsi_completo = pd.merge(df_corsi_mappati, df_periodo_gruppi, how='left', on='GruppoCorso')
    df_corsi_completo['AnnoScadenza'] = df_corsi_completo['DataCorso'].apply(lambda x: x.year) + df_corsi_completo['PeriodicitaCorso']
    df_scadenza = df_corsi_completo[df_corsi_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['Dipendente', 'RagioneSociale', 'GruppoCorso'], keep='first')
    df_scadenza['DataCorso'] = pd.to_datetime(df_scadenza['DataCorso'], format='%d-%m-%Y').apply(lambda x: x.replace(year=anno_riferimento))
    df_scadenza['DataCorso'] = df_scadenza['DataCorso'].dt.strftime('%d-%m-%Y')
    df_completo_aggiornato = pd.merge(df_scadenza, df_aggiornamento, on='TipoCorso', how='left')
    colonne_ordinate = ['TipoCorso', 'Aggiornamento'] + [col for col in df_completo_aggiornato.columns if col not in ['TipoCorso', 'Aggiornamento']]
    df_completo_aggiornato = df_completo_aggiornato[colonne_ordinate]
    return df_completo_aggiornato

# Funzione per processare i documenti
def processa_documenti(file_documenti, df_mappa_documenti, df_periodo_documenti, anno_riferimento):
    df_documenti = pd.read_excel(file_documenti)
    df_documenti_cleaned = df_documenti[['Documenti', 'Data', 'RagioneSociale']]
    df_documenti_mappati = pd.merge(df_documenti_cleaned, df_mappa_documenti, how='left', left_on='Documenti', right_on='TipoDocumento')
    if 'GruppoDocumenti' not in df_documenti_mappati.columns:
        st.error("Errore: 'GruppoDocumenti' non trovato dopo la mappatura dei documenti.")
        return pd.DataFrame()  
    df_documenti_completo = pd.merge(df_documenti_mappati, df_periodo_documenti, how='left', on='GruppoDocumenti')
    if 'PeriodicitaDoc' not in df_documenti_completo.columns:
        st.error("Errore: 'PeriodicitaDoc' non trovato dopo la mappatura della periodicità.")
        return pd.DataFrame()  
    df_documenti_completo['AnnoScadenza'] = df_documenti_completo['Data'].apply(lambda x: x.year) + df_documenti_completo['PeriodicitaDoc']
    df_scadenza = df_documenti_completo[df_documenti_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['RagioneSociale', 'GruppoDocumenti'], keep='first')
    df_scadenza['Data'] = pd.to_datetime(df_scadenza['Data'], format='%d-%m-%Y').apply(lambda x: x.replace(year=anno_riferimento))
    df_scadenza['Data'] = df_scadenza['Data'].dt.strftime('%d-%m-%Y')
    df_scadenza = df_scadenza.drop(columns=['Documenti', 'TipoDocumento', 'PeriodicitaDoc', 'AnnoScadenza'], errors='ignore')
    return df_scadenza

# Funzione per convertire DataFrame in Excel
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# Genera file in base alla selezione della sezione
col4, col5, col6 = st.columns([1, 1, 1])
with col5:
   # Pulsante di generazione file con chiave unica per la sezione corrente
if st.button("GENERA FILE", key=f"genera_file_button_{sezione_corrente}"):
    if file_caricato:
        if sezione_corrente == "Formazione":
            df_finale = processa_corsi(file_caricato, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento)
            excel_finale = convert_df_to_excel(df_finale)
            st.download_button("Scarica file formazione", data=excel_finale, file_name=f'Corsi_scadenza_{anno_riferimento}_completo.xlsx')
        elif sezione_corrente == "Documenti":
            df_finale = processa_documenti(file_caricato, df_mappa_documenti, df_periodo_documenti, anno_riferimento)
            excel_finale = convert_df_to_excel(df_finale)
            st.download_button("Scarica file documenti", data=excel_finale, file_name=f'Documenti_scadenza_{anno_riferimento}_completo.xlsx')
    else:
        st.error("Carica un file prima di generare.")
