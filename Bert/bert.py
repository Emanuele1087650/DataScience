import numpy as np
import pandas as pd
import random
import torch
from transformers import BertTokenizer, BertForSequenceClassification, AdamW, get_linear_schedule_with_warmup
from torch.utils.data import TensorDataset, DataLoader, random_split
from tabulate import tabulate
import time
import datetime
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Step 1: Data Loading and Tokenization
df = pd.read_csv('binary_cleaned.csv')
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

# Initialize BERT tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)

def prepare_data(df):
    sentences = df['Text']
    labels = df['Binary'].tolist()
    
    input_ids = []
    attention_masks = []

    for sent in sentences:
        encoded_dict = tokenizer.encode_plus(
            sent, 
            add_special_tokens=True,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        input_ids.append(encoded_dict['input_ids'])
        attention_masks.append(encoded_dict['attention_mask'])

    input_ids = torch.cat(input_ids, dim=0)
    attention_masks = torch.cat(attention_masks, dim=0)
    labels = torch.tensor(labels)

    return TensorDataset(input_ids, attention_masks, labels)

train_dataset = prepare_data(train_df)
test_dataset = prepare_data(test_df)

# Save the datasets
torch.save(train_dataset, 'training_dataset.pt')
torch.save(test_dataset, 'test_dataset.pt')

# Display a sample sentence's encoding
def print_rand_sentence_encoding(dataset):
    index = random.randint(0, len(dataset) - 1)
    input_ids, attention_masks, labels = dataset[index]
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    token_ids = input_ids.tolist()
    attention = attention_masks.tolist()

    table = np.array([tokens, token_ids, attention]).T
    print("Example sentence and its encoding:")
    print(tabulate(table, headers=['Tokens', 'Token IDs', 'Attention Mask'], tablefmt='fancy_grid'))

print_rand_sentence_encoding(train_dataset)

# Step 2: Model Training
# Load pre-trained BERT model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

# Load the training dataset
dataset = torch.load('training_dataset.pt')

# Split dataset into training and validation
train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

batch_size = 16
train_dataloader = DataLoader(train_dataset, sampler=torch.utils.data.RandomSampler(train_dataset), batch_size=batch_size)
validation_dataloader = DataLoader(val_dataset, sampler=torch.utils.data.SequentialSampler(val_dataset), batch_size=batch_size)

# Optimizer and scheduler
optimizer = AdamW(model.parameters(), lr=2e-5, eps=1e-8)
total_steps = len(train_dataloader) * 4  # Number of epochs
scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)

# Device setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# Training function
def format_time(elapsed):
    elapsed_rounded = int(round((elapsed)))
    return str(datetime.timedelta(seconds=elapsed_rounded))

epochs = 4
best_eval_loss = float('inf')
training_stats = []

for epoch_i in range(epochs):
    print(f'\nEpoch {epoch_i + 1}/{epochs}')
    print('Training...')
    total_train_loss = 0
    model.train()
    t0 = time.time()

    for step, batch in enumerate(train_dataloader):
        b_input_ids = batch[0].to(device)
        b_input_mask = batch[1].to(device)
        b_labels = batch[2].to(device)

        model.zero_grad()
        outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask, labels=b_labels)
        loss = outputs.loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        total_train_loss += loss.item()

    avg_train_loss = total_train_loss / len(train_dataloader)
    training_time = format_time(time.time() - t0)

    # Validation
    print('\nValidation')
    model.eval()
    total_eval_loss = 0
    total_eval_accuracy = 0
    t0 = time.time()

    for batch in validation_dataloader:
        b_input_ids = batch[0].to(device)
        b_input_mask = batch[1].to(device)
        b_labels = batch[2].to(device)

        with torch.no_grad():
            outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask, labels=b_labels)

        loss = outputs.loss
        logits = outputs.logits

        total_eval_loss += loss.item()
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()

        total_eval_accuracy += np.sum(np.argmax(logits, axis=1).flatten() == label_ids.flatten()) / len(label_ids)

    avg_val_accuracy = total_eval_accuracy / len(validation_dataloader)
    avg_val_loss = total_eval_loss / len(validation_dataloader)
    validation_time = format_time(time.time() - t0)

    print(f"Training Loss: {avg_train_loss:.2f}")
    print(f"Validation Loss: {avg_val_loss:.2f}, Accuracy: {avg_val_accuracy:.2f}")
    print(f"Training took: {training_time}, Validation took: {validation_time}")

    if avg_val_loss < best_eval_loss:
        torch.save(model.state_dict(), 'best_model_state.bin')
        best_eval_loss = avg_val_loss

    training_stats.append({
        'epoch': epoch_i + 1,
        'Training Loss': avg_train_loss,
        'Valid. Loss': avg_val_loss,
        'Valid. Accur.': avg_val_accuracy,
        'Training Time': training_time,
        'Validation Time': validation_time
    })

print("\nTraining complete!")

# Step 3: Testing and Evaluation
model.load_state_dict(torch.load('best_model_state.bin'))
model.eval()
model.to(device)

test_dataset = torch.load('test_dataset.pt')
test_dataloader = DataLoader(test_dataset, sampler=torch.utils.data.SequentialSampler(test_dataset), batch_size=16)

true_labels = []
predictions = []

for batch in test_dataloader:
    b_input_ids, b_input_mask, b_labels = batch
    b_input_ids = b_input_ids.to(model.device)
    b_input_mask = b_input_mask.to(model.device)
    b_labels = b_labels.to(model.device)

    with torch.no_grad():
        outputs = model(b_input_ids, token_type_ids=None, attention_mask=b_input_mask)

    logits = outputs.logits.detach().cpu().numpy()
    label_ids = b_labels.to('cpu').numpy()

    predictions.extend(np.argmax(logits, axis=1))
    true_labels.extend(label_ids)

accuracy = accuracy_score(true_labels, predictions)
conf_matrix = confusion_matrix(true_labels, predictions)
class_report = classification_report(true_labels, predictions)

print("Accuracy:", accuracy)
print("Confusion Matrix:\n", conf_matrix)
print("Classification Report:\n", class_report)
