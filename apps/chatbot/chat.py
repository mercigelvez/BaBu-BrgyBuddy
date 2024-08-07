from datetime import datetime, timedelta, timezone
import random
import re
import traceback
from flask import session
import joblib
import json
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import os
from PIL import Image, ImageDraw, ImageFont
import io
import base64

import requests

from apps.models import Appointment
from apps import db

script_dir = os.path.dirname(os.path.abspath(__file__))

# Load both intent files
with open(os.path.join(script_dir, "intents2.json")) as file:
    english_data = json.load(file)
with open(os.path.join(script_dir, "intents3.json")) as file:
    tagalog_data = json.load(file)

# Load both models
english_model = joblib.load(os.path.join(script_dir, "chatmodel.joblib"))
tagalog_model = joblib.load(os.path.join(script_dir, "chatmodeltagalog.joblib"))

lemmatizer = WordNetLemmatizer()


def preprocess_input(user_input):
    tokens = word_tokenize(user_input)
    tokens = [
        lemmatizer.lemmatize(token.lower())
        for token in tokens
        if token not in string.punctuation
    ]
    return " ".join(tokens)


appointment_data = {}


def get_response(user_input, language):
    # Check if the user wants to schedule an appointment
    if "schedule" in user_input.lower() and "appointment_data" not in session:
        session["appointment_data"] = {"appointment_step": "full_name"}
        session["last_activity"] = datetime.utcnow()
        return "To schedule an appointment, please provide your full name."

    # If we're in the middle of scheduling an appointment, continue with that process
    if "appointment_data" in session:
        return handle_appointment_scheduling(user_input, language)

    # Otherwise, proceed with normal conversation
    if language == "english":
        model = english_model
        data = english_data
    else:  # default to Tagalog
        model = tagalog_model
        data = tagalog_data

    intent = model.predict([user_input])[0]
    confidence_scores = model.predict_proba([user_input])
    confidence = confidence_scores.max()

    for intent_data in data["intents"]:
        if intent_data["tag"] == intent:
            if confidence > 0.2:
                responses = intent_data["responses"]
                return random.choice(responses)
            else:
                return (
                    "I'm not quite sure. Can you please rephrase your question?"
                    if language == "english"
                    else "Hindi ako sigurado. Pwede mo bang ulitin ang tanong mo?"
                )

    return (
        "I'm sorry, I'm not sure how to respond to that."
        if language == "english"
        else "Paumanhin, hindi ko alam kung paano sasagutin 'yan."
    )


def ensure_naive_datetime(dt):
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def handle_appointment_scheduling(user_input, language):
    print("Session data at start:", session)
    try:
        current_time = ensure_naive_datetime(datetime.now())

        if "appointment_data" not in session or "last_activity" not in session:
            session["appointment_data"] = {"appointment_step": "full_name"}
            session["last_activity"] = current_time.isoformat()
            return "Let's start over. To schedule an appointment, please provide your full name."

        # Convert last_activity to datetime object
        last_activity = session.get("last_activity")
        if isinstance(last_activity, str):
            last_activity = ensure_naive_datetime(datetime.fromisoformat(last_activity))
        elif isinstance(last_activity, datetime):
            last_activity = ensure_naive_datetime(last_activity)
        else:
            # If it's neither a string nor a datetime, reset the session
            session.pop("appointment_data", None)
            session.pop("last_activity", None)
            return "There was an issue with your session. Please start over."

        # Check if the session has expired
        if current_time - last_activity > timedelta(days=30):
            session.pop("appointment_data", None)
            session.pop("last_activity", None)
            return "Scheduling session has expired. Please start over."

        # Update last activity
        session["last_activity"] = current_time.isoformat()

        appointment_data = session["appointment_data"]

        if appointment_data["appointment_step"] == "full_name":
            appointment_data["full_name"] = user_input
            appointment_data["appointment_step"] = "address"
            session["appointment_data"] = appointment_data
            return "Thank you. Now, please provide your address."

        elif appointment_data["appointment_step"] == "address":
            appointment_data["address"] = user_input
            appointment_data["appointment_step"] = "birthday"
            session["appointment_data"] = appointment_data
            return "Great. What's your birthday? (Please use YYYY-MM-DD format)"

        elif appointment_data["appointment_step"] == "birthday":
            if re.match(r"\d{4}-\d{2}-\d{2}", user_input):
                appointment_data["birthday"] = user_input
                appointment_data["appointment_step"] = "birthplace"
                session["appointment_data"] = appointment_data
                return "Thank you. What's your birthplace?"
            else:
                return "Please provide your birthday in YYYY-MM-DD format."

        elif appointment_data["appointment_step"] == "birthplace":
            appointment_data["birthplace"] = user_input
            appointment_data["appointment_step"] = "purpose"
            session["appointment_data"] = appointment_data
            return "What's the purpose of your appointment?"

        elif appointment_data["appointment_step"] == "purpose":
            appointment_data["purpose"] = user_input
            appointment_data["appointment_step"] = "appointment_date"
            session["appointment_data"] = appointment_data
            return "When would you like to schedule your appointment? Please enter a date in YYYY-MM-DD format, or type 'today' or 'ngayon' for the earliest available date."

        elif appointment_data["appointment_step"] == "appointment_date":
            if user_input.lower() in ["today", "ngayon"]:
                appointment_date = datetime.now().date()
            else:
                try:
                    appointment_date = datetime.strptime(user_input, "%Y-%m-%d").date()
                except ValueError:
                    return "The date format is incorrect. Please use YYYY-MM-DD format (e.g., 2023-07-15) or type 'today'/'ngayon'."

            appointment_data["appointment_date"] = appointment_date.strftime("%Y-%m-%d")
            appointment_data["appointment_step"] = "confirm"
            session["appointment_data"] = appointment_data

            confirmation_text = f"""
            Please confirm your appointment details:
            Full Name: {appointment_data['full_name']}
            Address: {appointment_data['address']}
            Birthday: {appointment_data['birthday']}
            Birthplace: {appointment_data['birthplace']}
            Purpose: {appointment_data['purpose']}
            Appointment Date: {appointment_data['appointment_date']}

            Do you confirm this appointment? (Yes/No)
            """
            return confirmation_text

        elif appointment_data["appointment_step"] == "confirm":
            if user_input.lower() in ["oo", "yes", "confirm", "okay"]:
                # Save the appointment to the database
                result = schedule_appointment(appointment_data)
                if result["status"] == "success":
                    # Generate the ticket image
                    ticket_image = generate_appointment_ticket_image(appointment_data)
                    if ticket_image:
                        session.pop("appointment_data", None)
                        return {
                            "message": "Your appointment has been scheduled successfully.",
                            "ticket_image": ticket_image
                        }
                    else:
                        return "Your appointment has been scheduled, but there was an error generating the ticket. Please contact support."
                else:
                    return result["message"]
            else:
                session.pop("appointment_data", None)
                return "Appointment scheduling cancelled. How else can I assist you?"

    except Exception as e:
        print(f"An exception occurred: {str(e)}")
        traceback.print_exc()  # This will print the full stack trace
        session.pop("appointment_data", None)
        session.pop("last_activity", None)
        return "An unexpected error occurred. Please try again."


def schedule_appointment(data):
    try:
        new_appointment = Appointment(
            full_name=data["full_name"],
            address=data["address"],
            birthday=datetime.strptime(data["birthday"], "%Y-%m-%d").date(),
            birthplace=data["birthplace"],
            purpose=data["purpose"],
            appointment_date=datetime.strptime(data["appointment_date"], "%Y-%m-%d"),
        )
        db.session.add(new_appointment)
        db.session.commit()
        return {
            "status": "success",
            "message": "Your appointment has been scheduled successfully.",
        }
    except Exception as e:
        db.session.rollback()
        print(f"Error scheduling appointment: {str(e)}")
        print(f"Full error traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"There was an error scheduling your appointment: {str(e)}. Please try again later.",
        }


import logging

logger = logging.getLogger(__name__)


def generate_appointment_ticket_image(appointment_data):
    try:
        logger.debug("Generating appointment ticket image")

        # Create a new image with a light background
        width, height = 600, 400
        background_color = (240, 248, 255)  # Light blue background
        img = Image.new("RGB", (width, height), color=background_color)
        d = ImageDraw.Draw(img)

        # Load fonts
        try:
            # Try to use a more universally available font
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            main_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except IOError:
            logger.warning("DejaVu Sans font not found, using default font")
            title_font = ImageFont.load_default()
            main_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Add BaBu logo
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(
            script_dir, "..", "static", "assets", "img", "babu-logo.png"
        )
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((80, 80))  # Resize logo as needed
            img.paste(logo, (10, 10), logo)
        except Exception as e:
            logger.error(f"Error loading logo: {str(e)}")


        # Add title
        d.text((100, 30), "SCHEDULE TICKET", font=title_font, fill=(0, 100, 0))

        # Add horizontal line
        d.line([(10, 100), (width - 10, 100)], fill=(0, 100, 0), width=2)

        # Add appointment details
        details = [
            f"Name: {appointment_data['full_name']}",
            f"Address: {appointment_data['address']}",
            f"Birthday: {appointment_data['birthday']}",
            f"Birthplace: {appointment_data['birthplace']}",
            f"Purpose: {appointment_data['purpose']}",
            f"Appointment Date: {appointment_data['appointment_date']}",
        ]

        y_position = 120
        for detail in details:
            d.text((20, y_position), detail, font=main_font, fill=(0, 0, 0))
            y_position += 30

        # Add horizontal line
        d.line([(10, 320), (width - 10, 320)], fill=(0, 100, 0), width=2)

        # Add reminders
        d.text((20, 330), "MAHALAGANG PAALALA:", font=main_font, fill=(0, 100, 0))
        reminders = [
            "• Dalhin ang ticket na ito sa araw ng schedule",
            "• Magdala ng valid ID",
            "• Ito ay valid lamang para sa araw ng iyong schedule",
        ]

        y_position = 355
        for reminder in reminders:
            d.text((20, y_position), reminder, font=small_font, fill=(0, 0, 0))
            y_position += 20

        # Add decorative elements
        d.rectangle([(0, 0), (width, height)], outline=(0, 100, 0), width=5)
        d.rectangle([(5, 5), (width - 5, height - 5)], outline=(0, 150, 0), width=2)

        # Save the image to a bytes buffer
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        # Encode the image as base64
        logger.debug("Ticket image generated successfully")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error generating ticket image: {str(e)}")
        logger.error(traceback.format_exc())
        return None


if __name__ == "__main__":
    # For testing purposes, you can set the language preference here
    language_preference = input("Choose language (english/tagalog): ").lower()

    print(
        "BaBu: Hi, I'm Babu. How can I assist you today?"
        if language_preference == "english"
        else "BaBu: Kumusta, ako si Babu. Paano kita matutulungan ngayon?"
    )

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print(
                "BaBu: Goodbye!"
                if language_preference == "english"
                else "BaBu: Paalam!"
            )
            break
        response = get_response(user_input, language_preference)
        print("BaBu:", response)
