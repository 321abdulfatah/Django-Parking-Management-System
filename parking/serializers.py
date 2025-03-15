from rest_framework import serializers
from .models import User, Parking

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'phone_number', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_phone_number(self, value):
        if not value.startswith('09') or len(value) != 10 or value[2] not in ['3', '4', '5', '6', '8', '9']:
            raise serializers.ValidationError("Invalid phone number")
        return value

class ParkingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parking
        fields = ['parking_name', 'latitude', 'longitude', 'price_per_hour', 'image']

    def get_image_url(self, obj):
        if obj.image:
            return self.context['request'].build_absolute_uri(obj.image.url)
        return None

class RegisterSerializer(serializers.Serializer):
    user = UserSerializer()
    parking = ParkingSerializer()

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        parking_data = validated_data.pop('parking')
        user = User.objects.create_user(**user_data)
        parking = Parking.objects.create(user=user, **parking_data)
        return {'user': user, 'parking': parking}
    

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        if phone_number and password:
            user = User.objects.filter(phone_number=phone_number).first()
            if user and user.check_password(password):
                data['user'] = user
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'phone_number' and 'password'.")

        return data