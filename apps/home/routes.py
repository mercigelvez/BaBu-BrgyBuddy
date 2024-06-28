
# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.chatbot.chat import get_response, preprocess_input
from flask import Blueprint, jsonify, request, redirect, url_for, flash, abort, make_response
from datetime import datetime, timedelta
from apps.models import ChatHistory, Message
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
        'Today': today_chats,
        'Yesterday': yesterday_chats,
        'Last 7 Days': last_week_chats,
        'Older': older_chats
    }
    
    return render_template("home/index.html", segment="index", grouped_chats=grouped_chats)

@blueprint.route("/admin_only")
@blueprint.route("/tables.html")
@login_required
@role_required('admin')
def admin_only():
    if not current_user.is_authenticated or current_user.role != 'admin':
        abort(403)  # Forbidden

    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = Users.query.count()
    
    users = Users.query.order_by(Users.id).offset(offset).limit(per_page).all()
    
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    
    for user in users:
        user.last_login_str = user.last_login.strftime("%Y-%m-%d %H:%M:%S") if user.last_login else "Never"
        user.avg_session_duration_str = f"{user.avg_session_duration} seconds"
    
    return render_template("home/tables.html", 
                           segment="tables", 
                           users=users, 
                           pagination=pagination)


@blueprint.route('/chat_analytics')
@login_required
@role_required('admin')
def chat_analytics():
    return render_template('home/chat_analytics.html', segment='chat_analytics')


@blueprint.route("/<template>")
@login_required
def route_template(template):
    try:
        if template in ['tables', 'tables.html'] or template.startswith('admin'):
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

    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    user_id = current_user.id
    user_language = current_user.language_preference  # Assuming you have this field in your User model

    predict_logger.debug(f"User input: {user_input}")
    predict_logger.debug(f"User ID: {user_id}")
    predict_logger.debug(f"User Language: {user_language}")

    cleaned_input = preprocess_input(user_input)
    response = get_response(cleaned_input, user_language)  # Pass language to get_response

    # Get or create the chat history for the current user
    chat_history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.id.desc()).first()
    if not chat_history:
        chat_history = ChatHistory(user_id=user_id, title="Untitled")
        db.session.add(chat_history)
        db.session.commit()

    # Append the new message to the chat history
    new_message_user = Message(
        chat_history_id=chat_history.id, sender="user", message=user_input
    )
    new_message_bot = Message(
        chat_history_id=chat_history.id, sender="Bot", message=response
    )
    db.session.add(new_message_user)
    db.session.add(new_message_bot)
    db.session.commit()

    predict_logger.debug(f"Response: {response}")

    return jsonify({"answer": response})


@blueprint.route('/new_chat', methods=['POST'])
def new_chat():
    if current_user.is_authenticated:
        user_id = current_user.id
        initial_message = request.form.get('initial_message', '')
        title = "Untitled" if len(initial_message) < 20 else initial_message[:20]

        chat_history = ChatHistory(user_id=user_id, title=title)
        db.session.add(chat_history)
        db.session.commit()

        return jsonify({'success': True})
    else:
        return jsonify({'error': 'User not authenticated'}), 401

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


@blueprint.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    chat_history_id = request.args.get('chat_history_id')
    if chat_history_id:
        chat_history = ChatHistory.query.get(chat_history_id)
        if chat_history:
            messages = [{'sender': message.sender, 'message': message.message} for message in chat_history.messages]
            return jsonify({'messages': messages})
        else:
            return jsonify({'messages': []})
    else:
        return jsonify({'error': 'Missing chat_history_id parameter'}), 400
    
    
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
        return jsonify({"success": False, "error": "incorrect_password", "message": "Invalid current password"}), 400

    # Check if the new username already exists (if username is changed)
    if username != current_user.username and Users.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists"}), 400

    try:
        # Update the user's information
        current_user.username = username
        current_user.email = email

        if new_password:
            # Check if the new password is the same as the current password
            if verify_pass(new_password, current_user.password):
                return jsonify({"success": False, "error": "same_password", "message": "New password cannot be the same as the current password"}), 400
            current_user.password = hash_pass(new_password)

        # Save the changes to the database
        db.session.commit()
        return jsonify({"success": True, "message": "Profile updated successfully"}), 200

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


@blueprint.route('/rename_chat/<int:chat_id>', methods=['POST'])
@login_required
def rename_chat(chat_id):
    chat = ChatHistory.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    new_title = request.json.get('title')
    chat.title = new_title
    db.session.commit()
    return jsonify({'success': True})

from sqlalchemy.exc import SQLAlchemyError

@blueprint.route('/delete_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    try:
        chat = ChatHistory.query.get_or_404(chat_id)
        if chat.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Delete associated messages first
        Message.query.filter_by(chat_history_id=chat.id).delete()
        
        db.session.delete(chat)
        db.session.commit()
        return jsonify({'success': True})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    
@blueprint.route('/api/chat_analytics')
@login_required
@role_required('admin')
def api_chat_analytics():
    # Get data for the last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # Total users
    total_users = Users.query.count()

    # Total messages
    total_messages = Message.query.filter(Message.timestamp >= start_date).count()

    # Messages per day
    messages_per_day = db.session.query(
        func.date(Message.timestamp).label('date'),
        func.count(Message.id).label('count')
    ).filter(Message.timestamp >= start_date).group_by(func.date(Message.timestamp)).all()

    # Average session duration
    users_with_sessions = Users.query.filter(Users.total_sessions > 0).all()
    if users_with_sessions:
        avg_session_duration = sum(user.avg_session_duration for user in users_with_sessions) / len(users_with_sessions)
    else:
        avg_session_duration = 0

    # Active users per day (users who sent a message)
    active_users_per_day = db.session.query(
        func.date(Message.timestamp).label('date'),
        func.count(func.distinct(ChatHistory.user_id)).label('count')
    ).join(ChatHistory).filter(Message.timestamp >= start_date).group_by(func.date(Message.timestamp)).all()

    return jsonify({
        'total_users': total_users,
        'total_messages': total_messages,
        'messages_per_day': [{'date': str(m.date), 'count': m.count} for m in messages_per_day],
        'avg_session_duration': round(avg_session_duration, 2),
        'active_users_per_day': [{'date': str(u.date), 'count': u.count} for u in active_users_per_day]
    })
    

import csv
from io import StringIO

@blueprint.route('/api/chat_analytics_download')
@login_required
@role_required('admin')
def api_chat_analytics_download():
    # Get the analytics data
    analytics_data = api_chat_analytics().get_json()

    # Create a StringIO object to write our CSV to
    si = StringIO()
    cw = csv.writer(si)

    # Write the headers
    cw.writerow(['Metric', 'Value'])

    # Write the simple metrics
    cw.writerow(['Total Users', analytics_data['total_users']])
    cw.writerow(['Total Messages', analytics_data['total_messages']])
    cw.writerow(['Average Session Duration', analytics_data['avg_session_duration']])

    # Write a blank row
    cw.writerow([])

    # Write the Messages per Day data
    cw.writerow(['Date', 'Messages'])
    for day in analytics_data['messages_per_day']:
        cw.writerow([day['date'], day['count']])

    # Write a blank row
    cw.writerow([])

    # Write the Active Users per Day data
    cw.writerow(['Date', 'Active Users'])
    for day in analytics_data['active_users_per_day']:
        cw.writerow([day['date'], day['count']])

    # Create the response
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=chat_analytics.csv"
    output.headers["Content-type"] = "text/csv"

    return output