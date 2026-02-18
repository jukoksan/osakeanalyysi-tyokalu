"""
Osakeanalyysi Web-työkalu
Versio: 1.3.0
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
import time
from deep_translator import GoogleTranslator

# Asetukset
VERSION = "1.4.0"
DB_NAME = "stocks.db"

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


# --- Tietokanta ---
def init_db():
    """Alustaa SQLite-tietokannan ja ajaa tarvittavat migraatiot."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Portfoliot-taulu
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            created_at TEXT
        )
    """)

    # Luo oletussalkku jos ei ole portfolioita
    c.execute("SELECT COUNT(*) FROM portfolios")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO portfolios (name, created_at) VALUES (?, ?)",
            ("Salkku 1", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

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
    conn.commit()
    conn.close()

def get_portfolios():
    """Palauttaa kaikki salkut listana (id, name)."""
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT id, name FROM portfolios ORDER BY id").fetchall()
    conn.close()
    return rows  # [(id, name), ...]

def create_portfolio(name: str) -> int:
    """Luo uuden salkun, palauttaa sen id:n."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO portfolios (name, created_at) VALUES (?, ?)",
        (name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid

def rename_portfolio(portfolio_id: int, new_name: str):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE portfolios SET name = ? WHERE id = ?", (new_name, portfolio_id))
    conn.commit()
    conn.close()

def delete_portfolio(portfolio_id: int):
    """Poistaa salkun ja sen kaikki osakkeet."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM stocks WHERE portfolio_id = ?", (portfolio_id,))
    conn.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
    conn.commit()
    conn.close()

def save_fi_cache(results: list, timestamp: str):
    """Tallentaa Suomen pörssin datan tietokantaan JSON-muodossa."""
    import json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO fi_cache (id, data, synced_at)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET data=excluded.data, synced_at=excluded.synced_at
    """, (json.dumps(results, ensure_ascii=False), timestamp))
    conn.commit()
    conn.close()

def load_fi_cache():
    """Lataa Suomen pörssin datan tietokannasta. Palauttaa (list, str) tai (None, None)."""
    import json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    row = c.execute("SELECT data, synced_at FROM fi_cache WHERE id = 1").fetchone()
    conn.close()
    if row:
        return json.loads(row[0]), row[1]
    return None, None

def get_stocks(portfolio_id: int = 1):
    """Hakee salkun osakkeet tietokannasta"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(
        "SELECT * FROM stocks WHERE portfolio_id = ? ORDER BY symbol",
        conn, params=(portfolio_id,)
    )
    conn.close()
    return df

def add_stock(symbol, portfolio_id: int = 1):
    """Lisää osakkeen tietokantaan"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO stocks (symbol, portfolio_id, added_at) VALUES (?, ?, ?)",
            (symbol.upper(), portfolio_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return True, "Osake lisätty onnistuneesti!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Osake on jo tässä salkussa."
    except Exception as e:
        conn.close()
        return False, f"Virhe: {str(e)}"

def delete_stock(symbol, portfolio_id: int = 1):
    """Poistaa osakkeen tietokannasta"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM stocks WHERE symbol = ? AND portfolio_id = ?", (symbol, portfolio_id))
    conn.commit()
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
def fetch_stock_data(symbol, period="6mo"):
    """Hakee osakekurssit ja info Yahoosta (välimuistissa 5 min)"""
    stock = yf.Ticker(symbol)
    df = stock.history(period=period)
    info = stock.info
    return df, info

@st.cache_data(ttl=300)
def fetch_stock_history(symbol, start_date, end_date):
    """Hakee pitkän historian backtestingiä varten (välimuistissa 5 min)"""
    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)
    return df

@st.cache_data(ttl=86400, show_spinner=False)
def translate_to_finnish(text):
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
    except Exception:
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

# --- Streamlit UI ---
def main():
    st.set_page_config(
        page_title="Osakeanalyysi-työkalu",
        page_icon="📈",
        layout="wide"
    )
    
    st.title(f"📈 Osakeanalyysi-työkalu v{VERSION}")
    st.markdown("**Tekninen analyysi, backtesting ja päivittäiset signaalit**")
    
    # Alusta tietokanta
    init_db()
    
    # Sivupalkki - Osakkeiden hallinta
    with st.sidebar:
        st.header("🗂️ Salkut")

        portfolios = get_portfolios()
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
                        create_portfolio(new_pname.strip())
                        st.rerun()
            else:
                st.info("Maksimimäärä (5) salkkuja saavutettu.")

        # Lisää yksittäinen osake
        st.markdown("---")
        with st.form("add_stock_form"):
            new_symbol = st.text_input("Osaketunnus (esim. AAPL, NOKIA.HE)", "").upper()
            submit = st.form_submit_button("➕ Lisää osake")
            if submit and new_symbol:
                success, message = add_stock(new_symbol, active_portfolio_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

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
                if st.button("✅ Tuo kaikki salkkuun", key="import_file"):
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
            st.info("Ei osakkeita. Lisää ensimmäinen osake yllä.")

    # Päänäkymä
    stocks_df = get_stocks(active_portfolio_id)

    # Välilehdet — salkku-välilehti ei vaadi osakkeita etukäteen
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analyysi",
        "🔁 Backtesting",
        "🇫🇮 Suomen pörssi",
        "ℹ️ Tietoa",
    ])

    # --- ANALYYSI-välilehti ---
    with tab1:
        st.header(f"📊 Päivittäinen analyysi – {active_portfolio_name}")

        if stocks_df.empty:
            st.info("👈 Lisää osakkeita vasemmalta aloittaaksesi analyysin")
        else:
            # Auto-refresh -asetukset
            col_r1, col_r2 = st.columns([2, 1])
            with col_r1:
                auto_refresh = st.toggle("🔄 Automaattinen päivitys", value=False,
                                         help="Päivittää datan automaattisesti valitun väliajoin")
            with col_r2:
                refresh_interval = st.selectbox(
                    "Väli",
                    options=[30, 60, 120, 300],
                    format_func=lambda x: f"{x}s" if x < 60 else f"{x//60} min",
                    index=1,
                    disabled=not auto_refresh,
                )

            col_btn, col_ts = st.columns([1, 3])
            with col_btn:
                manual_refresh = st.button("🔄 Päivitä nyt")
            with col_ts:
                st.caption(f"Viimeksi päivitetty: {datetime.now().strftime('%H:%M:%S')}")

            if manual_refresh:
                fetch_stock_data.clear()
                st.rerun()

            # Analysoi kaikki osakkeet
            results = []
            with st.spinner("Analysoidaan osakkeita..."):
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
                        "Tunnus": r["symbol"],
                        "Yritys": r["company"],
                        "Hinta (€)": r["price"],
                        "RSI": r["rsi"] if r["rsi"] else "-",
                        "SMA50": r["sma50"] if r["sma50"] else "-",
                        "SMA200": r["sma200"] if r["sma200"] else "-",
                        "P/E": round(r["pe_ratio"], 2) if r["pe_ratio"] else "-",
                        "P/B": round(r["pb_ratio"], 2) if r["pb_ratio"] else "-",
                        "ROE %": round(r["roe"] * 100, 1) if r["roe"] else "-",
                        "Osinko %": round(r["dividend_yield"], 2) if r["dividend_yield"] else "-",
                        "Signaali": f"{r['signal_color']} {r['signal']}"
                    })

                df_display = pd.DataFrame(display_data)
                st.dataframe(df_display, width='stretch', hide_index=True)

                csv = df_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Lataa CSV",
                    data=csv,
                    file_name=f"osakeanalyysi_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )

                # --- Fundamenttianalyysi & uutiset per osake ---
                st.markdown("---")
                st.subheader("🔍 Yksittäinen osake – fundamentit, kaaviot ja uutiset")
                detail_symbol = st.selectbox(
                    "Valitse osake",
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
                            st.info("Ei uutisia saatavilla.")
                    except Exception:
                        st.info("Uutisten haku epäonnistui.")

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

            # Auto-refresh silmukka
            if auto_refresh:
                time.sleep(refresh_interval)
                fetch_stock_data.clear()
                st.rerun()
    
    # --- BACKTESTING-välilehti ---
    with tab2:
        st.header("🔁 Backtesting - Strategian testaus")
        st.markdown("Testaa kuinka eri strategiat olisivat toimineet historialla")

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

        if st.button("▶️ Aja backtesting"):
            if stocks_df.empty:
                st.warning("Lisää ensin osakkeita omaan salkkuun.")
            else:
                backtest_results = []
                with st.spinner("Ajetaan backtestingiä..."):
                    for symbol in stocks_df["symbol"]:
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

                    styled_df = df_display.style.applymap(
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
            selected_symbol = st.selectbox("Valitse osake", symbols, key="bt_symbol_select")
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

        st.header("🇫🇮 Suomen pörssi – Nasdaq Helsinki (OMXH)")
        st.markdown(
            f"Lista sisältää **{len(FINNISH_STOCKS)}** Helsingin pörssin osaketta. "
            "Kurssit haetaan Yahoo Financesta (.HE-suffiksi)."
        )

        # Auto-refresh asetukset
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            fi_auto_refresh = st.toggle(
                "🔄 Automaattinen päivitys",
                value=False,
                key="fi_auto_refresh",
                help="Päivittää Suomen pörssin datan automaattisesti",
            )
        with col_r2:
            fi_refresh_interval = st.selectbox(
                "Väli",
                options=[60, 120, 300],
                format_func=lambda x: f"{x//60} min",
                index=0,
                disabled=not fi_auto_refresh,
                key="fi_refresh_interval",
            )

        col_btn1, col_btn2, col_ts = st.columns([1, 1, 4])
        with col_btn1:
            sync_all = st.button("🔄 Synkkaa kaikki", key="fi_sync")
        with col_btn2:
            clear_cache_btn = st.button("🗑️ Tyhjennä cache", key="fi_clear_cache")
        with col_ts:
            ts_placeholder = st.empty()
            saved_ts = st.session_state.get("fi_last_sync")
            if saved_ts:
                ts_placeholder.caption(f"🕒 Viimeksi synkattu: **{saved_ts}**")

        if clear_cache_btn:
            fetch_stock_data.clear()
            st.toast("Cache tyhjennetty!", icon="🗑️")

        # Hae data — VAIN kun nappia painetaan manuaalisesti tai auto-refresh on päällä
        if sync_all or fi_auto_refresh:
            st.session_state["fi_sync_requested"] = True

        if st.session_state.get("fi_sync_requested"):
            fi_results = []
            progress_bar = st.progress(0, text="Haetaan kursseja...")
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
                            "Tunnus": symbol,
                            "Yritys": FINNISH_STOCKS[symbol],
                            "Hinta": latest_price,
                            "Muutos %": change_pct,
                            "RSI": rsi_val if rsi_val is not None else "-",
                            "SMA50": sma50_val if sma50_val is not None else "-",
                            "Signaali": signal,
                            "Valuutta": currency,
                            "P/E": round(pe, 2) if pe else "-",
                            "Markkina-arvo": f"{market_cap/1e9:.1f} Mrd" if market_cap else "-",
                        })
                except Exception:
                    pass  # virheelliset ohitetaan hiljaisesti
                progress_bar.progress((idx + 1) / total, text=f"Haetaan: {symbol} ({idx+1}/{total})")

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

            # Suodatin — lisätty signaali-suodatin
            col_f1, col_f2 = st.columns([3, 1])
            with col_f1:
                search_fi = st.text_input("🔍 Hae yhtiötä tai tunnusta", "", key="fi_search")
            with col_f2:
                signal_filter = st.selectbox(
                    "Signaali",
                    options=["Kaikki", "🟢 OSTA", "🔴 MYY", "🟡 PIDÄ"],
                    key="fi_signal_filter",
                )

            if search_fi:
                mask = (
                    fi_df["Tunnus"].str.contains(search_fi.upper(), na=False)
                    | fi_df["Yritys"].str.contains(search_fi, case=False, na=False)
                )
                fi_df = fi_df[mask]
            if signal_filter != "Kaikki" and "Signaali" in fi_df.columns:
                fi_df = fi_df[fi_df["Signaali"] == signal_filter]

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

            style_cols = {"Muutos %": color_change}
            if "Signaali" in fi_df.columns:
                styled = fi_df.style.applymap(color_change, subset=["Muutos %"]).applymap(
                    color_signal, subset=["Signaali"]
                )
            else:
                styled = fi_df.style.applymap(color_change, subset=["Muutos %"])
            st.dataframe(styled, width='stretch', hide_index=True)

            # Lisää yksittäisiä osakkeita salkkuun taulukosta
            st.markdown("---")
            col_sel1, col_sel2 = st.columns([2, 1])
            with col_sel1:
                selected_fi = st.multiselect(
                    "Valitse osakkeet salkkuun lisäämistä varten",
                    options=list(FINNISH_STOCKS.keys()),
                    format_func=lambda s: f"{s} – {FINNISH_STOCKS[s]}",
                    key="fi_multiselect",
                )
            with col_sel2:
                st.write("")
                st.write("")
                if st.button("➕ Lisää valitut salkkuun", key="fi_add_selected") and selected_fi:
                    added, skipped, errs = add_stocks_bulk(selected_fi, active_portfolio_id)
                    st.success(f"Lisätty '{active_portfolio_name}': {added}, jo listalla: {skipped}")
                    st.rerun()

            # CSV-lataus
            csv_fi = fi_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Lataa taulukko CSV",
                data=csv_fi,
                file_name=f"suomen_porssi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        else:
            st.info("Paina **🔄 Synkkaa kaikki** ladataksesi ajantasaiset kurssit.")

        # Auto-refresh loppusilmukka
        if fi_auto_refresh:
            time.sleep(fi_refresh_interval)
            fetch_stock_data.clear()
            st.session_state["fi_sync_requested"] = True
            st.rerun()

    # --- TIETOA-välilehti ---
    with tab4:
        st.header("ℹ️ Tietoa työkalusta")
        st.caption(f"Versio {VERSION} | Päivitetty {datetime.now().strftime('%d.%m.%Y')}")
        
        st.markdown("""
        ### 🎯 Mitä tämä työkalu tekee?
        
        Tämä on osakeanalyysi-työkalu, joka auttaa sinua:
        - 📊 Seuraamaan osakkeiden teknistä analyysiä päivittäin
        - 🔔 Saamaan osto/myynti/pidä-signaaleja
        - 🔁 Testaamaan strategioita historiallisella datalla (backtesting)
        - 📈 Visualisoimaan hintoja, indikaattoreita ja kaupankäyntisignaaleja
        
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
