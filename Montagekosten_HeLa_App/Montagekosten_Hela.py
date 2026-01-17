import streamlit as st
from PIL import Image

# Logo anzeigen (in der Sidebar oben)
logo = Image.open("Logo_Hela_final-2.jpg")
st.sidebar.image(logo, width=200)


import pandas as pd
from datetime import datetime, timedelta
import holidays
import math

st.set_page_config(layout="wide")
st.title("🛠️ Montagekosten – Detaillierte Zuschlagsaufstellung")

# === Seitenleiste ===
st.sidebar.subheader("📊 Stundensätze (€)")
rate_mech = st.sidebar.number_input("Mechaniker (€)", value=70.0, step=1.0)
rate_elec = st.sidebar.number_input("Elektriker (€)", value=75.0, step=1.0)
rate_prog = st.sidebar.number_input("Programmierer (€)", value=100.0, step=1.0)

st.sidebar.subheader("🧾 Kundendaten")
kunde = st.sidebar.text_input("Kunde", "HeLa GmbH")
projekt = st.sidebar.text_input("Projektname", "Frankfurt Umbau")
auftragsnr = st.sidebar.text_input("Auftragsnummer", "AUF-2026-001")
einsatzort = st.sidebar.text_input("Einsatzort", "Frankfurt")

startdatum = st.sidebar.date_input("Startdatum", datetime.today())
tage = st.sidebar.slider("Anzahl Einsatztage", 1, 14, 1)

startzeit_global = st.sidebar.selectbox("Startzeit (alle Tage)", [f"{h:02d}:00" for h in range(24)], index=8)
endzeit_global = st.sidebar.selectbox("Endzeit (alle Tage)", [f"{h:02d}:00" for h in range(24)], index=17)

pausen_options = {"Keine Pause": 0, "30 Minuten": 0.5, "45 Minuten": 0.75, "1 Stunde": 1.0}
pause_global = st.sidebar.selectbox("Pause für alle Tage", list(pausen_options.keys()))

kmpreis = st.sidebar.number_input("Kilometerpreis (€)", value=1.25, step=0.05)

# Tagespauschale
st.sidebar.markdown("### 💶 Pauschale aktivieren")
pauschale_aktiv = st.sidebar.checkbox("Pauschale aktivieren")
pauschbetrag = st.sidebar.number_input("Tagespauschale (€)", value=0.0, step=1.0)

# Übernachtung / Verpflegung manuell
st.sidebar.markdown("### 🏨 Manuelle Zusatzkosten")
uebernachtungskosten = st.sidebar.number_input("Übernachtungskosten (€)", value=0.0, step=1.0)
verpflegungskosten = st.sidebar.number_input("Verpflegungskosten (€)", value=0.0, step=1.0)

# === Feiertage Baden-Württemberg ===
year = startdatum.year
bw_feiertage = holidays.Germany(years=year, state='BW')

# === Eingaben pro Tag ===
tage_daten = []
for i in range(tage):
    tag_datum = startdatum + timedelta(days=i)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### Tag {i+1}")
        datum = st.date_input(f"Datum {i+1}", tag_datum, key=f"datum_{i}")
    with col2:
        startzeit = st.selectbox(f"Startzeit {i+1}", [f"{h:02d}:00" for h in range(24)], index=int(startzeit_global[:2]), key=f"start_{i}")
    with col3:
        endzeit = st.selectbox(f"Endzeit {i+1}", [f"{h:02d}:00" for h in range(24)], index=int(endzeit_global[:2]), key=f"end_{i}")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        mech = st.number_input(f"Mechaniker", 0, 10, 0, key=f"mech_{i}")
    with col_m2:
        elec = st.number_input(f"Elektriker", 0, 10, 0, key=f"elec_{i}")
    with col_m3:
        prog = st.number_input(f"Programmierer", 0, 10, 0, key=f"prog_{i}")

    km = st.number_input("Kilometer", 0, 2000, 0, step=10, key=f"km_{i}")
    uebernachtung = st.checkbox("Übernachtung", key=f"uebernachtung_{i}")
    verpflegung = st.checkbox("Verpflegung", key=f"verpflegung_{i}")

    tage_daten.append({
        "datum": datum,
        "wochentag": datum.strftime("%A"),
        "feiertag": "Ja" if datum in bw_feiertage else "Nein",
        "start": startzeit,
        "ende": endzeit,
        "pause": pausen_options[pause_global],
        "mech": mech,
        "elec": elec,
        "prog": prog,
        "km": km,
        "uebernachtung": uebernachtung,
        "verpflegung": verpflegung
    })

# === Kalkulation ===
rows = []
gesamtkosten = 0
for eintrag in tage_daten:
    start_h = int(eintrag["start"].split(":")[0])
    end_h = int(eintrag["ende"].split(":")[0])
    arbeitszeit = (24 - start_h + end_h) if end_h <= start_h else (end_h - start_h)
    arbeitszeit -= eintrag["pause"]

    std_normal = max(0, min(8, arbeitszeit))
    std_25 = max(0, min(2, arbeitszeit - 8))
    std_50 = max(0, min(2, arbeitszeit - 10))
    std_100 = max(0, arbeitszeit - 12)

    # Summen nach Personentyp
    summe_mech = eintrag["mech"] * (std_normal * rate_mech + std_25 * rate_mech * 1.25 + std_50 * rate_mech * 1.5 + std_100 * rate_mech * 2)
    summe_elec = eintrag["elec"] * (std_normal * rate_elec + std_25 * rate_elec * 1.25 + std_50 * rate_elec * 1.5 + std_100 * rate_elec * 2)
    summe_prog = eintrag["prog"] * (std_normal * rate_prog + std_25 * rate_prog * 1.25 + std_50 * rate_prog * 1.5 + std_100 * rate_prog * 2)

    personen = eintrag["mech"] + eintrag["elec"] + eintrag["prog"]
    fahrzeuge = math.ceil(personen / 3) if personen > 0 else 0
    km_kosten = eintrag["km"] * kmpreis * fahrzeuge

    tagespausch = pauschbetrag if pauschale_aktiv else 0
    uebernachtung_kosten = uebernachtungskosten if eintrag["uebernachtung"] else 0
    verpflegung_kosten = verpflegungskosten if eintrag["verpflegung"] else 0

    summe = summe_mech + summe_elec + summe_prog + km_kosten + tagespausch + uebernachtung_kosten + verpflegung_kosten
    gesamtkosten += summe

    rows.append({
        "Datum": eintrag["datum"],
        "Wochentag": eintrag["wochentag"],
        "Feiertag": eintrag["feiertag"],
        "Zeit": f"{eintrag['start']} - {eintrag['ende']}",
        "Pause": pause_global,
        "Mechaniker": eintrag["mech"],
        "Elektriker": eintrag["elec"],
        "Programmierer": eintrag["prog"],
        "Std normal": std_normal,
        "Std 25%": std_25,
        "Std 50%": std_50,
        "Std 100%": std_100,
        "km": eintrag["km"],
        "Fahrzeuge": fahrzeuge,
        "€ km": round(km_kosten, 2),
        "€ 25%": round((eintrag["mech"] * std_25 * rate_mech * 0.25) + (eintrag["elec"] * std_25 * rate_elec * 0.25) + (eintrag["prog"] * std_25 * rate_prog * 0.25), 2),
        "€ 50%": round((eintrag["mech"] * std_50 * rate_mech * 0.5) + (eintrag["elec"] * std_50 * rate_elec * 0.5) + (eintrag["prog"] * std_50 * rate_prog * 0.5), 2),
        "€ 100%": round((eintrag["mech"] * std_100 * rate_mech) + (eintrag["elec"] * std_100 * rate_elec) + (eintrag["prog"] * std_100 * rate_prog), 2),
        "Zusatzkosten €": uebernachtung_kosten + verpflegung_kosten + tagespausch,
        "Tagessumme €": round(summe, 2)
    })

df = pd.DataFrame(rows)
st.dataframe(df)

st.success(f"💰 **Gesamtkosten (alle Tage): {gesamtkosten:,.2f} €**")

# Download Excel
from io import BytesIO
excel_buffer = BytesIO()
df.to_excel(excel_buffer, index=False, engine="openpyxl")
st.download_button("📥 Excel herunterladen", data=excel_buffer.getvalue(), file_name="Montagekosten.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
