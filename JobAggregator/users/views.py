from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.urls import reverse_lazy

from users.forms import LoginUserForm


# Create your views here.


class UserLogin(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': "Авторизация"}

