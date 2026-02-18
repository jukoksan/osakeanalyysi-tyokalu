# Changelog

Kaikki projektin merkittävät muutokset dokumentoidaan tähän tiedostoon.

Formaatti perustuu [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) -standardiin,
ja projekti noudattaa [Semantic Versioning](https://semver.org/spec/v2.0.0.html) -versiointia.

## [1.3.0] - 2026-02-19

### Lisätty
- 🤖 **Automaattinen osakeyhteenveto** – rule-based analyysi jokaiselle osakkeelle analyysi-välilehdellä
  - Värikoodatut pisteet arvostuksesta (P/E, P/B), kannattavuudesta (ROE, nettomarginaali), teknisestä tilanteesta (RSI, SMA50/200), velkaantumisesta (D/E) ja osinkotuotosta
  - Kokonaissignaali (OSTA/MYY) yhteenvedossa
  - Huomautus: ei sijoitusneuvontaa
- 🌐 **Yrityksen kuvaus käännetään suomeksi** – Google Translaten kautta (deep-translator)
  - Käännös välimuistitetaan 24 tunniksi
  - Palautuu alkuperäiseen englantiin jos käännös epäonnistuu

### Korjattu
- 🔢 **Osinko % näytti väärän arvon** – yfinance palauttaa arvon jo prosentteina, korjattu kertominen 100:lla pois
- 🔍 **Suomen pörssi -taulukko näytti vain suodatetut osakkeet synkrauksen jälkeen** – suodatin ja hakukenttä nollataan nyt automaattisesti synkrauksen yhteydessä
- ➕ **Valmet (VALMT.HE) lisätty Suomen pörssin listaukseen**

## [1.2.0] - 2026-02-18

### Lisätty
- 🇫🇮 **Suomen pörssi -välilehti** – kaikki ~100 Nasdaq Helsinki (OMXH) -yhtiötä listattuna
  - "Synkkaa kaikki" -nappi hakee ajantasaiset kurssit Yahoo Financesta
  - "Lisää kaikki salkkuun" -nappi lisää kaikki OMXH-osakkeet omaan salkkuun kerralla
  - Osakkeiden valinta multiselect-listasta ja lisäys salkkuun
  - Yhtiöhaku (tunnus tai nimi)
  - CSV-vienti koko Suomen pörssin listauksesta
  - Edistymispalkki synkronoinnin aikana
- 📂 **Import txt-tiedostosta** – tuo osaketunnuksia omaan salkkuun tekstitiedostosta
  - Tukee .txt ja .csv -muotoja
  - Tukee rivinvaihto-, pilkku- tai välilyöntierottelua
  - Esimerkkitiedoston lataus
- 🔄 **Automaattinen päivitys (auto-refresh)**
  - Analyysi- ja Suomen pörssi -välilehdillä toggle-kytkin
  - Säädettävä intervalli (30 s – 5 min)
  - Cache tyhjennetään automaattisesti päivityksen yhteydessä
  - "Viimeksi päivitetty" -aikaleima
- 🗑️ **Tyhjennä cache** -nappi Suomen pörssi -välilehdellä

### Muutettu
- Välilehtirakenne: 4 välilehteä (Analyysi / Backtesting / Suomen pörssi / Tietoa)
- Analyysi-välilehti ei enää vaadi `return`ia tyhjällä salkulla — kaikki välilehdet ovat aina käytettävissä
- Sidebarin otsikko "Osakkeiden hallinta" → "Oma salkku"

## [1.1.0] - 2026-02-18

### Lisätty
- 📊 **MACD-indikaattori** – histogrammi + signaaliviiva hinta- ja MACD-kaavioissa
- 📉 **Bollinger Bands** – yläkaista, alakaista ja keskilinja hintakaaviossa
- 📈 **Equity Curve -kaavio** – pääoman kehitys backtestingissä päivätasolla
- ⚡ **Kaupankäyntikulujen simulointi** – säädettävä komissioprosentti (0–1 %) backtestingissä
- 🏆 **Riskimittarit backtestingiin**
  - Max Drawdown (suurin kertynyt tappio huipusta)
  - Sharpe Ratio (riskikorjattu tuotto, annualisoitu)
  - Win Rate % (voittavien kauppojen osuus)
- 🚀 **Suorituskykyparannus** – signaaligenerointi vektorisoitu (NumPy/pandas), ei enää rivitason `for`-silmukkaa
- 🗄️ **Välimuisti (caching)** – yfinance-HTTP-kutsut välimuistissa 5 min (`@st.cache_data`)

### Muutettu
- Backtesting-tulostaulukko sisältää nyt Win Rate, Max Drawdown ja Sharpe Ratio -sarakkeet
- Yhteenvetomittarit laajennettu: lisätty keskim. Max Drawdown ja Sharpe Ratio
- Kaaviot-osio: järjestys Equity Curve → Hinta → MACD → RSI

## [1.0.0] - 2026-02-18

### Lisätty
- 🌐 Streamlit-pohjainen web-käyttöliittymä
- 🗂️ SQLite-tietokanta osakkeiden hallintaan
- ➕ Osakkeiden lisäys ja poisto käyttöliittymästä
- 📊 Päivittäinen tekninen analyysi
  - RSI (Relative Strength Index)
  - SMA50 (50 päivän liukuva keskiarvo)
  - SMA200 (200 päivän liukuva keskiarvo)
- 📈 Tunnuslukujen näyttö
  - P/E (Price-to-Earnings)
  - Markkina-arvo
  - Ajantasainen hinta
- 🔔 Automaattiset osto/myynti/pidä-signaalit
  - OSTA: RSI < 30 ja hinta > SMA50
  - MYY: RSI > 70 tai hinta < SMA200
  - PIDÄ: Neutraali tila
- 🔁 Backtesting-toiminto
  - Testaa strategiaa 1-10 vuoden historialla
  - Vertaa strategiaa vs Buy & Hold -menetelmään
  - Kauppojen määrän seuranta
  - Tuottojen laskenta prosentteina
  - Ylisuorituksen mittaus
- 📈 Interaktiiviset kaaviot (Plotly)
  - Hintakaavio SMA-indikaattoreiden kanssa
  - RSI-kaavio yliostettu/ylimyyty-tasoilla
  - Kaupankäyntisignaalien visualisointi (osto/myynti-merkinnät)
  - Kauppahistorian taulukko
- 📥 CSV-vienti
  - Päivittäisen analyysin vienti
  - Backtesting-tulosten vienti
- 🇺🇸 USA:n osakkeiden tuki (esim. AAPL, MSFT, GOOGL)
- 🇫🇮 Suomen osakkeiden tuki (esim. NOKIA.HE, NESTE.HE)
- ℹ️ Tietoa-välilehti ohjeineen ja vastuuvapauslausekkeella
- 📝 Kattava dokumentaatio (README.md)
- 🔧 Asennusohjeet ja riippuvuuksien hallinta (requirements.txt)

### Teknologiat
- Python 3.8+
- Streamlit 1.28.0+
- yfinance 0.2.28+ (Yahoo Finance API)
- pandas 2.0.0+
- ta 0.11.0+ (Technical Analysis Library)
- plotly 5.17.0+
- SQLite3

### Huomioitavaa
- ⚠️ Työkalu on tarkoitettu vain koulutus- ja tutkimustarkoituksiin
- ⚠️ Ei takaa tuottoja tai voittoja
- ⚠️ Historiallinen suorituskyky ei takaa tulevia tuloksia
- ⚠️ Käyttö omalla vastuulla

## [Unreleased]

### Suunniteltu tuleviin versioihin
- Lisää teknisiä indikaattoreita (MACD, Bollinger Bands, ATR, Volume)
- Riskimittarit (Max Drawdown, Win Rate, Sharpe Ratio)
- Equity curve -kaavio (pääoman kehitys ajassa)
- Kaupankäyntikulujen huomiointi backtestingissä
- Useita strategioita (momentum, mean reversion, breakout)
- Strategioiden vertailu keskenään
- Parametrien optimointi
- Sähköposti/Telegram-ilmoitukset
- Fundamenttien analyysi (P/B, ROE, velkaisuus)
- Uutisten sentiment-analyysi
- Portfolio-optimointi
- Multi-user tuki

---

## Versioinnin selitys

- **MAJOR** (X.0.0): Yhteensopimattomia muutoksia
- **MINOR** (0.X.0): Uusia ominaisuuksia, taaksepäin yhteensopivia
- **PATCH** (0.0.X): Bugfixejä ja pieniä parannuksia

## Kategoriat

- **Lisätty** - Uudet ominaisuudet
- **Muutettu** - Muutokset olemassa oleviin ominaisuuksiin
- **Poistettu** - Poistetut ominaisuudet
- **Korjattu** - Bugfixit
- **Turvallisuus** - Tietoturvaan liittyvät korjaukset
