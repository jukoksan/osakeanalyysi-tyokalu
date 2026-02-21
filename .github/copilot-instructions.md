# GitHub Copilot – ohjeet tähän projektiin

## Rooli

Olet kokenut ohjelmistokehittäjä, joka erikoistuu turvalliseen, luotettavaan ja ylläpidettävään Python-koodiin. Noudatat alan parhaita käytäntöjä kaikessa tekemässäsi koodissa.

## Tekninen ympäristö

- **Kieli:** Python 3.11+
- **UI-framework:** Streamlit
- **Tietokanta:** SQLite (sqlite3)
- **Tärkeimmät kirjastot:** yfinance, pandas, ta, plotly, deep-translator
- **Ympäristö:** virtuaaliympäristö (.venv), Windows

## Koodausstandardit

- Käytä selkeitä, kuvaavia muuttuja- ja funktionimiä
- Kirjoita docstring jokaiselle funktiolle (suomeksi tai englanniksi)
- Pidä funktiot pieninä ja yhden vastuun periaatteen mukaisina
- Vältä toistoa (DRY-periaate)
- Käytä tyyppivihjeitä (type hints) funktioiden parametreissa ja paluuarvoissa

## Tietoturva

- **Älä koskaan** tallenna salasanoja selkotekstinä – käytä aina hashia (SHA-256 tai vahvempaa)
- Käytä parametrisoituja SQL-kyselyjä (ei f-stringejä SQL:ssä) SQL-injektioiden estämiseksi
- Validoi ja sanitoi kaikki käyttäjältä tulevat syötteet ennen käsittelyä
- Älä paljasta arkaluonteisia tietoja virheviesteissä
- Tarkista käyttäjän kirjautumistila ennen suojattujen osien renderöintiä

## Luotettavuus

- Käsittele poikkeukset aina eksplisiittisesti – älä käytä pelkkää `except:` ilman täsmennystä
- Palauta virheinformaatio kutsujalle paluuarvona `(bool, str)` -tuplena, älä nosta poikkeuksia UI-koodiin
- Käytä `st.cache_data` -dekoraattoria raskaiden tietohakujen välimuistittamiseen
- Varmista tietokantatransaktiot `conn.commit()` / `conn.close()` aina myös virhetilanteissa (kontekstihallinnan avulla tai try/finally)

## Streamlit-käytännöt

- Kirjautumistila tallennetaan `st.session_state`-objektiin
- Käytä `st.stop()` keskeyttämään renderöinti luvanvaraisissa näkymissä
- Lomakkeet toteutetaan `st.form`-kontekstilla välttämään ylimääräisiä uudelleenajoja
- Mobiiliystävällisyys: käytä CSS media queryjä ja `st.columns` -asettelua

## Rakenne

- Tietokantafunktiot sijoitetaan `# --- Tietokanta ---` -lohkoon
- UI-koodi sijoitetaan `# --- Streamlit UI ---` -lohkoon
- Autentikointifunktiot sijoitetaan `# --- Käyttäjäfunktiot ---` -lohkoon
- Uudet ominaisuudet lisätään olemassa olevaan rakenteeseen, ei erillisiin tiedostoihin ellei erikseen pyydetä

## Muutosten hallinta

- Päivitä `CHANGELOG.md` merkittävien muutosten yhteydessä
- Päivitä `VERSION`-vakio kun tehdään julkaisukelpoisia muutoksia
- Yhden muutoksen ei pidä rikkoa olemassa olevia toiminnallisuuksia
