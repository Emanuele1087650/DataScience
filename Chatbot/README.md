# Chatbot Setup e Utilizzo

Questo documento guida l'installazione, la configurazione e l'utilizzo del chatbot basato su Rasa con integrazione Telegram.

---

## Prerequisiti

- Miniconda o Anaconda (gestore di ambienti Conda)
- Git
- ngrok
- Account su RapidAPI
- Bot Telegram creato con @BotFather

---

## 1. Creazione dell'ambiente Conda

Esegui i seguenti comandi per preparare l'ambiente virtuale Conda:

```bash
conda create --name chatbot python=3.9
conda activate chatbot
```

---

## 2. Clonazione del repository

Esegui il comando seguente per clonare la repository e posizionarti nella cartella del progetto:

```bash
git clone https://github.com/Emanuele1087650/DataScience
cd Chatbot
```

---

## 3. Installazione delle dipendenze

Installa tutte le librerie necessarie con il seguente comando:

```bash
pip install -r requirements.txt
```

---

## 4. Configurazione delle chiavi API

1. Registrati su [RapidAPI](https://rapidapi.com) e ottieni la tua chiave `RAPID_API_KEY`.
2. Nella root del progetto, crea un file `.env` con il seguente contenuto:

```dotenv
RAPID_API_KEY=<YOUR_RAPID_API_KEY>
```

---

## 5. Configurazione Telegram

1. Su Telegram, avvia @BotFather e crea un nuovo bot. Prendi nota di **TOKEN** e **BOT_USERNAME**.
2. Installa e avvia ngrok (porta 5005):

```bash
ngrok http 5005
```

Copia l'URL HTTPS generato (es. `https://abcd1234.ngrok.io`).

3. Modifica `credentials.yml` aggiungendo:

```yaml
telegram:
  access_token: "<YOUR_TELEGRAM_TOKEN>"
  verify: "<YOUR_BOT_USERNAME>"
  webhook_url: "<NGROK_URL>/webhooks/telegram/webhook"
```

Sostituisci i placeholder con i tuoi valori.

---

## 6. Addestramento del modello

Avvia il processo di training del modello eseguendo:

```bash
rasa train
```

---

## 7. Avvio dei servizi

Per far partire il server Rasa, utilizza il seguente comando:

```bash
rasa run --enable-api
```

In un altro terminale esegui:

```bash
rasa run actions
```

---

## 8. Test e interazione via Telegram

1. Su Telegram, cerca il tuo bot (username impostato con BotFather).
2. Invia `/start` o un messaggio qualsiasi per iniziare.
3. Esempi di comandi:
   - `Ciao` → saluto
   - `Vorrei cercare un hotel` → ricerca hotel
   - `Puoi consigliarmi un volo economico?` → ricerca voli
   - `Dammi l'itinerario più economico che trovi` → crea itinerario





