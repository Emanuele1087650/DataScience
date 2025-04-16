import pandas as pd
import numpy as np
import gensim.downloader as api
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Carica il modello Word2Vec pre-addestrato
w2v_model = api.load("word2vec-google-news-300")

# La dimensione dell'embedding
DIMENSION = 300  # La dimensione degli embedding in Word2Vec
zero_vector = np.zeros(DIMENSION)  # Vettore zero da utilizzare in caso di assenza di parole nel vocabolario

# Funzione per calcolare l'embedding medio di ogni documento (frase)
def embedding_feats(list_of_lists, w2v_model):
    feats = []
    for tokens in list_of_lists:
        feat_for_this = np.zeros(DIMENSION)
        count_for_this = 0
        for token in tokens:
            if token in w2v_model:
                feat_for_this += w2v_model[token]
                count_for_this += 1
        if count_for_this > 0:
            feats.append(feat_for_this / count_for_this)  # Media degli embedding
        else:
            feats.append(zero_vector)  # Se nessuna parola è nel vocabolario, usa il vettore zero
    return feats

# Caricamento del dataset
dataset = pd.read_csv("dataset.csv")  # Cambia con il percorso del tuo dataset

# Preprocessing del testo: tokenizzazione (divisione in parole)
dataset['tokens'] = dataset['text'].apply(lambda x: x.lower().split() if isinstance(x, str) else [])

# Suddivisione del dataset in training (70%) e test (30%)
train_set, test_set = train_test_split(dataset, test_size=0.3, stratify=dataset['label'], random_state=42)

# Prepara i dati di training
X_train = embedding_feats(train_set['tokens'], w2v_model)
y_train = train_set['label']

# Prepara i dati di test
X_test = embedding_feats(test_set['tokens'], w2v_model)
y_test = test_set['label']

# Preprocessing delle etichette: converti le etichette da stringhe a numeri
label_encoder = LabelEncoder()

# Applica l'encoder alle etichette di training e test
y_train = label_encoder.fit_transform(y_train)
y_test = label_encoder.transform(y_test)

# One-hot encoding delle etichette
y_train = to_categorical(y_train)
y_test = to_categorical(y_test)

# Definisci il modello neurale
model = Sequential()
model.add(Dense(512, input_dim=DIMENSION, activation='relu'))
model.add(Dropout(0.5))  # Dropout per evitare overfitting
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(y_train.shape[1], activation='softmax'))  # Softmax per classificazione multiclasse

# Compilazione del modello
model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

# Addestramento del modello
history = model.fit(np.array(X_train), np.array(y_train), epochs=10, batch_size=32, validation_split=0.2)

# Valutazione sul test set
y_pred_prob = model.predict(np.array(X_test))
y_pred = np.argmax(y_pred_prob, axis=1)

# Calcolare la metrica di accuratezza
y_test_labels = np.argmax(y_test, axis=1)  # Ritorna le etichette originali per il confronto
print(f"Test Accuracy: {accuracy_score(y_test_labels, y_pred):.4f}")

# Stampa il classification report
print("\nClassification Report:\n", classification_report(y_test_labels, y_pred))

# Matrice di confusione
cm = confusion_matrix(y_test_labels, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=train_set['label'].unique(), yticklabels=train_set['label'].unique())
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.show()

# Funzione per inferire la classe di nuovi testi
def predict_new_texts(new_texts):
    # Tokenizza i nuovi testi
    new_tokens = [text.lower().split() for text in new_texts]
    
    # Calcola gli embeddings per i nuovi testi
    X_new = embedding_feats(new_tokens, w2v_model)
    
    # Predici le classi
    y_new_pred_prob = model.predict(np.array(X_new))
    y_new_pred = np.argmax(y_new_pred_prob, axis=1)
    
    # Decodifica le etichette predette
    y_new_pred_labels = label_encoder.inverse_transform(y_new_pred)
    
    return y_new_pred_labels

# Esempio di inferenza
new_texts = [
    "This vacuum cleaner is incredibly powerful and lightweight.",
    "This vacuum cleaner is incredibly powerful and lightweight. It easily picks up dust and pet hair, and the detachable handheld part is perfect for cleaning sofas and curtains.",
    "An unforgettable novel full of emotional depth.",
    "I love this denim jacket! It fits perfectly.",
    "The new wireless earbuds offer crystal-clear sound."
]

# Previsione per i nuovi testi
predictions = predict_new_texts(new_texts)
print("\nPredictions for new texts:")
for text, label in zip(new_texts, predictions):
    print(f"Text: {text}\nPredicted Label: {label}\n")
