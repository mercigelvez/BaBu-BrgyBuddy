from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from imblearn.over_sampling import RandomOverSampler
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import pandas as pd
import string
import json
import os
from joblib import dump

def preprocess_text(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text)
    tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token not in stop_words and token not in string.punctuation]
    return ' '.join(tokens)

def train_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(script_dir, 'intents3.json')) as file:
        data = json.load(file)

    patterns = []
    tags = []
    for intent in data['intents']:
        for pattern in intent['patterns']:
            patterns.append(pattern.lower())
            tags.append(intent['tag'])

    df = pd.DataFrame({'pattern': patterns, 'tag': tags})
    df['pattern'] = df['pattern'].apply(preprocess_text)

    X_train, X_test, y_train, y_test = train_test_split(df['pattern'], df['tag'], test_size=0.2, random_state=42)

    oversampler = RandomOverSampler(random_state=42)
    X_train_resampled, y_train_resampled = oversampler.fit_resample(X_train.to_frame(), y_train)
    X_train_resampled = X_train_resampled.squeeze()

    param_grid = {
        'multinomialnb__alpha': [0.1, 0.5, 1.0],
        'tfidfvectorizer__ngram_range': [(1, 1), (1, 2), (2, 2)]
    }

    pipeline = make_pipeline(
        TfidfVectorizer(),
        MultinomialNB()
    )

    stratified_kfold = StratifiedKFold(n_splits=5)

    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=stratified_kfold,
        scoring='accuracy'
    )

    print("Fitting GridSearchCV...")
    grid_search.fit(X_train_resampled, y_train_resampled)
    print("GridSearchCV fitting complete.")

    print("Best Parameters:", grid_search.best_params_)
    print("Best Score:", grid_search.best_score_)

    dump(grid_search.best_estimator_, os.path.join(script_dir, 'chatmodeltagalog.joblib'))
    print("Model trained and saved successfully.")

if __name__ == "__main__":
    train_model()