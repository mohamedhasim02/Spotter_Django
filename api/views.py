import json
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView 
from django.shortcuts import render
from django.views.generic import TemplateView
from .services.geo_service import *
from .services.folium_service import *
import pandas as pd
from functools import reduce
from django.conf import settings
from .serializers import RouteRequestSerializer

class GasStationMapInfoView(APIView):
    def get(self, request):
        location = [37.7749, -122.4194]  # San Francisco coordinates

        m = folium.Map(location=location, zoom_start=12)
        folium.Marker(location, popup="San Francisco").add_to(m)
        return HttpResponse(m._repr_html_())


    def post(self, request):
        try:          
            serializer = RouteRequestSerializer(data=request.data)
            if(not serializer.is_valid()):
                    return HttpResponse(
                        json.dumps({"errors": serializer.errors}),
                        content_type="application/json",
                        status=400
                    )
            
            validated_data =  serializer.validated_data

            total_fuel_price, map = resolve_route_fuel_request(validated_data)

            response = json.dumps({
                "total_fuel_price": total_fuel_price,
                "map": map._repr_html_() 
            })

            return HttpResponse(response, status=200)

        except Exception as e:
            return HttpResponse({"error": f"Internal server error"}, status=500)
            
       

class GasStationMapView(APIView):
    def post(self, request):
    
        try:          
            serializer = RouteRequestSerializer(data=request.data)
            if(not serializer.is_valid()):
                    return HttpResponse(
                        json.dumps({"errors": serializer.errors}),
                        content_type="application/json",
                        status=400
                    )
            
            validated_data =  serializer.validated_data
            total_fuel_price, map = resolve_route_fuel_request(validated_data)
            
            return render(request, 'api/map_template.html', {
            'map': map._repr_html_(),
            'total_fuel_price': total_fuel_price,
        })

        except Exception as e:
            return HttpResponse({"error": f"Internal server error"}, status=500)


