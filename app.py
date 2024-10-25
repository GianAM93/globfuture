# Importa le librerie necessarie
import streamlit as st
import pandas as pd
from io import BytesIO
import xlsxwriter

# Funzione per processare i dati
def processa_corsi(file_corsi, file_ateco, file_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento):
    # Carica i dati dal file caricato
    df_corsi = pd.read_excel(file_corsi)
    df_ateco = pd.read_excel(file_ateco)
    df_aggiornamento = pd.read_excel(file_aggiornamento)

    # Pulizia iniziale dei dati di corsi
    df_corsi_cleaned = df_corsi[['TipoCorso', 'DataCorso', 'RagioneSociale', 'Dipendente', 'Localita']]
    
    # Unione con ATECO
    df_corsi_ateco = pd.merge(df_corsi_cleaned, df_ateco, how='left', on='RagioneSociale')
    
    # Unione con mappatura gruppi
    df_corsi_mappati = pd.merge(df_corsi_ateco, df_mappa_corsi, how='left', on='TipoCorso')

    # Identifica le aziende edili e aggiorna 'GruppoCorso' se necessario
    df_corsi_mappati['CodATECO'] = df_corsi_mappati['CodATECO'].astype(str)
    settore_edile = df_corsi_mappati['CodATECO'].str.startswith(('41', '42', '43'))
    df_corsi_mappati.loc[settore_edile & df_corsi_mappati['GruppoCorso'].str.contains('Specifica', case=False), 'GruppoCorso'] = 'SpecificaEdile'
    
    # Unione con periodicità
    df_corsi_completo = pd.merge(df_corsi_mappati, df_periodo_gruppi, how='left', on='GruppoCorso')

    # Calcolo dell'anno di scadenza
    df_corsi_completo['AnnoScadenza'] = df_corsi_completo['DataCorso'].apply(lambda x: x.year) + df_corsi_completo['PeriodicitaCorso']
    df_scadenza = df_corsi_completo[df_corsi_completo['AnnoScadenza'] == anno_riferimento]

    # Rimozione duplicati
    df_scadenza = df_scadenza.drop_duplicates(subset=['Dipendente', 'RagioneSociale', 'GruppoCorso'], keep='first')
    df_scadenza['DataCorso'] = pd.to_datetime(df_scadenza['DataCorso'], format='%d-%m-%Y').apply(lambda x: x.replace(year=anno_riferimento))
    df_scadenza['DataCorso'] = df_scadenza['DataCorso'].dt.strftime('%d-%m-%Y')

    # Unione con aggiornamenti e rimozione colonne non necessarie
    df_completo_aggiornato = pd.merge(df_scadenza, df_aggiornamento, on='TipoCorso', how='left')
    colonne_ordinate = ['TipoCorso', 'Aggiornamento'] + [col for col in df_completo_aggiornato.columns if col not in ['TipoCorso', 'Aggiornamento']]
    df_completo_aggiornato = df_completo_aggiornato[colonne_ordinate]
    
    return df_completo_aggiornato

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

# Interfaccia Streamlit
st.title("Gestione Corsi e Scadenze")

# Caricamento dei file
file_corsi = st.file_uploader("Carica il file dei corsi (Corsi_yyyy.xlsx)", type="xlsx")
file_ateco = st.file_uploader("Carica il file Aziende ATECO", type="xlsx")
file_aggiornamento = st.file_uploader("Carica il file Corso Aggiornamento", type="xlsx")

# Caricamento Google Sheet in DataFrame direttamente
df_mappa_corsi = pd.read_excel("MappaCorsi.xlsx") # Converte i Google Sheets in .xlsx per caricarli localmente
df_periodo_gruppi = pd.read_excel("PeriodoGruppi.xlsx") # Stesso approccio

# Input per l'anno di riferimento
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Esegui la generazione dei file
if st.button("Genera File"):
    if file_corsi and file_ateco and file_aggiornamento:
        df_finale = processa_corsi(file_corsi, file_ateco, file_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento)
        
        # Converte e salva in Excel
        excel_finale = convert_df_to_excel(df_finale)
        st.download_button("Scarica file completo", data=excel_finale, file_name=f'Corsi_scadenza_{anno_riferimento}_completo.xlsx')

        # Salva file diviso per gruppo
        excel_per_gruppo = save_groups_to_excel(df_finale)
        st.download_button("Scarica file diviso per gruppo", data=excel_per_gruppo, file_name=f'Programma_{anno_riferimento}_per_gruppo.xlsx')
    else:
        st.error("Carica tutti i file richiesti.")
