import pandas as pd
import numpy as np
import fasttext
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Carica il modello fastText pre-addestrato
# Puoi scaricare il modello "cc.en.300.bin" da https://fasttext.cc/docs/en/crawl-vectors.html
model = fasttext.load_model("cc.en.300.bin")

# Funzione per calcolare l'embedding medio di ogni documento (frase) usando fastText
def embedding_feats_fasttext(list_of_lists, model):
    feats = []
    for tokens in list_of_lists:
        feat_for_this = np.zeros(300)  # Dimensione dell'embedding (fastText produce embedding di dimensione 300)
        count_for_this = 0
        for token in tokens:
            feat_for_this += model.get_word_vector(token)  # Recupera l'embedding per ciascuna parola
            count_for_this += 1
        if count_for_this > 0:
            feats.append(feat_for_this / count_for_this)  # Media degli embedding per il documento
        else:
            feats.append(np.zeros(300))  # Se nessuna parola è nel vocabolario, usa il vettore zero
    return feats

# Caricamento del dataset
dataset = pd.read_csv("dataset.csv")  # Cambia con il percorso del tuo dataset

# Preprocessing del testo: tokenizzazione (divisione in parole)
dataset['tokens'] = dataset['text'].apply(lambda x: x.lower().split() if isinstance(x, str) else [])

# Codifica delle etichette in numerico
label_encoder = LabelEncoder()

# Applica la codifica alle etichette
dataset['label'] = label_encoder.fit_transform(dataset['label'])

# Suddivisione del dataset in training (70%) e test (30%)
train_set, test_set = train_test_split(dataset, test_size=0.3, stratify=dataset['label'], random_state=42)

# Prepara i dati di training
X_train = embedding_feats_fasttext(train_set['tokens'], model)
y_train = train_set['label']

# Prepara i dati di test
X_test = embedding_feats_fasttext(test_set['tokens'], model)
y_test = test_set['label']

# One-hot encoding delle etichette
y_train = to_categorical(y_train)
y_test = to_categorical(y_test)

# Definisci il modello neurale
model_nn = Sequential()
model_nn.add(Dense(512, input_dim=300, activation='relu'))
model_nn.add(Dropout(0.5))  # Dropout per evitare overfitting
model_nn.add(Dense(256, activation='relu'))
model_nn.add(Dropout(0.5))
model_nn.add(Dense(y_train.shape[1], activation='softmax'))  # Softmax per classificazione multiclasse

# Compilazione del modello
model_nn.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])

# Addestramento del modello
history = model_nn.fit(np.array(X_train), np.array(y_train), epochs=10, batch_size=32, validation_split=0.2)

# Valutazione sul test set
y_pred_prob = model_nn.predict(np.array(X_test))
y_pred = np.argmax(y_pred_prob, axis=1)

# Calcolare la metrica di accuratezza
y_test_labels = np.argmax(y_test, axis=1)  # Ritorna le etichette originali per il confronto
print(f"Test Accuracy: {accuracy_score(y_test_labels, y_pred):.4f}")

# Stampa il classification report
# Stampa il classification report con i nomi delle etichette
print("\nClassification Report:\n", classification_report(y_test_labels, y_pred, target_names=label_encoder.classes_))

# Matrice di confusione
cm = confusion_matrix(y_test_labels, y_pred)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.title("Confusion Matrix")
plt.show()

# Funzione per inferenza su nuovi testi
def predict_new_texts(new_texts):
    new_tokens = [text.lower().split() for text in new_texts]
    X_new = embedding_feats_fasttext(new_tokens, model)
    y_pred_prob_new = model_nn.predict(np.array(X_new))
    y_pred_new = np.argmax(y_pred_prob_new, axis=1)
    
    # Restituisci le etichette originali invece dei numeri
    y_pred_new_labels = label_encoder.inverse_transform(y_pred_new)
    
    return y_pred_new_labels

# Esempio di inferenza
new_texts = [
    "This vacuum cleaner is incredibly powerful and lightweight.",
    "This vacuum cleaner is incredibly powerful and lightweight. It easily picks up dust and pet hair, and the detachable handheld part is perfect for cleaning sofas and curtains.",
    "An unforgettable novel full of emotional depth.",
    "I love this denim jacket! It fits perfectly.",
    "The new wireless earbuds offer crystal-clear sound."
]
predictions = predict_new_texts(new_texts)
print("Predictions for new texts:", predictions)

