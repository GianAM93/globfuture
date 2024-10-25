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
df_periodo_gruppi = carica_file_excel("PeriodoGruppo.xlsx")
df_mappa_documenti = carica_file_excel("MappaDocumenti.xlsx")
df_periodo_documenti = carica_file_excel("PeriodicitaDocumenti.xlsx")

# Controllo che i DataFrame siano stati caricati
if any(df is None for df in [df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, df_mappa_documenti, df_periodo_documenti]):
    st.stop()  # Interrompe l'applicazione se manca un file

# Container principale
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Titolo e sottotitolo
st.markdown("""
    <div style="text-align: center;">
        <span style="font-size: 3rem;">🔮</span>
        <span class="title-text">SCOPRI IL FUTURO!</span>
    </div>
    <div class="subtitle-text">Scegli cosa vuoi filtrare</div>
""", unsafe_allow_html=True)

# Contenitore centrato per i pulsanti
st.markdown('<div class="button-container">', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    formazione = st.button("📚 Formazione", key="formazione")
with col2:
    documenti = st.button("📄 Documenti", key="documenti")

# Determina la sezione selezionata
if "sezione_selezionata" not in st.session_state:
    st.session_state["sezione_selezionata"] = "Formazione"
if formazione:
    st.session_state["sezione_selezionata"] = "Formazione"
if documenti:
    st.session_state["sezione_selezionata"] = "Documenti"

st.markdown(f"<h3 style='text-align: center; color: #FF4B4B;'>Sezione: {st.session_state['sezione_selezionata']}</h3>", 
            unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# File upload e selettore anno
st.markdown('<div class="section-box">', unsafe_allow_html=True)
file_caricato = st.file_uploader(
    f"Carica il file {st.session_state['sezione_selezionata'].lower()} da filtrare",
    type="xlsx",
    help="Seleziona un file Excel (.xlsx)"
)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    anno_riferimento = st.number_input(
        "Anno di riferimento",
        min_value=2023,
        step=1,
        format="%d",
        value=2025,
        help="Seleziona l'anno di riferimento per l'analisi"
    )
st.markdown('</div>', unsafe_allow_html=True)

# Funzioni di elaborazione
@st.cache_data
def processa_corsi(file_corsi, df_ateco, df_aggiornamento, df_mappa_corsi, df_periodo_gruppi, anno_riferimento):
    df_corsi = pd.read_excel(file_corsi)
    df_corsi_cleaned = df_corsi[['TipoCorso', 'DataCorso', 'RagioneSociale', 'Dipendente', 'Localita']]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Elaborazione dati ATECO...")
    df_corsi_ateco = pd.merge(df_corsi_cleaned, df_ateco, how='left', on='RagioneSociale')
    progress_bar.progress(25)
    
    status_text.text("Mappatura corsi...")
    df_corsi_mappati = pd.merge(df_corsi_ateco, df_mappa_corsi, how='left', on='TipoCorso')
    progress_bar.progress(50)
    
    df_corsi_mappati['CodATECO'] = df_corsi_mappati['CodATECO'].astype(str)
    settore_edile = df_corsi_mappati['CodATECO'].str.startswith(('41', '42', '43'))
    df_corsi_mappati.loc[settore_edile & df_corsi_mappati['GruppoCorso'].str.contains('Specifica', case=False), 'GruppoCorso'] = 'SpecificaEdile'
    
    status_text.text("Calcolo scadenze...")
    df_corsi_completo = pd.merge(df_corsi_mappati, df_periodo_gruppi, how='left', on='GruppoCorso')
    df_corsi_completo['AnnoScadenza'] = df_corsi_completo['DataCorso'].apply(lambda x: x.year) + df_corsi_completo['PeriodicitaCorso']
    progress_bar.progress(75)
    
    df_scadenza = df_corsi_completo[df_corsi_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['Dipendente', 'RagioneSociale', 'GruppoCorso'], keep='first')
    df_scadenza['DataCorso'] = pd.to_datetime(df_scadenza['DataCorso']).apply(lambda x: x.replace(year=anno_riferimento))
    df_scadenza['DataCorso'] = df_scadenza['DataCorso'].dt.strftime('%d-%m-%Y')
    
    status_text.text("Aggiornamento dati finali...")
    df_completo_aggiornato = pd.merge(df_scadenza, df_aggiornamento, on='TipoCorso', how='left')
    colonne_ordinate = ['TipoCorso', 'Aggiornamento'] + [col for col in df_completo_aggiornato.columns if col not in ['TipoCorso', 'Aggiornamento']]
    df_completo_aggiornato = df_completo_aggiornato[colonne_ordinate]
    
    progress_bar.progress(100)
    status_text.text("Elaborazione completata!")
    
    return df_completo_aggiornato

@st.cache_data
def processa_documenti(file_documenti, df_mappa_documenti, df_periodo_documenti, anno_riferimento):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Caricamento documenti...")
    df_documenti = pd.read_excel(file_documenti)
    df_documenti_cleaned = df_documenti[['Documenti', 'Data', 'RagioneSociale']]
    progress_bar.progress(33)
    
    status_text.text("Mappatura documenti...")
    df_documenti_mappati = pd.merge(df_documenti_cleaned, df_mappa_documenti, how='left', left_on='Documenti', right_on='TipoDocumento')
    progress_bar.progress(66)
    
    df_documenti_completo = pd.merge(df_documenti_mappati, df_periodo_documenti, how='left', on='GruppoDocumenti')
    df_documenti_completo['AnnoScadenza'] = df_documenti_completo['Data'].apply(lambda x: x.year) + df_documenti_completo['PeriodicitaDoc']
    df_scadenza = df_documenti_completo[df_documenti_completo['AnnoScadenza'] == anno_riferimento]
    df_scadenza = df_scadenza.drop_duplicates(subset=['RagioneSociale', 'GruppoDocumenti'], keep='first')
    
    status_text.text("Finalizzazione elaborazione...")
    df_scadenza['Data'] = pd.to_datetime(df_scadenza['Data']).apply(lambda x: x.replace(year=anno_riferimento))
    df_scadenza['Data'] = df_scadenza['Data'].dt.strftime('%d-%m-%Y')
    df_scadenza = df_scadenza.drop(columns=['Documenti', 'TipoDocumento', 'PeriodicitaDoc', 'AnnoScadenza'], errors='ignore')
    
    progress_bar.progress(100)
    status_text.text("Elaborazione completata!")
    
    return df_scadenza

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.markdown('<div class="section-box">', unsafe_allow_html=True)
if st.button("🚀 GENERA FILE", use_container_width=True):
    if file_caricato:
        try:
            with st.spinner('Elaborazione in corso...'):
                if st.session_state["sezione_selezionata"] == "Formazione":
                    df_finale = processa_corsi(file_caricato, df_ateco, df_aggiornamento, 
                                             df_mappa_corsi, df_periodo_gruppi, anno_riferimento)
                    excel_finale = convert_df_to_excel(df_finale)
                    st.success('Elaborazione completata con successo!')
                    st.download_button(
                        "📥 Scarica file formazione",
                        data=excel_finale,
                        file_name=f'Corsi_scadenza_{anno_riferimento}_completo.xlsx',
                        mime='application/vnd.ms-excel'
                    )
                else:
                    df_finale = processa_documenti(file_caricato, df_mappa_documenti, 
                                                 df_periodo_documenti, anno_riferimento)
                    excel_finale = convert_df_to_excel(df_finale)
                    st.success('Elaborazione completata con successo!')
                    st.download_button(
                        "📥 Scarica file documenti",
                        data=excel_finale,
                        file_name=f'Documenti_scadenza_{anno_riferimento}_completo.xlsx',
                        mime='application/vnd.ms-excel'
                    )
        except Exception as e:
            st.error(f"Si è verificato un errore durante l'elaborazione: {str(e)}")
    else:
        st.warning("⚠️ Carica un file valido per generare l'output.")
st.markdown('</div>', unsafe_allow_html=True)
