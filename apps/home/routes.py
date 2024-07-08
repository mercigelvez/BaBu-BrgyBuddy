# -*- encoding: utf-8 -*-

from importlib import import_module
import os
import sys
from apps.home import blueprint
from flask import render_template, request
from flask_paginate import get_page_args, Pagination
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.chatbot.chat import get_response, preprocess_input, schedule_appointment
from flask import (
    Blueprint,
    jsonify,
    request,
    redirect,
    url_for,
    flash,
    abort,
    make_response,
)
from datetime import datetime, timedelta
from apps.models import Announcement, Appointment, ChatHistory, Message
from apps import db
from apps.authentication.util import check_timeout
from apps.authentication.models import Users
from apps.authentication.util import hash_pass, verify_pass, role_required
from sqlalchemy import func
import logging
from datetime import datetime, timedelta


@blueprint.route("/index")
@login_required
@check_timeout
def index():
    if current_user.role != "admin":
        return redirect(url_for("home_blueprint.public_chatbot"))

    # Get the current date
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # Group chat histories
    today_chats = []
    yesterday_chats = []
    last_week_chats = []
    older_chats = []

    for chat in current_user.chat_histories:
        chat_date = chat.timestamp.date()
        if chat_date == today:
            today_chats.append(chat)
        elif chat_date == yesterday:
            yesterday_chats.append(chat)
        elif week_ago < chat_date < yesterday:
            last_week_chats.append(chat)
        else:
            older_chats.append(chat)

    grouped_chats = {
        "Today": today_chats,
        "Yesterday": yesterday_chats,
        "Last 7 Days": last_week_chats,
        "Older": older_chats,
    }

    return render_template(
        "home/index.html", segment="index", grouped_chats=grouped_chats
    )


@blueprint.route("/admin_only")
@blueprint.route("/tables.html")
@login_required
@role_required("admin")
def admin_only():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)  # Forbidden

    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    total = Users.query.count()

    users = Users.query.order_by(Users.id).offset(offset).limit(per_page).all()

    pagination = Pagination(
        page=page, per_page=per_page, total=total, css_framework="bootstrap4"
    )

    for user in users:
        user.last_login_str = (
            user.last_login.strftime("%Y-%m-%d %H:%M:%S")
            if user.last_login
            else "Never"
        )
        user.avg_session_duration_str = f"{user.avg_session_duration} seconds"

    return render_template(
        "home/tables.html", segment="tables", users=users, pagination=pagination
    )


@blueprint.route("/chat_analytics")
@login_required
@role_required("admin")
def chat_analytics():
    return render_template("home/chat_analytics.html", segment="chat_analytics")



@blueprint.route("/<template>")
@login_required
def route_template(template):
    try:
        if template in ["tables", "tables.html"] or template.startswith("admin"):
            abort(403)  # Forbidden for non-admin users trying to access admin pages

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except:
        return render_template("home/page-500.html"), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None


import json

# start of changes
predict_logger = logging.getLogger(__name__)


@blueprint.route("/predict", methods=["POST"])
def predict():
    predict_logger.debug("Entered predict route")
    data = request.get_json()
    user_input = data.get("message")

    # Remove the authentication check
    # if not current_user.is_authenticated:
    #     return jsonify({"error": "User not authenticated"}), 401

    # Use a default language if user is not authenticated
    user_language = (
        current_user.language_preference if current_user.is_authenticated else "en"
    )

    predict_logger.debug(f"User input: {user_input}")
    predict_logger.debug(f"User Language: {user_language}")

    cleaned_input = preprocess_input(user_input)
    response = get_response(cleaned_input, user_language)

    # Remove chat history saving for unauthenticated users
    # if current_user.is_authenticated:
    #     # Save chat history logic here

    predict_logger.debug(f"Response: {response}")

    return jsonify({"answer": response})


@blueprint.route("/new_chat", methods=["POST"])
def new_chat():
    if current_user.is_authenticated:
        user_id = current_user.id
        initial_message = request.form.get("initial_message", "")
        title = "Untitled" if len(initial_message) < 20 else initial_message[:20]

        chat_history = ChatHistory(user_id=user_id, title=title)
        db.session.add(chat_history)
        db.session.commit()

        return jsonify({"success": True})
    else:
        return jsonify({"error": "User not authenticated"}), 401


def save_current_chat_history(user_id):
    # Get the current chat history for the user
    current_chat_history = (
        ChatHistory.query.filter_by(user_id=user_id)
        .order_by(ChatHistory.id.desc())
        .first()
    )

    if current_chat_history:
        # Commit the current chat history to the database
        db.session.commit()


@blueprint.route("/get_chat_history", methods=["GET"])
def get_chat_history():
    chat_history_id = request.args.get("chat_history_id")
    if chat_history_id:
        chat_history = ChatHistory.query.get(chat_history_id)
        if chat_history:
            messages = [
                {"sender": message.sender, "message": message.message}
                for message in chat_history.messages
            ]
            return jsonify({"messages": messages})
        else:
            return jsonify({"messages": []})
    else:
        return jsonify({"error": "Missing chat_history_id parameter"}), 400


from sqlalchemy.exc import IntegrityError
import pprint


@blueprint.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    print("========= update_profile route =========")
    pprint.pprint(request.form)

    username = request.form.get("username")
    email = request.form.get("email")
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")

    # Check if the provided current password matches the stored hash
    if not verify_pass(current_password, current_user.password):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "incorrect_password",
                    "message": "Invalid current password",
                }
            ),
            400,
        )

    # Check if the new username already exists (if username is changed)
    if (
        username != current_user.username
        and Users.query.filter_by(username=username).first()
    ):
        return jsonify({"success": False, "message": "Username already exists"}), 400

    try:
        # Update the user's information
        current_user.username = username
        current_user.email = email

        if new_password:
            # Check if the new password is the same as the current password
            if verify_pass(new_password, current_user.password):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "same_password",
                            "message": "New password cannot be the same as the current password",
                        }
                    ),
                    400,
                )
            current_user.password = hash_pass(new_password)

        # Save the changes to the database
        db.session.commit()
        return (
            jsonify({"success": True, "message": "Profile updated successfully"}),
            200,
        )

    except IntegrityError:
        db.session.rollback()
        return jsonify({"success": False, "message": "Database error occurred"}), 500

    except Exception as e:
        db.session.rollback()
        print(f"Unexpected error: {str(e)}")
        return jsonify({"success": False, "message": "Unexpected error occurred"}), 500


@blueprint.route("/get_current_user", methods=["GET"])
def get_current_user():
    if current_user.is_authenticated:
        user_data = {
            "username": current_user.username,
            "email": current_user.email,
            # Add any other user information you need
        }
        return jsonify(user_data)
    else:
        return jsonify({"error": "User not authenticated"}), 401


@blueprint.route("/check_current_password", methods=["POST"])
def check_current_password():
    # Get the current password from the request data
    current_password = request.form.get("current_password")

    # Get the current user's stored password hash
    stored_password_hash = current_user.password

    # Check if the provided current password matches the stored hash
    is_valid = verify_pass(current_password, stored_password_hash)

    return jsonify({"is_valid": is_valid})


@blueprint.route("/rename_chat/<int:chat_id>", methods=["POST"])
@login_required
def rename_chat(chat_id):
    chat = ChatHistory.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    new_title = request.json.get("title")
    chat.title = new_title
    db.session.commit()
    return jsonify({"success": True})


from sqlalchemy.exc import SQLAlchemyError


@blueprint.route("/delete_chat/<int:chat_id>", methods=["POST"])
@login_required
def delete_chat(chat_id):
    try:
        chat = ChatHistory.query.get_or_404(chat_id)
        if chat.user_id != current_user.id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # Delete associated messages first
        Message.query.filter_by(chat_history_id=chat.id).delete()

        db.session.delete(chat)
        db.session.commit()
        return jsonify({"success": True})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@blueprint.route("/api/chat_analytics")
@login_required
@role_required("admin")
def api_chat_analytics():
    # Get data for the last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # Total users
    total_users = Users.query.count()

    # Total messages
    total_messages = Message.query.filter(Message.timestamp >= start_date).count()

    # Messages per day
    messages_per_day = (
        db.session.query(
            func.date(Message.timestamp).label("date"),
            func.count(Message.id).label("count"),
        )
        .filter(Message.timestamp >= start_date)
        .group_by(func.date(Message.timestamp))
        .all()
    )

    # Average session duration
    users_with_sessions = Users.query.filter(Users.total_sessions > 0).all()
    if users_with_sessions:
        avg_session_duration = sum(
            user.avg_session_duration for user in users_with_sessions
        ) / len(users_with_sessions)
    else:
        avg_session_duration = 0

    # Active users per day (users who sent a message)
    active_users_per_day = (
        db.session.query(
            func.date(Message.timestamp).label("date"),
            func.count(func.distinct(ChatHistory.user_id)).label("count"),
        )
        .join(ChatHistory)
        .filter(Message.timestamp >= start_date)
        .group_by(func.date(Message.timestamp))
        .all()
    )

    return jsonify(
        {
            "total_users": total_users,
            "total_messages": total_messages,
            "messages_per_day": [
                {"date": str(m.date), "count": m.count} for m in messages_per_day
            ],
            "avg_session_duration": round(avg_session_duration, 2),
            "active_users_per_day": [
                {"date": str(u.date), "count": u.count} for u in active_users_per_day
            ],
        }
    )


import csv
from io import StringIO


@blueprint.route("/api/chat_analytics_download")
@login_required
@role_required("admin")
def api_chat_analytics_download():
    # Get the analytics data
    analytics_data = api_chat_analytics().get_json()

    # Create a StringIO object to write our CSV to
    si = StringIO()
    cw = csv.writer(si)

    # Write the headers
    cw.writerow(["Metric", "Value"])

    # Write the simple metrics
    cw.writerow(["Total Users", analytics_data["total_users"]])
    cw.writerow(["Total Messages", analytics_data["total_messages"]])
    cw.writerow(["Average Session Duration", analytics_data["avg_session_duration"]])

    # Write a blank row
    cw.writerow([])

    # Write the Messages per Day data
    cw.writerow(["Date", "Messages"])
    for day in analytics_data["messages_per_day"]:
        cw.writerow([day["date"], day["count"]])

    # Write a blank row
    cw.writerow([])

    # Write the Active Users per Day data
    cw.writerow(["Date", "Active Users"])
    for day in analytics_data["active_users_per_day"]:
        cw.writerow([day["date"], day["count"]])

    # Create the response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=chat_analytics.csv"
    output.headers["Content-type"] = "text/csv"

    return output


@blueprint.route("/chatbot")
def public_chatbot():
    return render_template("home/chatbot.html", segment="chatbot")


@blueprint.route("/landingpage")
def landingpage():
    return render_template("landing-page.html", segment="landingpage")


@blueprint.route("/tables")
@login_required
def tables():
    return render_template("home/tables.html", segment="tables")


@blueprint.route("/get_appointments", methods=["GET"])
def get_appointments():
    appointments = Appointment.query.all()
    appointment_list = [
        {
            "id": apt.id,
            "title": f"{apt.full_name} - {apt.purpose}",
            "start": apt.appointment_date.isoformat(),
            "end": (apt.appointment_date + timedelta(hours=1)).isoformat(),
            "address": apt.address,
            "birthday": apt.birthday.isoformat(),
            "birthplace": apt.birthplace,
        }
        for apt in appointments
    ]
    return jsonify(appointment_list)




# CHATBOT MANAGEMENT---------------------------------------------------

# Define the path to the intents file
INTENTS_FILE = 'intents3.json'

def get_intents_file_path():
    """Get the full path to the intents file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    apps_dir = os.path.dirname(current_dir)
    return os.path.join(apps_dir, 'chatbot', INTENTS_FILE)

@blueprint.route("/intent_management")
@login_required
@role_required("admin")
def intent_management():
    intents_file = get_intents_file_path()
    with open(intents_file) as file:
        intents = json.load(file)
    return render_template("home/intent_management.html", segment="intent_management", intents=intents['intents'])

@blueprint.route("/api/intents", methods=['GET', 'POST'])
@login_required
@role_required("admin")
def api_intents():
    intents_file = get_intents_file_path()
    if request.method == 'GET':
        with open(intents_file) as file:
            intents = json.load(file)
        return jsonify(intents)
    elif request.method == 'POST':
        new_intent = request.json
        with open(intents_file) as file:
            intents = json.load(file)
        intents['intents'].append(new_intent)
        with open(intents_file, 'w') as file:
            json.dump(intents, file, indent=2)
        retrain_model()
        return jsonify({"message": "Intent added successfully"}), 201

@blueprint.route("/api/intents/<string:tag>", methods=['PUT', 'DELETE'])
@login_required
@role_required("admin")
def api_intent(tag):
    intents_file = get_intents_file_path()
    with open(intents_file) as file:
        intents = json.load(file)
    
    intent_index = next((index for (index, d) in enumerate(intents['intents']) if d["tag"] == tag), None)
    
    if intent_index is None:
        return jsonify({"error": "Intent not found"}), 404
    
    if request.method == 'PUT':
        updated_intent = request.json
        intents['intents'][intent_index] = updated_intent
    elif request.method == 'DELETE':
        del intents['intents'][intent_index]
    
    with open(intents_file, 'w') as file:
        json.dump(intents, file, indent=2)
    
    retrain_model()
    return jsonify({"message": "Intent updated successfully"})

def retrain_model():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    apps_dir = os.path.dirname(current_dir)
    chatbot_dir = os.path.join(apps_dir, 'chatbot')
    sys.path.append(chatbot_dir)

    try:
        train_module = import_module('train')
        
        if hasattr(train_module, 'train_model'):
            train_module.train_model()
            print("Model retrained and saved successfully.")
            return True
        else:
            print("Error: Could not find train_model function in train.py")
            return False
    except Exception as e:
        print(f"Error retraining model: {str(e)}")
        return False
    finally:
        sys.path.remove(chatbot_dir)
        

@blueprint.route("/api/retrain", methods=['POST'])
@login_required
@role_required("admin")
def api_retrain():
    try:
        retrain_model()
        return jsonify({"message": "Model retrained successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


import math

def get_paginated_intents(page, per_page):
    file_path = get_intents_file_path()
    with open(file_path, 'r') as file:
        all_intents = json.load(file)['intents']
    
    total_intents = len(all_intents)
    total_pages = math.ceil(total_intents / per_page)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_intents = all_intents[start:end]
    
    return {
        'intents': paginated_intents,
        'total_pages': total_pages,
        'current_page': page,
        'total_intents': total_intents
    }

#------ANNOUNCEMENT----------# 
    
@blueprint.route("/api/announcements", methods=['GET', 'POST'])
@login_required
@role_required("admin")
def manage_announcements():
    if request.method == 'GET':
        announcements = Announcement.query.all()
        return jsonify([{
            'id': a.id,
            'message': a.message,
            'enabled': a.enabled,
            'created_at': a.created_at.isoformat(),
            'updated_at': a.updated_at.isoformat()
        } for a in announcements])
    elif request.method == 'POST':
        data = request.json
        new_announcement = Announcement(message=data['message'], enabled=data['enabled'])
        db.session.add(new_announcement)
        db.session.commit()
        return jsonify({'message': 'Announcement created successfully'}), 201

@blueprint.route("/api/announcements/<int:id>", methods=['PUT', 'DELETE'])
@login_required
@role_required("admin")
def manage_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    if request.method == 'PUT':
        data = request.json
        announcement.message = data['message']
        announcement.enabled = data['enabled']
        db.session.commit()
        return jsonify({'message': 'Announcement updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(announcement)
        db.session.commit()
        return jsonify({'message': 'Announcement deleted successfully'})

@blueprint.route("/api/announcements/<int:id>/toggle", methods=['POST'])
@login_required
@role_required("admin")
def toggle_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    announcement.enabled = not announcement.enabled
    db.session.commit()
    return jsonify({'message': 'Announcement toggled successfully'})

@blueprint.route("/api/current_announcement", methods=['GET'])
def get_current_announcement():
    announcement = Announcement.query.filter_by(enabled=True).order_by(Announcement.id.desc()).first()
    if announcement:
        return jsonify({"announcement": announcement.message})
    else:
        return jsonify({"announcement": None})
    
@blueprint.route("/announcement_management")
@login_required
@role_required("admin")
def announcement_management():
    return render_template("home/announcement_management.html", segment="announcement_management")