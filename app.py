import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Carica il CSS personalizzato da style.css
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()  # Applica il CSS personalizzato

# Imposta lo stato iniziale per il pulsante attivo
if "sezione" not in st.session_state:
    st.session_state["sezione"] = "Formazione"  # Default alla Formazione

# Funzione per alternare lo stato del pulsante
def set_sezione(sezione):
    st.session_state["sezione"] = sezione

# Interfaccia dei pulsanti "interruttori"
col1, col2 = st.columns(2)
with col1:
    if st.button(
        "Formazione",
        on_click=set_sezione,
        args=("Formazione",),
        key="formazione_btn",
        help="Seleziona Formazione",
    ):
        st.session_state["sezione"] = "Formazione"

with col2:
    if st.button(
        "Documenti",
        on_click=set_sezione,
        args=("Documenti",),
        key="documenti_btn",
        help="Seleziona Documenti",
    ):
        st.session_state["sezione"] = "Documenti"

# Assegna le classi CSS ai pulsanti
st.markdown(
    f"""
    <script>
    const btn1 = window.parent.document.querySelectorAll('.stButton button')[0];
    const btn2 = window.parent.document.querySelectorAll('.stButton button')[1];
    
    btn1.className = '{'active' if st.session_state["sezione"] == "Formazione" else 'inactive'}';
    btn2.className = '{'active' if st.session_state["sezione"] == "Documenti" else 'inactive'}';
    </script>
    """,
    unsafe_allow_html=True,
)

# Visualizza la sezione selezionata
st.write(f"Hai selezionato: {st.session_state['sezione']}")


# Carica i file di mappatura dalla cartella ".data"
def carica_file_mappatura():
    file_ateco = './.data/AziendeAteco.xlsx'
    file_mappa_corsi = './.data/MappaCorsi.xlsx'
    file_periodo_gruppi = './.data/PeriodoGruppi.xlsx'
    file_aggiornamento = './.data/Corso_Aggiornamento.xlsx'
    file_mappa_documenti = './.data/MappaDocumenti.xlsx'
    file_periodicita_documenti = './.data/PeriodicitaDocumenti.xlsx'
    
    df_ateco = pd.read_excel(file_ateco)
    df_mappa_corsi = pd.read_excel(file_mappa_corsi)
    df_periodo_gruppi = pd.read_excel(file_periodo_gruppi)
    df_aggiornamento = pd.read_excel(file_aggiornamento)
    df_mappa_documenti = pd.read_excel(file_mappa_documenti)
    df_periodicita_documenti = pd.read_excel(file_periodicita_documenti)
    
    return df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento, df_mappa_documenti, df_periodicita_documenti

# Funzione per processare i dati dei corsi
def processa_corsi(file_corsi, df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento, anno_riferimento):
    df_corsi = pd.read_excel(file_corsi)
    df_corsi_cleaned = df_corsi[['TipoCorso', 'DataCorso', 'RagioneSociale', 'Dipendente', 'Localita']]
    df_corsi_ateco = pd.merge(df_corsi_cleaned, df_ateco, how='left', on='RagioneSociale')
    df_corsi_mappati = pd.merge(df_corsi_ateco, df_mappa_corsi, how='left', on='TipoCorso')
    settore_edile = df_corsi_mappati['CodATECO'].astype(str).str.startswith(('41', '42', '43'))
    df_corsi_mappati.loc[settore_edile & df_corsi_mappati['GruppoCorso'].str.contains('Specifica', case=False), 'GruppoCorso'] = 'SpecificaEdile'
    df_corsi_completo = pd.merge(df_corsi_mappati, df_periodo_gruppi, how='left', on='GruppoCorso')
    df_corsi_completo['AnnoScadenza'] = df_corsi_completo['DataCorso'].apply(lambda x: x.year) + df_corsi_completo['PeriodicitaCorso']
    df_scadenza = df_corsi_completo[df_corsi_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['Dipendente', 'RagioneSociale', 'GruppoCorso'], keep='first')
    df_scadenza['DataCorso'] = pd.to_datetime(df_scadenza['DataCorso']).apply(lambda x: x.replace(year=anno_riferimento)).dt.strftime('%d-%m-%Y')
    df_completo_aggiornato = pd.merge(df_scadenza, df_aggiornamento, on='TipoCorso', how='left')
    colonne_ordinate = ['TipoCorso', 'Aggiornamento'] + [col for col in df_completo_aggiornato.columns if col not in ['TipoCorso', 'Aggiornamento']]
    df_completo_aggiornato = df_completo_aggiornato[colonne_ordinate]
    df_finale_completo = df_completo_aggiornato.drop(columns=['TipoCorso', 'PeriodicitaCorso', 'AnnoScadenza'])
    excel_first_file = BytesIO()
    with pd.ExcelWriter(excel_first_file, engine='xlsxwriter') as writer:
        df_finale_completo.to_excel(writer, index=False)
    excel_grouped_file = BytesIO()
    with pd.ExcelWriter(excel_grouped_file, engine='xlsxwriter') as writer:
        for gruppo, group_data in df_completo_aggiornato.groupby('GruppoCorso'):
            group_data.drop(columns=['TipoCorso', 'Localita', 'CodATECO', 'GruppoCorso', 'PeriodicitaCorso', 'AnnoScadenza'], inplace=True)
            group_data.to_excel(writer, sheet_name=gruppo[:31], index=False)
    return excel_first_file.getvalue(), excel_grouped_file.getvalue()

# Funzione per processare i documenti con rimozione dei duplicati
def processa_documenti(file_documenti, df_mappa_documenti, df_periodicita_documenti, anno_riferimento):
    df_documenti = pd.read_excel(file_documenti)
    df_documenti_cleaned = df_documenti[['Documenti', 'Data', 'RagioneSociale']]
    df_documenti_mappati = pd.merge(df_documenti_cleaned, df_mappa_documenti, how='left', left_on='Documenti', right_on='TipoDocumento')
    df_documenti_completo = pd.merge(df_documenti_mappati, df_periodicita_documenti, how='left', on='GruppoDocumenti')
    df_documenti_completo['AnnoScadenza'] = df_documenti_completo['Data'].apply(lambda x: x.year) + df_documenti_completo['PeriodicitaDoc']
    df_scadenza = df_documenti_completo[df_documenti_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['RagioneSociale', 'GruppoDocumenti'], keep='first')
    df_scadenza['Data'] = pd.to_datetime(df_scadenza['Data']).apply(lambda x: x.replace(year=anno_riferimento)).dt.strftime('%d-%m-%Y')
    df_finale_documenti = df_scadenza[['Data', 'RagioneSociale', 'GruppoDocumenti']]
    excel_documenti_file = BytesIO()
    with pd.ExcelWriter(excel_documenti_file, engine='xlsxwriter') as writer:
        df_finale_documenti.to_excel(writer, index=False)
    return excel_documenti_file.getvalue()

# Layout dell'interfaccia
st.title("Gestione Corsi e Documenti")

# Selezione tra corsi e documenti
opzione = st.selectbox("Scegli l'analisi da eseguire", ["Corsi", "Documenti"])

# Caricamento file e selezione anno
file_caricato = st.file_uploader(f"Carica il file {opzione.lower()} (Formato .xlsx)", type="xlsx")
anno_riferimento = st.number_input("Anno di riferimento", min_value=2023, step=1, format="%d", value=2025)

# Carica i file di mappatura
df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento, df_mappa_documenti, df_periodicita_documenti = carica_file_mappatura()

# Genera file in base alla selezione
if st.button("Genera File") and file_caricato:
    if opzione == "Corsi":
        excel_first_file, excel_grouped_file = processa_corsi(file_caricato, df_ateco, df_mappa_corsi, df_periodo_gruppi, df_aggiornamento, anno_riferimento)
        st.download_button("Scarica file completo dei corsi", data=excel_first_file, file_name=f"Corsi_scadenza_{anno_riferimento}_completo.xlsx")
        st.download_button("Scarica file dei corsi per gruppo", data=excel_grouped_file, file_name=f"Programma_{anno_riferimento}_per_gruppo.xlsx")
    elif opzione == "Documenti":
        excel_documenti_file = processa_documenti(file_caricato, df_mappa_documenti, df_periodicita_documenti, anno_riferimento)
        st.download_button("Scarica file dei documenti", data=excel_documenti_file, file_name=f"Documenti_scadenza_{anno_riferimento}.xlsx")
