# 📈 Osakeanalyysi-työkalu

[![Versio](https://img.shields.io/badge/versio-1.2.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)

Pythonilla ja Streamlit-käyttöliittymällä toteutettu osakeanalyysi-työkalu, joka auttaa päivittäisessä teknisessä analyysissä ja strategioiden testaamisessa.

📋 **[Katso muutosloki (CHANGELOG)](CHANGELOG.md)** kaikista versioista ja päivityksistä.

## 🎯 Ominaisuudet

### 📊 Päivittäinen analyysi
- Tekninen analyysi (RSI, SMA50, SMA200, MACD, Bollinger Bands)
- Tunnusluvut (P/E, markkina-arvo)
- Automaattiset osto/myynti/pidä-signaalit
- CSV-raporttien lataus

### 🔁 Backtesting
- Testaa strategioita historiallisella datalla (1-10 vuotta)
- Säädettävät kaupankäyntikulut (0–1 %)
- Vertaa strategiaa vs Buy & Hold
- Riskimittarit: Max Drawdown, Sharpe Ratio, Win Rate
- Näe kauppojen määrä ja tuotto
- Ylisuorituksen laskenta

### 📈 Interaktiiviset kaaviot
- Hintakaaviot SMA50/SMA200 + Bollinger Bands
- MACD-kaavio histogrammilla
- RSI-kaavio yliostettu/ylimyyty-tasoilla
- Equity Curve -kaavio (pääoman kehitys ajassa)
- Kaupankäyntisignaalit kaaviossa (osto/myynti-merkinnät)
- Kauppahistorian näyttö

### 🗂️ Osakkeiden hallinta
- Lisää/poista osakkeita web-käyttöliittymästä
- Osakkeet tallennetaan SQLite-tietokantaan
- Tukee sekä Suomen että USA:n osakkeita

## 🚀 Käyttöönotto

### 1. Asenna riippuvuudet

```bash
pip install -r requirements.txt
```

### 2. Käynnistä sovellus

```bash
streamlit run app.py
```

### 3. Avaa selain

Sovellus avautuu automaattisesti osoitteeseen: `http://localhost:8501`

## 💡 Käyttöohjeet

### Osakkeiden lisääminen
1. Kirjoita osaketunnus vasemman sivupalkin kenttään (esim. `AAPL`, `MSFT`, `NOKIA.HE`)
2. Paina "Lisää osake"
3. Osake tallentuu tietokantaan pysyvästi

### Päivittäinen analyysi
1. Siirry "Analyysi"-välilehdelle
2. Paina "Päivitä analyysi" -nappia päivittääksesi kaikki osakkeet
3. Tarkastele signaaleja:
   - 🟢 **OSTA**: RSI < 30 ja hinta > SMA50
   - 🔴 **MYY**: RSI > 70 tai hinta < SMA200
   - 🟡 **PIDÄ**: Ei osto- tai myyntisignaalia

### Backtesting
1. Siirry "Backtesting"-välilehdelle
2. Valitse ajanjakso (1-10 vuotta)
3. Aseta aloituspääoma
4. Paina "Aja backtesting"
5. Tarkastele tuloksia:
   - Vertaa strategian tuottoa Buy & Hold -menetelmään
   - Katso kauppojen määrä
   - Lataa tulokset CSV-muodossa

### Kaavioiden tarkastelu
1. Aja ensin backtesting
2. Scroll alas "Kaaviot"-osioon
3. Valitse osake pudotusvalikosta
4. Tarkastele:
   - Hintakaavio + SMA50 + SMA200
   - Kaupankäyntisignaalit (vihreät = osto, punaiset = myynti)
   - RSI-kaavio
   - Kauppahistoria

## 📊 Indikaattorit

### RSI (Relative Strength Index)
- Mittaa hinnanmuutoksen nopeutta ja suuruutta
- Asteikko 0-100
- **< 30**: Ylimyyty (mahdollinen ostotilaisuus)
- **> 70**: Yliostettu (mahdollinen myyntitilaisuus)

### SMA50 (50 päivän liukuva keskiarvo)
- Lyhyen aikavälin trendi
- Hinta SMA50 yläpuolella = nouseva trendi

### SMA200 (200 päivän liukuva keskiarvo)
- Pitkän aikavälin trendi
- Hinta SMA200 alapuolella = mahdollinen heikko trendi

## 🔧 Strategian logiikka

### Ostosignaali
1. RSI on alle 30 (osake ylimyyty)
2. JA hinta on SMA50 keskiarvon yläpuolella

### Myyntisignaali
1. RSI on yli 70 (osake yliostettu)
2. TAI hinta on SMA200 keskiarvon alapuolella

### Backtesting-säännöt
- Aloituspääoma sijoitetaan kokonaan ostavaan positioon
- Käteisenä, kun myyntisignaali
- Ei shorttausta
- Ei kaupankäyntikuluja (voidaan lisätä jatkokehityksessä)

## 📝 Esimerkkejä osakkeista

### USA:n osakkeet
- `AAPL` - Apple
- `MSFT` - Microsoft
- `GOOGL` - Google
- `AMZN` - Amazon
- `TSLA` - Tesla

### Suomen osakkeet
- `NOKIA.HE` - Nokia
- `NESTE.HE` - Neste
- `FORTUM.HE` - Fortum
- `UPM.HE` - UPM-Kymmene
- `SAMPO.HE` - Sampo

## 🛠️ Teknologiat

- **Python 3.8+**
- **Streamlit** - Web-käyttöliittymä
- **yfinance** - Osakekurssien haku (Yahoo Finance API)
- **pandas** - Datan käsittely ja analyysi
- **ta** - Tekniset indikaattorit
- **plotly** - Interaktiiviset kaaviot
- **SQLite** - Paikallinen tietokanta

## 🔮 Jatkokehitysideoita

### Lyhyen aikavälin
- [ ] Lisää indikaattoreita (MACD, Bollinger Bands, ATR)
- [ ] Kaupankäyntikulujen huomiointi backtestingissä
- [ ] Max drawdown, win rate, Sharpe ratio -mittarit
- [ ] Equity curve -kaavio (pääoman kehitys ajassa)

### Keskipitkän aikavälin
- [ ] Useita strategioita (momentum, mean reversion, breakout)
- [ ] Strategioiden vertailu keskenään
- [ ] Optimointi (parhaat parametrit backtestingillä)
- [ ] Sähköposti/Telegram-ilmoitukset signaaileista

### Pitkän aikavälin
- [ ] Fundamenttien analyysi (P/E, P/B, ROE, velkaisuus)
- [ ] Uutisten sentiment-analyysi
- [ ] Koneoppiminen ennusteiden parantamiseksi
- [ ] Portfolio-optimointi (usean osakkeen yhdistelmät)
- [ ] Multi-user tuki (kirjautuminen, omat listat)

## ⚠️ Vastuuvapauslauseke

**TÄRKEÄÄ**: Tämä työkalu on tarkoitettu vain koulutus- ja tutkimustarkoituksiin.

- ❌ Ei ole sijoitusneuvontaa
- ❌ Ei takaa tuottoja tai voittoja
- ❌ Historiallinen suorituskyky ei takaa tulevia tuloksia
- ✅ Käytä omalla vastuullasi
- ✅ Konsultoi aina rahoitusalan ammattilaista ennen sijoituspäätöksiä

Osakemarkkinoihin sijoittaminen sisältää aina riskin pääoman menettämisestä.

## 📄 Lisenssi

Tämä projekti on vapaa käyttää ja muokata henkilökohtaisiin tarkoituksiin.

## 🆘 Tuki ja kehitys

Jos kohtaat ongelmia:
1. Tarkista että kaikki riippuvuudet on asennettu: `pip install -r requirements.txt`
2. Varmista että Python-versio on 3.8 tai uudempi
3. Tarkista internettiyhteys (datan haku vaatii yhteyden)

## 📞 Yhteystiedot

Kysymykset ja palaute ovat tervetulleita!

---

**Onnea sijoittamiseen! 📈💰**
