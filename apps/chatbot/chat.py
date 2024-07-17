from datetime import datetime, timedelta
import random
import re
import traceback
import uuid
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
import logging

from apps.models import Appointment
from apps import db

# Set up logging
logger = logging.getLogger(__name__)

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


def get_response(user_input, language="tagalog"):
    if "schedule" in user_input.lower() and "appointment_data" not in session:
        session["appointment_data"] = {"appointment_step": "full_name"}
        session["last_activity"] = datetime.utcnow()
        return "Para mag-schedule ng appointment, pakibigay ang iyong buong pangalan."

    if "appointment_data" in session:
        return handle_appointment_scheduling(user_input, language)

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


def handle_appointment_scheduling(user_input, language="tagalog"):
    print("Session data at start:", session)
    try:
        current_time = ensure_naive_datetime(datetime.now())

        if "appointment_data" not in session or "last_activity" not in session:
            session["appointment_data"] = {"appointment_step": "full_name"}
            session["last_activity"] = current_time.isoformat()
            return "Magsimula tayo ulit. Para mag-schedule ng appointment, pakibigay ang iyong buong pangalan."

        last_activity = session.get("last_activity")
        if isinstance(last_activity, str):
            last_activity = ensure_naive_datetime(datetime.fromisoformat(last_activity))
        elif isinstance(last_activity, datetime):
            last_activity = ensure_naive_datetime(last_activity)
        else:
            session.pop("appointment_data", None)
            session.pop("last_activity", None)
            return "May problema sa iyong session. Pakiulit mula sa simula."

        if current_time - last_activity > timedelta(days=30):
            session.pop("appointment_data", None)
            session.pop("last_activity", None)
            return "Nag-expire na ang scheduling session. Pakiulit mula sa simula."

        session["last_activity"] = current_time.isoformat()

        appointment_data = session["appointment_data"]

        if appointment_data["appointment_step"] == "full_name":
            appointment_data["full_name"] = user_input
            appointment_data["appointment_step"] = "address"
            session["appointment_data"] = appointment_data
            return "Salamat. Ngayon, pakibigay ang iyong address."

        elif appointment_data["appointment_step"] == "address":
            appointment_data["address"] = user_input
            appointment_data["appointment_step"] = "birthday"
            session["appointment_data"] = appointment_data
            return (
                "Mahusay. Ano ang iyong kaarawan? (Pakigamit ang format na YYYY-MM-DD)"
            )

        elif appointment_data["appointment_step"] == "birthday":
            if re.match(r"\d{4}-\d{2}-\d{2}", user_input):
                appointment_data["birthday"] = user_input
                appointment_data["appointment_step"] = "birthplace"
                session["appointment_data"] = appointment_data
                return "Salamat. Ano ang iyong lugar ng kapanganakan?"
            else:
                return "Pakibigay ang iyong kaarawan sa format na YYYY-MM-DD."

        elif appointment_data["appointment_step"] == "birthplace":
            appointment_data["birthplace"] = user_input
            appointment_data["appointment_step"] = "purpose"
            session["appointment_data"] = appointment_data
            return "Ano ang layunin ng iyong appointment?"

        elif appointment_data["appointment_step"] == "purpose":
            appointment_data["purpose"] = user_input
            appointment_data["appointment_step"] = "appointment_date"
            session["appointment_data"] = appointment_data
            return "Kailan mo gustong i-schedule ang iyong appointment? Pakienter ang petsa sa format na YYYY-MM-DD, o i-type ang 'ngayon' para sa pinakamaagang available na petsa."

        elif appointment_data["appointment_step"] == "appointment_date":
            if user_input.lower() in ["today", "ngayon"]:
                appointment_date = datetime.now().date()
                appointment_data["appointment_date"] = appointment_date.strftime(
                    "%Y-%m-%d"
                )
                appointment_data["appointment_step"] = "appointment_time"
                session["appointment_data"] = appointment_data
                return "Anong oras mo gustong i-schedule ang iyong appointment? Pakigamit ang format na HH:MM AM/PM (hal., 02:30 PM)."
            else:
                try:
                    appointment_date = datetime.strptime(user_input, "%Y-%m-%d").date()
                    appointment_data["appointment_date"] = appointment_date.strftime(
                        "%Y-%m-%d"
                    )
                    appointment_data["appointment_step"] = "appointment_time"
                    session["appointment_data"] = appointment_data
                    return "Anong oras mo gustong i-schedule ang iyong appointment? Pakigamit ang format na HH:MM AM/PM (hal., 02:30 PM)."
                except ValueError:
                    return "Mali ang format ng petsa. Pakigamit ang format na YYYY-MM-DD (hal., 2023-07-15) o i-type ang 'ngayon'."

        elif appointment_data["appointment_step"] == "appointment_time":
            try:
                appointment_time = datetime.strptime(user_input, "%I:%M %p").time()
                appointment_data["appointment_time"] = appointment_time.strftime(
                    "%I:%M %p"
                )
                appointment_data["appointment_step"] = "confirm"
                session["appointment_data"] = appointment_data

                confirmation_text = f"""
                Pakikumpirma ang mga detalye ng iyong appointment:
                Buong Pangalan: {appointment_data['full_name']}
                Address: {appointment_data['address']}
                Kaarawan: {appointment_data['birthday']}
                Lugar ng Kapanganakan: {appointment_data['birthplace']}
                Layunin: {appointment_data['purpose']}
                Petsa ng Appointment: {appointment_data['appointment_date']}
                Oras ng Appointment: {appointment_data['appointment_time']}

                Kinukumpirma mo ba ang appointment na ito? (Oo/Hindi)
                """
                return confirmation_text
            except ValueError:
                return "Mali ang format ng oras. Pakigamit ang format na HH:MM AM/PM (hal., 02:30 PM)."

        elif appointment_data["appointment_step"] == "confirm":
            if user_input.lower() in ["oo", "yes", "confirm", "okay"]:
                result = schedule_appointment(appointment_data)
                if result["status"] == "success":
                    appointment_data["appointment_id"] = result["appointment_id"]
                    ticket_image = generate_appointment_ticket_image(appointment_data)
                    if ticket_image:
                        session.pop("appointment_data", None)
                        return {
                            "message": "Matagumpay na na-schedule ang iyong appointment.",
                            "ticket_image": ticket_image,
                        }
                    else:
                        return "Na-schedule na ang iyong appointment, ngunit may error sa pag-generate ng ticket. Mangyaring makipag-ugnayan sa support."
                else:
                    return result["message"]
            else:
                session.pop("appointment_data", None)
                return "Kinansela ang pag-schedule ng appointment. Paano pa kita matutulungan?"

    except Exception as e:
        print(f"May naganap na exception: {str(e)}")
        traceback.print_exc()
        session.pop("appointment_data", None)
        session.pop("last_activity", None)
        return "May nangyaring hindi inaasahang error. Pakisubukang muli."


def schedule_appointment(data):
    try:
        appointment_datetime = datetime.strptime(
            f"{data['appointment_date']} {data['appointment_time']}",
            "%Y-%m-%d %I:%M %p",
        )
        new_appointment = Appointment(
            full_name=data["full_name"],
            address=data["address"],
            birthday=datetime.strptime(data["birthday"], "%Y-%m-%d").date(),
            birthplace=data["birthplace"],
            purpose=data["purpose"],
            appointment_date=appointment_datetime,
        )
        db.session.add(new_appointment)
        db.session.commit()
        return {
            "status": "success",
            "message": "Matagumpay na na-schedule ang iyong appointment.",
            "appointment_id": new_appointment.appointment_id
        }
    except Exception as e:
        db.session.rollback()
        print(f"Error sa pag-schedule ng appointment: {str(e)}")
        print(f"Buong error traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"Nagkaroon ng error sa pag-schedule ng iyong appointment: {str(e)}. Pakisubukang muli mamaya.",
        }

def generate_appointment_ticket_image(appointment_data):
    try:
        logger.debug("Gumagawa ng appointment ticket image")

        width, height = 600, 400
        background_color = (240, 248, 255)
        img = Image.new("RGB", (width, height), color=background_color)
        d = ImageDraw.Draw(img)

        # Load fonts
        try:
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
        logo_path = os.path.join(script_dir, "..", "static", "assets", "img", "babu-logo.png")
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo = logo.resize((80, 80))
            img.paste(logo, (10, 10), logo)
        except Exception as e:
            logger.error(f"Error loading logo: {str(e)}")
            # Continue without the logo if it can't be loaded

        # Add title
        d.text((100, 30), "SCHEDULE TICKET", font=title_font, fill=(0, 100, 0))

        # Add horizontal line
        d.line([(10, 100), (width - 10, 100)], fill=(0, 100, 0), width=2)

        # Add appointment ID on the right side
        appointment_id_text = f"ID: {appointment_data['appointment_id']}"
        appointment_id_bbox = d.textbbox((0, 0), appointment_id_text, font=main_font)
        appointment_id_width = appointment_id_bbox[2] - appointment_id_bbox[0]
        d.text((width - appointment_id_width - 20, 70), appointment_id_text, font=main_font, fill=(0, 100, 0))

        details = [
            f"Pangalan: {appointment_data['full_name']}",
            f"Address: {appointment_data['address']}",
            f"Kaarawan: {appointment_data['birthday']}",
            f"Lugar ng Kapanganakan: {appointment_data['birthplace']}",
            f"Layunin: {appointment_data['purpose']}",
            f"Petsa ng Appointment: {appointment_data['appointment_date']}",
            f"Oras ng Appointment: {appointment_data['appointment_time']}",
        ]

        y_position = 120
        for detail in details:
            d.text((20, y_position), detail, font=main_font, fill=(0, 0, 0))
            y_position += 30

        d.line([(10, 320), (width - 10, 320)], fill=(0, 100, 0), width=2)

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
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
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
