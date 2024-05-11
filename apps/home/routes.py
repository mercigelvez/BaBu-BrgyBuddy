# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.chatbot.chat import get_response, preprocess_input
from flask import Blueprint, jsonify, request

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None

@blueprint.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON data'}), 400

    user_input = data.get('message')
    if not user_input:
        return jsonify({'error': 'Missing message parameter'}), 400

    cleaned_input = preprocess_input(user_input)
    response = get_response(cleaned_input)
    return jsonify({'answer': response})