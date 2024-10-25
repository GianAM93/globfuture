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

    /* Container per i pulsanti */
    .button-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 20px auto;
        max-width: 600px;
    }

    /* Stile dei pulsanti non selezionati */
    .stButton > button {
        color: #FF6B6B;
        border: 2px solid #FF6B6B;
        background-color: transparent;
        font-weight: bold;
        padding: 10px 30px;
        min-width: 150px;
        transition: all 0.3s ease;
    }

    /* Stile del pulsante selezionato */
    .stButton > button:active,
    .stButton > button.selected {
        background-color: #FF6B6B !important;
        color: white !important;
        border-color: #FF6B6B !important;
    }

    /* Rimuovi il focus outline predefinito di Streamlit */
    .stButton > button:focus {
        box-shadow: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Titolo
st.markdown("<h1>SCOPRI IL FUTURO! 😉</h1>", unsafe_allow_html=True)

# Contenitore personalizzato per i pulsanti
st.markdown('<div class="button-container">', unsafe_allow_html=True)

# Imposta lo stato del pulsante selezionato
if "sezione_selezionata" not in st.session_state:
    st.session_state["sezione_selezionata"] = "Formazione"  # Default

# Crea le colonne per i pulsanti
col1, col2 = st.columns([1, 1])

# Visualizzazione dei pulsanti
with col1:
    if st.button(
        "Formazione",
        key="formazione_btn",
        help="Formazione",
        use_container_width=True
    ):
        st.session_state["sezione_selezionata"] = "Formazione"

with col2:
    if st.button(
        "Documenti",
        key="documenti_btn",
        help="Documenti",
        use_container_width=True
    ):
        st.session_state["sezione_selezionata"] = "Documenti"

st.markdown('</div>', unsafe_allow_html=True)

# Aggiungi JavaScript per gestire lo stato visivo dei pulsanti
st.markdown(
    f"""
    <script>
        // Funzione per aggiornare lo stato dei pulsanti
        function updateButtonStates() {{
            const sezione = '{st.session_state["sezione_selezionata"]}';
            const buttons = document.querySelectorAll('.stButton button');
            buttons.forEach(button => {{
                if (button.innerText === sezione) {{
                    button.classList.add('selected');
                }} else {{
                    button.classList.remove('selected');
                }}
            }});
        }}
        // Esegui all'avvio e ogni volta che cambia lo stato
        updateButtonStates();
    </script>
    """,
    unsafe_allow_html=True
)

sezione_corrente = st.session_state["sezione_selezionata"]
st.markdown("</div>", unsafe_allow_html=True)

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

