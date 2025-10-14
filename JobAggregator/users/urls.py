from tkinter.font import names

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from users.views import UserLogin

urlpatterns = [
    path('login/', UserLogin.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='main'), name='logout'),
]