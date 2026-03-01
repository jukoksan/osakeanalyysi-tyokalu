# Changelog

Kaikki projektin merkittävät muutokset dokumentoidaan tähän tiedostoon.

Formaatti perustuu [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) -standardiin,
ja projekti noudattaa [Semantic Versioning](https://semver.org/spec/v2.0.0.html) -versiointia.

## [1.12.0] - 2026-03-01

### Korjattu
- 🐛 **Yahoo Finance rate limit -virhe** – `fetch_stock_data` ja `fetch_stock_history` saivat retry-logiikan exponential backoffilla (2s → 3s → 5s, max 3 yritystä). Estää "Too Many Requests" -virheen kaatamasta analyysiä.
- 🐛 **Analyysihaut vyöryttivät pyyntöjä kerralla** – analyysisilmukkaan lisätty 0,5 s viive jokaisen osakkeen väliin rate limit -virheiden välttämiseksi.
- 💬 **Selkeämpi rate limit -virheilmoitus** – käyttäjä näkee nyt "⏳ Yahoo Finance rajoittaa hakuja – odota hetki ja päivitä uudelleen" teknisen virheviestin sijaan.

### Muutettu
- 🏷️ **Tietoa-välilehden nimi** muutettu "📖 Käyttöohjeet" (FI) / "📖 User Guide" (EN) – kuvastaa paremmin välilehden sisältöä.

## [1.11.0] - 2026-03-01

### Korjattu
- 🐛 **Tietokannan häviäminen idle-tilasta herätessä** – `DB_NAME` muutettu suhteellisesta polusta absoluuttiseksi (`os.path.abspath(__file__)`) jotta `stocks.db` tallennetaan aina projektin juureen riippumatta Streamlitin käynnistyshakemistosta. Tämä esti käyttöliittymästä luotujen käyttäjien sekä lisättyjen osakkeiden häviämisen uudelleenkäynnistyksen yhteydessä.

### Lisätty
- 📋 **Käyttöohjeet salkkuun lisäämisestä** – Käyttöohjeet-välilehteen lisätty selkeä vaiheistettu ohje (FI & EN):
  - Osakkeiden lisääminen Suomen pörssi-, USA- ja EU ETF -välilehdiltä
  - Massatuonti `.txt`/`.csv`-tiedostosta sivupalkin kautta
  - Salkkujen luominen, vaihtaminen ja poistaminen

## [1.10.0] - 2026-02-22

### Lisätty
- 🧪 **Unit testit** – 65 pytest-testiä kattavat: salasanahashaus, käännösfunktio, DataFrame-sarakkeiden uudelleennimeäminen, osaketunnusten parsinta, käyttäjähallinta (CRUD), salkku & osakkeet, rahastot & NAV-kirjaukset, signaalien generointi (4 strategiaa), kaupankäynnin simulointi
- 🔁 **GitHub Actions CI-pipeline** – unit testit ajetaan automaattisesti jokaisessa pull requestissa ja push:ssa (`main`/`master`), Python 3.11 & 3.12 matriisilla
- 🌐 **Monikielisyys (Suomi / English)** – koko käyttöliittymä suomeksi ja englanniksi
  - `TRANSLATIONS`-sanakirja (~300 avainta) kattaa kaikki välilehdet, otsikot, napit, sarakkeiden nimet ja virheilmoitukset
  - `t(key, **kwargs)`-apufunktio – palauttaa oikean käännöksen aktiivisen käyttäjän kielen perusteella
  - Kielen valinta kirjautumissivulla (ennen kirjautumista) ja profiilisivupalkissa (tallennetaan kantaan)
  - `language`-sarake `users`-tauluun, automaattinen skeemapäivitys vanhoille tietokannoille
  - `update_user_language(user_id, lang)` –funktio kielen tallentamiseen
  - Kaikki välilehdet käännetty: Analyysi, Suomen pörssi, USA:n pörssi, EU ETF:t, Omat rahastot, Tietoa
  - Sarakkeiden nimet vaihdetaan dynaamisesti – suodattimet ja tyylitys toimivat molemmilla kielillä
  - Tietoa-välilehti: täysi sisältö kahdella kielellä (ehdollinen renderöinti)
- 📌 **NAV-lähdeohje** – Omat rahastot -välilehteen lisätty opas missä NAV-arvo löytyy (OP, Morningstar, Kauppalehti, Nordnet)

## [1.9.0] - 2026-02-22

### Lisätty
- 📒 **Omat rahastot -välilehti** – manuaalinen NAV-seuranta omille sijoitusrahastoille
  - `funds`- ja `fund_nav`-taulut SQLite-kantaan (automaattinen migraatio)
  - Rahastojen hallinta: lisää, poista (nimi, ISIN, muistiinpanot)
  - NAV-kirjaukset: syötä arvo päivämäärällä, päivitä tai poista kirjaus
  - Tunnusluvut: viimeisin NAV, ensimmäinen NAV, kokonaistuotto %, kirjausten määrä
  - Interaktiivinen kehityskäyrä (Plotly)
  - NAV-taulukko + CSV-lataus
  - Sopii OP, Nordea, Seligson jne. rahastoille, joita ei saa Yahoo Financesta

## [1.8.0] - 2026-02-22

### Lisätty
- 🇪🇺 **EU / Pohjoismaat ETF:t -välilehti** – UCITS-indeksirahastot omana välilehtenä
  - `EU_ETFS`-sanakirja: ~40 tunnettua UCITS ETF:ää Frankfurt (.DE), Lontoo (.L), Tukholma (.ST) ja Pariisi (.PA) -pörssistä
  - Kattaa: maailma (MSCI World, FTSE All-World), S&P 500, NASDAQ, Eurooppa, kehittyvät markkinat, pienet yhtiöt, sektori-ETF:t, korko, raaka-aineet ja osinko-ETF:t
  - `eu_cache`-taulu SQLite-kantaan synkatun datan säilyttämiseksi
  - `save_eu_cache` / `load_eu_cache` -funktiot välimuistitallennukseen
  - Sama toiminnallisuus kuin Suomen pörssi ja USA:n pörssi -välilehdissä
  - Hinta näytetään valuutan mukaan (Valuutta-sarake)

## [1.7.0] - 2026-02-22

### Lisätty
- 🇺🇸 **USA:n pörssi -välilehti** – NYSE/NASDAQ-osakkeet omana välilehtenä
  - `US_STOCKS`-sanakirja: ~110 tunnettua US-osaketta ja ETF:ää (teknologia, rahoitus, terveydenhuolto, energia jne.)
  - `us_cache`-taulu SQLite-kantaan: synkattu data säilyy uudelleenkäynnistyksen yli
  - `save_us_cache` / `load_us_cache` -funktiot välimuistitallennukseen
  - Sama toiminnallisuus kuin Suomen pörssi -välilehdessä: synkkaus, haku, signaalisuodatin, CSV-lataus, automaattinen päivitys
  - Hinnat ja markkina-arvot näytetään USD-muodossa (Hinta ($) -sarake)
  - Valitut osakkeet voi lisätä suoraan aktiiviseen salkkuun

## [1.6.1] - 2026-02-22

### Korjattu
- **`sqlite3.OperationalError: database is locked`** – lisätty `timeout=10` `init_db`-yhteyteen, jotta lyhyet lukitukset eivät kaada käynnistystä
- **`sqlite3.IntegrityError: UNIQUE constraint failed: users.username`** – migraatio tarkistaa nyt ensin onko `jukka` jo olemassa ennen kuin yrittää nimetä `admin`-tunnuksen uudelleen
- **Admin-salasana ei toiminut** – `init_db` varmistaa nyt aina että `jukka`-käyttäjällä on oikea hash; lisätty suora DB-korjaus olemassa olevalle tietokannalle
- **Otsikko jäi yläpalkin alle** – kirjautumis- ja päänäkymän `padding-top` kasvatettu `1rem/1.5rem` → `4rem`

## [1.6.0] - 2026-02-21

### Lisätty
- 🔒 **Roolipohjainen käyttäjähallinta** – Admin- ja User-roolit
  - `role`-sarake `users`-tauluun (oletusarvo `user`), automaattinen migraatio
  - Profiilissa näytetään roolimerkki: 🔒 Admin tai 👤 User
  - Admin-käyttäjällä profiilissa erillinen käyttäjänhallintaosio:
    - Lista kaikista käyttäjistä (tunnus, kutsumanimi, rooli)
    - Käyttäjän poisto (ei voi poistaa itseään)
    - Uuden käyttäjän luomislomake (tunnus, kutsumanimi, sähköposti, rooli, salasana)
  - Vain admin voi luoda uusia käyttäjiä – rekisteröitymislomake poistettu kirjautumisnäkymästä
- 👥 **Testikäyttäjä `testuser`** – luodaan automaattisesti (rooli: user, salasana: testpass)

### Muutettu
- `get_user_by_username` palauttaa nyt myös `role`-sarakkeen (indeksi 5)
- `create_user` ottaa nyt valinnaisen `role`-parametrin (oletus `"user"`)
- Kirjautuminen tallentaa `role` session_stateen
- Kirjaudu ulos tyhjentää myös `role`-avaimen session_statesta

## [1.5.0] - 2026-02-21

### Lisätty
- 🔐 **Käyttäjähallinta ja kirjautuminen** – sovellus on nyt kirjautumisen takana
  - Kirjautumisnäkymä käyttäjätunnuksella ja salasanalla
  - Rekisteröityminen uudelle tilille kirjautumisnäkymästä
  - Salasanat tallennetaan SHA-256-tiivisteenä (ei selkotekstinä)
  - `users`-taulu SQLiteen, oletuskäyttäjä luodaan automaattisesti ensimmäisellä käynnistyksellä
- 👤 **Profiilisivu sivupalkissa** – kirjautuneen käyttäjän hallinta
  - Kutsumanimn ja sähköpostin muuttaminen
  - Salasanan vaihtaminen (vanhan salasanan vahvistus vaaditaan)
  - Kirjaudu ulos -painike
- 📊 **Välilehtijärjestys muutettu** – Analyysi → Suomen pörssi → Backtesting → Tietoa
- 🎯 **Backtesting-osakevalinta** – voi ajaa yksittäiselle osakkeelle tai kaikille salkun osakkeille
- 📝 **GitHub Copilot -ohjeet** – lisätty `.github/copilot-instructions.md` AI-avusteista kehitystä varten

### Muutettu
- ❌ **Osakkeen lisäyslomake poistettu analyysistä** – osakkeet lisätään vain Suomen pörssi -välilehdeltä
- 📱 **Otsikko pienennetty mobiilissa** – CSS media query pienentää h1-fonttia alle 768 px leveyksillä
- 📋 **"Päivittäinen analyysi" -otsikko pienennetty** – `st.header` → `st.subheader` tilansäästön vuoksi
- ⛔ **Automaattinen päivitys poistettu analyysi-välilehdeltä** – toggle, välivalikko ja refresh-silmukka poistettu
- 🇨🇳 **Tyhjän salkun ohjausviestit päivitetty** – ohjataan nyt Suomen pörssi -välilehteen

## [1.4.0] - 2026-02-19

### Lisätty
- 💾 **Suomen pörssin data tallennetaan SQLiteen** – synkattu lista pysyy muistissa sivun refreshin yli
  - Ensimmäisen synkrauksen jälkeen taulukko latautuu automaattisesti DB:stä joka kerta
  - Uusi synkraus vain kun käyttäjä haluaa tuoreet tiedot
  - Aikaleima näytetään muodossa **pp.kk.vvvv HH:MM:SS**
- 🗂️ **Monisalkku-tuki (max 5 salkkua)** – useita salkkuja eri sisällöillä
  - Luo, nimeä uudelleen ja poista salkkuja sidebarista
  - Aktiivinen salkku valitaan sidebarista – analyysi, lisäys ja poisto kohdistuvat aina siihen
  - Vanhat osakkeet siirtyvät automaattisesti "Salkku 1":een (migraatio)
  - Suomen pörssi -listasta lisäys menee aktiiviseen salkkuun

### Korjattu
- 🔍 **Signaalisuodatin ei nollautunut synkrauksen jälkeen** – korjattu käyttämällä `st.rerun()` ja poistamalla widget-avaimet session_statesta
- ⏱️ **Synkrauksen aikaleima näkyy heti** sivun avautuessa ilman erillistä synkrauspainiketta
- 🗑️ **"Lisää kaikki salkkuun" -nappi poistettu** – aiheutti Too Many Requests -virheitä analyysi-välilehdellä

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
