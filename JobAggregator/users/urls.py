from tkinter.font import names

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from users.views import UserLogin

from users.views import UsersCreate

urlpatterns = [
    path('login/', UserLogin.as_view(), name='login'),
    path('registration/', UsersCreate.as_view(), name='registration'),
    path('logout/', LogoutView.as_view(next_page='main'), name='logout'),
]