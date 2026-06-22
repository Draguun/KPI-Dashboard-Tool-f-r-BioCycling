import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import urllib.parse

# ==========================================
# 1. KONFIGURATION DER SEITE
# ==========================================
st.set_page_config(page_title="Biogas Operations Dashboard", layout="wide")

def format_ger(val, decimals=0):
    try:
        if pd.isna(val) or np.isinf(val): return "0"
        val = float(val)
        if decimals == 0:
            s = f"{val:,.0f}"
        else:
            s = f"{val:,.{decimals}f}"
        return s.replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "0"

# ==========================================
# 1.b STAMMDATEN DER ANLAGEN (INKL. KOORDINATEN)
# ==========================================
anlagen_infos = {
    "Alteno": {
        "adresse": "Altenoer Straße 10, 15926 Luckau",
        "kontakt": "Michael Brunsch", "tel": "0151 11305773", "mail": "michael.brunsch@veolia.com",
        "kapazitaet": "85.000 t", "kategorie": "2.3",
        "beschreibung": "Leistungsstarke Biomethan-Aufbereitungsanlage (BGAA) mit einer hohen Jahreskapazität. Fokussiert auf die Einspeisung von reinem Biomethan ins Netz."
    },
    "Bardowick": {
        "adresse": "Adendorfer Weg, 21357 Bardowick",
        "koordinaten": "53.30886926107773, 10.414738931640144",
        "kontakt": "Patrick Reinecke", "tel": "0151 58763806", "mail": "patrick.reinecke@veolia.com",
        "kapazitaet": "36.300 t", "kategorie": "2.3",
        "beschreibung": "Kompakte Stromerzeugungsanlage (BHKW). Spezialisiert auf die direkte Verstromung von Biogas mit Netzeinspeisung."
    },
    "Geislingen": {
        "adresse": "In Leinetal 1, 73312 Geislingen an der Steige",
        "koordinaten": "48.581316660452295, 9.79032880186433",
        "kontakt": "Lars Gänzle", "tel": "0151 11305774", "mail": "lars.gaenzle@veolia.com",
        "kapazitaet": "34.000 t", "kategorie": "2.3",
        "beschreibung": "Kompakte Biomethan-Aufbereitungsanlage (BGAA) im Leinetal. Bereitet Rohgas effizient zu einspeisefähigem Biomethan auf."
    },
    "Gröden": {
        "adresse": "Nord 2, 49322 Gröden",
        "kontakt": "Robert Hannig", "tel": "0157 80668443", "mail": "robert.hannig@veolia.com",
        "kapazitaet": "118.000 t", "kategorie": "2.3",
        "beschreibung": "Größte Anlage im Verbund (BGAA). Verarbeitet massive Inputmengen zur großvolumigen Biomethan-Netzeinspeisung."
    },
    "Rhade": {
        "adresse": "Industriestraße 11, 27404 Rhade",
        "kontakt": "Ralf Lilienthal", "tel": "0171 4759741", "mail": "ralf.lilienthal@veolia.com",
        "kapazitaet": "55.000 t", "kategorie": "2.3",
        "beschreibung": "Mittelgroße Stromerzeugungsanlage (BHKW). Konstante Stromproduktion und Einspeisung ins lokale Stromnetz."
    },
    "Schkopau": {
        "adresse": "Berliner Straße 100, 06258 Schkopau",
        "kontakt": "Steffen Bieler", "tel": "0176 40084279", "mail": "steffen.bieler@veolia.com",
        "kapazitaet": "110.000 t", "kategorie": "2.3",
        "beschreibung": "Sehr leistungsstarkes BHKW-Kraftwerk. Wandelt große Mengen an Input effizient in elektrische Energie um."
    }
}

# ==========================================
# 2. DATEN LADEN & SMARTE BERECHNUNGEN
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdD8tMJFZRP7Y4Pzxa24uKeQauCoauqRtDDGtaQgk53zBdW0XzIUfgjFZqXVYCNh3KkhIVFA3tHgzn/pub?output=csv"
    
    try:
        df = pd.read_csv(google_sheet_url)
    except Exception as e:
        st.error("Fehler beim Laden der Daten.")
        return pd.DataFrame()

    df.columns = df.columns.str.strip()
    if df.empty: return df

    rename_map = {}
    for col in df.columns:
        c_low = col.lower()
        if 'einspeisung' in c_low and 'strom' in c_low: rename_map[col] = 'Einspeisung Strom (kWh)'
        elif 'netzbezug' in c_low and 'strom' in c_low: rename_map[col] = 'Netzbezug Strom (kWh)'
        elif 'rohgas' in c_low and 'bgaa' in c_low: rename_map[col] = 'Rohgas zur BGAA (kWh)'
        elif 'biomethan' in c_low: rename_map[col] = 'Eingespeistes Biomethan (kWh)'
        elif 'energieerlöse' in c_low: rename_map[col] = 'Energieerlöse (€/kWh)'
        elif 'bhkw produktion' in c_low: rename_map[col] = 'BHKW Produktion gesamt (kWh)'
        elif 'input fest' in c_low: rename_map[col] = 'Input Fest (t)'
        elif 'input flüssig' in c_low: rename_map[col] = 'Input Flüssig (t)'
        elif 'fackel' in c_low: rename_map[col] = 'Fackelverbrauch (kWh)'
        elif 'hygienisierung' in c_low or 'heizkessel' in c_low: rename_map[col] = 'Hygienisierung und Heizkessel (kWh)'
        elif 'auslastung' in c_low: rename_map[col] = 'Anlagenauslastung (%)'
        elif 'gatefee' in c_low: rename_map[col] = 'GateFee (€/t)'
        elif 'wasserverbrauch' in c_low: rename_map[col] = 'Wasserverbrauch (m³)'
        
    df.rename(columns=rename_map, inplace=True)

    erwartete_spalten = [
        'Input Fest (t)', 'Input Flüssig (t)', 'BHKW Produktion gesamt (kWh)',
        'Netzbezug Strom (kWh)', 'Einspeisung Strom (kWh)', 'Rohgas zur BGAA (kWh)',
        'Eingespeistes Biomethan (kWh)', 'Fackelverbrauch (kWh)',
        'Hygienisierung und Heizkessel (kWh)', 'GateFee (€/t)', 'Energieerlöse (€/kWh)',
        'Anlagenauslastung (%)', 'FOS/TAC', 'Wasserverbrauch (m³)'
    ]
    for col in erwartete_spalten:
        if col not in df.columns:
            df[col] = 0.0

    if 'Datum' in df.columns:
        df['Datum'] = pd.to_datetime(df['Datum'], format='mixed', dayfirst=True)
    elif 'Zeitstempel' in df.columns:
        df['Datum'] = pd.to_datetime(df['Zeitstempel'], format='mixed', dayfirst=True)
    
    df['Jahr'] = df['Datum'].dt.year

    def clean_numbers(val):
        if pd.isna(val): return 0.0
        val_str = str(val).strip()
        if ',' in val_str:
            val_str = val_str.replace('.', '')
            val_str = val_str.replace(',', '.')
        return val_str

    kpi_spalten = [col for col in df.columns if col not in ['Datum', 'Zeitstempel', 'Anlage', 'Typ', 'Jahr']]
    for col in kpi_spalten:
        df[col] = df[col].apply(clean_numbers)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    anlagen_typ = {
        "Alteno": "Biomethan (BGAA)",
        "Bardowick": "Strom (BHKW)",
        "Gröden": "Biomethan (BGAA)",
        "Geislingen": "Biomethan (BGAA)",
        "Schkopau": "Strom (BHKW)",
        "Rhade": "Strom (BHKW)"
    }
    if 'Anlage' in df.columns:
        df['Typ'] = df['Anlage'].map(anlagen_typ)

    def get_c(row, col_name):
        return row[col_name] if col_name in row else 0.0

    for index, row in df.iterrows():
        input_ges = get_c(row, 'Input Fest (t)') + get_c(row, 'Input Flüssig (t)')
        df.at[index, 'Input_Gesamt (t)'] = input_ges
        
        eigen_strom = (get_c(row, 'BHKW Produktion gesamt (kWh)') + get_c(row, 'Netzbezug Strom (kWh)')) - get_c(row, 'Einspeisung Strom (kWh)')
        df.at[index, 'Eigenverbrauch Strom (kWh)'] = max(0, eigen_strom)
        
        rohgas = get_c(row, 'Rohgas zur BGAA (kWh)')
        biomethan = get_c(row, 'Eingespeistes Biomethan (kWh)')
        schlupf_kwh = max(0, rohgas - biomethan)
        df.at[index, 'Schlupf BGAA (kWh)'] = schlupf_kwh
        df.at[index, 'Schlupf BGAA (%)'] = (schlupf_kwh / rohgas) * 100 if rohgas > 0 else 0.0

        ist_bgaa = "BGAA" in str(row.get('Typ', ''))
        strom_einspeisung = get_c(row, 'Einspeisung Strom (kWh)')
        eingespeist_gesamt = biomethan if ist_bgaa else strom_einspeisung
        df.at[index, 'Gesamte Einspeisung (kWh)'] = eingespeist_gesamt
        
        if input_ges > 0:
            produziert = biomethan if ist_bgaa else get_c(row, 'BHKW Produktion gesamt (kWh)')
            df.at[index, 'Spezifischer Ertrag (kWh/t)'] = produziert / input_ges
        else:
            df.at[index, 'Spezifischer Ertrag (kWh/t)'] = 0.0

        df.at[index, 'Umsatz GateFee (€)'] = get_c(row, 'GateFee (€/t)') * input_ges
        df.at[index, 'Umsatz Energieerlöse (€)'] = get_c(row, 'Energieerlöse (€/kWh)') * eingespeist_gesamt

        if ist_bgaa:
            df.at[index, 'Gesamtwirkungsgrad (%)'] = (biomethan / rohgas) * 100 if rohgas > 0 else 0.0
        else:
            bhkw_prod = get_c(row, 'BHKW Produktion gesamt (kWh)')
            df.at[index, 'Gesamtwirkungsgrad (%)'] = (strom_einspeisung / bhkw_prod) * 100 if bhkw_prod > 0 else 0.0

    if 'Datum' in df.columns:
        df = df.sort_values(by="Datum", ascending=False)

    return df

df = load_data()

if df.empty:
    st.warning("Noch keine Daten vorhanden.")
    st.stop()

# ==========================================
# 3. SIDEBAR
# ==========================================
st.sidebar.title("Veolia Biogas Dashboard")
st.sidebar.markdown("---")

st.sidebar.markdown("### 📝 Datenerfassung")
st.sidebar.link_button("Neue Daten eintragen", "https://forms.gle/FuDanXDR8wmqwUQh9", type="primary")
st.sidebar.markdown("---")

anlagen_liste = ["Alle Anlagen"] + list(df["Anlage"].dropna().unique())
st.sidebar.markdown("### 🏭 Standort wählen:")
selected_anlage = st.sidebar.radio("", anlagen_liste, label_visibility="collapsed")

st.sidebar.markdown("---")

st.sidebar.markdown("### 📅 Zeitraum:")
jahre_liste = ["Alle Jahre"] + list(df["Jahr"].dropna().unique())
selected_jahr = st.sidebar.selectbox("", jahre_liste, label_visibility="collapsed")

df_filtered = df
if selected_anlage != "Alle Anlagen":
    df_filtered = df_filtered[df_filtered["Anlage"] == selected_anlage]
if selected_jahr != "Alle Jahre":
    df_filtered = df_filtered[df_filtered["Jahr"] == selected_jahr]

if df_filtered.empty:
    st.info("Für diese Auswahl (Anlage / Jahr) liegen noch keine Daten vor.")
    st.stop()

# ==========================================
# 4. HAUPT-DASHBOARD
# ==========================================
st.title("🌱 Biogas Operations Dashboard")

# -------------------------------------------------------------
# ANSICHT A: EINZELNE ANLAGE
# -------------------------------------------------------------
if selected_anlage != "Alle Anlagen":
    typ_bezeichnung = df_filtered.iloc[0].get('Typ', 'Unbekannt')
    st.subheader(f"{selected_anlage} ({typ_bezeichnung}) - Berichtsjahr: {selected_jahr}")
    
    info = anlagen_infos.get(selected_anlage)
    if info:
        # Hier checkt der Code: Gibt es Koordinaten? Wenn ja, nutze sie. Wenn nein, nutze die Adresse!
        search_query = info.get('koordinaten', info['adresse'])
        encoded_address = urllib.parse.quote(search_query)
        # Die offizielle, robustere Map-URL
        map_url = f"https://maps.google.com/maps?q={encoded_address}&t=k&z=17&output=embed"

        with st.container():
            st.markdown("""
            <style>
            .infobox {
                background-color: #f8f9fa;
                border-left: 5px solid #28a745;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            </style>
            """, unsafe_allow_html=True)
            
            col_info, col_map = st.columns([2, 1])
            with col_info:
                st.markdown('<div class="infobox">', unsafe_allow_html=True)
                st.markdown(f"**ℹ️ Zusammenfassung:** {info['beschreibung']}")
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**📍 Betriebsstätte:**<br>{info['adresse']}", unsafe_allow_html=True)
                    st.markdown(f"<br>**⚙️ Anlagendaten:**<br>⚖️ Kapazität: {info['kapazitaet']}<br>🔖 Kategorie: {info['kategorie']}", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**📞 Notfallkontakt:**<br>👨‍💼 {info['kontakt']}<br>📱 {info['tel']}<br>✉️ <a href='mailto:{info['mail']}'>{info['mail']}</a>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_map:
                map_html = f"""
                <div style="border-radius: 12px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.15); border: 1px solid #ddd;">
                    <iframe width="100%" height="245" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="{map_url}"></iframe>
                </div>
                """
                st.components.v1.html(map_html, height=255)
    
    avg_auslastung = df_filtered['Anlagenauslastung (%)'].mean()
    avg_fostac = df_filtered['FOS/TAC'].mean()
    avg_wirkungsgrad = df_filtered['Gesamtwirkungsgrad (%)'].mean()
    avg_spez_ertrag = df_filtered['Spezifischer Ertrag (kWh/t)'].mean()
    avg_schlupf = df_filtered['Schlupf BGAA (%)'].mean()
    
    sum_eigenstrom = df_filtered['Eigenverbrauch Strom (kWh)'].sum()
    sum_einspeisung = df_filtered['Gesamte Einspeisung (kWh)'].sum()
    sum_input = df_filtered['Input_Gesamt (t)'].sum()
    summe_gatefee = df_filtered['Umsatz GateFee (€)'].sum()
    summe_erloes = df_filtered['Umsatz Energieerlöse (€)'].sum()

    st.markdown("#### 🔬 Biologie & Effizienz (Durchschnitt im gewählten Zeitraum)")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Auslastung (Ø)", f"{format_ger(avg_auslastung, 1)} %")
    c2.metric("FOS/TAC (Ø)", f"{format_ger(avg_fostac, 2)}")
    c3.metric("Netto-Wirkungsgrad (Ø)", f"{format_ger(avg_wirkungsgrad, 1)} %")
    c4.metric("Spez. Ertrag (Ø)", f"{format_ger(avg_spez_ertrag)} kWh/t")
    if "BGAA" in str(typ_bezeichnung):
        c5.metric("Gas-Schlupf (Ø)", f"{format_ger(avg_schlupf, 2)} %")
    else:
        c5.metric("Eigenstrombedarf (Summe)", f"{format_ger(sum_eigenstrom)} kWh")

    st.markdown("#### 💶 Wirtschaft & Produktion (Gesamtsummen im gewählten Zeitraum)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"GateFee (Summe)", f"{format_ger(summe_gatefee)} €")
    c2.metric(f"Energieerlöse (Summe)", f"{format_ger(summe_erloes)} €")
    c3.metric("Input (Summe)", f"{format_ger(sum_input, 1)} t")
    c4.metric("Gesamte Einspeisung", f"{format_ger(sum_einspeisung)} kWh")

    st.markdown("---")
    st.markdown("### 📈 Historische Kern-Verläufe")
    
    if 'Datum' in df_filtered.columns:
        df_chart = df_filtered.sort_values(by="Datum", ascending=True)
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            fig1 = px.line(df_chart, x="Datum", y="FOS/TAC", markers=True, title="🔬 FOS/TAC Verlauf", template="plotly_white")
            fig1.add_hline(y=0.3, line_dash="dash", line_color="green")
            st.plotly_chart(fig1, use_container_width=True)
        with r1_c2:
            fig2 = px.line(df_chart, x="Datum", y="Gesamtwirkungsgrad (%)", markers=True, title="⚡ Effizienz / Nettoquote (%)", template="plotly_white")
            fig2.update_traces(line_color="orange") 
            st.plotly_chart(fig2, use_container_width=True)

        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            fig3 = px.line(df_chart, x="Datum", y="Anlagenauslastung (%)", markers=True, title="⚙️ Anlagen-Auslastung (%)", template="plotly_white")
            fig3.update_traces(line_color="blue")
            st.plotly_chart(fig3, use_container_width=True)
        with r2_c2:
            if "BGAA" in str(typ_bezeichnung):
                df_melted = df_chart.melt(id_vars=["Datum"], value_vars=["Eingespeistes Biomethan (kWh)", "Schlupf BGAA (kWh)"], var_name="Kategorie", value_name="Energie (kWh)")
                fig4 = px.bar(df_melted, x="Datum", y="Energie (kWh)", color="Kategorie", title="⛽ Gasproduktion & Schlupf", barmode="stack", template="plotly_white")
            else:
                df_melted = df_chart.melt(id_vars=["Datum"], value_vars=["Einspeisung Strom (kWh)", "Eigenverbrauch Strom (kWh)"], var_name="Kategorie", value_name="Energie (kWh)")
                fig4 = px.bar(df_melted, x="Datum", y="Energie (kWh)", color="Kategorie", title="🔌 Stromproduktion & Eigenbedarf", barmode="stack", template="plotly_white")
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🔍 Zusätzliche Detail-Auswertungen")
        ausgeschlossene_kpis = [
            'Datum', 'Zeitstempel', 'Anlage', 'Typ', 'Jahr',
            'FOS/TAC', 'Gesamtwirkungsgrad (%)', 'Anlagenauslastung (%)',
            'Eingespeistes Biomethan (kWh)', 'Schlupf BGAA (kWh)', 'Schlupf BGAA (%)',
            'Einspeisung Strom (kWh)', 'Eigenverbrauch Strom (kWh)', 'Gesamte Einspeisung (kWh)'
        ]
        moegliche_kpis = [col for col in df.columns if col not in ausgeschlossene_kpis]
        
        selected_kpi = st.selectbox("Wähle einen weiteren Wert, den du als Verlauf sehen möchtest:", moegliche_kpis)
        if selected_kpi:
            fig_extra = px.line(df_chart, x="Datum", y=selected_kpi, markers=True, title=f"Verlauf: {selected_kpi}", template="plotly_white")
            fig_extra.update_traces(line_color="purple")
            st.plotly_chart(fig_extra, use_container_width=True)

# -------------------------------------------------------------
# ANSICHT B: ÜBERSICHT ÜBER ALLE ANLAGEN
# -------------------------------------------------------------
else:
    st.markdown("---")
    st.subheader(f"📊 Dashboard Übersicht: Alle Anlagen im Vergleich (Zeitraum: {selected_jahr})")
    
    df_agg_mean = df_filtered.groupby(['Anlage', 'Typ']).agg({
        'Gesamtwirkungsgrad (%)': 'mean',
        'Anlagenauslastung (%)': 'mean',
        'FOS/TAC': 'mean',
        'Spezifischer Ertrag (kWh/t)': 'mean'
    }).reset_index()

    df_agg_sum = df_filtered.groupby(['Anlage', 'Typ']).agg({
        'Umsatz GateFee (€)': 'sum',
        'Umsatz Energieerlöse (€)': 'sum',
        'Gesamte Einspeisung (kWh)': 'sum',
        'Input_Gesamt (t)': 'sum'
    }).reset_index()

    st.markdown("### 🍰 Performance-Vergleich: Anteile der Anlagen")
    c_pie1, c_pie2 = st.columns(2)
    with c_pie1:
        fig_pie1 = px.pie(df_agg_sum, values='Gesamte Einspeisung (kWh)', names='Anlage', 
                          title="Anteil an der Gesamteinspeisung (Energie)", template="plotly_white", hole=0.3)
        fig_pie1.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie1, use_container_width=True)
    with c_pie2:
        fig_pie2 = px.pie(df_agg_sum, values='Input_Gesamt (t)', names='Anlage', 
                          title="Anteil am Gesamt-Input (Tonnage)", template="plotly_white", hole=0.3)
        fig_pie2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie2, use_container_width=True)

    st.markdown("---")
    st.markdown("### ⚙️ Detail-Vergleich der Leistungskennzahlen")
    r1_c1, r1_c2 = st.columns(2)
    with r1_c1:
        fig_eff = px.bar(df_agg_mean, x="Anlage", y="Gesamtwirkungsgrad (%)", color="Typ", 
                         title="⚡ Netto-Wirkungsgrad (Durchschnitt)", text_auto='.1f', template="plotly_white")
        fig_eff.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_eff, use_container_width=True)
        
    with r1_c2:
        fig_ausl = px.bar(df_agg_mean, x="Anlage", y="Anlagenauslastung (%)", color="Typ", 
                          title="⚙️ Anlagen-Auslastung (Durchschnitt %)", text_auto='.1f', template="plotly_white")
        fig_ausl.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_ausl, use_container_width=True)

    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        fig_bio = px.scatter(df_agg_mean, x="FOS/TAC", y="Spezifischer Ertrag (kWh/t)", color="Typ", 
                             text="Anlage", title="🔬 Biologie vs. Ertrag (Durchschnitt)")
        fig_bio.add_vline(x=0.3, line_dash="dash", line_color="green")
        fig_bio.update_traces(marker=dict(size=14), textposition="top center")
        st.plotly_chart(fig_bio, use_container_width=True)
        
    with r2_c2:
        df_sum_melt = df_agg_sum.melt(id_vars=["Anlage", "Typ"], value_vars=["Umsatz GateFee (€)", "Umsatz Energieerlöse (€)"], 
                                      var_name="Umsatzart", value_name="Euro (€)")
        fig_umsatz = px.bar(df_sum_melt, x="Anlage", y="Euro (€)", color="Umsatzart", 
                            title="💶 Wirtschaft: Erlöse im Vergleich (Summe)", barmode="stack", template="plotly_white")
        fig_umsatz.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig_umsatz, use_container_width=True)