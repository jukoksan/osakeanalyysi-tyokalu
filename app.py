"""
Osakeanalyysi Web-työkalu
Versio: 1.5.0
Teknologiat: Python, Streamlit, SQLite, yfinance, pandas, ta

Ominaisuudet:
- Oma salkku: osakkeiden hallinta, txt-import, tallennus tietokantaan
- Suomen pörssi -välilehti: kaikki OMXH-osakkeet listattuna ja synkattavissa
- Tekninen analyysi (RSI, SMA50, SMA200, MACD, Bollinger Bands)
- Volyymi-kaavio (väripalkit + MA20)
- Fundamenttianalyysi (P/E, P/B, ROE, osinko, D/E, EPS, nettomarginaali)
- Yrityksen kuvaus ja uutiset
- Tunnusluvut (P/E, markkina-arvo)
- Osto/Myynti/Pidä-signaalit
- Backtesting: 4 strategiaa (RSI+SMA, Momentum, Mean Reversion, MACD)
- Riskimittarit (Max Drawdown, Sharpe Ratio, Win Rate)
- Equity curve -kaavio
- Interaktiiviset kaaviot
- Automaattinen päivitys (säädettävä intervalli)
"""

import streamlit as st
import sqlite3
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import io
import os
import time
import hashlib
from deep_translator import GoogleTranslator

# Asetukset
VERSION = "1.11.0"
# Käytetään absoluuttista polkua jotta tietokanta säilyy Streamlitin uudelleenkäynnistyksissä
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stocks.db")

# --- Käyttöliittymän käännökset (FI / EN) ---
TRANSLATIONS: dict[str, dict[str, str]] = {
    "fi": {
        # Sovellus
        "app_subtitle": "Tekninen analyysi, backtesting ja päivittäiset signaalit",
        # Välilehdet
        "tab_analysis": "📊 Analyysi",
        "tab_fi": "🇫🇮 Suomen pörssi",
        "tab_us": "🇺🇸 USA:n pörssi",
        "tab_eu": "🇪🇺 EU / Pohjoismaat ETF:t",
        "tab_funds": "📒 Omat rahastot",
        "tab_backtest": "🔁 Backtesting",
        "tab_info": "📖 Käyttöohjeet",
        # Sivupalkki
        "sidebar_portfolios": "🗂️ Salkut",
        "sidebar_active": "Aktiivinen salkku",
        "sidebar_import": "📂 Tuo osakkeet tiedostosta",
        "sidebar_import_hint": "Tue muodot: .txt tai .csv, yksi tunnus per rivi tai pilkuilla erotettuna",
        "sidebar_import_example": "📄 Lataa esimerkkitiedosto",
        "sidebar_import_btn": "✅ Tuo kaikki salkkuun",
        "sidebar_no_stocks": "Ei osakkeita. Lisää osakkeita 🇫🇮 Suomen pörssi -välilehdestä.",
        "sidebar_last_portfolio": "Viimeistä salkkua ei voi poistaa.",
        "sidebar_max_portfolios": "Maksimimäärä (5) salkkuja saavutettu.",
        "sidebar_new_portfolio_placeholder": "esim. Kasvu-salkku",
        # Profiili
        "profile_nickname": "Kutsumanimi",
        "profile_email": "Sähköposti",
        "profile_save": "💾 Tallenna",
        "profile_saved": "Tallennettu!",
        "profile_change_pw": "### Vaihda salasana",
        "profile_old_pw": "Vanha salasana",
        "profile_new_pw": "Uusi salasana",
        "profile_new_pw2": "Uusi salasana uudelleen",
        "profile_change_pw_btn": "🔄 Vaihda",
        "profile_language": "🌐 Kieli / Language",
        "profile_language_save": "💾 Tallenna kieli",
        "profile_logout": "🚪 Kirjaudu ulos",
        "profile_user_mgmt": "🔒 Käyttäjänhallinta",
        "profile_create_user": "**Luo uusi käyttäjä**",
        "profile_username_lbl": "Käyttäjätunnus",
        "profile_nickname_lbl": "Kutsumanimi",
        "profile_email_lbl": "Sähköposti",
        "profile_role_lbl": "Rooli",
        "profile_password_lbl": "Salasana",
        "profile_password2_lbl": "Salasana uudelleen",
        "profile_create_btn": "➕ Luo käyttäjä",
        "profile_pw_mismatch": "Salasanat eivät täsmää.",
        "profile_pw_short": "Salasanan on oltava vähintään 4 merkkiä.",
        "profile_username_empty": "Käyttäjätunnus ei voi olla tyhjä.",
        # Kirjautuminen
        "login_username": "Käyttäjätunnus",
        "login_password": "Salasana",
        "login_btn": "🔓 Kirjaudu",
        "login_error": "❌ Väärä käyttäjätunnus tai salasana.",
        # Analyysi
        "analysis_header": "📊 Päivittäinen analyysi",
        "analysis_refresh": "🔄 Päivitä nyt",
        "analysis_last_updated": "Viimeksi päivitetty",
        "analysis_spinner": "Analysoidaan osakkeita...",
        "analysis_download": "📥 Lataa CSV",
        "analysis_detail": "🔍 Yksittäinen osake – fundamentit, kaaviot ja uutiset",
        "analysis_select": "Valitse osake",
        "analysis_no_stocks": "🇫🇮 Lisää osakkeita Suomen pörssi -välilehdestä aloittaaksesi analyysin",
        "analysis_sector": "Toimiala",
        # Sarakkeet
        "col_symbol": "Tunnus",
        "col_company": "Yritys",
        "col_price_eur": "Hinta (€)",
        "col_price_usd": "Hinta ($)",
        "col_change": "Muutos %",
        "col_signal": "Signaali",
        "col_currency": "Valuutta",
        "col_market_cap": "Markkina-arvo",
        "col_pe": "P/E",
        "col_pb": "P/B",
        "col_roe": "ROE %",
        "col_dividend": "Osinko %",
        "col_sma50": "SMA50",
        "col_sma200": "SMA200",
        "col_name": "Yritys",
        "col_etf_name": "Nimi",
        # Suomen pörssi
        "fi_header": "🇫🇮 Suomen pörssi – Nasdaq Helsinki (OMXH)",
        "fi_count": "Lista sisältää **{n}** Helsingin pörssin osaketta. Kurssit haetaan Yahoo Financesta (.HE-suffiksi).",
        "fi_auto_refresh": "🔄 Automaattinen päivitys",
        "fi_auto_refresh_help": "Päivittää Suomen pörssin datan automaattisesti",
        "fi_interval": "Väli",
        "fi_sync_all": "🔄 Synkkaa kaikki",
        "fi_clear_cache": "🗑️ Tyhjennä cache",
        "fi_cache_cleared": "Cache tyhjennetty!",
        "fi_last_synced": "🕒 Viimeksi synkattu: **{ts}**",
        "fi_search": "🔍 Hae yhtiötä tai tunnusta",
        "fi_signal_filter": "Signaali",
        "fi_signal_all": "Kaikki",
        "fi_add_multiselect": "Valitse osakkeet salkkuun lisäämistä varten",
        "fi_add_btn": "➕ Lisää valitut salkkuun",
        "fi_added": "Lisätty '{portfolio}': {added}, jo listalla: {skipped}",
        "fi_fetching": "Haetaan: {symbol} ({idx}/{total})",
        "fi_fetching_start": "Haetaan kursseja...",
        "fi_press_sync": "Paina **🔄 Synkkaa kaikki** ladataksesi ajantasaiset kurssit.",
        "fi_download": "📥 Lataa taulukko CSV",
        # USA:n pörssi
        "us_header": "🇺🇸 USA:n pörssi – NYSE / NASDAQ",
        "us_count": "Lista sisältää **{n}** yhdysvaltalaista osaketta ja ETF:ää. Kurssit haetaan Yahoo Financesta (USD).",
        "us_auto_refresh_help": "Päivittää USA:n pörssin datan automaattisesti",
        "us_add_multiselect": "Valitse osakkeet salkkuun lisäämistä varten",
        "us_add_btn": "➕ Lisää valitut salkkuun",
        "us_download": "📥 Lataa taulukko CSV",
        # EU ETF
        "eu_header": "🇪🇺 EU / Pohjoismaat – UCITS ETF:t",
        "eu_count": "Lista sisältää **{n}** eurooppalaista UCITS-indeksirahastoa (ETF). Kurssit haetaan Yahoo Financesta (Frankfurt .DE, Lontoo .L, Tukholma .ST jne.).",
        "eu_auto_refresh_help": "Päivittää EU ETF -datan automaattisesti",
        "eu_search": "🔍 Hae ETF:ää tai tunnusta",
        "eu_add_multiselect": "Valitse ETF:t salkkuun lisäämistä varten",
        "eu_add_btn": "➕ Lisää valitut salkkuun",
        "eu_download": "📥 Lataa taulukko CSV",
        # Omat rahastot
        "funds_header": "📒 Omat rahastot – manuaalinen NAV-seuranta",
        "funds_desc": "Lisää omat sijoitusrahastosi (esim. OP-, Nordea- tai Seligson-rahastot) ja kirjaa NAV-arvo käsin. Työkalu laskee tuoton ja piirtää kehityskäyrän.",
        "funds_add_expander": "➕ Lisää uusi rahasto",
        "funds_name_lbl": "Rahaston nimi *",
        "funds_name_ph": "esim. OP-Suomi Indeksi",
        "funds_isin_lbl": "ISIN-koodi (valinnainen)",
        "funds_isin_ph": "esim. FI0008807637",
        "funds_notes_lbl": "Muistiinpanot (valinnainen)",
        "funds_notes_ph": "esim. Kuukausisäästö 100 €/kk",
        "funds_add_btn": "✅ Lisää rahasto",
        "funds_name_required": "Anna rahaston nimi.",
        "funds_fund_added": "Rahasto '{name}' lisätty.",
        "funds_select": "Valitse rahasto",
        "funds_delete_btn": "🗑️ Poista rahasto",
        "funds_confirm_delete": "Poistetaanko **{name}** ja kaikki sen NAV-kirjaukset?",
        "funds_confirm_yes": "✅ Kyllä, poista",
        "funds_confirm_no": "❌ Peruuta",
        "funds_nav_date": "Päivämäärä",
        "funds_nav_value": "NAV-arvo (€)",
        "funds_nav_save": "💾 Tallenna NAV",
        "funds_no_entries": "Ei NAV-kirjauksia. Lisää ensimmäinen arvo yllä.",
        "funds_latest_nav": "Viimeisin NAV",
        "funds_first_nav": "Ensimmäinen NAV",
        "funds_total_return": "Kokonaistuotto",
        "funds_entries_count": "Kirjauksia",
        "funds_chart_title": "{name} – NAV-kehitys",
        "funds_entries_header": "##### Kirjaukset",
        "funds_col_date": "Päivämäärä",
        "funds_col_nav": "NAV (€)",
        "funds_delete_entry_expander": "🗑️ Poista kirjaus",
        "funds_delete_entry_select": "Valitse poistettava päivämäärä",
        "funds_delete_entry_btn": "🗑️ Poista valittu kirjaus",
        "funds_download": "📥 Lataa CSV",
        "funds_empty": "Lisää ensin rahasto yllä olevalla lomakkeella.",
        "funds_nav_where_header": "#### 📌 Mistä NAV-arvo löytyy?",
        "funds_nav_where_body": (
            "**OP-rahastot:** [op.fi](https://op.fi) → Rahastot → valitse rahasto → Kurssikehitys-välilehti\n\n"
            "**Muut lähteet:**\n\n"
            "| Lähde | Osoite |\n|---|---|\n"
            "| Morningstar | [morningstar.fi](https://www.morningstar.fi) |\n"
            "| Kauppalehti | [kauppalehti.fi/rahastot](https://www.kauppalehti.fi/rahastot) |\n"
            "| Nordnet | [nordnet.fi](https://www.nordnet.fi) |\n\n"
            "💡 **Vinkki:** Riittää kirjata arvo kerran kuukaudessa – kehityskäyrä näyttää silti rahaston kasvun pitkällä aikavälillä."
        ),
        # Tietoa-välilehti
        "info_header": "ℹ️ Tietoa työkalusta",
        "info_version": "Versio",
        "info_updated": "Päivitetty",
        # Backtesting
        "bt_header": "🔁 Backtesting - Strategian testaus",
        "bt_desc": "Testaa kuinka eri strategiat olisivat toimineet historialla",
        "bt_stock_label": "📈 Osake",
        "bt_all_stocks": "📂 Kaikki salkun osakkeet",
        "bt_years": "Vuodet taaksepäin",
        "bt_capital": "Aloituspääoma (€)",
        "bt_strategy": "🤖 Strategia",
        "bt_commission": "Kaupankäyntikulut (%)",
        "bt_run_btn": "▶️ Aja backtesting",
        "bt_no_stocks": "Lisää ensin osakkeita omaan salkkuun.",
        "bt_select_stock": "Valitse osake",
        # Uutiset
        "news_no_news": "Ei uutisia saatavilla.",
        "news_fetch_error": "Uutisten haku epäonnistui.",
    },
    "en": {
        # App
        "app_subtitle": "Technical analysis, backtesting and daily signals",
        # Tabs
        "tab_analysis": "📊 Analysis",
        "tab_fi": "🇫🇮 Finnish Stocks",
        "tab_us": "🇺🇸 US Stocks",
        "tab_eu": "🇪🇺 EU / Nordic ETFs",
        "tab_funds": "📒 My Funds",
        "tab_backtest": "🔁 Backtesting",
        "tab_info": "📖 User Guide",
        # Sidebar
        "sidebar_portfolios": "🗂️ Portfolios",
        "sidebar_active": "Active portfolio",
        "sidebar_import": "📂 Import stocks from file",
        "sidebar_import_hint": "Supported formats: .txt or .csv, one symbol per line or comma-separated",
        "sidebar_import_example": "📄 Download example file",
        "sidebar_import_btn": "✅ Import all to portfolio",
        "sidebar_no_stocks": "No stocks. Add stocks from the 🇫🇮 Finnish Stocks tab.",
        "sidebar_last_portfolio": "Cannot delete the last portfolio.",
        "sidebar_max_portfolios": "Maximum number (5) of portfolios reached.",
        "sidebar_new_portfolio_placeholder": "e.g. Growth portfolio",
        # Profile
        "profile_nickname": "Display name",
        "profile_email": "Email",
        "profile_save": "💾 Save",
        "profile_saved": "Saved!",
        "profile_change_pw": "### Change password",
        "profile_old_pw": "Current password",
        "profile_new_pw": "New password",
        "profile_new_pw2": "New password again",
        "profile_change_pw_btn": "🔄 Change",
        "profile_language": "🌐 Language / Kieli",
        "profile_language_save": "💾 Save language",
        "profile_logout": "🚪 Log out",
        "profile_user_mgmt": "🔒 User management",
        "profile_create_user": "**Create new user**",
        "profile_username_lbl": "Username",
        "profile_nickname_lbl": "Display name",
        "profile_email_lbl": "Email",
        "profile_role_lbl": "Role",
        "profile_password_lbl": "Password",
        "profile_password2_lbl": "Password again",
        "profile_create_btn": "➕ Create user",
        "profile_pw_mismatch": "Passwords do not match.",
        "profile_pw_short": "Password must be at least 4 characters.",
        "profile_username_empty": "Username cannot be empty.",
        # Login
        "login_username": "Username",
        "login_password": "Password",
        "login_btn": "🔓 Log in",
        "login_error": "❌ Incorrect username or password.",
        # Analysis
        "analysis_header": "📊 Daily analysis",
        "analysis_refresh": "🔄 Refresh now",
        "analysis_last_updated": "Last updated",
        "analysis_spinner": "Analysing stocks...",
        "analysis_download": "📥 Download CSV",
        "analysis_detail": "🔍 Individual stock – fundamentals, charts and news",
        "analysis_select": "Select stock",
        "analysis_no_stocks": "🇫🇮 Add stocks from the Finnish Stocks tab to start analysis",
        "analysis_sector": "Sector",
        # Columns
        "col_symbol": "Symbol",
        "col_company": "Company",
        "col_price_eur": "Price (€)",
        "col_price_usd": "Price ($)",
        "col_change": "Change %",
        "col_signal": "Signal",
        "col_currency": "Currency",
        "col_market_cap": "Market cap",
        "col_pe": "P/E",
        "col_pb": "P/B",
        "col_roe": "ROE %",
        "col_dividend": "Dividend %",
        "col_sma50": "SMA50",
        "col_sma200": "SMA200",
        "col_name": "Company",
        "col_etf_name": "Name",
        # Finnish stocks
        "fi_header": "🇫🇮 Finnish Stock Exchange – Nasdaq Helsinki (OMXH)",
        "fi_count": "The list contains **{n}** Helsinki Stock Exchange stocks. Prices fetched from Yahoo Finance (.HE suffix).",
        "fi_auto_refresh": "🔄 Auto-refresh",
        "fi_auto_refresh_help": "Automatically refreshes Finnish stock data",
        "fi_interval": "Interval",
        "fi_sync_all": "🔄 Sync all",
        "fi_clear_cache": "🗑️ Clear cache",
        "fi_cache_cleared": "Cache cleared!",
        "fi_last_synced": "🕒 Last synced: **{ts}**",
        "fi_search": "🔍 Search company or symbol",
        "fi_signal_filter": "Signal",
        "fi_signal_all": "All",
        "fi_add_multiselect": "Select stocks to add to portfolio",
        "fi_add_btn": "➕ Add selected to portfolio",
        "fi_added": "Added to '{portfolio}': {added}, already listed: {skipped}",
        "fi_fetching": "Fetching: {symbol} ({idx}/{total})",
        "fi_fetching_start": "Fetching prices...",
        "fi_press_sync": "Press **🔄 Sync all** to load current prices.",
        "fi_download": "📥 Download CSV",
        # US stocks
        "us_header": "🇺🇸 US Stock Exchange – NYSE / NASDAQ",
        "us_count": "The list contains **{n}** US stocks and ETFs. Prices fetched from Yahoo Finance (USD).",
        "us_auto_refresh_help": "Automatically refreshes US stock data",
        "us_add_multiselect": "Select stocks to add to portfolio",
        "us_add_btn": "➕ Add selected to portfolio",
        "us_download": "📥 Download CSV",
        # EU ETF
        "eu_header": "🇪🇺 EU / Nordics – UCITS ETFs",
        "eu_count": "The list contains **{n}** European UCITS ETFs. Prices fetched from Yahoo Finance (Frankfurt .DE, London .L, Stockholm .ST etc.).",
        "eu_auto_refresh_help": "Automatically refreshes EU ETF data",
        "eu_search": "🔍 Search ETF or symbol",
        "eu_add_multiselect": "Select ETFs to add to portfolio",
        "eu_add_btn": "➕ Add selected to portfolio",
        "eu_download": "📥 Download CSV",
        # My Funds
        "funds_header": "📒 My Funds – manual NAV tracking",
        "funds_desc": "Add your own investment funds (e.g. OP, Nordea or Seligson) and record the NAV manually. The tool calculates returns and plots a performance chart.",
        "funds_add_expander": "➕ Add new fund",
        "funds_name_lbl": "Fund name *",
        "funds_name_ph": "e.g. OP-Finland Index",
        "funds_isin_lbl": "ISIN code (optional)",
        "funds_isin_ph": "e.g. FI0008807637",
        "funds_notes_lbl": "Notes (optional)",
        "funds_notes_ph": "e.g. Monthly savings €100/month",
        "funds_add_btn": "✅ Add fund",
        "funds_name_required": "Please enter a fund name.",
        "funds_fund_added": "Fund '{name}' added.",
        "funds_select": "Select fund",
        "funds_delete_btn": "🗑️ Delete fund",
        "funds_confirm_delete": "Delete **{name}** and all its NAV entries?",
        "funds_confirm_yes": "✅ Yes, delete",
        "funds_confirm_no": "❌ Cancel",
        "funds_nav_date": "Date",
        "funds_nav_value": "NAV value (€)",
        "funds_nav_save": "💾 Save NAV",
        "funds_no_entries": "No NAV entries. Add the first value above.",
        "funds_latest_nav": "Latest NAV",
        "funds_first_nav": "First NAV",
        "funds_total_return": "Total return",
        "funds_entries_count": "Entries",
        "funds_chart_title": "{name} – NAV performance",
        "funds_entries_header": "##### Entries",
        "funds_col_date": "Date",
        "funds_col_nav": "NAV (€)",
        "funds_delete_entry_expander": "🗑️ Delete entry",
        "funds_delete_entry_select": "Select date to delete",
        "funds_delete_entry_btn": "🗑️ Delete selected entry",
        "funds_download": "📥 Download CSV",
        "funds_empty": "Add a fund first using the form above.",
        "funds_nav_where_header": "#### 📌 Where to find the NAV value?",
        "funds_nav_where_body": (
            "**OP Funds:** [op.fi](https://op.fi) → Funds → select fund → Price history tab\n\n"
            "**Other sources:**\n\n"
            "| Source | Address |\n|---|---|\n"
            "| Morningstar | [morningstar.fi](https://www.morningstar.fi) |\n"
            "| Kauppalehti | [kauppalehti.fi/rahastot](https://www.kauppalehti.fi/rahastot) |\n"
            "| Nordnet | [nordnet.fi](https://www.nordnet.fi) |\n\n"
            "💡 **Tip:** Recording the value once a month is enough – the chart will clearly show long-term growth."
        ),
        # Info tab
        "info_header": "ℹ️ About this tool",
        "info_version": "Version",
        "info_updated": "Updated",
        # Backtesting
        "bt_header": "🔁 Backtesting - Strategy Testing",
        "bt_desc": "Test how different strategies would have performed on historical data",
        "bt_stock_label": "📈 Stock",
        "bt_all_stocks": "📂 All portfolio stocks",
        "bt_years": "Years back",
        "bt_capital": "Initial capital (€)",
        "bt_strategy": "🤖 Strategy",
        "bt_commission": "Trading fees (%)",
        "bt_run_btn": "▶️ Run backtesting",
        "bt_no_stocks": "First add stocks to your portfolio.",
        "bt_select_stock": "Select stock",
        # News
        "news_no_news": "No news available.",
        "news_fetch_error": "Failed to fetch news.",
    },
}


def t(key: str, **kwargs) -> str:
    """Palauttaa käännetyn merkkijonon session_state-kielen mukaan.
    Tukee muuttujakorvauksia: t('fi_count', n=42) -> 'Lista sisältää **42** ...'
    """
    lang = st.session_state.get("lang", "fi")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["fi"]).get(key, TRANSLATIONS["fi"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def _remap_df_columns(df: "pd.DataFrame", col_keys: list) -> "pd.DataFrame":
    """Uudelleennimeää DataFrame-sarakkeet nykyisen kielen mukaan.

    Käsittelee tilanteen, jossa välimuistissa oleva data on tallennettu eri
    kielellä kuin aktiivinen kieli – estää KeyError-virheet.

    Args:
        df: DataFrame, jonka sarakkeet halutaan kääntää.
        col_keys: Lista TRANSLATIONS-avaimen arvoista (esim. ['col_symbol', ...]).
    Returns:
        DataFrame oikeilla sarakeotsikoilla.
    """
    remap = {}
    for key in col_keys:
        current_name = t(key)
        for lang_dict in TRANSLATIONS.values():
            other_name = lang_dict.get(key, "")
            if other_name and other_name != current_name and other_name in df.columns:
                remap[other_name] = current_name
    return df.rename(columns=remap) if remap else df


# --- Suomen pörssin osakkeet (Nasdaq Helsinki / OMXH) ---
# Lähde: Nasdaq Helsinki listatut yhtiöt, Yahoo Finance .HE-suffiksi
FINNISH_STOCKS = {
    # Suuryhtiöt (Large Cap)
    "NOKIA.HE":    "Nokia",
    "NESTE.HE":    "Neste",
    "FORTUM.HE":   "Fortum",
    "UPM.HE":      "UPM-Kymmene",
    "STERV.HE":    "Stora Enso R",
    "KNEBV.HE":    "KONE",
    "WRTBV.HE":    "Wärtsilä",
    "VALMT.HE":    "Valmet",
    "SAMPO.HE":    "Sampo",
    "ELISA.HE":    "Elisa",
    "ORNBV.HE":    "Orion B",
    "OUT1V.HE":    "Outokumpu",
    "CGCBV.HE":    "Cargotec B",
    "TIETO.HE":    "TietoEVRY",
    "METSB.HE":    "Metsä Board B",
    "KEMIRA.HE":   "Kemira",
    "KESBV.HE":    "Kesko B",
    "KESAV.HE":    "Kesko A",
    "FSKRS.HE":    "Fiskars",
    "WRT1V.HE":    "Wärtsilä (alt.)",
    # Keskisuuret (Mid Cap)
    "QTCOM.HE":    "Qt Group",
    "REVENIO.HE":  "Revenio Group",
    "TOKMANNI.HE": "Tokmanni",
    "KAMUX.HE":    "Kamux",
    "YIT.HE":      "YIT",
    "LAT1V.HE":    "Lassila & Tikanoja",
    "PIHLIS.HE":   "Pihlajalinna",
    "OLVAS.HE":    "Olvi A",
    "OLVBS.HE":    "Olvi B",
    "HKSAV.HE":    "HKScan A",
    "TELIA1.HE":   "Telia Finland",
    "ATRAV.HE":    "Atresmedia (alt.) / Atria A",
    "ATRIA.HE":    "Atria",
    "CAPMAN.HE":   "CapMan",
    "CAPIT.HE":    "Capitalium",
    "TERVE.HE":    "Pihlajalinna (alt.)",
    "OKDBV.HE":    "Outokumpu B",
    "METSO.HE":    "Metso",
    "MRLCR.HE":    "Marimekko",
    "MARIMEKKO.HE":"Marimekko",
    "SSABBV.HE":   "SSAB B",
    "SSABAV.HE":   "SSAB A",
    "KSLAV.HE":    "Kesla A",
    "KSLBV.HE":    "Kesla B",
    "ALMA.HE":     "Alma Media",
    "SANOMA.HE":   "Sanoma",
    "TELIA.HE":    "Telia",
    "AIFORIA.HE":  "Aiforia",
    "ETTE.HE":     "Enfo",
    "PIIPPO.HE":   "Piippo",
    "PANOSTX.HE":  "Panostaja",
    "PUUILO.HE":   "Puuilo",
    "EFECTE.HE":   "Efecte",
    "HARVIA.HE":   "Harvia",
    "LEHTO.HE":    "Lehto Group",
    "SUOMINEN.HE": "Suominen",
    "BOREO.HE":    "Boreo",
    "BYGGMAX.HE":  "Byggmax",
    "DIGIA.HE":    "Digia",
    "EEZY.HE":     "Eezy",
    "ENENTO.HE":   "Enento Group",
    "EVO1V.HE":    "Evli",
    "FONDIA.HE":   "Fondia",
    "GOFORE.HE":   "Gofore",
    "HELO.HE":     "Helo",
    "HEEROS.HE":   "Heeros",
    "HONKARAKENNE.HE": "Honkarakenne",
    "IFA1V.HE":    "Ilkka-Yhtymä A",
    "IFB1V.HE":    "Ilkka-Yhtymä B",
    "INDERES.HE":  "Inderes",
    "JARVI.HE":    "Järvenpään Messu",
    "KERTO.HE":    "Kertoma",
    "KREATE.HE":   "Kreate Group",
    "LOUDSPRING.HE": "Loudspring",
    "LIFA.HE":     "Lifa Air",
    "MACOM.HE":    "Macom",
    "METSA.HE":    "Metsä Fibre",
    "NETUM.HE":    "Netum Group",
    "NIXU.HE":     "Nixu",
    "NORDICID.HE": "Nordic ID",
    "OMASP.HE":    "Oma Säästöpankki",
    "OVARO.HE":    "Ovaro Kiinteistösijoitus",
    "PROSPER.HE":  "Prosper Capital",
    "QPR.HE":      "QPR Software",
    "RAUTE.HE":    "Raute",
    "REMEDY.HE":   "Remedy Entertainment",
    "REKA.HE":     "Reka Industrial",
    "ROBIT.HE":    "Robit",
    "SCANFIL.HE":  "Scanfil",
    "SIILI.HE":    "Siili Solutions",
    "SILMÄASEMA.HE": "Silmäasema",
    "SOLWERS.HE":  "Solwers",
    "SPT.HE":      "Soprano",
    "TALENOM.HE":  "Talenom",
    "TECNOTREE.HE": "Tecnotree",
    "TELE2.HE":    "Tele2",
    "TIKKURILA.HE": "Tikkurila",
    "TORNATOR.HE": "Tornator",
    "TREMOR.HE":   "Tremor Video",
    "TULIKIVI.HE": "Tulikivi A",
    "TURKISTUOTTAJAT.HE": "Turkistuottajat",
    "UPONOR.HE":   "Uponor",
    "VAISALA.HE":  "Vaisala A",
    "VAISALB.HE":  "Vaisala B",
    "VASAV.HE":    "Vasa Hospital",
    "VKL.HE":      "Viking Line",
    "VIAFIN.HE":   "Viafin Service",
    "VINCIT.HE":   "Vincit",
    "WITTED.HE":   "Witted Megacorp",
    "YAPO.HE":     "Yapo",
}

# --- Yhdysvaltain pörssin osakkeet (NYSE / NASDAQ) ---
# Lähde: S&P 500 ja muut tunnetut US-osakkeet, Yahoo Finance (ei suffiksia)
US_STOCKS = {
    # Teknologia
    "AAPL":   "Apple",
    "MSFT":   "Microsoft",
    "NVDA":   "NVIDIA",
    "GOOGL":  "Alphabet (Google) A",
    "GOOG":   "Alphabet (Google) C",
    "META":   "Meta Platforms",
    "AMZN":   "Amazon",
    "TSLA":   "Tesla",
    "AVGO":   "Broadcom",
    "AMD":    "Advanced Micro Devices",
    "INTC":   "Intel",
    "QCOM":   "Qualcomm",
    "TXN":    "Texas Instruments",
    "CRM":    "Salesforce",
    "ORCL":   "Oracle",
    "ADBE":   "Adobe",
    "NOW":    "ServiceNow",
    "SNOW":   "Snowflake",
    "PLTR":   "Palantir",
    "IBM":    "IBM",
    "CSCO":   "Cisco",
    "HPQ":    "HP Inc.",
    "DELL":   "Dell Technologies",
    "NET":    "Cloudflare",
    "PANW":   "Palo Alto Networks",
    "CRWD":   "CrowdStrike",
    # Rahoitus
    "JPM":    "JPMorgan Chase",
    "BAC":    "Bank of America",
    "WFC":    "Wells Fargo",
    "GS":     "Goldman Sachs",
    "MS":     "Morgan Stanley",
    "BLK":    "BlackRock",
    "V":      "Visa",
    "MA":     "Mastercard",
    "AXP":    "American Express",
    "BRK-B":  "Berkshire Hathaway B",
    "C":      "Citigroup",
    "USB":    "U.S. Bancorp",
    "COF":    "Capital One",
    # Terveydenhuolto
    "JNJ":    "Johnson & Johnson",
    "UNH":    "UnitedHealth Group",
    "PFE":    "Pfizer",
    "MRK":    "Merck",
    "ABBV":   "AbbVie",
    "LLY":    "Eli Lilly",
    "TMO":    "Thermo Fisher Scientific",
    "ABT":    "Abbott Laboratories",
    "BMY":    "Bristol-Myers Squibb",
    "AMGN":   "Amgen",
    "GILD":   "Gilead Sciences",
    "MDT":    "Medtronic",
    # Kulutus (harkinnanvarainen)
    "HD":     "Home Depot",
    "MCD":    "McDonald's",
    "NKE":    "Nike",
    "SBUX":   "Starbucks",
    "TGT":    "Target",
    "LOW":    "Lowe's",
    "BKNG":   "Booking Holdings",
    "MAR":    "Marriott International",
    # Kulutus (välttämätön)
    "WMT":    "Walmart",
    "PG":     "Procter & Gamble",
    "KO":     "Coca-Cola",
    "PEP":    "PepsiCo",
    "COST":   "Costco",
    "PM":     "Philip Morris",
    "MO":     "Altria",
    "CL":     "Colgate-Palmolive",
    # Teollisuus
    "BA":     "Boeing",
    "CAT":    "Caterpillar",
    "GE":     "GE Aerospace",
    "HON":    "Honeywell",
    "MMM":    "3M",
    "RTX":    "Raytheon Technologies",
    "LMT":    "Lockheed Martin",
    "DE":     "Deere & Company",
    "UPS":    "UPS",
    "FDX":    "FedEx",
    # Energia
    "XOM":    "ExxonMobil",
    "CVX":    "Chevron",
    "COP":    "ConocoPhillips",
    "SLB":    "Schlumberger",
    "EOG":    "EOG Resources",
    # Materiaalit & Muut
    "LIN":    "Linde",
    "APD":    "Air Products",
    "ECL":    "Ecolab",
    "NEM":    "Newmont",
    # Kiinteistöt
    "AMT":    "American Tower",
    "PLD":    "Prologis",
    "EQIX":   "Equinix",
    "SPG":    "Simon Property Group",
    # Viestintä & Viihde
    "DIS":    "Walt Disney",
    "NFLX":   "Netflix",
    "T":      "AT&T",
    "VZ":     "Verizon",
    "CMCSA":  "Comcast",
    "SPOT":   "Spotify",
    # Indeksirahastot (ETF)
    "SPY":    "SPDR S&P 500 ETF",
    "QQQ":    "Invesco QQQ (NASDAQ-100)",
    "DIA":    "SPDR Dow Jones ETF",
    "IWM":    "iShares Russell 2000 ETF",
    "VOO":    "Vanguard S&P 500 ETF",
}

# --- EU / Pohjoismaiset ETF:t (pörssi: Frankfurt .DE, Lontoo .L, Tukholma .ST) ---
# Saatavilla Yahoo Financessa, suomalaisille sijoittajille tyypilliset UCITS-rahastot
EU_ETFS = {
    # Maailma / Kehittynyt maailma
    "EUNL.DE":   "iShares Core MSCI World UCITS ETF (EUR, DE)",
    "IWDA.L":    "iShares Core MSCI World UCITS ETF (USD, L)",
    "SWDA.L":    "iShares Core MSCI World UCITS ETF (GBP, L)",
    "VWCE.DE":   "Vanguard FTSE All-World UCITS ETF (EUR, DE)",
    "VWRL.L":    "Vanguard FTSE All-World UCITS ETF (GBP, L)",
    "SSAC.L":    "iShares MSCI ACWI UCITS ETF (L)",
    # S&P 500
    "CSPX.L":    "iShares Core S&P 500 UCITS ETF (USD, L)",
    "SXR8.DE":   "iShares Core S&P 500 UCITS ETF (EUR, DE)",
    "VUAA.L":    "Vanguard S&P 500 UCITS ETF (USD, L)",
    "VUSA.L":    "Vanguard S&P 500 UCITS ETF (GBP, L)",
    "SPYL.L":    "SPDR S&P 500 UCITS ETF (L)",
    # NASDAQ / Teknologia
    "CNDX.L":    "iShares NASDAQ 100 UCITS ETF (USD, L)",
    "SXRV.DE":   "iShares NASDAQ 100 UCITS ETF (EUR, DE)",
    "EQQQ.L":    "Invesco EQQQ NASDAQ-100 UCITS ETF (GBP, L)",
    # Eurooppa
    "MEUD.PA":   "Lyxor Core MSCI EMU DR UCITS ETF (PA)",
    "IMEU.L":    "iShares Core MSCI Europe UCITS ETF (L)",
    "VEUR.L":    "Vanguard FTSE Developed Europe UCITS ETF (L)",
    "EXW1.DE":   "iShares Core EURO STOXX 50 UCITS ETF (DE)",
    # Pohjoismaat
    "NORDE.ST":  "Xetra-Gold ETC (Stockholm placeholder)",
    "DNDX.ST":   "Danske Invest Sverige Index (Stockholm)",
    # Kehittyvät markkinat
    "IS3N.DE":   "iShares Core MSCI EM IMI UCITS ETF (EUR, DE)",
    "EMIM.L":    "iShares Core MSCI EM IMI UCITS ETF (USD, L)",
    "VFEM.L":    "Vanguard FTSE Emerging Markets UCITS ETF (L)",
    "EEMS.L":    "iShares MSCI EM Small Cap UCITS ETF (L)",
    # Pienet yhtiöt
    "IUSN.DE":   "iShares MSCI World Small Cap UCITS ETF (DE)",
    "WSML.L":    "iShares MSCI World Small Cap UCITS ETF (L)",
    # Sektori-ETF:t
    "QDVE.DE":   "iShares S&P 500 Information Technology ETF (DE)",
    "HEAL.L":    "iShares Healthcare Innovation UCITS ETF (L)",
    "INRG.L":    "iShares Global Clean Energy UCITS ETF (L)",
    "IQQH.DE":   "iShares Global Clean Energy UCITS ETF (DE)",
    # Korko / Joukkovelkakirja
    "IEAG.L":    "iShares Core Euro Aggregate Bond UCITS ETF (L)",
    "EUNA.DE":   "iShares Core Euro Government Bond UCITS ETF (DE)",
    "IBCI.L":    "iShares € Inflation Linked Govt Bond UCITS ETF (L)",
    # Raaka-aineet
    "4GLD.DE":   "Xetra-Gold ETC (fyysinen kulta, DE)",
    "PHAU.L":    "WisdomTree Physical Gold ETC (L)",
    "ISIL.L":    "iShares Physical Silver ETC (L)",
    # Osinko-ETF:t
    "VHYL.L":    "Vanguard FTSE All-World High Dividend Yield UCITS ETF (L)",
    "IDVY.L":    "iShares Euro Dividend UCITS ETF (L)",
}


# --- Tietokanta ---
def init_db():
    """Alustaa SQLite-tietokannan ja ajaa tarvittavat migraatiot."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    c = conn.cursor()

    # Portfoliot-taulu (luodaan ensin jos ei ole olemassa)
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            user_id    INTEGER NOT NULL DEFAULT 1,
            created_at TEXT
        )
    """)

    # Migraatio: lisää user_id-sarake jos puuttuu (vanhat kannat)
    portfolio_cols = [row[1] for row in c.execute("PRAGMA table_info(portfolios)").fetchall()]
    if "user_id" not in portfolio_cols:
        c.execute("ALTER TABLE portfolios ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")

    # Tarkista onko vanha stocks-taulu ilman portfolio_id:tä
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(stocks)").fetchall()]
    if "portfolio_id" not in existing_cols and "id" in existing_cols:
        # Migraatio: siirrä vanhat osakkeet portfolioon 1
        c.execute("ALTER TABLE stocks RENAME TO stocks_old")
        c.execute("""
            CREATE TABLE stocks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol       TEXT NOT NULL,
                portfolio_id INTEGER NOT NULL DEFAULT 1,
                added_at     TEXT,
                UNIQUE(symbol, portfolio_id)
            )
        """)
        c.execute("""
            INSERT OR IGNORE INTO stocks (symbol, portfolio_id, added_at)
            SELECT symbol, 1, added_at FROM stocks_old
        """)
        c.execute("DROP TABLE stocks_old")
    elif "portfolio_id" not in existing_cols:
        # Täysin uusi taulu
        c.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol       TEXT NOT NULL,
                portfolio_id INTEGER NOT NULL DEFAULT 1,
                added_at     TEXT,
                UNIQUE(symbol, portfolio_id)
            )
        """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fi_cache (
            id        INTEGER PRIMARY KEY CHECK (id = 1),
            data      TEXT,
            synced_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS us_cache (
            id        INTEGER PRIMARY KEY CHECK (id = 1),
            data      TEXT,
            synced_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS eu_cache (
            id        INTEGER PRIMARY KEY CHECK (id = 1),
            data      TEXT,
            synced_at TEXT
        )
    """)

    # Omat rahastot -taulut
    c.execute("""
        CREATE TABLE IF NOT EXISTS funds (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL DEFAULT 1,
            name       TEXT NOT NULL,
            isin       TEXT,
            notes      TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS fund_nav (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_id    INTEGER NOT NULL,
            nav        REAL NOT NULL,
            nav_date   TEXT NOT NULL,
            created_at TEXT,
            UNIQUE(fund_id, nav_date),
            FOREIGN KEY(fund_id) REFERENCES funds(id) ON DELETE CASCADE
        )
    """)

    # Käyttäjät-taulu
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            email        TEXT,
            role         TEXT NOT NULL DEFAULT 'user',
            created_at   TEXT
        )
    """)
    # Migraatio: lisää role-sarake jos puuttuu
    user_cols = [row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in user_cols:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        # Aseta jukka adminiksi
        c.execute("UPDATE users SET role='admin' WHERE username='jukka'")
    # Migraatio: lisää language-sarake jos puuttuu
    if "language" not in user_cols:
        c.execute("ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'fi'")

    # Luo oletuskäyttäjä jos ei käyttäjiä
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_pw = hashlib.sha256("!#nassu".encode()).hexdigest()
        c.execute(
            "INSERT INTO users (username, password_hash, display_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("jukka", default_pw, "Jukka", "", "admin", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    # Migraatio: päivitä vanhan "admin"-oletuskäyttäjän tunnukset jos jukka ei vielä ole olemassa
    else:
        jukka_exists = c.execute("SELECT 1 FROM users WHERE username='jukka'").fetchone()
        if not jukka_exists:
            new_pw = hashlib.sha256("!#nassu".encode()).hexdigest()
            c.execute(
                "UPDATE users SET username=?, password_hash=?, display_name=?, role=? WHERE username=? AND display_name=?",
                ("jukka", new_pw, "Jukka", "admin", "admin", "Administraattori")
            )
        # Varmista että jukka on admin ja salasana on oikein
        correct_pw = hashlib.sha256("!#nassu".encode()).hexdigest()
        c.execute(
            "UPDATE users SET password_hash=?, display_name='Jukka', role='admin' WHERE username='jukka' AND password_hash != ?",
            (correct_pw, correct_pw)
        )
        c.execute("UPDATE users SET role='admin' WHERE username='jukka'")

    # Luo testikäyttäjä jos ei ole
    test_pw = hashlib.sha256("testpass".encode()).hexdigest()
    c.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, display_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        ("testuser", test_pw, "Test User", "", "user", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()

# --- Käyttäjäfunktiot ---

def _hash_pw(password: str) -> str:
    """Laskee SHA-256-tiivisteen annetulle salasanalle."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_by_username(username: str):
    """Palauttaa käyttäjärivin tai None."""
    conn = sqlite3.connect(DB_NAME)
    try:
        row = conn.execute(
            "SELECT id, username, password_hash, display_name, email, role, language FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    finally:
        conn.close()
    return row  # (id, username, password_hash, display_name, email, role, language)

def get_all_users() -> list[tuple]:
    """Palauttaa kaikki käyttäjät listana (id, username, display_name, role). Vain adminille."""
    conn = sqlite3.connect(DB_NAME)
    try:
        rows = conn.execute(
            "SELECT id, username, display_name, role FROM users ORDER BY id"
        ).fetchall()
    finally:
        conn.close()
    return rows

def delete_user(user_id: int) -> None:
    """Poistaa käyttäjän ja hänen salkkujensa osakkeet tietokannasta."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM stocks WHERE portfolio_id IN (SELECT id FROM portfolios WHERE user_id=?)", (user_id,))
        conn.execute("DELETE FROM portfolios WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    finally:
        conn.close()

def verify_password(username: str, password: str) -> bool:
    """Tarkistaa käyttäjätunnuksen ja salasanan."""
    row = get_user_by_username(username)
    if row is None:
        return False
    return row[2] == _hash_pw(password)

def create_user(username: str, password: str, display_name: str = "", email: str = "", role: str = "user") -> tuple[bool, str]:
    """Luo uuden käyttäjän. Palauttaa (onnistui, viesti)."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, display_name, email, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username.strip(), _hash_pw(password), display_name.strip(), email.strip(), role, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True, "Käyttäjä luotu!"
    except sqlite3.IntegrityError:
        return False, "Käyttäjätunnus on jo käytössä."
    finally:
        conn.close()

def update_user_profile(user_id: int, display_name: str, email: str) -> None:
    """Päivittää käyttäjän kutsumanian ja sähköpostiosoitteen tietokantaan."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "UPDATE users SET display_name=?, email=? WHERE id=?",
            (display_name.strip(), email.strip(), user_id)
        )
        conn.commit()
    finally:
        conn.close()

def update_user_language(user_id: int, language: str) -> None:
    """Päivittää käyttäjän kieliasetuksen tietokantaan."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("UPDATE users SET language=? WHERE id=?", (language, user_id))
        conn.commit()
    finally:
        conn.close()

def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    """Vaihtaa käyttäjän salasanan. Vanhan salasanan on täsmättävä."""
    conn = sqlite3.connect(DB_NAME)
    try:
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
        if row is None or row[0] != _hash_pw(old_password):
            return False, "Vanha salasana on väärin."
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash_pw(new_password), user_id))
        conn.commit()
    finally:
        conn.close()
    return True, "Salasana vaihdettu!"

# ---------------------------------------------

def get_portfolios(user_id: int) -> list[tuple]:
    """Palauttaa käyttäjän omat salkut listana (id, name)."""
    conn = sqlite3.connect(DB_NAME)
    try:
        rows = conn.execute(
            "SELECT id, name FROM portfolios WHERE user_id = ? ORDER BY id",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()
    return rows  # [(id, name), ...]

def ensure_user_portfolio(user_id: int) -> None:
    """Luo käyttäjälle oletussalkun jos hänellä ei ole yhtään salkkua."""
    if not get_portfolios(user_id):
        create_portfolio("Salkku 1", user_id)

def ensure_user_portfolio_by_uname(username: str) -> None:
    """Luo oletussalkun käyttäjälle käyttäjänimen perusteella (admin-käyttöön)."""
    row = get_user_by_username(username)
    if row:
        ensure_user_portfolio(row[0])

def create_portfolio(name: str, user_id: int) -> int:
    """Luo uuden salkun käyttäjälle, palauttaa sen id:n."""
    conn = sqlite3.connect(DB_NAME)
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO portfolios (name, user_id, created_at) VALUES (?, ?, ?)",
            (name, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        pid = c.lastrowid
        conn.commit()
    finally:
        conn.close()
    return pid

def rename_portfolio(portfolio_id: int, new_name: str) -> None:
    """Nimeää salkun uudelleen."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("UPDATE portfolios SET name = ? WHERE id = ?", (new_name, portfolio_id))
        conn.commit()
    finally:
        conn.close()

def delete_portfolio(portfolio_id: int) -> None:
    """Poistaa salkun ja sen kaikki osakkeet."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM stocks WHERE portfolio_id = ?", (portfolio_id,))
        conn.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
        conn.commit()
    finally:
        conn.close()

def save_fi_cache(results: list, timestamp: str) -> None:
    """Tallentaa Suomen pörssin datan tietokantaan JSON-muodossa."""
    import json
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("""
            INSERT INTO fi_cache (id, data, synced_at)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET data=excluded.data, synced_at=excluded.synced_at
        """, (json.dumps(results, ensure_ascii=False), timestamp))
        conn.commit()
    finally:
        conn.close()

def load_fi_cache() -> tuple[list | None, str | None]:
    """Lataa Suomen pörssin datan tietokannasta. Palauttaa (list, str) tai (None, None)."""
    import json
    conn = sqlite3.connect(DB_NAME)
    try:
        row = conn.execute("SELECT data, synced_at FROM fi_cache WHERE id = 1").fetchone()
    finally:
        conn.close()
    if row:
        return json.loads(row[0]), row[1]
    return None, None

def save_us_cache(results: list, timestamp: str) -> None:
    """Tallentaa USA:n pörssin datan tietokantaan JSON-muodossa."""
    import json
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("""
            INSERT INTO us_cache (id, data, synced_at)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET data=excluded.data, synced_at=excluded.synced_at
        """, (json.dumps(results, ensure_ascii=False), timestamp))
        conn.commit()
    finally:
        conn.close()

def load_us_cache() -> tuple[list | None, str | None]:
    """Lataa USA:n pörssin datan tietokannasta. Palauttaa (list, str) tai (None, None)."""
    import json
    conn = sqlite3.connect(DB_NAME)
    try:
        row = conn.execute("SELECT data, synced_at FROM us_cache WHERE id = 1").fetchone()
    finally:
        conn.close()
    if row:
        return json.loads(row[0]), row[1]
    return None, None

def save_eu_cache(results: list, timestamp: str) -> None:
    """Tallentaa EU ETF:ien datan tietokantaan JSON-muodossa."""
    import json
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("""
            INSERT INTO eu_cache (id, data, synced_at)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET data=excluded.data, synced_at=excluded.synced_at
        """, (json.dumps(results, ensure_ascii=False), timestamp))
        conn.commit()
    finally:
        conn.close()

def load_eu_cache() -> tuple[list | None, str | None]:
    """Lataa EU ETF:ien datan tietokannasta. Palauttaa (list, str) tai (None, None)."""
    import json
    conn = sqlite3.connect(DB_NAME)
    try:
        row = conn.execute("SELECT data, synced_at FROM eu_cache WHERE id = 1").fetchone()
    finally:
        conn.close()
    if row:
        return json.loads(row[0]), row[1]
    return None, None

# --- Omat rahastot -funktiot ---

def get_funds(user_id: int) -> list[dict]:
    """Palauttaa käyttäjän kaikki rahastot listana."""
    conn = sqlite3.connect(DB_NAME)
    try:
        rows = conn.execute(
            "SELECT id, name, isin, notes, created_at FROM funds WHERE user_id=? ORDER BY name",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "name": r[1], "isin": r[2], "notes": r[3], "created_at": r[4]} for r in rows]

def add_fund(user_id: int, name: str, isin: str, notes: str) -> tuple[bool, str]:
    """Lisää uuden rahaston. Palauttaa (onnistui, viesti)."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "INSERT INTO funds (user_id, name, isin, notes, created_at) VALUES (?,?,?,?,?)",
            (user_id, name.strip(), isin.strip(), notes.strip(), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True, f"Rahasto '{name}' lisätty."
    except sqlite3.IntegrityError:
        return False, "Rahasto on jo olemassa."
    finally:
        conn.close()

def delete_fund(fund_id: int) -> None:
    """Poistaa rahaston ja kaikki sen NAV-kirjaukset."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM fund_nav WHERE fund_id=?", (fund_id,))
        conn.execute("DELETE FROM funds WHERE id=?", (fund_id,))
        conn.commit()
    finally:
        conn.close()

def add_fund_nav(fund_id: int, nav: float, nav_date: str) -> tuple[bool, str]:
    """Lisää tai päivittää NAV-arvon tietylle päivämäärälle. Palauttaa (onnistui, viesti)."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            """
            INSERT INTO fund_nav (fund_id, nav, nav_date, created_at)
            VALUES (?,?,?,?)
            ON CONFLICT(fund_id, nav_date) DO UPDATE SET nav=excluded.nav
            """,
            (fund_id, nav, nav_date, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True, "NAV tallennettu."
    except Exception as e:  # noqa: BLE001
        return False, str(e)
    finally:
        conn.close()

def get_fund_nav_history(fund_id: int) -> pd.DataFrame:
    """Palauttaa rahaston NAV-historian DataFramena (nav_date, nav)."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql(
            "SELECT nav_date, nav FROM fund_nav WHERE fund_id=? ORDER BY nav_date",
            conn, params=(fund_id,)
        )
    finally:
        conn.close()
    return df

def delete_fund_nav(fund_id: int, nav_date: str) -> None:
    """Poistaa yhden NAV-kirjauksen."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM fund_nav WHERE fund_id=? AND nav_date=?", (fund_id, nav_date))
        conn.commit()
    finally:
        conn.close()

def get_stocks(portfolio_id: int = 1) -> pd.DataFrame:
    """Hakee salkun osakkeet tietokannasta."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql(
            "SELECT * FROM stocks WHERE portfolio_id = ? ORDER BY symbol",
            conn, params=(portfolio_id,)
        )
    finally:
        conn.close()
    return df

def add_stock(symbol: str, portfolio_id: int = 1) -> tuple[bool, str]:
    """Lisää osakkeen tietokantaan. Palauttaa (onnistui, viesti)."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "INSERT INTO stocks (symbol, portfolio_id, added_at) VALUES (?, ?, ?)",
            (symbol.upper(), portfolio_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True, "Osake lisätty onnistuneesti!"
    except sqlite3.IntegrityError:
        return False, "Osake on jo tässä salkussa."
    except Exception as e:
        return False, f"Virhe: {e}"
    finally:
        conn.close()

def delete_stock(symbol: str, portfolio_id: int = 1) -> None:
    """Poistaa osakkeen tietokannasta."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("DELETE FROM stocks WHERE symbol = ? AND portfolio_id = ?", (symbol, portfolio_id))
        conn.commit()
    finally:
        conn.close()

def add_stocks_bulk(symbols: list[str], portfolio_id: int = 1) -> tuple[int, int, list[str]]:
    """
    Lisää useita osakkeita kerralla tiettyyn salkkuun.
    Palauttaa (lisätty, jo_olemassa, virheelliset)
    """
    added = 0
    skipped = 0
    errors = []
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for raw in symbols:
        symbol = raw.strip().upper()
        if not symbol:
            continue
        try:
            c.execute(
                "INSERT INTO stocks (symbol, portfolio_id, added_at) VALUES (?, ?, ?)",
                (symbol, portfolio_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            added += 1
        except sqlite3.IntegrityError:
            skipped += 1
        except Exception as e:
            errors.append(f"{symbol}: {e}")
    conn.commit()
    conn.close()
    return added, skipped, errors

def parse_symbols_from_text(text: str) -> list[str]:
    """
    Parsii osaketunnukset tekstitiedostosta tai tekstistä.
    Tukee pilkku-, välilyönti- tai rivinvaihtoerottelua.
    """
    import re
    tokens = re.split(r"[\s,;]+", text)
    return [t.strip().upper() for t in tokens if t.strip()]

# --- Tekninen analyysi ---
@st.cache_data(ttl=300)
def fetch_stock_data(symbol: str, period: str = "6mo") -> tuple[pd.DataFrame, dict]:
    """Hakee osakekurssit ja info Yahoosta (välimuistissa 5 min)."""
    stock = yf.Ticker(symbol)
    df = stock.history(period=period)
    info = stock.info
    return df, info

@st.cache_data(ttl=300)
def fetch_stock_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Hakee pitkän historian backtestingiä varten (välimuistissa 5 min)."""
    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)
    return df

@st.cache_data(ttl=86400, show_spinner=False)
def translate_to_finnish(text: str) -> str:
    """Kääntää tekstin suomeksi Google Translaten avulla. Välimuistissa 24h."""
    if not text:
        return text
    try:
        # Google Translate rajoittaa 5000 merkkiin per pyynö
        chunks, size = [], 4900
        for i in range(0, len(text), size):
            chunks.append(text[i:i+size])
        translated = " ".join(
            GoogleTranslator(source="en", target="fi").translate(chunk)
            for chunk in chunks
        )
        return translated
    except Exception as e:  # noqa: BLE001
        return text  # palautetaan alkuperäinen jos käännös epäonnistuu

def get_stock_analysis(symbol, period="6mo"):
    """
    Hakee osakkeen datan ja tekee teknisen analyysin
    Palauttaa: (success, data/error_message)
    """
    try:
        # Hae data (välimuistista)
        df, info = fetch_stock_data(symbol, period)
        
        if df.empty:
            return False, f"Ei dataa osakkeelle {symbol}"
        
        df = df.reset_index()
        
        # Laske indikaattorit
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
        df["SMA50"] = df["Close"].rolling(window=50).mean()
        df["SMA200"] = df["Close"].rolling(window=200).mean()

        # MACD
        macd_ind = ta.trend.MACD(df["Close"])
        df["MACD"] = macd_ind.macd()
        df["MACD_signal"] = macd_ind.macd_signal()

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
        df["BB_upper"] = bb.bollinger_hband()
        df["BB_lower"] = bb.bollinger_lband()
        df["BB_mid"] = bb.bollinger_mavg()
        
        # Hae tunnusluvut
        latest = df.iloc[-1]
        
        # Määritä signaali
        signal = "PIDÄ"
        signal_color = "🟡"
        
        if pd.notna(latest["RSI"]) and pd.notna(latest["SMA50"]):
            if latest["RSI"] < 30 and latest["Close"] > latest["SMA50"]:
                signal = "OSTA"
                signal_color = "🟢"
            elif latest["RSI"] > 70 or (pd.notna(latest["SMA200"]) and latest["Close"] < latest["SMA200"]):
                signal = "MYY"
                signal_color = "🔴"
        
        result = {
            "symbol": symbol,
            "company": info.get("longName", symbol),
            "price": round(latest["Close"], 2),
            "rsi": round(latest["RSI"], 1) if pd.notna(latest["RSI"]) else None,
            "sma50": round(latest["SMA50"], 2) if pd.notna(latest["SMA50"]) else None,
            "sma200": round(latest["SMA200"], 2) if pd.notna(latest["SMA200"]) else None,
            "market_cap": info.get("marketCap", None),
            "pe_ratio": info.get("trailingPE", None),
            # Laajennetut fundamentit
            "pb_ratio":        info.get("priceToBook", None),
            "roe":             info.get("returnOnEquity", None),
            "dividend_yield":  info.get("dividendYield", None),
            "revenue":         info.get("totalRevenue", None),
            "profit_margin":   info.get("profitMargins", None),
            "debt_to_equity":  info.get("debtToEquity", None),
            "eps":             info.get("trailingEps", None),
            "sector":          info.get("sector", None),
            "industry":        info.get("industry", None),
            "country":         info.get("country", None),
            "website":         info.get("website", None),
            "summary":         info.get("longBusinessSummary", None),
            "signal": signal,
            "signal_color": signal_color,
            "df": df,
            "info": info,
        }
        
        return True, result
        
    except Exception as e:
        return False, f"Virhe: {str(e)}"

# --- Backtesting ---

def _generate_signals(df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """
    Laskee osto/myynti-signaalit valitun strategian mukaan.
    Palauttaa df:n Signal-sarakkeella ("BUY" / "SELL" / "HOLD").
    """
    df = df.copy()

    # Varmistetaan, että indikaattorit lasketaan vain tarvittaessa
    if "RSI" not in df.columns:
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    if "SMA50" not in df.columns:
        df["SMA50"] = df["Close"].rolling(window=50).mean()
    if "SMA200" not in df.columns:
        df["SMA200"] = df["Close"].rolling(window=200).mean()

    df["Signal"] = "HOLD"

    if strategy == "RSI + SMA (perus)":
        # Alkuperäinen strategia
        buy = (df["RSI"] < 30) & (df["Close"] > df["SMA50"])
        sell = (df["RSI"] > 70) | (df["Close"] < df["SMA200"])
        df.loc[buy, "Signal"] = "BUY"
        df.loc[sell & ~buy, "Signal"] = "SELL"

    elif strategy == "Momentum (SMA-risteytys)":
        # Golden Cross / Death Cross: SMA50 ylittää/alittaa SMA200
        prev_sma50 = df["SMA50"].shift(1)
        prev_sma200 = df["SMA200"].shift(1)
        buy = (df["SMA50"] > df["SMA200"]) & (prev_sma50 <= prev_sma200)
        sell = (df["SMA50"] < df["SMA200"]) & (prev_sma50 >= prev_sma200)
        df.loc[buy, "Signal"] = "BUY"
        df.loc[sell, "Signal"] = "SELL"

    elif strategy == "Mean Reversion (Bollinger Bands)":
        # Osta kun hinta koskettaa alakaistaa, myy yläkaistaa
        bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
        df["BB_upper"] = bb.bollinger_hband()
        df["BB_lower"] = bb.bollinger_lband()
        buy = df["Close"] <= df["BB_lower"]
        sell = df["Close"] >= df["BB_upper"]
        df.loc[buy, "Signal"] = "BUY"
        df.loc[sell & ~buy, "Signal"] = "SELL"

    elif strategy == "MACD-risteytys":
        # Osta kun MACD ylittää signaaliviivan, myy kun alittaa
        macd_ind = ta.trend.MACD(df["Close"])
        df["MACD"] = macd_ind.macd()
        df["MACD_signal"] = macd_ind.macd_signal()
        prev_macd = df["MACD"].shift(1)
        prev_sig = df["MACD_signal"].shift(1)
        buy = (df["MACD"] > df["MACD_signal"]) & (prev_macd <= prev_sig)
        sell = (df["MACD"] < df["MACD_signal"]) & (prev_macd >= prev_sig)
        df.loc[buy, "Signal"] = "BUY"
        df.loc[sell, "Signal"] = "SELL"

    return df


def _simulate_trades(df: pd.DataFrame, initial_capital: float, commission: float):
    """Simuloi kaupankäynti signaalien perusteella. Palauttaa tulokset."""
    capital = initial_capital
    shares = 0.0
    in_position = False
    trades = 0
    winning_trades = 0
    trade_history = []
    equity_curve = []
    buy_price = 0.0

    for i in range(len(df)):
        price = df.loc[i, "Close"]
        sig = df.loc[i, "Signal"]

        if sig == "BUY" and not in_position:
            cost = capital * commission
            shares = (capital - cost) / price
            capital = 0.0
            in_position = True
            buy_price = price
            trades += 1
            trade_history.append(("BUY", df.loc[i, "Date"], price))

        elif sig == "SELL" and in_position:
            gross = shares * price
            cost = gross * commission
            capital = gross - cost
            if price > buy_price:
                winning_trades += 1
            shares = 0.0
            in_position = False
            trade_history.append(("SELL", df.loc[i, "Date"], price))

        equity_curve.append({"Date": df.loc[i, "Date"], "Value": capital + shares * price})

    if in_position:
        gross = shares * df.iloc[-1]["Close"]
        strategy_final = gross - gross * commission
    else:
        strategy_final = capital

    equity_df = pd.DataFrame(equity_curve)
    equity_df["Peak"] = equity_df["Value"].cummax()
    equity_df["Drawdown"] = (equity_df["Value"] - equity_df["Peak"]) / equity_df["Peak"]
    max_drawdown = equity_df["Drawdown"].min() * 100

    daily_returns = equity_df["Value"].pct_change().dropna()
    sharpe_ratio = round(
        (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5), 2
    ) if daily_returns.std() > 0 else 0.0

    win_rate = round((winning_trades / trades * 100) if trades > 0 else 0.0, 1)
    strategy_return = ((strategy_final - initial_capital) / initial_capital) * 100

    return {
        "strategy_final": round(strategy_final, 2),
        "strategy_return": round(strategy_return, 2),
        "trades": trades,
        "win_rate": win_rate,
        "max_drawdown": round(max_drawdown, 2),
        "sharpe_ratio": sharpe_ratio,
        "trade_history": trade_history,
        "equity_df": equity_df,
    }


STRATEGIES = [
    "RSI + SMA (perus)",
    "Momentum (SMA-risteytys)",
    "Mean Reversion (Bollinger Bands)",
    "MACD-risteytys",
]


def backtest_strategy(symbol, years=5, initial_capital=10000, commission=0.001, strategy="RSI + SMA (perus)"):
    """
    Testaa valittua strategiaa historiallisella datalla.
    Vertaa Buy & Hold -menetelmään.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)

        df = fetch_stock_history(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

        if df.empty or len(df) < 200:
            return False, "Ei tarpeeksi dataa backtestingiin (vaaditaan vähintään 200 päivää)"

        df = df.reset_index()

        # Laske perus-indikaattorit
        df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
        df["SMA50"] = df["Close"].rolling(window=50).mean()
        df["SMA200"] = df["Close"].rolling(window=200).mean()

        # MACD (käytetään myös kaaviossa)
        macd_ind = ta.trend.MACD(df["Close"])
        df["MACD"] = macd_ind.macd()
        df["MACD_signal"] = macd_ind.macd_signal()

        # Generoi signaalit valitulla strategialla
        df = _generate_signals(df, strategy)

        # Simuloi kaupankäynti
        sim = _simulate_trades(df, initial_capital, commission)

        # Buy & Hold vertailu
        buy_hold_shares = (initial_capital * (1 - commission)) / df.iloc[0]["Close"]
        buy_hold_gross = buy_hold_shares * df.iloc[-1]["Close"]
        buy_hold_final = buy_hold_gross * (1 - commission)
        buy_hold_return = ((buy_hold_final - initial_capital) / initial_capital) * 100

        return True, {
            "symbol": symbol,
            "strategy": strategy,
            "initial_capital": initial_capital,
            "strategy_final": sim["strategy_final"],
            "strategy_return": sim["strategy_return"],
            "buy_hold_final": round(buy_hold_final, 2),
            "buy_hold_return": round(buy_hold_return, 2),
            "trades": sim["trades"],
            "win_rate": sim["win_rate"],
            "max_drawdown": sim["max_drawdown"],
            "sharpe_ratio": sim["sharpe_ratio"],
            "df": df,
            "trade_history": sim["trade_history"],
            "equity_df": sim["equity_df"],
        }

    except Exception as e:
        return False, f"Virhe backtestingissä: {str(e)}"

# --- Automaattinen yhteenveto ---
def generate_stock_summary(detail):
    """
    Generoi automaattisen analyysiyhteenvedon osakkeen datan perusteella.
    Palauttaa listan (teksti, väri) -tupleja.
    """
    points = []

    price     = detail.get("price")
    rsi       = detail.get("rsi")
    sma50     = detail.get("sma50")
    sma200    = detail.get("sma200")
    pe        = detail.get("pe_ratio")
    pb        = detail.get("pb_ratio")
    roe       = detail.get("roe")
    div       = detail.get("dividend_yield")
    de        = detail.get("debt_to_equity")
    margin    = detail.get("profit_margin")
    eps       = detail.get("eps")
    signal    = detail.get("signal", "")

    # Arvostus
    if pe is not None:
        if pe < 10:
            points.append((f"P/E-luku {pe:.1f} viittaa matalaan arvostukseen – osake saattaa olla aliarvostettu.", "green"))
        elif pe < 20:
            points.append((f"P/E-luku {pe:.1f} on kohtuullisella tasolla markkinoille.", "blue"))
        elif pe < 35:
            points.append((f"P/E-luku {pe:.1f} on korkeahko – markkinat odottavat kasvua.", "orange"))
        else:
            points.append((f"P/E-luku {pe:.1f} on korkea – arvostus hinnoittelee merkittävää kasvua.", "red"))

    if pb is not None:
        if pb < 1:
            points.append((f"P/B-luku {pb:.2f} on alle tasearvon – mahdollisesti aliarvostettu.", "green"))
        elif pb < 3:
            points.append((f"P/B-luku {pb:.2f} on normaalilla tasolla.", "blue"))
        else:
            points.append((f"P/B-luku {pb:.2f} on korkea suhteessa kirja-arvoon.", "orange"))

    # Kannattavuus
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct >= 20:
            points.append((f"ROE {roe_pct:.1f} % on erinomainen – yhtiö tuottaa hyvin omalle pääomalle.", "green"))
        elif roe_pct >= 10:
            points.append((f"ROE {roe_pct:.1f} % on hyvällä tasolla.", "blue"))
        elif roe_pct >= 0:
            points.append((f"ROE {roe_pct:.1f} % on heikko – pääoman tuotto jää matalaksi.", "orange"))
        else:
            points.append((f"ROE {roe_pct:.1f} % on negatiivinen – yhtiö tuottaa tappiota.", "red"))

    if margin is not None:
        m_pct = margin * 100
        if m_pct >= 20:
            points.append((f"Nettomarginaali {m_pct:.1f} % on erinomainen.", "green"))
        elif m_pct >= 8:
            points.append((f"Nettomarginaali {m_pct:.1f} % on hyvällä tasolla.", "blue"))
        elif m_pct >= 0:
            points.append((f"Nettomarginaali {m_pct:.1f} % on matala.", "orange"))
        else:
            points.append((f"Nettomarginaali {m_pct:.1f} % on negatiivinen.", "red"))

    # Tekninen analyysi
    if rsi is not None:
        if rsi < 30:
            points.append((f"RSI {rsi:.0f} – osake on teknisesti ylimyyty, mahdollinen ostomahdollisuus.", "green"))
        elif rsi > 70:
            points.append((f"RSI {rsi:.0f} – osake on teknisesti yliostettu, myyntipaine voi kasvaa.", "red"))
        else:
            points.append((f"RSI {rsi:.0f} on neutraalilla alueella (30–70).", "blue"))

    if price is not None and sma50 is not None and sma200 is not None:
        if price > sma50 > sma200:
            points.append(("Hinta on sekä SMA50- että SMA200-tason yläpuolella – vahva nouseva trendi.", "green"))
        elif price > sma50:
            points.append(("Hinta on SMA50-tason yläpuolella – lyhyen aikavälin trendi positiivinen.", "green"))
        elif price < sma50 < sma200:
            points.append(("Hinta on sekä SMA50- että SMA200-tason alapuolella – laskeva trendi.", "red"))
        else:
            points.append(("Hinta on SMA50-liukuvan keskiarvon alapuolella – heikko lyhyen aikavälin signaali.", "orange"))

    # Velkaantuminen
    if de is not None:
        if de < 0.5:
            points.append((f"Velkaantumisaste D/E {de:.2f} on matala – vakaa tase.", "green"))
        elif de < 1.5:
            points.append((f"Velkaantumisaste D/E {de:.2f} on kohtuullinen.", "blue"))
        else:
            points.append((f"Velkaantumisaste D/E {de:.2f} on korkea – velkataakka merkittävä.", "red"))

    # Osinko
    if div is not None and div > 0:
        div_pct = div  # yfinance palauttaa jo prosentteina
        if div_pct >= 4:
            points.append((f"Osinkotuotto {div_pct:.2f} % on korkea – houkutteleva tuloa hakeville sijoittajille.", "green"))
        elif div_pct >= 2:
            points.append((f"Osinkotuotto {div_pct:.2f} % on kohtuullinen.", "blue"))
        else:
            points.append((f"Osinkotuotto {div_pct:.2f} % on matala.", "orange"))
    elif div == 0 or div is None:
        points.append(("Yhtiö ei maksa osinkoa tai tieto ei ole saatavilla.", "gray"))

    # Kokonaissignaali
    if signal == "OSTA":
        points.append(("Tekninen kokonaissignaali: OSTA – molemmat indikaattorit suosivat ostoa.", "green"))
    elif signal == "MYY":
        points.append(("Tekninen kokonaissignaali: MYY – molemmat indikaattorit suosivat myyntiä.", "red"))

    return points

# --- Kaaviot ---
def plot_price_chart(df, symbol, trade_history=None):
    """Luo hintakaavion indikaattoreiden ja signaalien kanssa"""
    fig = go.Figure()
    
    # Hinta
    fig.add_trace(go.Scatter(
        x=df["Date"], 
        y=df["Close"],
        name="Hinta",
        line=dict(color="blue", width=2)
    ))
    
    # SMA50
    if "SMA50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["SMA50"],
            name="SMA50",
            line=dict(color="orange", width=1.5, dash="dash")
        ))
    
    # SMA200
    if "SMA200" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["SMA200"],
            name="SMA200",
            line=dict(color="red", width=1.5, dash="dash")
        ))

    # Bollinger Bands
    if "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["BB_upper"],
            name="BB Yläkaista",
            line=dict(color="rgba(128,0,128,0.4)", width=1),
        ))
        fig.add_trace(go.Scatter(
            x=df["Date"],
            y=df["BB_lower"],
            name="BB Alakaista",
            line=dict(color="rgba(128,0,128,0.4)", width=1),
            fill="tonexty",
            fillcolor="rgba(128,0,128,0.06)",
        ))
    
    # Kauppasignaalit (jos backtesting)
    if trade_history:
        buy_dates = [t[1] for t in trade_history if t[0] == "BUY"]
        buy_prices = [t[2] for t in trade_history if t[0] == "BUY"]
        sell_dates = [t[1] for t in trade_history if t[0] == "SELL"]
        sell_prices = [t[2] for t in trade_history if t[0] == "SELL"]
        
        if buy_dates:
            fig.add_trace(go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode="markers",
                name="Osto",
                marker=dict(color="green", size=10, symbol="triangle-up")
            ))
        
        if sell_dates:
            fig.add_trace(go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode="markers",
                name="Myynti",
                marker=dict(color="red", size=10, symbol="triangle-down")
            ))
    
    fig.update_layout(
        title=f"{symbol} - Hinta ja indikaattorit",
        xaxis_title="Päivämäärä",
        yaxis_title="Hinta (€)",
        hovermode="x unified",
        height=500
    )
    
    return fig

def plot_macd_chart(df):
    """Luo MACD-kaavion"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["MACD"],
        name="MACD",
        line=dict(color="blue", width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["MACD_signal"],
        name="Signaaliviiva",
        line=dict(color="orange", width=1.5, dash="dash")
    ))

    # Histogrammi (MACD - signaali)
    macd_hist = df["MACD"] - df["MACD_signal"]
    colors = ["green" if v >= 0 else "red" for v in macd_hist]
    fig.add_trace(go.Bar(
        x=df["Date"],
        y=macd_hist,
        name="Histogrammi",
        marker_color=colors,
        opacity=0.6
    ))

    fig.add_hline(y=0, line_color="gray", line_width=1)
    fig.update_layout(
        title="MACD",
        xaxis_title="Päivämäärä",
        yaxis_title="MACD",
        hovermode="x unified",
        height=300,
        barmode="overlay"
    )
    return fig

def plot_equity_curve(equity_df, symbol, initial_capital):
    """Luo equity curve -kaavion (pääoman kehitys)"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity_df["Date"],
        y=equity_df["Value"],
        name="Strategia",
        line=dict(color="blue", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,0,255,0.05)"
    ))

    fig.add_hline(
        y=initial_capital,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Aloituspääoma ({initial_capital:.0f} €)"
    )

    fig.update_layout(
        title=f"{symbol} – Pääoman kehitys (Equity Curve)",
        xaxis_title="Päivämäärä",
        yaxis_title="Portfolion arvo (€)",
        hovermode="x unified",
        height=350,
    )
    return fig

def plot_rsi_chart(df):
    """Luo RSI-kaavion"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=df["RSI"],
        name="RSI",
        line=dict(color="purple", width=2)
    ))
    
    # Yliostettu/ylimyyty-tasot
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Yliostettu (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Ylimyyty (30)")
    
    fig.update_layout(
        title="RSI (Relative Strength Index)",
        xaxis_title="Päivämäärä",
        yaxis_title="RSI",
        yaxis_range=[0, 100],
        hovermode="x unified",
        height=300
    )
    
    return fig


def plot_volume_chart(df, symbol):
    """Luo volyymi-kaavion väripalkeilla (vihreä = nousu, punainen = lasku)"""
    colors = [
        "green" if df["Close"].iloc[i] >= df["Close"].iloc[i - 1] else "red"
        for i in range(len(df))
    ]
    colors[0] = "gray"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Date"],
        y=df["Volume"],
        name="Volyymi",
        marker_color=colors,
        opacity=0.7,
    ))

    # 20 pv volyymikeskiarvo
    vol_ma = df["Volume"].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=df["Date"],
        y=vol_ma,
        name="Vol MA(20)",
        line=dict(color="orange", width=1.5, dash="dash"),
    ))

    fig.update_layout(
        title=f"{symbol} – Volyymi",
        xaxis_title="Päivämäärä",
        yaxis_title="Volyymi (kpl)",
        hovermode="x unified",
        height=280,
    )
    return fig

# --- Kirjautumissivu ---
def show_login_page():
    lang = st.session_state.get("lang", "fi")
    st.markdown("""
<style>
.block-container { padding-top: 4rem !important; }
.app-header h2 { margin: 0 0 0.1rem 0; font-size: 1.4rem; font-weight: 700; }
.app-header p  { margin: 0 0 1rem 0; font-size: 0.85rem; color: #666; }
.login-box { max-width: 420px; }
@media (max-width: 768px) {
    .app-header h2 { font-size: 1.1rem !important; }
}
</style>
<div class="app-header">
  <h2>📈 Osakeanalyysi-työkalu v""" + VERSION + """</h2>
  <p>""" + t("app_subtitle") + """</p>
</div>
""", unsafe_allow_html=True)

    # Kielenvalinta ennen kirjautumista
    col_lang, _ = st.columns([1, 3])
    with col_lang:
        login_lang = st.selectbox(
            "🌐",
            options=["fi", "en"],
            format_func=lambda l: "🇫🇮 Suomi" if l == "fi" else "🇬🇧 English",
            index=0 if lang == "fi" else 1,
            key="login_lang_select",
            label_visibility="collapsed",
        )
        if login_lang != lang:
            st.session_state["lang"] = login_lang
            st.rerun()

    with st.form("login_form"):
        username = st.text_input(t("login_username"))
        password = st.text_input(t("login_password"), type="password")
        submitted = st.form_submit_button(t("login_btn"), use_container_width=True)
        if submitted:
            if verify_password(username.strip(), password):
                row = get_user_by_username(username.strip())
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = row[0]
                st.session_state["username"] = row[1]
                st.session_state["display_name"] = row[3] or row[1]
                st.session_state["email"] = row[4] or ""
                st.session_state["role"] = row[5]
                st.session_state["lang"] = row[6] if row[6] in ("fi", "en") else "fi"
                ensure_user_portfolio(row[0])
                st.rerun()
            else:
                st.error(t("login_error"))


def show_profile_sidebar():
    """Näyttää käyttäjäprofiilin sivupalkissa."""
    display = st.session_state.get("display_name", st.session_state.get("username", ""))
    user_id = st.session_state["user_id"]
    role    = st.session_state.get("role", "user")
    role_badge = "🔒 Admin" if role == "admin" else "👤 User"

    with st.expander(f"{role_badge} {display}", expanded=False):
        st.markdown("### Profiili / Profile")
        with st.form("profile_form"):
            upd_display = st.text_input(t("profile_nickname"), value=st.session_state.get("display_name", ""))
            upd_email   = st.text_input(t("profile_email"),    value=st.session_state.get("email", ""))
            if st.form_submit_button(t("profile_save"), use_container_width=True):
                update_user_profile(user_id, upd_display, upd_email)
                st.session_state["display_name"] = upd_display
                st.session_state["email"] = upd_email
                st.success(t("profile_saved"))
                st.rerun()

        # Kielenvalinta
        st.markdown("---")
        st.markdown(f"**{t('profile_language')}**")
        with st.form("lang_form"):
            current_lang = st.session_state.get("lang", "fi")
            new_lang = st.selectbox(
                t("profile_language"),
                options=["fi", "en"],
                format_func=lambda l: "🇫🇮 Suomi" if l == "fi" else "🇬🇧 English",
                index=0 if current_lang == "fi" else 1,
                label_visibility="collapsed",
            )
            if st.form_submit_button(t("profile_language_save"), use_container_width=True):
                update_user_language(user_id, new_lang)
                st.session_state["lang"] = new_lang
                st.rerun()

        st.markdown("---")
        st.markdown(t("profile_change_pw"))
        with st.form("pw_form"):
            old_pw  = st.text_input(t("profile_old_pw"), type="password")
            new_pw1 = st.text_input(t("profile_new_pw"), type="password")
            new_pw2 = st.text_input(t("profile_new_pw2"), type="password")
            if st.form_submit_button(t("profile_change_pw_btn"), use_container_width=True):
                if new_pw1 != new_pw2:
                    st.error(t("profile_pw_mismatch"))
                elif len(new_pw1) < 4:
                    st.error(t("profile_pw_short"))
                else:
                    ok, msg = change_password(user_id, old_pw, new_pw1)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        # Admin: käyttäjänhallinta
        if role == "admin":
            st.markdown("---")
            st.markdown(t("profile_user_mgmt"))
            users = get_all_users()
            for u in users:
                uid, uname, udisp, urole = u
                badge = "🔒" if urole == "admin" else "👤"
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"{badge} **{uname}** ({udisp or '-'})")
                with col2:
                    if uid != user_id:
                        if st.button("🗑️", key=f"del_user_{uid}", help=f"Poista {uname}"):
                            delete_user(uid)
                            st.rerun()

            st.markdown(t("profile_create_user"))
            with st.form("admin_create_user"):
                nu_username = st.text_input(t("profile_username_lbl"))
                nu_display  = st.text_input(t("profile_nickname_lbl"))
                nu_email    = st.text_input(t("profile_email_lbl"))
                nu_role     = st.selectbox(t("profile_role_lbl"), options=["user", "admin"],
                                           format_func=lambda r: "👤 User" if r == "user" else "🔒 Admin")
                nu_pw1      = st.text_input(t("profile_password_lbl"), type="password")
                nu_pw2      = st.text_input(t("profile_password2_lbl"), type="password")
                if st.form_submit_button(t("profile_create_btn"), use_container_width=True):
                    if not nu_username.strip():
                        st.error(t("profile_username_empty"))
                    elif len(nu_pw1) < 4:
                        st.error(t("profile_pw_short"))
                    elif nu_pw1 != nu_pw2:
                        st.error(t("profile_pw_mismatch"))
                    else:
                        ok, msg = create_user(nu_username, nu_pw1, nu_display, nu_email, nu_role)
                        if ok:
                            ensure_user_portfolio_by_uname(nu_username)
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        st.markdown("---")
        if st.button(t("profile_logout"), use_container_width=True):
            for key in ["logged_in", "user_id", "username", "display_name", "email", "role", "lang"]:
                st.session_state.pop(key, None)
            st.rerun()



# --- Streamlit UI ---
def main():
    st.set_page_config(
        page_title="Osakeanalyysi-työkalu",
        page_icon="📈",
        layout="wide"
    )

    # Alusta tietokanta
    init_db()

    # Tarkista kirjautuminen
    if not st.session_state.get("logged_in", False):
        show_login_page()
        st.stop()

    st.markdown("""
<style>
/* Pienennä ylätila */
.block-container { padding-top: 4rem !important; }
/* Otsikkofonttikoko */
.app-header h2 { margin: 0 0 0.1rem 0; font-size: 1.4rem; font-weight: 700; }
.app-header p  { margin: 0; font-size: 0.85rem; color: #666; }
@media (max-width: 768px) {
    .app-header h2 { font-size: 1.1rem !important; }
}
</style>
<div class="app-header">
  <h2>📈 Osakeanalyysi-työkalu v""" + VERSION + """</h2>
  <p>""" + t("app_subtitle") + """</p>
</div>
""", unsafe_allow_html=True)
    
    # Sivupalkki - Osakkeiden hallinta
    with st.sidebar:
        show_profile_sidebar()
        st.header("🗂️ Salkut")

        portfolios = get_portfolios(st.session_state["user_id"])
        portfolio_names = [p[1] for p in portfolios]
        portfolio_ids   = [p[0] for p in portfolios]

        # Valitse aktiivinen salkku
        active_idx = st.selectbox(
            "Aktiivinen salkku",
            options=range(len(portfolios)),
            format_func=lambda i: portfolio_names[i],
            key="active_portfolio_idx",
        )
        active_portfolio_id   = portfolio_ids[active_idx]
        active_portfolio_name = portfolio_names[active_idx]

        # Salkun hallinta: nimeä uudelleen / poista
        with st.expander("✏️ Hallitse salkkuja"):
            # Uudelleennimeä
            new_name = st.text_input("Uusi nimi aktiiviselle salkulle", value=active_portfolio_name, key="rename_input")
            if st.button("💾 Tallenna nimi", key="rename_btn"):
                if new_name.strip():
                    rename_portfolio(active_portfolio_id, new_name.strip())
                    st.rerun()

            # Poista salkku (ei sallita jos vain yksi jäljellä)
            if len(portfolios) > 1:
                if st.button(f"🗑️ Poista '{active_portfolio_name}'", key="del_portfolio_btn"):
                    delete_portfolio(active_portfolio_id)
                    st.rerun()
            else:
                st.caption("Viimeistä salkkua ei voi poistaa.")

            # Luo uusi salkku
            st.markdown("---")
            if len(portfolios) < 5:
                new_pname = st.text_input("Uuden salkun nimi", placeholder="esim. Kasvu-salkku", key="new_portfolio_name")
                if st.button("➕ Luo uusi salkku", key="create_portfolio_btn"):
                    if new_pname.strip():
                        create_portfolio(new_pname.strip(), st.session_state["user_id"])
                        st.rerun()
            else:
                st.info("Maksimimäärä (5) salkkuja saavutettu.")

        # --- Import txt-tiedostosta ---
        st.markdown("---")
        st.subheader("📂 Tuo osakkeet tiedostosta")
        st.caption("Tue muodot: .txt tai .csv, yksi tunnus per rivi tai pilkuilla erotettuna")

        # Lataa esimerkkitiedosto
        example_txt = "NOKIA.HE\nNESTE.HE\nFORTUM.HE\nAPPL\nMSFT\nGOOGL\n"
        st.download_button(
            label="📄 Lataa esimerkkitiedosto",
            data=example_txt,
            file_name="osakkeet_esimerkki.txt",
            mime="text/plain",
        )

        uploaded_file = st.file_uploader(
            "Valitse tiedosto", type=["txt", "csv"], label_visibility="collapsed"
        )
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            symbols_to_import = parse_symbols_from_text(content)
            if symbols_to_import:
                st.info(f"Löydetty {len(symbols_to_import)} tunnusta: {', '.join(symbols_to_import[:10])}" +
                        (f" ... (+{len(symbols_to_import)-10} lisää)" if len(symbols_to_import) > 10 else ""))
                if st.button(t("sidebar_import_btn"), key="import_file"):
                    added, skipped, errs = add_stocks_bulk(symbols_to_import, active_portfolio_id)
                    st.success(f"Lisätty: {added}, jo listalla: {skipped}")
                    if errs:
                        st.warning("Virheitä: " + "; ".join(errs))
                    st.rerun()
            else:
                st.warning("Tiedostossa ei löydetty osakekoodeja.")

        # Näytä salkku
        st.markdown("---")
        st.subheader(f"📋 {active_portfolio_name}")
        stocks_df_sidebar = get_stocks(active_portfolio_id)

        if not stocks_df_sidebar.empty:
            for _, row in stocks_df_sidebar.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(row["symbol"])
                with col2:
                    if st.button("🗑️", key=f"del_{active_portfolio_id}_{row['symbol']}"):
                        delete_stock(row["symbol"], active_portfolio_id)
                        st.rerun()
        else:
            st.info(t("sidebar_no_stocks"))

    # Päänäkymä
    stocks_df = get_stocks(active_portfolio_id)

    # Välilehdet — salkku-välilehti ei vaadi osakkeita etukäteen
    tab1, tab3, tab5, tab6, tab7, tab2, tab4 = st.tabs([
        t("tab_analysis"),
        t("tab_fi"),
        t("tab_us"),
        t("tab_eu"),
        t("tab_funds"),
        t("tab_backtest"),
        t("tab_info"),
    ])

    # --- ANALYYSI-välilehti ---
    with tab1:
        st.subheader(f"{t('analysis_header')} – {active_portfolio_name}")

        if stocks_df.empty:
            st.info(t("analysis_no_stocks"))
        else:
            col_btn, col_ts = st.columns([1, 3])
            with col_btn:
                manual_refresh = st.button(t("analysis_refresh"))
            with col_ts:
                st.caption(f"{t('analysis_last_updated')}: {datetime.now().strftime('%H:%M:%S')}")

            if manual_refresh:
                fetch_stock_data.clear()
                st.rerun()

            # Analysoi kaikki osakkeet
            results = []
            with st.spinner(t("analysis_spinner")):
                for symbol in stocks_df["symbol"]:
                    success, data = get_stock_analysis(symbol)
                    if success:
                        results.append(data)
                    else:
                        st.warning(f"{symbol}: {data}")

            if results:
                display_data = []
                for r in results:
                    display_data.append({
                        t("col_symbol"): r["symbol"],
                        t("col_company"): r["company"],
                        t("col_price_eur"): r["price"],
                        "RSI": r["rsi"] if r["rsi"] else None,
                        t("col_sma50"): r["sma50"] if r["sma50"] else None,
                        t("col_sma200"): r["sma200"] if r["sma200"] else None,
                        t("col_pe"): round(r["pe_ratio"], 2) if r["pe_ratio"] else None,
                        t("col_pb"): round(r["pb_ratio"], 2) if r["pb_ratio"] else None,
                        t("col_roe"): round(r["roe"] * 100, 1) if r["roe"] else None,
                        t("col_dividend"): round(r["dividend_yield"], 2) if r["dividend_yield"] else None,
                        t("col_signal"): f"{r['signal_color']} {r['signal']}"
                    })

                df_display = pd.DataFrame(display_data)
                st.dataframe(df_display, width='stretch', hide_index=True)

                csv = df_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=t("analysis_download"),
                    data=csv,
                    file_name=f"osakeanalyysi_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )

                # --- Fundamenttianalyysi & uutiset per osake ---
                st.markdown("---")
                st.subheader(t("analysis_detail"))
                detail_symbol = st.selectbox(
                    t("analysis_select"),
                    options=[r["symbol"] for r in results],
                    key="detail_selectbox",
                )
                detail = next(r for r in results if r["symbol"] == detail_symbol)

                # Fundamentti-kortit
                st.markdown(f"#### {detail['company']} ({detail['symbol']})")
                if detail.get("sector"):
                    st.caption(f"Toimiala: {detail['sector']}  |  {detail.get('industry','')}  |  {detail.get('country','')}")
                if detail.get("website"):
                    st.caption(f"🌐 [{detail['website']}]({detail['website']})")

                fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
                fc1.metric("Hinta", f"{detail['price']}")
                fc2.metric("P/E", f"{round(detail['pe_ratio'],2)}" if detail["pe_ratio"] else "–")
                fc3.metric("P/B", f"{round(detail['pb_ratio'],2)}" if detail["pb_ratio"] else "–")
                fc4.metric("ROE", f"{round(detail['roe']*100,1)} %" if detail["roe"] else "–")
                fc5.metric("Osinko", f"{round(detail['dividend_yield'],2)} %" if detail["dividend_yield"] else "–")
                fc6.metric("D/E", f"{round(detail['debt_to_equity'],1)}" if detail["debt_to_equity"] else "–")

                fc7, fc8, fc9 = st.columns(3)
                fc7.metric("EPS", f"{round(detail['eps'],2)}" if detail["eps"] else "–")
                fc8.metric("Markkina-arvo",
                           f"{detail['market_cap']/1e9:.2f} Mrd" if detail["market_cap"] else "–")
                fc9.metric("Nettomarginaali",
                           f"{round(detail['profit_margin']*100,1)} %" if detail["profit_margin"] else "–")

                # Automaattinen yhteenveto
                summary_points = generate_stock_summary(detail)
                if summary_points:
                    st.markdown("#### 🤖 Automaattinen yhteenveto")
                    color_map = {
                        "green":  "#1a9e3f",
                        "red":    "#d93025",
                        "orange": "#e07b00",
                        "blue":   "#1a73e8",
                        "gray":   "#888888",
                    }
                    bullets_html = "".join(
                        f'<li style="color:{color_map.get(c,"#333")};margin-bottom:6px">{txt}</li>'
                        for txt, c in summary_points
                    )
                    st.markdown(
                        f'<ul style="padding-left:20px;line-height:1.7">{bullets_html}</ul>',
                        unsafe_allow_html=True,
                    )
                    st.caption("⚠️ Automaattinen analyysi perustuu tilastollisiin sääntöihin – ei sijoitusneuvontaa.")

                # Yrityksen kuvaus
                if detail.get("summary"):
                    with st.expander("📄 Yrityksen kuvaus"):
                        with st.spinner("Käännetään suomeksi..."):
                            fi_summary = translate_to_finnish(detail["summary"])
                        st.write(fi_summary)

                # Kaaviot: hinta + volume
                fig_d_price = plot_price_chart(detail["df"], detail["symbol"])
                st.plotly_chart(fig_d_price, width='stretch')

                if "Volume" in detail["df"].columns:
                    fig_d_vol = plot_volume_chart(detail["df"], detail["symbol"])
                    st.plotly_chart(fig_d_vol, width='stretch')

                if "MACD" in detail["df"].columns:
                    fig_d_macd = plot_macd_chart(detail["df"])
                    st.plotly_chart(fig_d_macd, width='stretch')

                fig_d_rsi = plot_rsi_chart(detail["df"])
                st.plotly_chart(fig_d_rsi, width='stretch')

                # Uutiset yfinancesta
                with st.expander("📰 Viimeisimmät uutiset"):
                    try:
                        ticker_obj = yf.Ticker(detail_symbol)
                        news = ticker_obj.news
                        if news:
                            for item in news[:8]:
                                title = item.get("title", "–")
                                link  = item.get("link", "#")
                                pub   = item.get("publisher", "")
                                ts    = item.get("providerPublishTime", None)
                                date_str = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M") if ts else ""
                                st.markdown(f"**[{title}]({link})**  \n{pub}  ·  {date_str}")
                                st.markdown("---")
                        else:
                            st.info(t("news_no_news"))
                    except Exception as e:  # noqa: BLE001
                        st.info(t("news_fetch_error"))

                st.markdown("---")
                st.subheader("📌 Signaalien logiikka")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**🟢 OSTA**")
                    st.markdown("- RSI < 30 (ylimyyty)")
                    st.markdown("- Hinta > SMA50")
                with col2:
                    st.markdown("**🔴 MYY**")
                    st.markdown("- RSI > 70 (yliostettu)")
                    st.markdown("- TAI hinta < SMA200")
                with col3:
                    st.markdown("**🟡 PIDÄ**")
                    st.markdown("- Ei osto- tai myyntisignaalia")


    
    # --- USA:n PÖRSSI -välilehti ---
    with tab5:
        # Lataa tallennettu data DB:stä session_stateen jos sivu on refreshattu
        if "us_data" not in st.session_state:
            cached_us_data, cached_us_ts = load_us_cache()
            if cached_us_data:
                st.session_state["us_data"] = cached_us_data
                st.session_state["us_last_sync"] = cached_us_ts

        st.header(t("us_header"))
        st.markdown(t("us_count", n=len(US_STOCKS)))

        # Auto-refresh asetukset
        col_ur1, col_ur2 = st.columns([2, 1])
        with col_ur1:
            us_auto_refresh = st.toggle(
                t("fi_auto_refresh"),
                value=False,
                key="us_auto_refresh",
                help=t("us_auto_refresh_help"),
            )
        with col_ur2:
            us_refresh_interval = st.selectbox(
                t("fi_interval"),
                options=[60, 120, 300],
                format_func=lambda x: f"{x//60} min",
                index=0,
                disabled=not us_auto_refresh,
                key="us_refresh_interval",
            )

        col_ubtn1, col_ubtn2, col_uts = st.columns([1, 1, 4])
        with col_ubtn1:
            us_sync_all = st.button(t("fi_sync_all"), key="us_sync")
        with col_ubtn2:
            us_clear_cache_btn = st.button(t("fi_clear_cache"), key="us_clear_cache")
        with col_uts:
            us_ts_placeholder = st.empty()
            us_saved_ts = st.session_state.get("us_last_sync")
            if us_saved_ts:
                us_ts_placeholder.caption(t("fi_last_synced", ts=us_saved_ts))

        if us_clear_cache_btn:
            fetch_stock_data.clear()
            st.toast(t("fi_cache_cleared"), icon="🗑️")

        # Hae data — VAIN kun nappia painetaan manuaalisesti tai auto-refresh on päällä
        if us_sync_all or us_auto_refresh:
            st.session_state["us_sync_requested"] = True

        if st.session_state.get("us_sync_requested"):
            us_results = []
            us_progress_bar = st.progress(0, text=t("fi_fetching_start"))
            us_symbols_list = list(US_STOCKS.keys())
            us_total = len(us_symbols_list)

            for idx, symbol in enumerate(us_symbols_list):
                try:
                    df_tmp, info_tmp = fetch_stock_data(symbol, period="6mo")
                    if not df_tmp.empty:
                        df_tmp = df_tmp.reset_index()
                        latest_price = round(df_tmp["Close"].iloc[-1], 2)
                        prev_price = df_tmp["Close"].iloc[-2] if len(df_tmp) > 1 else latest_price
                        change_pct = round((latest_price - prev_price) / prev_price * 100, 2)
                        market_cap = info_tmp.get("marketCap", None)
                        pe = info_tmp.get("trailingPE", None)
                        currency = info_tmp.get("currency", "USD")

                        rsi_val = None
                        sma50_val = None
                        signal = "🟡 PIDÄ"
                        if len(df_tmp) >= 15:
                            rsi_series = ta.momentum.RSIIndicator(df_tmp["Close"], window=14).rsi()
                            rsi_val = rsi_series.iloc[-1]
                            rsi_val = round(rsi_val, 1) if pd.notna(rsi_val) else None
                        if len(df_tmp) >= 50:
                            sma50_val = round(df_tmp["Close"].rolling(50).mean().iloc[-1], 2)

                        if rsi_val is not None and sma50_val is not None:
                            if rsi_val < 30 and latest_price > sma50_val:
                                signal = "🟢 OSTA"
                            elif rsi_val > 70:
                                signal = "🔴 MYY"

                        us_results.append({
                            t("col_symbol"): symbol,
                            t("col_company"): US_STOCKS[symbol],
                            t("col_price_usd"): latest_price,
                            t("col_change"): change_pct,
                            "RSI": rsi_val,
                            t("col_sma50"): sma50_val,
                            t("col_signal"): signal,
                            t("col_currency"): currency,
                            t("col_pe"): round(pe, 2) if pe else None,
                            t("col_market_cap"): f"{market_cap/1e9:.1f} Mrd" if market_cap else None,
                        })
                except Exception:  # noqa: BLE001
                    pass
                us_progress_bar.progress((idx + 1) / us_total, text=t("fi_fetching", symbol=symbol, idx=idx+1, total=us_total))

            us_progress_bar.empty()
            st.session_state["us_data"] = us_results
            st.session_state["us_last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            save_us_cache(us_results, st.session_state["us_last_sync"])
            st.session_state["us_sync_requested"] = False
            st.session_state.pop("us_signal_filter", None)
            st.session_state.pop("us_search", None)
            st.rerun()

        if "us_data" in st.session_state and st.session_state["us_data"]:
            us_df = pd.DataFrame(st.session_state["us_data"])
            us_df = _remap_df_columns(us_df, [
                "col_symbol", "col_company", "col_price_usd", "col_change",
                "col_sma50", "col_signal", "col_currency", "col_pe", "col_market_cap",
            ])

            col_uf1, col_uf2 = st.columns([3, 1])
            with col_uf1:
                search_us = st.text_input(t("fi_search"), "", key="us_search")
            with col_uf2:
                us_signal_filter = st.selectbox(
                    t("fi_signal_filter"),
                    options=[t("fi_signal_all"), "🟢 OSTA", "🔴 MYY", "🟡 PIDÄ"],
                    key="us_signal_filter",
                )

            us_sym_col = t("col_symbol")
            us_co_col  = t("col_company")
            us_sig_col = t("col_signal")
            us_chg_col = t("col_change")
            if search_us:
                mask_us = (
                    us_df[us_sym_col].str.contains(search_us.upper(), na=False)
                    | us_df[us_co_col].str.contains(search_us, case=False, na=False)
                )
                us_df = us_df[mask_us]
            if us_signal_filter != t("fi_signal_all") and us_sig_col in us_df.columns:
                us_df = us_df[us_df[us_sig_col] == us_signal_filter]

            def color_change_us(val: object) -> str:
                """Väritää muutos %-arvo vihreäksi tai punaiseksi."""
                if isinstance(val, (int, float)):
                    return "color: green" if val > 0 else ("color: red" if val < 0 else "")
                return ""

            def color_signal_us(val: object) -> str:
                """Väritää signaalin vihreäksi/punaiseksi."""
                if isinstance(val, str):
                    if "OSTA" in val:
                        return "color: green; font-weight: bold"
                    if "MYY" in val:
                        return "color: red; font-weight: bold"
                return ""

            if us_sig_col in us_df.columns:
                styled_us = us_df.style.map(color_change_us, subset=[us_chg_col]).map(
                    color_signal_us, subset=[us_sig_col]
                )
            else:
                styled_us = us_df.style.map(color_change_us, subset=[us_chg_col])
            st.dataframe(styled_us, width='stretch', hide_index=True)

            # Lisää yksittäisiä US-osakkeita salkkuun
            st.markdown("---")
            col_usel1, col_usel2 = st.columns([2, 1])
            with col_usel1:
                selected_us = st.multiselect(
                    t("us_add_multiselect"),
                    options=list(US_STOCKS.keys()),
                    format_func=lambda s: f"{s} – {US_STOCKS[s]}",
                    key="us_multiselect",
                )
            with col_usel2:
                st.write("")
                st.write("")
                if st.button(t("us_add_btn"), key="us_add_selected") and selected_us:
                    added, skipped, errs = add_stocks_bulk(selected_us, active_portfolio_id)
                    st.success(t("fi_added", portfolio=active_portfolio_name, added=added, skipped=skipped))
                    st.rerun()

            csv_us = us_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("us_download"),
                data=csv_us,
                file_name=f"usa_porssi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        else:
            st.info(t("fi_press_sync"))

        # Auto-refresh loppusilmukka
        if us_auto_refresh:
            time.sleep(us_refresh_interval)
            fetch_stock_data.clear()
            st.session_state["us_sync_requested"] = True
            st.rerun()

    # --- EU / POHJOISMAAT ETF:t -välilehti ---
    with tab6:
        if "eu_data" not in st.session_state:
            cached_eu_data, cached_eu_ts = load_eu_cache()
            if cached_eu_data:
                st.session_state["eu_data"] = cached_eu_data
                st.session_state["eu_last_sync"] = cached_eu_ts

        st.header(t("eu_header"))
        st.markdown(t("eu_count", n=len(EU_ETFS)))

        col_er1, col_er2 = st.columns([2, 1])
        with col_er1:
            eu_auto_refresh = st.toggle(
                t("fi_auto_refresh"),
                value=False,
                key="eu_auto_refresh",
                help=t("eu_auto_refresh_help"),
            )
        with col_er2:
            eu_refresh_interval = st.selectbox(
                t("fi_interval"),
                options=[60, 120, 300],
                format_func=lambda x: f"{x//60} min",
                index=0,
                disabled=not eu_auto_refresh,
                key="eu_refresh_interval",
            )

        col_ebtn1, col_ebtn2, col_ets = st.columns([1, 1, 4])
        with col_ebtn1:
            eu_sync_all = st.button(t("fi_sync_all"), key="eu_sync")
        with col_ebtn2:
            eu_clear_cache_btn = st.button(t("fi_clear_cache"), key="eu_clear_cache")
        with col_ets:
            eu_ts_placeholder = st.empty()
            eu_saved_ts = st.session_state.get("eu_last_sync")
            if eu_saved_ts:
                eu_ts_placeholder.caption(t("fi_last_synced", ts=eu_saved_ts))

        if eu_clear_cache_btn:
            fetch_stock_data.clear()
            st.toast(t("fi_cache_cleared"), icon="🗑️")

        if eu_sync_all or eu_auto_refresh:
            st.session_state["eu_sync_requested"] = True

        if st.session_state.get("eu_sync_requested"):
            eu_results = []
            eu_progress_bar = st.progress(0, text=t("fi_fetching_start"))
            eu_symbols_list = list(EU_ETFS.keys())
            eu_total = len(eu_symbols_list)

            for idx, symbol in enumerate(eu_symbols_list):
                try:
                    df_tmp, info_tmp = fetch_stock_data(symbol, period="6mo")
                    if not df_tmp.empty:
                        df_tmp = df_tmp.reset_index()
                        latest_price = round(df_tmp["Close"].iloc[-1], 4)
                        prev_price = df_tmp["Close"].iloc[-2] if len(df_tmp) > 1 else latest_price
                        change_pct = round((latest_price - prev_price) / prev_price * 100, 2)
                        currency = info_tmp.get("currency", "EUR")

                        rsi_val = None
                        sma50_val = None
                        signal = "🟡 PIDÄ"
                        if len(df_tmp) >= 15:
                            rsi_series = ta.momentum.RSIIndicator(df_tmp["Close"], window=14).rsi()
                            rsi_val = rsi_series.iloc[-1]
                            rsi_val = round(rsi_val, 1) if pd.notna(rsi_val) else None
                        if len(df_tmp) >= 50:
                            sma50_val = round(df_tmp["Close"].rolling(50).mean().iloc[-1], 4)

                        if rsi_val is not None and sma50_val is not None:
                            if rsi_val < 30 and latest_price > sma50_val:
                                signal = "🟢 OSTA"
                            elif rsi_val > 70:
                                signal = "🔴 MYY"

                        eu_results.append({
                            t("col_symbol"): symbol,
                            t("col_etf_name"): EU_ETFS[symbol],
                            t("col_price_eur"): latest_price,
                            t("col_change"): change_pct,
                            "RSI": rsi_val,
                            t("col_sma50"): sma50_val,
                            t("col_signal"): signal,
                            t("col_currency"): currency,
                        })
                except Exception:  # noqa: BLE001
                    pass
                eu_progress_bar.progress((idx + 1) / eu_total, text=t("fi_fetching", symbol=symbol, idx=idx+1, total=eu_total))

            eu_progress_bar.empty()
            st.session_state["eu_data"] = eu_results
            st.session_state["eu_last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            save_eu_cache(eu_results, st.session_state["eu_last_sync"])
            st.session_state["eu_sync_requested"] = False
            st.session_state.pop("eu_signal_filter", None)
            st.session_state.pop("eu_search", None)
            st.rerun()

        if "eu_data" in st.session_state and st.session_state["eu_data"]:
            eu_df = pd.DataFrame(st.session_state["eu_data"])
            eu_df = _remap_df_columns(eu_df, [
                "col_symbol", "col_etf_name", "col_price_eur", "col_change",
                "col_sma50", "col_signal", "col_currency",
            ])

            col_ef1, col_ef2 = st.columns([3, 1])
            with col_ef1:
                search_eu = st.text_input(t("eu_search"), "", key="eu_search")
            with col_ef2:
                eu_signal_filter = st.selectbox(
                    t("fi_signal_filter"),
                    options=[t("fi_signal_all"), "🟢 OSTA", "🔴 MYY", "🟡 PIDÄ"],
                    key="eu_signal_filter",
                )

            eu_sym_col = t("col_symbol")
            eu_nm_col  = t("col_etf_name")
            eu_sig_col = t("col_signal")
            eu_chg_col = t("col_change")
            if search_eu:
                mask_eu = (
                    eu_df[eu_sym_col].str.contains(search_eu.upper(), na=False)
                    | eu_df[eu_nm_col].str.contains(search_eu, case=False, na=False)
                )
                eu_df = eu_df[mask_eu]
            if eu_signal_filter != t("fi_signal_all") and eu_sig_col in eu_df.columns:
                eu_df = eu_df[eu_df[eu_sig_col] == eu_signal_filter]

            def color_change_eu(val: object) -> str:
                """Väritää muutos %-arvo vihreäksi tai punaiseksi."""
                if isinstance(val, (int, float)):
                    return "color: green" if val > 0 else ("color: red" if val < 0 else "")
                return ""

            def color_signal_eu(val: object) -> str:
                """Väritää signaalin vihreäksi/punaiseksi."""
                if isinstance(val, str):
                    if "OSTA" in val:
                        return "color: green; font-weight: bold"
                    if "MYY" in val:
                        return "color: red; font-weight: bold"
                return ""

            if eu_sig_col in eu_df.columns:
                styled_eu = eu_df.style.map(color_change_eu, subset=[eu_chg_col]).map(
                    color_signal_eu, subset=[eu_sig_col]
                )
            else:
                styled_eu = eu_df.style.map(color_change_eu, subset=[eu_chg_col])
            st.dataframe(styled_eu, width='stretch', hide_index=True)

            # Lisää ETF:iä salkkuun
            st.markdown("---")
            col_esel1, col_esel2 = st.columns([2, 1])
            with col_esel1:
                selected_eu = st.multiselect(
                    t("eu_add_multiselect"),
                    options=list(EU_ETFS.keys()),
                    format_func=lambda s: f"{s} – {EU_ETFS[s]}",
                    key="eu_multiselect",
                )
            with col_esel2:
                st.write("")
                st.write("")
                if st.button(t("eu_add_btn"), key="eu_add_selected") and selected_eu:
                    added, skipped, errs = add_stocks_bulk(selected_eu, active_portfolio_id)
                    st.success(t("fi_added", portfolio=active_portfolio_name, added=added, skipped=skipped))
                    st.rerun()

            csv_eu = eu_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("eu_download"),
                data=csv_eu,
                file_name=f"eu_etf_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        else:
            st.info(t("fi_press_sync"))

        if eu_auto_refresh:
            time.sleep(eu_refresh_interval)
            fetch_stock_data.clear()
            st.session_state["eu_sync_requested"] = True
            st.rerun()

    # --- OMAT RAHASTOT -välilehti ---
    with tab7:
        active_user_id = st.session_state.get("user_id", 1)
        st.header(t("funds_header"))
        st.markdown(t("funds_desc"))

        user_funds = get_funds(active_user_id)

        # --- Lisää uusi rahasto ---
        with st.expander("➕ Lisää uusi rahasto", expanded=not user_funds):
            with st.form("add_fund_form"):
                fn_col1, fn_col2 = st.columns([2, 1])
                with fn_col1:
                    new_fund_name = st.text_input("Rahaston nimi *", placeholder="esim. OP-Suomi Indeksi")
                with fn_col2:
                    new_fund_isin = st.text_input("ISIN-koodi (valinnainen)", placeholder="esim. FI0008807637")
                new_fund_notes = st.text_input("Muistiinpanot (valinnainen)", placeholder="esim. Kuukausisäästö 100 €/kk")
                submit_fund = st.form_submit_button("✅ Lisää rahasto")
                if submit_fund:
                    if not new_fund_name.strip():
                        st.error(t("funds_name_required"))
                    else:
                        ok, msg = add_fund(active_user_id, new_fund_name, new_fund_isin, new_fund_notes)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

        if not user_funds:
            st.info(t("funds_empty"))
        else:
            # --- Rahastokohtainen näkymä ---
            fund_options = {f["id"]: f"{f['name']}{' (' + f['isin'] + ')' if f['isin'] else ''}" for f in user_funds}
            selected_fund_id = st.selectbox(
                t("funds_select"),
                options=list(fund_options.keys()),
                format_func=lambda fid: fund_options[fid],
                key="fund_selectbox",
            )
            selected_fund = next(f for f in user_funds if f["id"] == selected_fund_id)

            fund_col1, fund_col2 = st.columns([3, 1])
            with fund_col1:
                st.markdown(f"#### {selected_fund['name']}")
                if selected_fund["isin"]:
                    st.caption(f"ISIN: `{selected_fund['isin']}`")
                if selected_fund["notes"]:
                    st.caption(f"📝 {selected_fund['notes']}")
            with fund_col2:
                if st.button(t("funds_delete_btn"), key="del_fund_btn"):
                    st.session_state["confirm_del_fund"] = selected_fund_id

            if st.session_state.get("confirm_del_fund") == selected_fund_id:
                st.warning(t("funds_confirm_delete", name=selected_fund['name']))
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button(t("funds_confirm_yes"), key="confirm_del_fund_yes"):
                        delete_fund(selected_fund_id)
                        st.session_state.pop("confirm_del_fund", None)
                        st.rerun()
                with cc2:
                    if st.button(t("funds_confirm_no"), key="confirm_del_fund_no"):
                        st.session_state.pop("confirm_del_fund", None)
                        st.rerun()

            st.markdown("---")

            # --- Lisää NAV-kirjaus ---
            with st.form("add_nav_form"):
                nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])
                with nav_col1:
                    nav_date_input = st.date_input(
                        t("funds_nav_date"),
                        value=datetime.today(),
                        key="nav_date_input",
                    )
                with nav_col2:
                    nav_value_input = st.number_input(
                        t("funds_nav_value"),
                        min_value=0.0001,
                        step=0.01,
                        format="%.4f",
                        key="nav_value_input",
                    )
                with nav_col3:
                    st.write("")
                    st.write("")
                    submit_nav = st.form_submit_button(t("funds_nav_save"))
                if submit_nav:
                    ok, msg = add_fund_nav(
                        selected_fund_id,
                        float(nav_value_input),
                        nav_date_input.strftime("%Y-%m-%d"),
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            # --- NAV-historia ---
            nav_df = get_fund_nav_history(selected_fund_id)

            if nav_df.empty:
                st.info(t("funds_no_entries"))
            else:
                nav_df["nav_date"] = pd.to_datetime(nav_df["nav_date"])
                nav_df = nav_df.sort_values("nav_date")

                first_nav = nav_df["nav"].iloc[0]
                last_nav = nav_df["nav"].iloc[-1]
                total_return = (last_nav - first_nav) / first_nav * 100
                last_date = nav_df["nav_date"].iloc[-1].strftime("%d.%m.%Y")
                first_date = nav_df["nav_date"].iloc[0].strftime("%d.%m.%Y")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(t("funds_latest_nav"), f"{last_nav:.4f} €", help=f"{t('funds_nav_date')}: {last_date}")
                m2.metric(t("funds_first_nav"), f"{first_nav:.4f} €", help=f"{t('funds_nav_date')}: {first_date}")
                arrow = "▲" if total_return >= 0 else "▼"
                m3.metric(t("funds_total_return"), f"{arrow} {total_return:+.2f} %")
                m4.metric(t("funds_entries_count"), f"{len(nav_df)} kpl")

                # Kehityskäyrä
                fig_fund = go.Figure()
                fig_fund.add_trace(go.Scatter(
                    x=nav_df["nav_date"],
                    y=nav_df["nav"],
                    mode="lines+markers",
                    name="NAV",
                    line={"color": "#1a73e8", "width": 2},
                    marker={"size": 5},
                    hovertemplate="%{x|%d.%m.%Y}: <b>%{y:.4f} €</b><extra></extra>",
                ))
                fig_fund.update_layout(
                    title=t("funds_chart_title", name=selected_fund['name']),
                    xaxis_title=t("funds_nav_date"),
                    yaxis_title=t("funds_nav_value"),
                    height=380,
                    hovermode="x unified",
                    margin={"l": 40, "r": 20, "t": 50, "b": 40},
                )
                st.plotly_chart(fig_fund, use_container_width=True)

                # NAV-taulukko muokkausmahdollisuudella
                st.markdown(t("funds_entries_header"))
                nav_display = nav_df.copy()
                nav_display["nav_date"] = nav_display["nav_date"].dt.strftime("%d.%m.%Y")
                nav_display = nav_display.rename(columns={"nav_date": t("funds_col_date"), "nav": t("funds_col_nav")})
                st.dataframe(nav_display, hide_index=True, use_container_width=True)

                # Poista yksittäinen kirjaus
                with st.expander(t("funds_delete_entry_expander")):
                    del_date_options = nav_df["nav_date"].dt.strftime("%Y-%m-%d").tolist()
                    del_date = st.selectbox(
                        t("funds_delete_entry_select"),
                        options=del_date_options,
                        format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%d.%m.%Y"),
                        key="del_nav_date",
                    )
                    if st.button(t("funds_delete_entry_btn"), key="del_nav_btn"):
                        delete_fund_nav(selected_fund_id, del_date)
                        st.rerun()

                # CSV-lataus
                csv_nav = nav_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=t("funds_download"),
                    data=csv_nav,
                    file_name=f"{selected_fund['name'].replace(' ', '_')}_nav_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )


        # --- NAV-lähdetiedot ---
        st.markdown("---")
        st.markdown(t("funds_nav_where_header"))
        st.markdown(t("funds_nav_where_body"))
    # --- BACKTESTING-välilehti ---
    with tab2:
        st.header(t("bt_header"))
        st.markdown(t("bt_desc"))

        # Osakevalinta
        bt_symbols = list(stocks_df["symbol"]) if not stocks_df.empty else []
        bt_options = [t("bt_all_stocks")] + bt_symbols
        bt_selection = st.selectbox(
            t("bt_stock_label"),
            options=bt_options,
            help=t("bt_all_stocks"),
        )
        bt_symbols_to_run = bt_symbols if bt_selection == t("bt_all_stocks") else [bt_selection]

        col1, col2 = st.columns(2)
        with col1:
            years = st.slider("Vuodet taaksepäin", 1, 10, 5)
        with col2:
            initial_capital = st.number_input("Aloituspääoma (€)", 1000, 1000000, 10000, 1000)

        col3, col4 = st.columns(2)
        with col3:
            selected_strategy = st.selectbox(
                "🤖 Strategia",
                options=STRATEGIES,
                help=(
                    "**RSI + SMA**: Osta ylimyyty + yli SMA50, myy yliostettu tai alle SMA200\n\n"
                    "**Momentum (SMA-risteytys)**: Golden/Death Cross — SMA50 ylittää SMA200\n\n"
                    "**Mean Reversion (BB)**: Osta Bollinger-alakaistalla, myy yläkaistalla\n\n"
                    "**MACD-risteytys**: Osta kun MACD ylittää signaaliviivan"
                ),
            )
        with col4:
            commission_pct = st.slider(
                "Kaupankäyntikulut (%)",
                min_value=0.0, max_value=1.0, value=0.1, step=0.05,
                help="Kulut per transaktio prosentteina",
            )
        commission = commission_pct / 100

        if st.button(t("bt_run_btn")):
            if not bt_symbols_to_run:
                st.warning(t("bt_no_stocks"))
            else:
                backtest_results = []
                with st.spinner("Ajetaan backtestingiä..."):
                    for symbol in bt_symbols_to_run:
                        success, data = backtest_strategy(symbol, years, initial_capital, commission, selected_strategy)
                        if success:
                            backtest_results.append(data)
                        else:
                            st.warning(f"{symbol}: {data}")

                if backtest_results:
                    st.session_state["backtest_results"] = backtest_results

                    # Näytä vertailutaulukko
                    st.subheader(f"📊 Tulokset: {selected_strategy} vs Buy & Hold")

                    display_data = []
                    for r in backtest_results:
                        outperformance = r["strategy_return"] - r["buy_hold_return"]
                    display_data.append({
                        "Osake": r["symbol"],
                        "Strategia loppu (€)": r["strategy_final"],
                        "Strategia tuotto (%)": r["strategy_return"],
                        "Buy&Hold loppu (€)": r["buy_hold_final"],
                        "Buy&Hold tuotto (%)": r["buy_hold_return"],
                        "Ylisuoritus (%)": round(outperformance, 2),
                        "Kauppoja": r["trades"],
                        "Win Rate (%)": r["win_rate"],
                        "Max Drawdown (%)": r["max_drawdown"],
                        "Sharpe Ratio": r["sharpe_ratio"],
                    })

                    df_display = pd.DataFrame(display_data)

                    def highlight_performance(val):
                        if isinstance(val, (int, float)):
                            if val > 0:
                                return "background-color: lightgreen"
                            elif val < 0:
                                return "background-color: lightcoral"
                        return ""

                    styled_df = df_display.style.map(
                        highlight_performance, subset=["Ylisuoritus (%)", "Max Drawdown (%)"]
                    )
                    st.dataframe(styled_df, width='stretch', hide_index=True)

                    csv = df_display.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Lataa backtesting-tulokset CSV",
                        data=csv,
                        file_name=f"backtesting_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                    )

                    avg_strategy = df_display["Strategia tuotto (%)"].mean()
                    avg_buyhold  = df_display["Buy&Hold tuotto (%)"].mean()
                    avg_drawdown = df_display["Max Drawdown (%)"].mean()
                    avg_sharpe   = df_display["Sharpe Ratio"].mean()

                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Keskim. strategia", f"{avg_strategy:.1f}%")
                    with col2:
                        st.metric("Keskim. Buy&Hold", f"{avg_buyhold:.1f}%")
                    with col3:
                        diff = avg_strategy - avg_buyhold
                        st.metric("Ero", f"{diff:.1f}%", delta=f"{diff:.1f}%")

                    col4, col5 = st.columns(2)
                    with col4:
                        st.metric("Keskim. Max Drawdown", f"{avg_drawdown:.1f}%")
                    with col5:
                        st.metric("Keskim. Sharpe Ratio", f"{avg_sharpe:.2f}")

        # --- KAAVIOT ---
        if "backtest_results" in st.session_state and st.session_state["backtest_results"]:
            st.markdown("---")
            bt_res = st.session_state["backtest_results"]
            strategy_label = bt_res[0].get("strategy", "")
            st.subheader(f"📈 Kaaviot – {strategy_label}")

            symbols = [r["symbol"] for r in bt_res]
            selected_symbol = st.selectbox(t("bt_select_stock"), symbols, key="bt_symbol_select")
            selected_data = next((r for r in bt_res if r["symbol"] == selected_symbol), None)

            if selected_data:
                # Equity Curve
                fig_equity = plot_equity_curve(
                    selected_data["equity_df"],
                    selected_symbol,
                    selected_data["initial_capital"]
                )
                st.plotly_chart(fig_equity, width='stretch')

                # Hintakaavio + indikaattorit + signaalit
                fig_price = plot_price_chart(
                    selected_data["df"], 
                    selected_symbol,
                    selected_data["trade_history"]
                )
                st.plotly_chart(fig_price, width='stretch')

                # MACD-kaavio
                if "MACD" in selected_data["df"].columns:
                    fig_macd = plot_macd_chart(selected_data["df"])
                    st.plotly_chart(fig_macd, width='stretch')
                
                # RSI-kaavio
                fig_rsi = plot_rsi_chart(selected_data["df"])
                st.plotly_chart(fig_rsi, width='stretch')

                # Volume-kaavio
                if "Volume" in selected_data["df"].columns:
                    fig_vol = plot_volume_chart(selected_data["df"], selected_symbol)
                    st.plotly_chart(fig_vol, width='stretch')

                # Kauppahistoria
                if selected_data["trade_history"]:
                    with st.expander("📋 Kauppahistoria"):
                        trade_df = pd.DataFrame(selected_data["trade_history"], columns=["Toiminto", "Päivämäärä", "Hinta"])
                        trade_df["Päivämäärä"] = pd.to_datetime(trade_df["Päivämäärä"]).dt.strftime("%Y-%m-%d")
                        trade_df["Hinta"] = trade_df["Hinta"].round(2)
                        st.dataframe(trade_df, width='stretch', hide_index=True)

    # --- SUOMEN PÖRSSI -välilehti ---
    with tab3:
        # Lataa tallennettu data DB:stä session_stateen jos sivu on refreshattu
        if "fi_data" not in st.session_state:
            cached_data, cached_ts = load_fi_cache()
            if cached_data:
                st.session_state["fi_data"] = cached_data
                st.session_state["fi_last_sync"] = cached_ts

        st.header(t("fi_header"))
        st.markdown(t("fi_count", n=len(FINNISH_STOCKS)))

        # Auto-refresh asetukset
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            fi_auto_refresh = st.toggle(
                t("fi_auto_refresh"),
                value=False,
                key="fi_auto_refresh",
                help=t("fi_auto_refresh_help"),
            )
        with col_r2:
            fi_refresh_interval = st.selectbox(
                t("fi_interval"),
                options=[60, 120, 300],
                format_func=lambda x: f"{x//60} min",
                index=0,
                disabled=not fi_auto_refresh,
                key="fi_refresh_interval",
            )

        col_btn1, col_btn2, col_ts = st.columns([1, 1, 4])
        with col_btn1:
            sync_all = st.button(t("fi_sync_all"), key="fi_sync")
        with col_btn2:
            clear_cache_btn = st.button(t("fi_clear_cache"), key="fi_clear_cache")
        with col_ts:
            ts_placeholder = st.empty()
            saved_ts = st.session_state.get("fi_last_sync")
            if saved_ts:
                ts_placeholder.caption(t("fi_last_synced", ts=saved_ts))

        if clear_cache_btn:
            fetch_stock_data.clear()
            st.toast(t("fi_cache_cleared"), icon="🗑️")

        # Hae data — VAIN kun nappia painetaan manuaalisesti tai auto-refresh on päällä
        if sync_all or fi_auto_refresh:
            st.session_state["fi_sync_requested"] = True

        if st.session_state.get("fi_sync_requested"):
            fi_results = []
            progress_bar = st.progress(0, text=t("fi_fetching_start"))
            symbols_list = list(FINNISH_STOCKS.keys())
            total = len(symbols_list)

            for idx, symbol in enumerate(symbols_list):
                try:
                    # 6 kuukautta: riittää RSI(14) + SMA50 laskentaan
                    df_tmp, info_tmp = fetch_stock_data(symbol, period="6mo")
                    if not df_tmp.empty:
                        df_tmp = df_tmp.reset_index()
                        latest_price = round(df_tmp["Close"].iloc[-1], 2)
                        prev_price = df_tmp["Close"].iloc[-2] if len(df_tmp) > 1 else latest_price
                        change_pct = round((latest_price - prev_price) / prev_price * 100, 2)
                        market_cap = info_tmp.get("marketCap", None)
                        pe = info_tmp.get("trailingPE", None)
                        currency = info_tmp.get("currency", "EUR")

                        # Laske RSI ja SMA50 signaaleja varten
                        rsi_val = None
                        sma50_val = None
                        signal = "🟡 PIDÄ"
                        if len(df_tmp) >= 15:
                            rsi_series = ta.momentum.RSIIndicator(df_tmp["Close"], window=14).rsi()
                            rsi_val = rsi_series.iloc[-1]
                            rsi_val = round(rsi_val, 1) if pd.notna(rsi_val) else None
                        if len(df_tmp) >= 50:
                            sma50_val = round(df_tmp["Close"].rolling(50).mean().iloc[-1], 2)

                        if rsi_val is not None and sma50_val is not None:
                            if rsi_val < 30 and latest_price > sma50_val:
                                signal = "🟢 OSTA"
                            elif rsi_val > 70:
                                signal = "🔴 MYY"

                        fi_results.append({
                            t("col_symbol"): symbol,
                            t("col_company"): FINNISH_STOCKS[symbol],
                            t("col_price_eur"): latest_price,
                            t("col_change"): change_pct,
                            "RSI": rsi_val,
                            t("col_sma50"): sma50_val,
                            t("col_signal"): signal,
                            t("col_currency"): currency,
                            t("col_pe"): round(pe, 2) if pe else None,
                            t("col_market_cap"): f"{market_cap/1e9:.1f} Mrd" if market_cap else None,
                        })
                except Exception as e:  # noqa: BLE001
                    pass  # virheelliset ohitetaan hiljaisesti
                progress_bar.progress((idx + 1) / total, text=t("fi_fetching", symbol=symbol, idx=idx+1, total=total))

            progress_bar.empty()
            st.session_state["fi_data"] = fi_results
            st.session_state["fi_last_sync"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            save_fi_cache(fi_results, st.session_state["fi_last_sync"])
            st.session_state["fi_sync_requested"] = False
            st.session_state.pop("fi_signal_filter", None)
            st.session_state.pop("fi_search", None)
            st.rerun()

        if "fi_data" in st.session_state and st.session_state["fi_data"]:
            fi_df = pd.DataFrame(st.session_state["fi_data"])
            fi_df = _remap_df_columns(fi_df, [
                "col_symbol", "col_company", "col_price_eur", "col_change",
                "col_sma50", "col_signal", "col_currency", "col_pe", "col_market_cap",
            ])

            # Suodatin — lisätty signaali-suodatin
            col_f1, col_f2 = st.columns([3, 1])
            with col_f1:
                search_fi = st.text_input(t("fi_search"), "", key="fi_search")
            with col_f2:
                signal_filter = st.selectbox(
                    t("fi_signal_filter"),
                    options=[t("fi_signal_all"), "🟢 OSTA", "🔴 MYY", "🟡 PIDÄ"],
                    key="fi_signal_filter",
                )

            sym_col = t("col_symbol")
            co_col  = t("col_company")
            sig_col = t("col_signal")
            chg_col = t("col_change")
            if search_fi:
                mask = (
                    fi_df[sym_col].str.contains(search_fi.upper(), na=False)
                    | fi_df[co_col].str.contains(search_fi, case=False, na=False)
                )
                fi_df = fi_df[mask]
            if signal_filter != t("fi_signal_all") and sig_col in fi_df.columns:
                fi_df = fi_df[fi_df[sig_col] == signal_filter]

            # Väritä muutos % ja signaali
            def color_change(val):
                if isinstance(val, (int, float)):
                    return "color: green" if val > 0 else ("color: red" if val < 0 else "")
                return ""

            def color_signal(val):
                if isinstance(val, str):
                    if "OSTA" in val:
                        return "color: green; font-weight: bold"
                    if "MYY" in val:
                        return "color: red; font-weight: bold"
                return ""

            if sig_col in fi_df.columns:
                styled = fi_df.style.map(color_change, subset=[chg_col]).map(
                    color_signal, subset=[sig_col]
                )
            else:
                styled = fi_df.style.map(color_change, subset=[chg_col])
            st.dataframe(styled, width='stretch', hide_index=True)

            # Lisää yksittäisiä osakkeita salkkuun taulukosta
            st.markdown("---")
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                selected_fi = st.multiselect(
                    t("fi_add_multiselect"),
                    options=list(FINNISH_STOCKS.keys()),
                    format_func=lambda s: f"{s} – {FINNISH_STOCKS[s]}",
                    key="fi_multiselect",
                )
            with col_sel2:
                st.write("")
                st.write("")
                if st.button(t("fi_add_btn"), key="fi_add_selected") and selected_fi:
                    added, skipped, errs = add_stocks_bulk(selected_fi, active_portfolio_id)
                    st.success(t("fi_added", portfolio=active_portfolio_name, added=added, skipped=skipped))
                    st.rerun()

            # CSV-lataus
            csv_fi = fi_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("fi_download"),
                data=csv_fi,
                file_name=f"suomen_porssi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        else:
            st.info(t("fi_press_sync"))

        # Auto-refresh loppusilmukka
        if fi_auto_refresh:
            time.sleep(fi_refresh_interval)
            fetch_stock_data.clear()
            st.session_state["fi_sync_requested"] = True
            st.rerun()

    # --- TIETOA-välilehti ---
    with tab4:
        st.header(t("info_header"))
        st.caption(f"{t('info_version')} {VERSION} | {t('info_updated')} {datetime.now().strftime('%d.%m.%Y')}")

        if st.session_state.get("lang", "fi") == "en":
            st.markdown("""
        ### 🎯 What does this tool do?

        This is a stock analysis tool that helps you:
        - 📊 Track daily technical analysis of stocks
        - 🔔 Receive buy/sell/hold signals
        - 🔁 Backtest strategies on historical data
        - 📈 Visualize prices, indicators and trading signals

        ---

        ## 📋 User Guide: How to Add Stocks to Your Portfolio

        ### 1️⃣ Via the Finnish Stocks tab
        1. Click the **🇫🇮 Finnish Stocks** tab in the top navigation.
        2. Press **🔄 Sync** to load the latest list from Helsinki Stock Exchange (OMXH).
        3. Browse or search the list, then click the **➕ Add** button next to any stock.
        4. The stock is immediately added to the **active portfolio** shown in the left sidebar.

        ### 2️⃣ Via the US Stocks tab
        1. Click the **🇺🇸 US Stocks** tab.
        2. Press **🔄 Sync** to fetch the latest S&P 500 list.
        3. Click **➕ Add** next to the desired stock to add it to your active portfolio.

        ### 3️⃣ Via the EU / Nordic ETFs tab
        1. Click the **🇪🇺 EU / Nordic ETFs** tab.
        2. Press **🔄 Sync**, then use **➕ Add** to add an ETF.

        ### 4️⃣ Import from a file (bulk add)
        1. In the **left sidebar**, find the **📂 Import stocks from file** section.
        2. Upload a `.txt` or `.csv` file — one ticker symbol per line, or comma-separated.
        3. Click **✅ Import all to portfolio**.
        4. Example file format:
           ```
           NOKIA.HE
           SAMPO.HE
           NESTE.HE
           ```
        5. You can download an example file via the **📄 Download example file** link.

        ### 5️⃣ Managing portfolios
        - You can create **up to 5 portfolios** using the ➕ button in the sidebar.
        - Switch the active portfolio by selecting it from the **🗂️ Portfolios** dropdown.
        - Remove a stock by clicking the 🗑️ trash icon next to it in the sidebar.
        - To remove a portfolio, click the 🗑️ icon next to its name (the last portfolio cannot be deleted).

        ---

        ### 📈 Technical Indicators

        **RSI (Relative Strength Index)**
        - Measures the speed and magnitude of price changes
        - < 30: Oversold (potential buying opportunity)
        - > 70: Overbought (potential selling opportunity)

        **SMA50 (50-day moving average)**
        - Short-term trend
        - Price above SMA50 = uptrend

        **SMA200 (200-day moving average)**
        - Long-term trend
        - Price below SMA200 = possible weak trend

        ### 🔁 Backtesting

        Backtesting tests how your strategy would have performed in the past:
        - **Strategy**: Active buy/sell according to signals
        - **Buy & Hold**: Buy at start, hold until end

        ⚠️ **IMPORTANT**: Past performance does not guarantee future returns!

        ### 🛠️ Technologies

        - **Python**: Programming language
        - **Streamlit**: Web interface
        - **yfinance**: Stock price data (Yahoo Finance)
        - **pandas**: Data processing
        - **ta**: Technical indicators
        - **plotly**: Interactive charts
        - **SQLite**: Data storage

        ### ⚠️ Disclaimer

        This tool is intended for educational and research purposes only.

        - Not investment advice
        - Does not guarantee returns
        - Use at your own risk
        - Always consult a professional before making investment decisions

        ### 📝 Future Development Ideas

        - 🔔 Email/Telegram notifications
        - 🌍 Multi-strategy optimisation (parameter search)
        - 📊 Side-by-side strategy comparison in the same chart
        - 💼 Portfolio optimisation (e.g. Markowitz)
        - 🤖 ML-based signals
            """)
        else:
            st.markdown("""
        ### 🎯 Mitä tämä työkalu tekee?

        Tämä on osakeanalyysi-työkalu, joka auttaa sinua:
        - 📊 Seuraamaan osakkeiden teknistä analyysiä päivittäin
        - 🔔 Saamaan osto/myynti/pidä-signaaleja
        - 🔁 Testaamaan strategioita historiallisella datalla (backtesting)
        - 📈 Visualisoimaan hintoja, indikaattoreita ja kaupankäyntisignaaleja

        ---

        ## 📋 Käyttöohjeet: Osakkeiden lisääminen salkkuun

        ### 1️⃣ Suomen pörssi -välilehdeltä
        1. Napsauta yläreunan navigaatiosta **🇫🇮 Suomen pörssi** -välilehteä.
        2. Paina **🔄 Synkronoi** ladataksesi ajantasaisen listan Helsingin pörssistä (OMXH).
        3. Selaa tai etsi listasta haluamasi osake ja napsauta sen vieressä olevaa **➕ Lisää** -painiketta.
        4. Osake lisätään välittömästi vasemmassa sivupalkissa näkyvään **aktiiviseen salkkuun**.

        ### 2️⃣ USA:n pörssi -välilehdeltä
        1. Napsauta **🇺🇸 USA:n pörssi** -välilehteä.
        2. Paina **🔄 Synkronoi** noutaaksesi ajantasaisen S&P 500 -listan.
        3. Napsauta haluamasi osakkeen vieressä **➕ Lisää** lisätäksesi sen aktiiviseen salkkuun.

        ### 3️⃣ EU / Pohjoismaat ETF:t -välilehdeltä
        1. Napsauta **🇪🇺 EU / Pohjoismaat ETF:t** -välilehteä.
        2. Paina **🔄 Synkronoi**, sitten **➕ Lisää** haluamasi ETF:n kohdalla.

        ### 4️⃣ Tuo tiedostosta (massalisäys)
        1. Etsi vasemmasta sivupalkista kohta **📂 Tuo osakkeet tiedostosta**.
        2. Lataa `.txt`- tai `.csv`-tiedosto — yksi tikkeri per rivi tai pilkuilla erotettuna.
        3. Napsauta **✅ Tuo kaikki salkkuun**.
        4. Esimerkkitiedoston muoto:
           ```
           NOKIA.HE
           SAMPO.HE
           NESTE.HE
           ```
        5. Voit ladata esimerkkitiedoston **📄 Lataa esimerkkitiedosto** -linkistä.

        ### 5️⃣ Salkkujen hallinta
        - Voit luoda **enintään 5 salkkua** sivupalkin ➕-painikkeella.
        - Vaihda aktiivinen salkku valitsemalla se **🗂️ Salkut**-pudotusvalikosta.
        - Poista osake salkusta napsauttamalla sen vieressä olevaa 🗑️-kuvaketta sivupalkissa.
        - Poista salkku napsauttamalla sen nimen vieressä olevaa 🗑️-kuvaketta (viimeistä salkkua ei voi poistaa).

        ---

        ### 📈 Tekniset indikaattorit

        **RSI (Relative Strength Index)**
        - Mittaa hinnanmuutoksen nopeutta ja suuruutta
        - < 30: Ylimyyty (mahdollinen ostotilaisuus)
        - > 70: Yliostettu (mahdollinen myyntitilaisuus)

        **SMA50 (50 päivän liukuva keskiarvo)**
        - Lyhyen aikavälin trendi
        - Hinta SMA50 yläpuolella = nouseva trendi

        **SMA200 (200 päivän liukuva keskiarvo)**
        - Pitkän aikavälin trendi
        - Hinta SMA200 alapuolella = mahdollinen heikko trendi

        ### 🔁 Backtesting

        Backtesting testaa kuinka strategiasi olisi toiminut menneisyydessä:
        - **Strategia**: Aktiivinen osto/myynti signaalien mukaan
        - **Buy & Hold**: Osta alussa, pidä loppuun

        ⚠️ **TÄRKEÄÄ**: Historiallinen suorituskyky ei takaa tulevaa tuottoa!

        ### 🛠️ Teknologiat

        - **Python**: Ohjelmointikieli
        - **Streamlit**: Web-käyttöliittymä
        - **yfinance**: Osakekurssien haku (Yahoo Finance)
        - **pandas**: Datan käsittely
        - **ta**: Tekniset indikaattorit
        - **plotly**: Interaktiiviset kaaviot
        - **SQLite**: Osakkeiden tallennus

        ### ⚠️ Vastuuvapauslauseke

        Tämä työkalu on tarkoitettu vain koulutus- ja tutkimustarkoituksiin.

        - Ei ole sijoitusneuvontaa
        - Ei takaa tuottoja
        - Käytä omalla vastuullasi
        - Konsultoi aina ammattilaista ennen sijoituspäätöksiä

        ### 📝 Jatkokehitysideoita

        - 🔔 Sähköposti/Telegram-ilmoitukset
        - 🌍 Monistrategioiden optimointi (parametrien haku)
        - 📊 Strategioiden rinnakkainen vertailu samassa kaaviossa
        - 💼 Portfolio-optimointi (esim. Markowitz)
        - 🤖 ML-pohjainen signaali
            """)

if __name__ == "__main__":
    main()
