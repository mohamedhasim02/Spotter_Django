from django.contrib import admin
from django.urls import path
from .views import GasStationMapInfoView, GasStationMapView

urlpatterns = [
  path('gas_stations/map/info', GasStationMapInfoView.as_view(), name='gas_station_info_map'),
  path('gas_stations/map/', GasStationMapView.as_view(), name='gas_station_map'),

]
