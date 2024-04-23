# -*- encoding: utf-8 -*-
"""

"""

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm, SignUpForm
from django.contrib.auth import authenticate
from django.core.mail import send_mail


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg = 'User created - please <a href="/login">login</a>.'
            success = True

            return redirect("/login/")

        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        user = authenticate(username=email)

        if user:
            send_password_reset_email(user)
            # Optionally, send a custom success message
            message = 'An email has been sent to your registered email address with instructions to reset your password.'
            return render(request, 'accounts/forgot_password_done.html', {'message': message})
        else:
            # Optionally, handle invalid email case (security best practice)
            message = 'The email address you entered is not associated with an account.'
            return render(request, 'accounts/forgot_password.html', {'message': message})
    else:
        return render(request, 'accounts/forgot_password.html')