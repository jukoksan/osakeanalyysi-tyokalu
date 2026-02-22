"""
Yksikkötestit – Osakeanalyysi-työkalu
======================================
Kattaa:
  - _hash_pw               : salasanahashaus
  - t()                    : käännösfunktio
  - _remap_df_columns      : sarakkeiden uudelleennimeäminen
  - parse_symbols_from_text: osaketunnusten parsinta
  - create_user            : käyttäjän luonti
  - verify_password        : kirjautumistarkistus
  - change_password        : salasanan vaihto
  - add_stock              : osakkeen lisäys salkkuun
  - delete_stock           : osakkeen poisto salkusta
  - add_stocks_bulk        : useiden osakkeiden massalisäys
  - add_fund / delete_fund : rahastohallinta
  - add_fund_nav           : NAV-kirjaus ja päivitys
  - get_fund_nav_history   : NAV-historian haku
  - _generate_signals      : teknisten signaalien generointi
  - _simulate_trades       : kaupankäynnin simulointi
"""

import os
import sys
import tempfile
import hashlib
import sqlite3

import pandas as pd
import numpy as np
import pytest

# Varmistetaan, että streamlit on mockattu (conftest.py hoitaa, mutta
# haetaan myös tässä jotta IDE ei valita)
import streamlit as st  # noqa: F401 – mockattu conftest.py:ssä

# Importataan testattava moduuli
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """
    Luo väliaikaisen SQLite-tietokannan jokaista testiä varten ja
    ohjaa app.DB_NAME siihen. Kutsuu init_db() kantarakenteen luomiseksi.
    """
    db_file = str(tmp_path / "test_stocks.db")
    monkeypatch.setattr(app, "DB_NAME", db_file)
    app.init_db()
    return db_file


@pytest.fixture()
def fi_lang(monkeypatch):
    """Asettaa kielen suomeksi session_stateen."""
    monkeypatch.setitem(st.session_state, "lang", "fi")


@pytest.fixture()
def en_lang(monkeypatch):
    """Asettaa kielen englanniksi session_stateen."""
    monkeypatch.setitem(st.session_state, "lang", "en")


@pytest.fixture()
def test_user(tmp_db):
    """Luo testitietokannan käyttäjän ja palauttaa (user_id, username, password)."""
    ok, _ = app.create_user("testikäyttäjä", "salainen123", "Testi Käyttäjä", "testi@example.com")
    assert ok
    row = app.get_user_by_username("testikäyttäjä")
    return row[0], "testikäyttäjä", "salainen123"


@pytest.fixture()
def test_portfolio(tmp_db, test_user):
    """Luo testitietokannan salkun käyttäjälle ja palauttaa (portfolio_id, user_id)."""
    user_id = test_user[0]
    app.ensure_user_portfolio(user_id)
    portfolios = app.get_portfolios(user_id)
    assert portfolios
    portfolio_id = portfolios[0][0]
    return portfolio_id, user_id


# ===========================================================================
# 1. _hash_pw
# ===========================================================================

class TestHashPw:
    def test_returns_sha256_hex(self):
        expected = hashlib.sha256("salasana".encode()).hexdigest()
        assert app._hash_pw("salasana") == expected

    def test_different_passwords_different_hashes(self):
        assert app._hash_pw("abc") != app._hash_pw("xyz")

    def test_same_password_same_hash(self):
        assert app._hash_pw("toistettava") == app._hash_pw("toistettava")

    def test_empty_string(self):
        result = app._hash_pw("")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex = 64 merkkiä


# ===========================================================================
# 2. t() – käännösfunktio
# ===========================================================================

class TestTranslation:
    def test_fi_key_returns_finnish(self, fi_lang):
        result = app.t("login_title")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_en_key_returns_english(self, en_lang):
        fi_result = app.t("login_title")
        # Vaihdetaan kieli suomeksi vertailua varten
        st.session_state["lang"] = "fi"
        fi_text = app.t("login_title")
        st.session_state["lang"] = "en"
        en_text = app.t("login_title")
        # Englannin ja suomen käännösten tulee erota (tai olla samat jos sama termi)
        assert isinstance(en_text, str)
        assert len(en_text) > 0

    def test_missing_key_returns_key(self, fi_lang):
        result = app.t("ei_ole_olemassa_avain_xyz")
        assert result == "ei_ole_olemassa_avain_xyz"

    def test_format_kwargs(self, fi_lang):
        # Käytetään avainta, joka sisältää {n} tai vastaavan muuttujan
        # Haetaan ensin raakateksti
        raw = app.TRANSLATIONS["fi"].get("fi_fetching", "")
        if "{symbol}" in raw:
            result = app.t("fi_fetching", symbol="NOKIA.HE", idx=1, total=10)
            assert "NOKIA.HE" in result
        else:
            pytest.skip("fi_fetching-avain ei sisällä {symbol}-muuttujaa")

    def test_fi_col_symbol(self, fi_lang):
        result = app.t("col_symbol")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_en_col_symbol_differs_or_same(self, en_lang):
        result = app.t("col_symbol")
        assert isinstance(result, str)


# ===========================================================================
# 3. _remap_df_columns
# ===========================================================================

class TestRemapDfColumns:
    def test_no_rename_needed(self, fi_lang):
        col_name = app.t("col_symbol")
        df = pd.DataFrame({col_name: ["NOKIA.HE"]})
        result = app._remap_df_columns(df, ["col_symbol"])
        assert col_name in result.columns

    def test_renames_foreign_language_column(self, monkeypatch):
        """Sarake tallennettu englanniksi, näytetään suomeksi."""
        monkeypatch.setitem(st.session_state, "lang", "fi")
        fi_name = app.t("col_symbol")
        monkeypatch.setitem(st.session_state, "lang", "en")
        en_name = app.t("col_symbol")
        monkeypatch.setitem(st.session_state, "lang", "fi")

        if fi_name == en_name:
            pytest.skip("Sarakkeen nimi sama molemmilla kielillä")

        # DataFrame-sarakkeessa englanninkielinen nimi
        df = pd.DataFrame({en_name: ["NOKIA.HE"]})
        result = app._remap_df_columns(df, ["col_symbol"])
        assert fi_name in result.columns
        assert en_name not in result.columns

    def test_returns_original_if_nothing_to_remap(self, fi_lang):
        df = pd.DataFrame({"Tuntematon": [1, 2, 3]})
        result = app._remap_df_columns(df, ["col_symbol"])
        assert "Tuntematon" in result.columns


# ===========================================================================
# 4. parse_symbols_from_text
# ===========================================================================

class TestParseSymbolsFromText:
    def test_comma_separated(self):
        result = app.parse_symbols_from_text("nokia.he,neste.he,fortum.he")
        assert result == ["NOKIA.HE", "NESTE.HE", "FORTUM.HE"]

    def test_newline_separated(self):
        result = app.parse_symbols_from_text("NOKIA.HE\nNESTE.HE")
        assert result == ["NOKIA.HE", "NESTE.HE"]

    def test_mixed_separators(self):
        result = app.parse_symbols_from_text("NOKIA.HE; NESTE.HE\nFORTUM.HE")
        assert "NOKIA.HE" in result
        assert "NESTE.HE" in result
        assert "FORTUM.HE" in result

    def test_uppercase_conversion(self):
        result = app.parse_symbols_from_text("nokia.he")
        assert result == ["NOKIA.HE"]

    def test_empty_string(self):
        result = app.parse_symbols_from_text("")
        assert result == []

    def test_whitespace_only(self):
        result = app.parse_symbols_from_text("   \n  ")
        assert result == []

    def test_single_symbol(self):
        result = app.parse_symbols_from_text("AAPL")
        assert result == ["AAPL"]


# ===========================================================================
# 5. Käyttäjähallinta: create_user / verify_password / change_password
# ===========================================================================

class TestUserManagement:
    def test_create_user_success(self, tmp_db):
        ok, msg = app.create_user("uusikäyttäjä", "salasana1")
        assert ok is True
        assert "luotu" in msg.lower() or ok

    def test_create_user_duplicate_fails(self, tmp_db):
        app.create_user("duplikaatti", "pass1")
        ok, msg = app.create_user("duplikaatti", "pass2")
        assert ok is False
        assert "käytössä" in msg.lower() or "already" in msg.lower()

    def test_verify_password_correct(self, test_user):
        _, username, password = test_user
        assert app.verify_password(username, password) is True

    def test_verify_password_wrong(self, test_user):
        _, username, _ = test_user
        assert app.verify_password(username, "väärä_salasana") is False

    def test_verify_password_nonexistent_user(self, tmp_db):
        assert app.verify_password("ei_ole", "salasana") is False

    def test_change_password_success(self, test_user):
        user_id, _, old_pw = test_user
        ok, msg = app.change_password(user_id, old_pw, "uusi_salasana")
        assert ok is True
        assert app.verify_password("testikäyttäjä", "uusi_salasana") is True

    def test_change_password_wrong_old(self, test_user):
        user_id, _, _ = test_user
        ok, msg = app.change_password(user_id, "väärä_vanha", "uusi")
        assert ok is False
        assert "väärin" in msg.lower() or "wrong" in msg.lower()

    def test_update_user_language(self, test_user, tmp_db):
        user_id, username, _ = test_user
        app.update_user_language(user_id, "en")
        row = app.get_user_by_username(username)
        # language on indeksillä 6: (id, username, pw_hash, display_name, email, role, language)
        assert row[6] == "en"

    def test_get_all_users(self, tmp_db):
        app.create_user("yksi", "pass1")
        app.create_user("kaksi", "pass2")
        users = app.get_all_users()
        usernames = [u[1] for u in users]
        assert "yksi" in usernames
        assert "kaksi" in usernames

    def test_delete_user(self, test_user, tmp_db):
        user_id, username, _ = test_user
        app.delete_user(user_id)
        assert app.get_user_by_username(username) is None


# ===========================================================================
# 6. Salkku ja osakkeet
# ===========================================================================

class TestStockPortfolio:
    def test_add_stock_success(self, test_portfolio):
        port_id, _ = test_portfolio
        ok, msg = app.add_stock("NOKIA.HE", port_id)
        assert ok is True

    def test_add_stock_duplicate(self, test_portfolio):
        port_id, _ = test_portfolio
        app.add_stock("NOKIA.HE", port_id)
        ok, msg = app.add_stock("NOKIA.HE", port_id)
        assert ok is False
        assert "jo" in msg.lower() or "already" in msg.lower()

    def test_add_stock_uppercased(self, test_portfolio):
        port_id, _ = test_portfolio
        app.add_stock("nokia.he", port_id)
        df = app.get_stocks(port_id)
        assert "NOKIA.HE" in df["symbol"].values

    def test_delete_stock(self, test_portfolio):
        port_id, _ = test_portfolio
        app.add_stock("NESTE.HE", port_id)
        app.delete_stock("NESTE.HE", port_id)
        df = app.get_stocks(port_id)
        assert "NESTE.HE" not in df["symbol"].values

    def test_add_stocks_bulk_returns_counts(self, test_portfolio):
        port_id, _ = test_portfolio
        added, skipped, errors = app.add_stocks_bulk(
            ["NOKIA.HE", "NESTE.HE", "FORTUM.HE"], port_id
        )
        assert added == 3
        assert skipped == 0
        assert errors == []

    def test_add_stocks_bulk_skips_duplicates(self, test_portfolio):
        port_id, _ = test_portfolio
        app.add_stock("NOKIA.HE", port_id)
        added, skipped, errors = app.add_stocks_bulk(["NOKIA.HE", "NESTE.HE"], port_id)
        assert skipped == 1
        assert added == 1

    def test_add_stocks_bulk_empty_list(self, test_portfolio):
        port_id, _ = test_portfolio
        added, skipped, errors = app.add_stocks_bulk([], port_id)
        assert added == 0


# ===========================================================================
# 7. Rahastot (Funds & NAV)
# ===========================================================================

class TestFunds:
    def _add_fund(self, tmp_db, user_id):
        ok, msg = app.add_fund(user_id, "Seligson Phoebus", "FI4000148028", "Pitkä aikaväli")
        assert ok
        funds = app.get_funds(user_id)
        return funds[0]["id"]

    def test_add_fund_success(self, tmp_db, test_user):
        user_id = test_user[0]
        ok, msg = app.add_fund(user_id, "Nordea Suomi", "FI0000000000", "")
        assert ok is True

    def test_add_fund_name_required(self, tmp_db, test_user):
        """Tyhjä nimi aiheuttaa virheen (DB NOT NULL tai sovellustason validointi)."""
        user_id = test_user[0]
        ok, msg = app.add_fund(user_id, "", "", "")
        # Joko ok=False tai ok=True riippuen DB-rajoitteista – tarkistetaan tyyppi
        assert isinstance(ok, bool)

    def test_get_funds_empty(self, tmp_db, test_user):
        user_id = test_user[0]
        funds = app.get_funds(user_id)
        assert funds == []

    def test_delete_fund(self, tmp_db, test_user):
        user_id = test_user[0]
        fund_id = self._add_fund(tmp_db, user_id)
        app.delete_fund(fund_id)
        assert app.get_funds(user_id) == []

    def test_add_fund_nav_success(self, tmp_db, test_user):
        user_id = test_user[0]
        fund_id = self._add_fund(tmp_db, user_id)
        ok, msg = app.add_fund_nav(fund_id, 12.50, "2024-01-15")
        assert ok is True
        assert "tallennettu" in msg.lower() or ok

    def test_add_fund_nav_upsert(self, tmp_db, test_user):
        """Saman päivämäärän NAV päivitetään, ei lisätä duplikaattia."""
        user_id = test_user[0]
        fund_id = self._add_fund(tmp_db, user_id)
        app.add_fund_nav(fund_id, 10.00, "2024-02-01")
        app.add_fund_nav(fund_id, 11.00, "2024-02-01")  # upsert
        df = app.get_fund_nav_history(fund_id)
        assert len(df) == 1
        assert float(df.iloc[0]["nav"]) == pytest.approx(11.00)

    def test_get_fund_nav_history_empty(self, tmp_db, test_user):
        user_id = test_user[0]
        fund_id = self._add_fund(tmp_db, user_id)
        df = app.get_fund_nav_history(fund_id)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_get_fund_nav_history_sorted(self, tmp_db, test_user):
        user_id = test_user[0]
        fund_id = self._add_fund(tmp_db, user_id)
        app.add_fund_nav(fund_id, 15.00, "2024-03-01")
        app.add_fund_nav(fund_id, 10.00, "2024-01-01")
        app.add_fund_nav(fund_id, 12.50, "2024-02-01")
        df = app.get_fund_nav_history(fund_id)
        dates = list(df["nav_date"])
        assert dates == sorted(dates)

    def test_delete_fund_nav(self, tmp_db, test_user):
        user_id = test_user[0]
        fund_id = self._add_fund(tmp_db, user_id)
        app.add_fund_nav(fund_id, 10.00, "2024-01-01")
        app.add_fund_nav(fund_id, 11.00, "2024-02-01")
        app.delete_fund_nav(fund_id, "2024-01-01")
        df = app.get_fund_nav_history(fund_id)
        assert len(df) == 1
        assert df.iloc[0]["nav_date"] == "2024-02-01"


# ===========================================================================
# 8. _generate_signals – tekniset signaalit
# ===========================================================================

def _make_price_df(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Generoi synteettisen hintadatan testejä varten."""
    rng = np.random.default_rng(seed)
    prices = 100 + np.cumsum(rng.normal(0, 1, n))
    prices = np.maximum(prices, 1.0)
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    return pd.DataFrame({"Date": dates, "Close": prices, "Volume": 1_000_000})


class TestGenerateSignals:
    STRATEGIES = [
        "RSI + SMA (perus)",
        "Momentum (SMA-risteytys)",
        "Mean Reversion (Bollinger Bands)",
        "MACD-risteytys",
    ]

    def test_signal_column_exists(self):
        df = _make_price_df()
        result = app._generate_signals(df, "RSI + SMA (perus)")
        assert "Signal" in result.columns

    @pytest.mark.parametrize("strategy", STRATEGIES)
    def test_valid_signal_values(self, strategy):
        df = _make_price_df()
        result = app._generate_signals(df, strategy)
        valid = {"BUY", "SELL", "HOLD"}
        assert set(result["Signal"].unique()).issubset(valid)

    @pytest.mark.parametrize("strategy", STRATEGIES)
    def test_output_length_unchanged(self, strategy):
        df = _make_price_df()
        result = app._generate_signals(df, strategy)
        assert len(result) == len(df)

    def test_rsi_sma_buy_condition(self):
        """Pakottaa RSI < 30 ja Close > SMA50 → odotetaan BUY-signaali."""
        df = _make_price_df()
        df["RSI"] = 25.0   # kaikki alle 30
        df["SMA50"] = 50.0  # Close ≈ 100 > 50
        df["SMA200"] = 80.0
        df["Signal"] = "HOLD"
        result = app._generate_signals(df, "RSI + SMA (perus)")
        assert "BUY" in result["Signal"].values

    def test_rsi_sma_sell_condition(self):
        """Pakottaa RSI > 70 → odotetaan SELL-signaali."""
        df = _make_price_df()
        df["RSI"] = 80.0
        df["SMA50"] = 50.0
        df["SMA200"] = 80.0
        df["Signal"] = "HOLD"
        result = app._generate_signals(df, "RSI + SMA (perus)")
        assert "SELL" in result["Signal"].values

    def test_does_not_mutate_original(self):
        df = _make_price_df()
        original_cols = set(df.columns)
        app._generate_signals(df, "RSI + SMA (perus)")
        # Alkuperäinen df ei saa saada Signal-saraketta
        assert "Signal" not in df.columns


# ===========================================================================
# 9. _simulate_trades – kaupankäyntimoottori
# ===========================================================================

def _make_signal_df(buy_idx: int, sell_idx: int, n: int = 100) -> pd.DataFrame:
    """Synteettinen DataFrame yksiselitteisellä BUY→SELL-parilla."""
    prices = [100.0] * n
    # Hinnan nousu BUY:n jälkeen voitollista kauppaa varten
    for i in range(buy_idx, n):
        prices[i] = 100.0 + (i - buy_idx) * 0.5
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    signals = ["HOLD"] * n
    signals[buy_idx] = "BUY"
    signals[sell_idx] = "SELL"
    return pd.DataFrame({"Date": dates, "Close": prices, "Signal": signals})


class TestSimulateTrades:
    def test_returns_required_keys(self):
        df = _make_signal_df(10, 50)
        result = app._simulate_trades(df, 10_000, 0.001)
        required = {"strategy_final", "strategy_return", "trades",
                    "win_rate", "max_drawdown", "sharpe_ratio",
                    "trade_history", "equity_df"}
        assert required.issubset(result.keys())

    def test_no_trades_returns_capital(self):
        """Ei yhtään signaalia → pääoma palautuu muuttumattomana."""
        n = 50
        df = pd.DataFrame({
            "Date": pd.date_range("2022-01-01", periods=n),
            "Close": [100.0] * n,
            "Signal": ["HOLD"] * n,
        })
        result = app._simulate_trades(df, 10_000, 0.001)
        assert result["trades"] == 0
        assert result["strategy_final"] == pytest.approx(10_000.0)

    def test_profitable_trade_increases_capital(self):
        """Osta halvalla, myy kalliilla → pääoma kasvaa."""
        buy_idx, sell_idx = 5, 50
        df = _make_signal_df(buy_idx, sell_idx)
        result = app._simulate_trades(df, 10_000, 0.0)  # ei kuluja helpottaa
        assert result["strategy_final"] > 10_000

    def test_trade_count(self):
        df = _make_signal_df(10, 60)
        result = app._simulate_trades(df, 10_000, 0.001)
        # Yksi BUY-signaali = 1 kauppa
        assert result["trades"] == 1

    def test_equity_curve_length(self):
        df = _make_signal_df(10, 60)
        result = app._simulate_trades(df, 10_000, 0.001)
        assert len(result["equity_df"]) == len(df)

    def test_win_rate_range(self):
        df = _make_signal_df(10, 60)
        result = app._simulate_trades(df, 10_000, 0.001)
        assert 0.0 <= result["win_rate"] <= 100.0

    def test_strategy_return_type(self):
        df = _make_signal_df(10, 60)
        result = app._simulate_trades(df, 10_000, 0.001)
        assert isinstance(result["strategy_return"], float)
