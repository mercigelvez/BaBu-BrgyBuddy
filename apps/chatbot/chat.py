import random
import joblib
import json
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# Load both intent files
with open(os.path.join(script_dir, 'intents2.json')) as file:
    english_data = json.load(file)
with open(os.path.join(script_dir, 'intents3.json')) as file:
    tagalog_data = json.load(file)

# Load both models
english_model = joblib.load(os.path.join(script_dir, 'chatmodel.joblib'))
tagalog_model = joblib.load(os.path.join(script_dir, 'chatmodeltagalog.joblib'))

lemmatizer = WordNetLemmatizer()

def preprocess_input(user_input):
    tokens = word_tokenize(user_input)
    tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens if token not in string.punctuation]
    return ' '.join(tokens)

def get_response(user_input, language):
    # Choose the appropriate model based on the language
    if language == 'english':
        model = english_model
        data = english_data
    else:  # default to English
        model = tagalog_model
        data = tagalog_data

    intent = model.predict([user_input])[0]
    confidence_scores = model.predict_proba([user_input])
    confidence = confidence_scores.max()

    for intent_data in data['intents']:
        if intent_data['tag'] == intent:
            if confidence > 0.2:
                responses = intent_data['responses']
                return random.choice(responses)
            else:
                return "I'm not quite sure. Can you please rephrase your question?" if language == 'english' else "Hindi ako sigurado. Pwede mo bang ulitin ang tanong mo?"

    return "I'm sorry, I'm not sure how to respond to that." if language == 'english' else "Paumanhin, hindi ko alam kung paano sasagutin 'yan."

if __name__ == "__main__":
    # For testing purposes, you can set the language preference here
    language_preference = input("Choose language (english/tagalog): ").lower()
    
    print("BaBu: Hi, I'm Babu. How can I assist you today?" if language_preference == 'english' else "BaBu: Kumusta, ako si Babu. Paano kita matutulungan ngayon?")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("BaBu: Goodbye!" if language_preference == 'english' else "BaBu: Paalam!")
            break
        response = get_response(user_input, language_preference)
        print("BaBu:", response)