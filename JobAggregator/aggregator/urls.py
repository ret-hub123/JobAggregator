from tkinter.font import names

from django.contrib import admin
from django.urls import path, include
from aggregator.views import Index, SearchVacantions, ResponseVacations, DataNotFound



urlpatterns = [
    path('', Index.as_view(), name='main'),
    path('search-vacantions/', SearchVacantions.as_view(), name='search_vacantions'),
    path('response-vacantions/', ResponseVacations.as_view(), name='response_vacantions'),
    path('data-not-found/', DataNotFound.as_view(), name='data_not_found'),
]