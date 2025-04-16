import pandas as pd
import re
from collections import Counter

def clean_text(text):
    """
    Pulisce il testo eliminando simboli speciali, emoticon e caratteri non utili per l'analisi.
    :param text: La stringa di testo da pulire
    :return: La stringa pulita
    """
    # Rimuove emoticon e simboli particolari usando regex
    text = re.sub(r'[\U00010000-\U0010FFFF]', '', text)  # Rimuove emoticon e caratteri Unicode

    # Rimuove caratteri non alfanumerici (eccetto spazi)
    text = re.sub(r'[^\w\s]', '', text)

    # Rimuove numeri
    text = re.sub(r'\d+', '', text)

    # Rimuove parole chiave specifiche (aggiungere le parole che si vogliono eliminare)
    keywords_to_remove = ['parola1', 'parola2', 'parola3']  # Aggiungere le parole che desideri rimuovere
    for keyword in keywords_to_remove:
        text = re.sub(fr'\b{keyword}\b', '', text, flags=re.IGNORECASE)

    # Rimuove spazi multipli
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def preprocess_and_map_sentiment(dataset_path, output_path):
    """
    Preprocessa il dataset, mappa i sentimenti e salva il risultato in un nuovo file.
    :param dataset_path: Percorso del file CSV contenente il dataset
    :param output_path: Percorso dove salvare il dataset preprocessato
    """
    # Carica il dataset
    df = pd.read_csv(dataset_path)

    # Dizionario per mappare i sentimenti a valori binari
    word_to_binary = {
        'Positive': 1, 'Joy': 1, 'Happiness': 1, 'Love': 1, 'Amusement': 1, 'Enjoyment': 1,
        'Admiration': 1, 'Affection': 1, 'Awe': 1, 'Surprise': 1, 'Acceptance': 1,
        'Adoration': 1, 'Anticipation': 1, 'Calmness': 1, 'Excitement': 1, 'Kind': 1,
        'Pride': 1, 'Elation': 1, 'Euphoria': 1, 'Contentment': 1, 'Serenity': 1,
        'Gratitude': 1, 'Hope': 1, 'Empowerment': 1, 'Compassion': 1, 'Tenderness': 1,
        'Fulfillment': 1, 'Reverence': 1, 'Curiosity': 1, 'Determination': 1, 'Zest': 1,
        'Hopeful': 1, 'Grateful': 1, 'Inspired': 1, 'Playful': 1, 'Happy': 1,
        'Negative': 0, 'Anger': 0, 'Fear': 0, 'Sadness': 0, 'Disgust': 0, 'Boredom': 0,
        'Despair': 0, 'Grief': 0, 'Loneliness': 0, 'Jealousy': 0, 'Resentment': 0,
        'Frustration': 0, 'Anxiety': 0, 'Intimidation': 0, 'Helplessness': 0,
        'Envy': 0, 'Regret': 0, 'Indifference': 0, 'Numbness': 0, 'Melancholy': 0,
        'Apprehensive': 0, 'Overwhelmed': 0, 'Bitterness': 0, 'Heartbreak': 0,
        'Betrayal': 0, 'Suffering': 0, 'Isolation': 0, 'Disappointment': 0,
        'LostLove': 0, 'Darkness': 0, 'Desperation': 0, 'Ruins': 0,
        'Neutral': 0.5, 'Disappointed': 0, 'Bitter': 0, 'Confusion': 0,
        'Shame': 0, 'Arousal': 1, 'Enthusiasm': 1, 'Nostalgia': 1,
        'Ambivalence': 0, 'Proud': 1, 'Empathetic': 1, 'Compassionate': 1,
        'Free-Spirited': 1, 'Confident': 1, 'Yearning': 0, 'Fearful': 0,
        'Jealous': 0, 'Devastated': 0, 'Frustrated': 0, 'Envious': 0,
        'Dismissive': 0, 'Thrill': 1, 'Bittersweet': 1, 'Overjoyed': 1,
        'Inspiration': 1, 'Motivation': 1, 'Contemplation': 0.5,
        'Joyfulreunion': 1, 'Satisfaction': 1, 'Blessed': 1, 'Reflection': 0.5,
        'Appreciation': 1, 'Confidence': 1, 'Accomplishment': 1,
        'Wonderment': 1, 'Optimism': 1, 'Enchantment': 1, 'Intrigue': 1,
        'Playfuljoy': 1, 'Mindfulness': 1, 'Dreamchaser': 1, 'Elegance': 1,
        'Whimsy': 1, 'Pensive': 0.5, 'Harmony': 1, 'Creativity': 1,
        'Radiance': 1, 'Wonder': 1, 'Rejuvenation': 1, 'Coziness': 1,
        'Adventure': 1, 'Melodic': 1, 'Festivejoy': 1, 'Innerjourney': 1,
        'Freedom': 1, 'Dazzle': 1, 'Adrenaline': 1, 'Artisticburst': 1,
        'Culinaryodyssey': 1, 'Resilience': 1, 'Immersion': 1, 'Spark': 1,
        'Marvel': 1, 'Emotionalstorm': 0, 'Lostlove': 0, 'Exhaustion': 0,
        'Sorrow': 0, 'Desolation': 0, 'Loss': 0, 'Heartache': 0,
        'Solitude': 0, 'Positivity': 1, 'Kindness': 1, 'Friendship': 1,
        'Success': 1, 'Exploration': 1, 'Amazement': 1, 'Romance': 1,
        'Captivation': 1, 'Tranquility': 1, 'Grandeur': 1, 'Emotion': 0.5,
        'Energy': 1, 'Celebration': 1, 'Charm': 1, 'Ecstasy': 1,
        'Colorful': 1, 'Hypnotic': 1, 'Connection': 1, 'Iconic': 1,
        'Journey': 1, 'Engagement': 1, 'Touched': 1, 'Suspense': 0.5,
        'Triumph': 1, 'Heartwarming': 1, 'Obstacle': 0, 'Sympathy': 0.5,
        'Pressure': 0, 'Renewed Effort': 1, 'Miscalculation': 0,
        'Challenge': 1, 'Solace': 1, 'Breakthrough': 1, 'Joy In Baking': 1,
        'Envisioning History': 1, 'Imagination': 1, 'Vibrancy': 1,
        'Mesmerizing': 1, 'Culinary Adventure': 1, 'Winter Magic': 1,
        'Thrilling Journey': 1, "Nature'S Beauty": 1, 'Celestial Wonder': 1,
        'Creative Inspiration': 1, 'Runway Creativity': 1, "Ocean'S Freedom": 1,
        'Whispers Of The Past': 1, 'Relief': 1, 'Embarrassed': 0,
        'Mischievous': 0.5, 'Sad': 0, 'Hate': 0, 'Bad': 0
    }

    # Pulizia del testo e mappatura dei sentimenti a valori binari
    df['Text'] = df['Text'].apply(clean_text)
    df['Sentiment_cleaned'] = df['Sentiment'].str.strip().str.title()
    df['Sentiment Binary'] = df['Sentiment_cleaned'].map(word_to_binary).fillna(-1).astype(int)

    # Trova tutte le parole non mappate
    unmapped_words = df[df['Sentiment Binary'] == -1]['Sentiment_cleaned'].unique()
    print("Parole non mappate (valore -1):")
    print(unmapped_words)

    # Mantiene solo il valore numerico nella colonna
    df.drop(columns=['Sentiment_cleaned'], inplace=True)

    # Salva il dataset in un file CSV
    df.to_csv(output_path, index=False)
    print(f"Dataset preprocessato e salvato in: {output_path}")

    # Calcola le frequenze dei valori binari
    binary_counts = df['Sentiment Binary'].value_counts()
    print("Frequenze nella colonna 'Sentiment Binary':")
    for value in [1, 0, -1]:
        print(f"Valore {value}: {binary_counts.get(value, 0)}")

# Esegui la funzione
input_csv = 'sentiment.csv'
output_csv = 'binary_cleaned.csv'
preprocess_and_map_sentiment(input_csv, output_csv)
