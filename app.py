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
    if st.button("Formazione", use_container_width=True, on_click=seleziona_sezione, args=("Formazione",)):
        seleziona_sezione("Formazione")
    if st.button("Documenti", use_container_width=True, on_click=seleziona_sezione, args=("Documenti",)):
        seleziona_sezione("Documenti")
with col3:
    pass

# Mostra quale sezione è attualmente attiva
sezione_corrente = st.session_state["sezione_selezionata"]
st.write(f"Hai selezionato: **{sezione_corrente}**")

# Area di caricamento file, selezione anno e pulsante genera file
st.write("---")  # linea di separazione

file_caricato = st.file_uploader(f"Carica il file {sezione_corrente.lower()} da filtrare", type="xlsx", key="file_uploader")

anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Pulsante genera file centrato
if st.button("GENERA FILE", key="genera_file_button"):
    if file_caricato:
        # Codice per l'elaborazione in base alla sezione selezionata
        if sezione_corrente == "Formazione":
            st.write("Elaborazione del file di formazione...")  # Sostituisci con il tuo codice specifico per formazione
        elif sezione_corrente == "Documenti":
            st.write("Elaborazione del file di documenti...")  # Sostituisci con il tuo codice specifico per documenti
    else:
        st.error("Carica un file prima di generare.")


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
        return pd.DataFrame()  # Restituisce un DataFrame vuoto per evitare errori successivi
    df_documenti_completo = pd.merge(df_documenti_mappati, df_periodo_documenti, how='left', on='GruppoDocumenti')
    if 'PeriodicitaDoc' not in df_documenti_completo.columns:
        st.error("Errore: 'PeriodicitaDoc' non trovato dopo la mappatura della periodicità.")
        return pd.DataFrame()  # Restituisce un DataFrame vuoto per evitare errori successivi
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

# Interfaccia Streamlit
st.title("Gestione Corsi e Documenti")

# Selezione tra corsi e documenti
opzione = st.selectbox("Scegli l'analisi da eseguire", ["Corsi", "Documenti"])

# Caricamento file in base alla scelta
if opzione == "Corsi":
    file_corsi = st.file_uploader("Carica il file dei corsi (Corsi_yyyy.xlsx)", type="xlsx")
    df_ateco = pd.read_excel("AziendeAteco.xlsx")
    df_aggiornamento = pd.read_excel("Corso_Aggiornamento.xlsx")
    df_mappa_corsi = pd.read_excel("MappaCorsi.xlsx")
    df_periodo_gruppi = pd.read_excel("PeriodoGruppi.xlsx")
elif opzione == "Documenti":
    file_documenti = st.file_uploader("Carica il file dei documenti (Documenti_yyyy.xlsx)", type="xlsx")
    df_mappa_documenti = pd.read_excel("MappaDocumenti.xlsx")
    df_periodo_documenti = pd.read_excel("PeriodicitaDocumenti.xlsx")

# Input per l'anno di riferimento
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Esegui la generazione dei file
if st.button("Genera File"):
    if opzione == "Corsi" and file_corsi:
        df_finale = processa_corsi(file_corsi, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento)
        excel_finale = convert_df_to_excel(df_finale)
        st.download_button("Scarica file corsi completo", data=excel_finale, file_name=f'Corsi_scadenza_{anno_riferimento}_completo.xlsx')
    elif opzione == "Documenti" and file_documenti:
        df_finale = processa_documenti(file_documenti, df_mappa_documenti, df_periodo_documenti, anno_riferimento)
        excel_finale = convert_df_to_excel(df_finale)
        st.download_button("Scarica file documenti completo", data=excel_finale, file_name=f'Documenti_scadenza_{anno_riferimento}_completo.xlsx')
    else:
        st.error("Carica tutti i file richiesti.")

