import pandas as pd
import nltk
from nltk.corpus import stopwords
import spacy


# Assicurati che NLTK abbia i pacchetti necessari
nltk.download('punkt')
nltk.download('stopwords')

# Funzione di preprocessing
def preprocess_data(file_path):
    # Carica il dataset
    df = pd.read_csv(file_path)
    
    # Rimuove eventuali spazi nei nomi delle colonne
    df.columns = df.columns.str.strip()

    # Rimuove i valori NaN e li sostituisce con stringa vuota
    df = df.dropna(subset=["text"])
    
    # Rimozione delle stopwords (parole comuni come 'and', 'the', 'of' in inglese)
    stop_words = set(stopwords.words('english'))  # Imposta la lingua su inglese
    
    # Assicurati che la colonna 'text' contenga solo stringhe
    df['text'] = df['text'].apply(lambda x: str(x) if isinstance(x, float) else x)
    
    # Tokenizzazione e rimozione delle stopwords
    df['text'] = df['text'].apply(lambda x: ' '.join([word for word in x.split() if word not in stop_words]))

    # Verifica e applica la lemmatizzazione con spaCy
    nlp = spacy.load('en_core_web_sm')  # Usa il modello inglese di spaCy
    df['text'] = df['text'].apply(lambda x: ' '.join([token.lemma_ for token in nlp(x)]))

    # Conversione del testo in minuscolo
    df['text'] = df['text'].str.lower()

    # Rimozione di caratteri speciali e punteggiatura
    df['text'] = df['text'].str.replace(r'[^a-zA-Z\s]', '', regex=True)  # Rimuove tutto tranne lettere e spazi

    # Rimozione di URL, mentions e hashtags (se presente nel testo)
    df['text'] = df['text'].str.replace(r'http\S+|www\S+', '', regex=True)  # Rimuove gli URL
    df['text'] = df['text'].str.replace(r'@\S+', '', regex=True)  # Rimuove mentions (@username)
    df['text'] = df['text'].str.replace(r'#\S+', '', regex=True)  # Rimuove hashtags (#hashtag)

    # Limita la lunghezza del testo a un numero massimo di parole
    max_length = 100  # Limite massimo di parole
    df['text'] = df['text'].apply(lambda x: ' '.join(x.split()[:max_length]))

    # Salva il dataset preprocessato in un nuovo file CSV
    df.to_csv("dataset.csv", index=False)

    return df

# Esempio di utilizzo
file_path = "ecommerceDataset.csv"  # Sostituisci con il percorso del tuo file
preprocessed_df = preprocess_data(file_path)

# Mostra i primi 5 record del nuovo dataset
print(preprocessed_df.head())
