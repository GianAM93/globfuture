import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Carica i file di mappatura dalla cartella ".data"
def carica_file_mappatura():
    file_ateco = './.data/AziendeAteco.xlsx'
    file_mappa_corsi = './.data/MappaCorsi.xlsx'
    file_periodo_gruppi = './.data/PeriodoGruppi.xlsx'
    file_aggiornamento = './.data/Corso_Aggiornamento.xlsx'
    df_ateco = pd.read_excel(file_ateco)
    df_mappa_corsi = pd.read_excel(file_mappa_corsi)
    df_periodo_gruppi = pd.read_excel(file_periodo_gruppi)
    df_aggiornamento = pd.read_excel(file_aggiornamento)
    return df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento

# Funzione per processare i dati dei corsi
def processa_corsi(file_corsi, df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento, anno_riferimento):
    # Carica il file dei corsi
    df_corsi = pd.read_excel(file_corsi)

    # Colonne da tenere
    df_corsi_cleaned = df_corsi[['TipoCorso', 'DataCorso', 'RagioneSociale', 'Dipendente', 'Localita']]

    # Unisci dati con i file di mappatura
    df_corsi_ateco = pd.merge(df_corsi_cleaned, df_ateco, how='left', on='RagioneSociale')
    df_corsi_mappati = pd.merge(df_corsi_ateco, df_mappa_corsi, how='left', on='TipoCorso')
    settore_edile = df_corsi_mappati['CodATECO'].astype(str).str.startswith(('41', '42', '43'))
    df_corsi_mappati.loc[settore_edile & df_corsi_mappati['GruppoCorso'].str.contains('Specifica', case=False), 'GruppoCorso'] = 'SpecificaEdile'
    df_corsi_completo = pd.merge(df_corsi_mappati, df_periodo_gruppi, how='left', on='GruppoCorso')

    # Calcola anno di scadenza
    df_corsi_completo['AnnoScadenza'] = df_corsi_completo['DataCorso'].apply(lambda x: x.year) + df_corsi_completo['PeriodicitaCorso']
    df_scadenza = df_corsi_completo[df_corsi_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['Dipendente', 'RagioneSociale', 'GruppoCorso'], keep='first')
    df_scadenza['DataCorso'] = pd.to_datetime(df_scadenza['DataCorso']).apply(lambda x: x.replace(year=anno_riferimento)).dt.strftime('%d-%m-%Y')
    
    # Unisci con aggiornamento
    df_completo_aggiornato = pd.merge(df_scadenza, df_aggiornamento, on='TipoCorso', how='left')
    colonne_ordinate = ['TipoCorso', 'Aggiornamento'] + [col for col in df_completo_aggiornato.columns if col not in ['TipoCorso', 'Aggiornamento']]
    df_completo_aggiornato = df_completo_aggiornato[colonne_ordinate]

    # Primo file da generare
    df_finale_completo = df_completo_aggiornato.drop(columns=['TipoCorso', 'PeriodicitaCorso', 'AnnoScadenza'])
    excel_first_file = BytesIO()
    with pd.ExcelWriter(excel_first_file, engine='xlsxwriter') as writer:
        df_finale_completo.to_excel(writer, index=False)

    # Secondo file diviso per gruppo
    excel_grouped_file = BytesIO()
    with pd.ExcelWriter(excel_grouped_file, engine='xlsxwriter') as writer:
        for gruppo, group_data in df_completo_aggiornato.groupby('GruppoCorso'):
            group_data.drop(columns=['TipoCorso', 'Localita', 'CodATECO', 'GruppoCorso', 'PeriodicitaCorso', 'AnnoScadenza'], inplace=True)
            group_data.to_excel(writer, sheet_name=gruppo[:31], index=False)

    return excel_first_file.getvalue(), excel_grouped_file.getvalue()

# Layout dell'interfaccia
st.title("Gestione Corsi")

# Sezione per caricamento file
file_corsi = st.file_uploader("Carica il file dei corsi (Corsi_yyyy.xlsx)", type="xlsx")
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Carica i file di mappatura
df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento = carica_file_mappatura()

# Genera file se il pulsante è premuto
if st.button("Genera File") and file_corsi:
    excel_first_file, excel_grouped_file = processa_corsi(file_corsi, df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento, anno_riferimento)
    
    # Pulsanti per scaricare i file generati
    st.download_button("Scarica file completo", data=excel_first_file, file_name=f"Corsi_scadenza_{anno_riferimento}_completo.xlsx")
    st.download_button("Scarica file per gruppo", data=excel_grouped_file, file_name=f"Programma_{anno_riferimento}_per_gruppo.xlsx")
