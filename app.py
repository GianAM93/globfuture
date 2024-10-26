import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# Stile del titolo e del sottotitolo
st.markdown(
    "<h1 style='text-align: center; font-family: sans-serif; font-weight: bold;'>SCOPRI IL FUTURO ! 🔮</h1>",
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

# Layout con due pulsanti affiancati
col1, col2 = st.columns([1, 1], gap="medium")
with col1:
    formazione = st.button("**Formazione**", use_container_width=True, on_click=seleziona_sezione, args=("Formazione",))
with col2:
    documenti = st.button("**Documenti**", use_container_width=True, on_click=seleziona_sezione, args=("Documenti",))

# Determina la sezione corrente in base al pulsante cliccato
sezione_corrente = st.session_state["sezione_selezionata"]

# Caricamento file e selezione anno senza linea separatrice
file_caricato = st.file_uploader(f"Carica il file {sezione_corrente.lower()} da filtrare", type="xlsx", key="file_uploader", label_visibility="collapsed")
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
    
    # Creazione del primo file (senza le colonne specificate)
    df_first_file = df_completo_aggiornato.drop(columns=['TipoCorso', 'PeriodicitaCorso', 'AnnoScadenza'], errors='ignore')
    
    # Creazione del secondo file suddiviso per GruppoCorso
    df_second_file = df_first_file.copy()
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for gruppo, group_data in df_second_file.groupby('GruppoCorso'):
            group_data = group_data.drop(columns=['TipoCorso', 'Localita', 'CodATECO', 'GruppoCorso', 'PeriodicitaCorso', 'AnnoScadenza'], errors='ignore')
            group_data.to_excel(writer, sheet_name=gruppo[:31], index=False)  # Troncamento nome foglio per Excel
    output.seek(0)
    
    return df_first_file, output.getvalue()

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

# Caricamento dati per mappatura dalla cartella .data
df_ateco = pd.read_excel(".data/AziendeAteco.xlsx")
df_aggiornamento = pd.read_excel(".data/Corso_Aggiornamento.xlsx")
df_mappa_corsi = pd.read_excel(".data/MappaCorsi.xlsx")
df_mappa_documenti = pd.read_excel(".data/MappaDocumenti.xlsx")
df_periodo_gruppi = pd.read_excel(".data/PeriodoGruppi.xlsx")
df_periodo_documenti = pd.read_excel(".data/PeriodicitaDocumenti.xlsx")

# Genera file in base alla selezione della sezione
col4, col5, col6 = st.columns([1, 1, 1])
with col5:
    if st.button("GENERA FILE", key="genera_file_button"):
        if sezione_corrente == "Formazione" and file_caricato:
            df_finale = processa_corsi(file_caricato, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento)

            # Primo file di formazione senza alcune colonne
            excel_first_file = convert_df_to_excel(df_finale.drop(columns=["TipoCorso", "PeriodicitaCorso", "AnnoScadenza"]))
            st.session_state["excel_first_file"] = excel_first_file

            # Secondo file di formazione suddiviso per GruppoCorso
            excel_second_file = save_groups_to_excel(df_finale)
            st.session_state["excel_second_file"] = excel_second_file

        elif sezione_corrente == "Documenti" and file_caricato:
            df_finale = processa_documenti(file_caricato, df_mappa_documenti, df_periodo_documenti, anno_riferimento)
            excel_finale = convert_df_to_excel(df_finale)
            st.session_state["excel_documenti_file"] = excel_finale

# Gestione pulsanti di download dei file generati
if "excel_first_file" in st.session_state:
    st.download_button("Scarica file formazione completo", data=st.session_state["excel_first_file"], file_name=f"Corsi_scadenza_{anno_riferimento}_completo.xlsx")
if "excel_second_file" in st.session_state:
    st.download_button("Scarica file formazione per Gruppo", data=st.session_state["excel_second_file"], file_name=f"Corsi_scadenza_{anno_riferimento}_per_Gruppo.xlsx")
if "excel_documenti_file" in st.session_state:
    st.download_button("Scarica file documenti", data=st.session_state["excel_documenti_file"], file_name=f"Documenti_scadenza_{anno_riferimento}_completo.xlsx")
