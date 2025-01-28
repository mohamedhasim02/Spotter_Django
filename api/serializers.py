from rest_framework import serializers

from api.services.geo_service import is_within_us



class CoordinatesSerializer(serializers.Serializer):
    longitude = serializers.FloatField(required=True)
    latitude = serializers.FloatField(required=True)

    def validate(self, data):
        lat = data.get("latitude")
        lon = data.get("longitude")

        # Validate if the coordinates are within the U.S.
        if not is_within_us(lat, lon):
            raise serializers.ValidationError("Coordinates are not within the United States.")
        
        return data

class RouteRequestSerializer(serializers.Serializer):
    start_coordinates = CoordinatesSerializer(required=True)
    end_coordinates = CoordinatesSerializer(required=True)
    car_mpg = serializers.IntegerField(required=True)
    car_max_miles = serializers.IntegerField(required=True)


#reference
# class CreateWorkLogSerializer(serializers.Serializer):
#     start_coordinates = serializers.IntegerField(required=True)
#     end_coordinates = serializers.FloatField(required=True)

#     def validate_hours_logged(self, value):
#         if value <= 0:
#             raise serializers.ValidationError("Hours logged must be greater than 0.")
#         return value

#     def validate(self, data):
#         if data['hours_logged'] > 24:
#             raise serializers.ValidationError("Hours logged cannot exceed 24 in a day.")
#         return data
