# Bank App - Panga Rakendus

See rakendus on loodud panga süsteemi jaoks, mis suudab suhelda teiste pankadega (sh barBank) tehingute töötlemiseks pankade vahel.

## Funktsionaalsus

- Kasutajate registreerimine ja autentimine
- Pangakontode loomine ja haldamine
- Sisemised ülekanded sama panga kontode vahel
- Pankadevahelised ülekanded (B2B) vastavalt spetsifikatsioonile
- Tehingute ajaloo vaatamine
- Mitme valuuta tugi (EUR, USD, GBP)

## Tehnilised omadused

- JWT autentimine pankadevaheliste tehingute jaoks
- RSA-256 võtmepaari kasutamine tehingute allkirjastamiseks
- JWKS endpoint avaliku võtme jagamiseks
- Keskpangaga suhtlemine pankade valideerimiseks
- Valuuta konverteerimine erinevate valuutade vahel

## Paigaldamine

1. Klooni repositoorium
2. Installi sõltuvused: `pip install -r requirements.txt`
3. Seadista keskkonnamuutujad `.env` failis:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///bank.db
   BANK_PREFIX=BNK
   CENTRAL_BANK_URL=http://central-bank-url
   CENTRAL_BANK_API_KEY=your_api_key
   BANK_NAME=Your Bank Name
   TRANSACTION_URL=http://your-domain/transactions/b2b
   JWKS_URL=http://your-domain/transactions/jwks
   OWNER_INFO=Bank Owner Information
   TEST_MODE=False
   ```
4. Initsialiseeri andmebaas: `flask init-db`
5. Genereeri RSA võtmepaar: `flask generate-keys`
6. Registreeri pank keskpangas: `flask register-bank`
7. Käivita rakendus: `flask run`

## API Endpointid

### Pankadevahelised tehingud

`POST /transactions/b2b`

Päring:
```json
{
  "jwt": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ.eyJhY2NvdW50RnJvbSI6Ijg0M2VhZjcwNzYxODRiZGI4Yjc0ZmFlYTE3ZDFjM2MzMjg3IiwiYWNjb3VudFRvIjoiQUJDMTIzNDU2IiwiY3VycmVuY3kiOiJFVVIiLCJhbW91bnQiOjEwMDAwLCJleHBsYW5hdGlvbiI6IlBheW1lbnQgZm9yIHNlcnZpY2VzIiwic2VuZGVyTmFtZSI6IkpvaG4gRG9lIn0.signature"
}
```

Vastus (200):
```json
{
  "receiverName": "Jane Smith"
}
```

### JWKS Endpoint

`GET /transactions/jwks`

Vastus: JSON Web Key Set (JWKS), mis sisaldab panga avalikku võtit.

## Testimine

Rakendus toetab TEST_MODE režiimi, mis võimaldab testida pankadevahelisi tehinguid ilma tegelike võrguühenduste loomiseta. Selleks seadista `.env` failis `TEST_MODE=True`.

## Turvanõuded

- Kõik pangad peavad autentima JWT abil, mis on allkirjastatud RSA-256 algoritmiga
- Iga pank peab genereerima ja turvaliselt säilitama RSA võtmepaari
- Avalik võti peab olema kättesaadav JWKS endpoindi kaudu
- Privaatset võtit tuleb kasutada kõigi väljuvate tehingute allkirjastamiseks