import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Caricamento del dataset
dataset = pd.read_csv("dataset.csv")



# Suddivisione del dataset
train_set, test_set = train_test_split(dataset, test_size=0.3, stratify=dataset['label'], random_state=42)
val_set, test_set = train_test_split(test_set, test_size=0.5, stratify=test_set['label'], random_state=42)

print(f"Train size: {len(train_set)}, Validation size: {len(val_set)}, Test size: {len(test_set)}")

# Vettorizzazione
vectorizer = TfidfVectorizer(max_features=5000)
X_train = vectorizer.fit_transform(train_set["text"])
X_val = vectorizer.transform(val_set["text"])
X_test = vectorizer.transform(test_set["text"])

y_train, y_val, y_test = train_set["label"], val_set["label"], test_set["label"]

# Definizione dei modelli
models = {
    "Naive Bayes": MultinomialNB(),
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "SVM": SVC(kernel='linear')
}

# Inferenza su nuovi testi
new_texts = [
    "This vacuum cleaner is incredibly powerful and lightweight.",
    "This vacuum cleaner is incredibly powerful and lightweight. It easily picks up dust and pet hair, and the detachable handheld part is perfect for cleaning sofas and curtains.",
    "An unforgettable novel full of emotional depth.",
    "I love this denim jacket! It fits perfectly.",
    "The new wireless earbuds offer crystal-clear sound."
]
X_new = vectorizer.transform(new_texts)

# Addestramento e valutazione per ogni modello
for name, model in models.items():
    print(f"\n=== {name} ===")
    model.fit(X_train, y_train)

    # Validation
    y_val_pred = model.predict(X_val)
    print(f"Validation Accuracy: {accuracy_score(y_val, y_val_pred):.4f}")

    # Test
    y_test_pred = model.predict(X_test)
    print(f"Test Accuracy: {accuracy_score(y_test, y_test_pred):.4f}")
    print("\nClassification Report:\n", classification_report(y_test, y_test_pred))

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_test_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
                xticklabels=model.classes_ if hasattr(model, "classes_") else sorted(dataset["label"].unique()),
                yticklabels=model.classes_ if hasattr(model, "classes_") else sorted(dataset["label"].unique()))
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.title(f"{name} - Confusion Matrix")
    plt.show()

    # Inferenza
    predictions = model.predict(X_new)
    print("Inferenza su nuovi testi:")
    for text, label in zip(new_texts, predictions):
        print(f"Testo: {text}\n → Predicted Label: {label}\n")
