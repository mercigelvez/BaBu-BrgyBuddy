import random
from flask_login import current_user
import joblib
import json
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string

import os

# Get the current script directory
import joblib

script_dir = os.path.dirname(os.path.abspath(__file__))

# Load intents from JSON file
with open(os.path.join(script_dir, 'intents2.json')) as file:
    data = json.load(file)

# Load the trained model
try:
    model = joblib.load(os.path.join(script_dir, 'chatmodel.joblib'))
except FileNotFoundError:
    print("Model file not found. Please ensure chatmodel.joblib exists.")
    exit()

# NLP Preprocessing
lemmatizer = WordNetLemmatizer()


def preprocess_input(user_input):
    tokens = word_tokenize(user_input)
    tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token not in string.punctuation]
    return ' '.join(tokens)


from apps.models import ChatHistory, Message
from apps import db

def get_response(user_input):
    cleaned_input = preprocess_input(user_input)
    intent = model.predict([cleaned_input])[0]

    print("Predicted intent:", intent)

    confidence_scores = model.predict_proba([cleaned_input])
    confidence = confidence_scores.max()

    print("Confidence:", confidence)

    for intent_data in data['intents']:
        if intent_data['tag'] == intent:
            if confidence > 0.2:
                response = random.choice(intent_data['responses'])
            else:
                response = "I'm not quite sure. Can you please rephrase your question?"
            break
    else:
        response = "I'm sorry, I'm not sure how to respond to that."

    return response
if __name__ == "__main__":
    print("BaBu: Hi, I'm Babu. How can I assist you today?")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("BaBu: Goodbye!")
            break
        response = get_response(user_input)
        print("BaBu:", response)
