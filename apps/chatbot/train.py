from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import RandomOverSampler
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import pandas as pd
import string
import json

import os

# Load intents from JSON file
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, 'intents.json')) as file:
    data = json.load(file)


# Extract patterns and intents from JSON
patterns = []
tags = []
for intent in data['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern.lower())  # Normalize text to lowercase
        tags.append(intent['tag'])

# NLP Preprocessing
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token not in stop_words and token not in string.punctuation]
    return ' '.join(tokens)

# Create DataFrame for training data
df = pd.DataFrame({'pattern': patterns, 'tag': tags})

# Preprocess text
df['pattern'] = df['pattern'].apply(preprocess_text)

# Create training data
X_train, X_test, y_train, y_test = train_test_split(df['pattern'], df['tag'], test_size=0.2, random_state=42)

# Oversample the training data to address class imbalance
oversampler = RandomOverSampler(random_state=42)
X_train_resampled, y_train_resampled = oversampler.fit_resample(X_train.to_frame(), y_train)

# Convert X_train_resampled back to Series and y_train_resampled to Series
X_train_resampled = X_train_resampled.squeeze()

# Define the parameter grid
param_grid = {
    'multinomialnb__alpha': [0.1, 0.5, 1.0],
    'tfidfvectorizer__ngram_range': [(1, 1), (1, 2), (2, 2)]
}

# Create a pipeline
pipeline = make_pipeline(
    TfidfVectorizer(),
    MultinomialNB()
)

# Create a StratifiedKFold object
stratified_kfold = StratifiedKFold(n_splits=5)

# Create a GridSearchCV object
grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=stratified_kfold,
    scoring='accuracy'
)

# Fit the GridSearchCV object
grid_search.fit(X_train_resampled, y_train_resampled)

# Fit the GridSearchCV object
print("Fitting GridSearchCV...")
grid_search.fit(X_train_resampled, y_train_resampled)
print("GridSearchCV fitting complete.")

# Print the best parameters and the best score
print("Best Parameters:", grid_search.best_params_)
print("Best Score:", grid_search.best_score_)

from joblib import dump

# Save the best model to a file
dump(grid_search.best_estimator_, 'chatmodel.joblib')