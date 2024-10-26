import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# Stile del titolo e del sottotitolo
st.markdown(
    "<h1 style='text-align: center; font-family: sans-serif; font-weight: bold;'>SCOPRI IL FUTURO ! 😉</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; font-family: sans-serif; font-size: 18px;'>Scegli cosa vuoi filtrare</p>",
    unsafe_allow_html=True
)

# Imposta lo stato iniziale per la selezione
if "sezione_selezionata" not in st.session_state:
    st.session_state["sezione_selezionata"] = "Formazione"  # Default

# Funzione per aggiornare la sezione selezionata
def seleziona_sezione(sezione):
    st.session_state["sezione_selezionata"] = sezione

# Layout con due pulsanti centrali
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    pass
with col2:
    # Pulsanti per la selezione
    formazione = st.button("Formazione", use_container_width=True, on_click=seleziona_sezione, args=("Formazione",))
    documenti = st.button("Documenti", use_container_width=True, on_click=seleziona_sezione, args=("Documenti",))
with col3:
    pass

# Variabile per sapere se è stata selezionata formazione o documenti
sezione_corrente = st.session_state["sezione_selezionata"]
st.write(f"Hai selezionato: **{sezione_corrente}**")

# Area di caricamento file e selezione anno di riferimento
st.write("---")  # linea di separazione
file_caricato = st.file_uploader(f"Carica il file {sezione_corrente.lower()} da filtrare", type="xlsx", key="file_uploader")
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

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
if st.button("GENERA FILE"):
    if sezione_corrente == "Formazione" and file_caricato:
        df_finale = processa_corsi(file_caricato, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento)
        excel_finale = convert_df_to_excel(df_finale)
        st.download_button("Scarica file formazione", data=excel_finale, file_name=f'Corsi_scadenza_{anno_riferimento}_completo.xlsx')
    elif sezione_corrente == "Documenti" and file_caricato:
        df_finale = processa_documenti(file_caricato, df_mappa_documenti, df_periodo_documenti, anno_riferimento)
        excel_finale = convert_df_to_excel(df_finale)
        st.download_button("Scarica file documenti", data=excel_finale, file_name=f'Documenti_scadenza_{anno_riferimento}_completo.xlsx')
    else:
        st.error("Carica un file valido per generare l'output.")
