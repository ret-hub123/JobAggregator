
from django.urls import path, include
from aggregator.views import Index, SearchVacantions, ResponseVacations, DataNotFound, FavouritesVacation, StatisticPage


urlpatterns = [
    path('', Index.as_view(), name='main'),
    path('search-vacantions/', SearchVacantions.as_view(), name='search_vacantions'),
    path('favourites-vacantions', FavouritesVacation.as_view(), name='favourites'),
    path('response-vacantions/', ResponseVacations.as_view(), name='response_vacantions'),
    path('statistics/', StatisticPage.as_view(), name='statistics'),
    path('data-not-found/', DataNotFound.as_view(), name='data_not_found'),
]