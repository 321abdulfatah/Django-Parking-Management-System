import os
import json
import cv2
import numpy as np
import base64

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser

from django.contrib.auth import login
from django.conf import settings
from django.core.files.storage import default_storage

from .models import Parking
from .serializers import RegisterSerializer, LoginSerializer, ParkingSerializer, UserSerializer

from .parking_management import ParkingManagement, get_min_coords

parking_managers = {}  # {parking_id: parking_manager_object}

class RegisterView(APIView):
    def post(self, request):
        data = {'user':{},'parking':{}}
        for key, value in request.data.items():
            if key in ['username','phone_number','password']:
                data['user'][key] = value
            else:
                data['parking'][key] = value
                
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            data = serializer.save()
            user = data['user']
            parking = data['parking']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            # Construct response data
            response_data = {
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user_id': user.id,
                'phone_number': user.phone_number,
                'parking_name': parking.parking_name
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    """
    API endpoint for user login with token authentication.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)  
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user_id': user.id,
                'phone_number': user.phone_number,
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckAnnotationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if user has associated parking
        if not hasattr(user, 'parking'):
            return Response(
                {"error": "Parking not found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        parking = user.parking

        # Check if parking has an image
        if not parking.image:
            return Response(
                {"error": "No image available for this parking"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Construct annotation filename and path
        image_basename = os.path.basename(str(parking.image))
        annotation_filename = f"{image_basename}.json"
        
        # Use Django's storage system for flexibility
        annotation_path = os.path.join('annotations', annotation_filename)
        exists = default_storage.exists(annotation_path)

        return Response({
            "exists": exists,
            "annotation_file": annotation_filename,
            "message": "Annotation file exists" if exists else "Annotation file not found"
        }, status=status.HTTP_200_OK)


class UserParkingView(generics.RetrieveAPIView):
    serializer_class = ParkingSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Get the parking linked to the current user
        return self.request.user.parking

class UserParkingImageView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user

        # Check if user has associated parking
        if not hasattr(user, 'parking'):
            return Response(
                {"error": "Parking not found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        parking = user.parking

        # Check if parking has an image
        if not parking.image:
            return Response(
                {"error": "No image available for this parking"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        full_image_url = request.build_absolute_uri(parking.image.url)
        return Response({"image": full_image_url},status=status.HTTP_200_OK)

class CreateAnnotationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check user has parking with image
        if not hasattr(user, 'parking'):
            return Response(
                {"error": "Parking not found for user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        parking = user.parking
        if not parking.image:
            return Response(
                {"error": "Parking has no associated image"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get annotation data from request
        annotation_data = request.data
        if not annotation_data:
            return Response(
                {"error": "Missing annotations data"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # sort points before save it from up to down and left to right
        sorting_annotation_data = sorted(annotation_data, key=get_min_coords)
        
        annotation_dir = 'annotations'    
        # Create annotation file
        image_basename = os.path.basename(str(parking.image))
        filename = f"{image_basename}.json"
        file_path = os.path.join(annotation_dir, filename)

        # Save JSON data
        with default_storage.open(file_path, 'w') as f:
            json.dump(sorting_annotation_data, f)
    
        # Assuming 'model' and 'json_file' are stored in the 'media' directory
        model_path = default_storage.path('model/yolov8s.pt')  # Path to the model file
        json_file_path = default_storage.path(file_path)  # Path to the JSON file

        # Initialize parking management object
        parking_managers[parking.id] = ParkingManagement(
                                            model=model_path,  # path to model file
                                            json_file=json_file_path,  # path to parking annotations file
                                            price_per_hour=parking.price_per_hour
                                        )
    
        return Response({
            "status": "success",
            "file": filename,
            "message": "Annotation saved successfully"
        }, status=status.HTTP_201_CREATED)
    
class ProcessImageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check user has parking with image
        if not hasattr(user, 'parking'):
            return Response(
                {"error": "Parking not found for user"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        parking = user.parking

        if not parking.image:
            return Response(
                {"error": "Parking has no associated image"},
                status=status.HTTP_400_BAD_REQUEST
            )

        annotation_dir = 'annotations'    
        # Create annotation file
        image_basename = os.path.basename(str(parking.image))
        filename = f"{image_basename}.json"
        file_path = os.path.join(annotation_dir, filename)

        if not default_storage.exists(file_path):
            return Response(
                {"error": "Parking has no annotation file, you must create annotation for your parking."},
                status=status.HTTP_400_BAD_REQUEST
            )


        # Assuming 'model' are stored in the 'media' directory
        model_path = default_storage.path('model/yolov8s.pt')  # Path to the model file
        json_file_path = default_storage.path(file_path)

        # Initialize parking management object
        if parking.id not in parking_managers:
            parking_managers[parking.id] = ParkingManagement(
                                                model=model_path,  # path to model file
                                                json_file=json_file_path,  # path to parking annotations file
                                                price_per_hour=parking.price_per_hour
                                            )

        # Check if parking has an instance of parking management
        if parking.id not in parking_managers:
            return Response(
                {"error": "You must Create Annotaion for your park before monitoring"},
                status=status.HTTP_404_NOT_FOUND
            )        

        image_file = request.FILES.get('image')

        if not image_file:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        ## read image
        image_data = image_file.read()
        image_array = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        processed_image = parking_managers[parking.id].process_data(image)

        ## Updata available for parking
        if parking_managers[parking.id].pr_info['Available']:
            parking.is_available = True
        
        else:
            parking.is_available = False

        # save image wit parking name for return to mobile app
        parking_images_dir = 'parking_images'    
        # Create image file
        image_name = str(parking.name)+ ".jpg"
        image_path = os.path.join(parking_images_dir, image_name)
        cv2.imwrite(default_storage.path(image_path), processed_image)
        
        _, buffer = cv2.imencode('.jpg', processed_image)
        processed_image_base64 = base64.b64encode(buffer).decode('utf-8')

        return Response({
                'processed_image': processed_image_base64,
                'spots': parking_managers[parking.id].spots,
                'pr_info': parking_managers[parking.id].pr_info,
            }, status=status.HTTP_200_OK)
    


########################################################################################
## Mobile Endpoints 
########################################################################################

class MobileRegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            # Construct response data
            response_data = {
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user_id': user.id,
                'phone_number': user.phone_number
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MobileLoginView(APIView):
    """
    API endpoint for user login with token authentication.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)  
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh_token': str(refresh),
                'access_token': str(refresh.access_token),
                'user_id': user.id,
                'phone_number': user.phone_number,
            }, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ParkingListView(generics.ListAPIView):
    queryset = Parking.objects.all()
    serializer_class = ParkingSerializer

class ParkingImageView(APIView):
    def get(self, request, *args, **kwargs):
        # Extract parking name from the request query parameters
        parking_name = request.query_params.get('parking_name', None)

        # Check if parking name is provided
        if not parking_name:
            return Response({"error": "Parking name is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the parking exists in the database
        try:
            parking = Parking.objects.get(parking_name=parking_name)
        except Parking.DoesNotExist:
            return Response({"error": "Parking not found."}, status=status.HTTP_404_NOT_FOUND)

        # Define the image directory and file path
        parking_images_dir = 'parking_images'
        image_name = f"{parking_name}.jpg"
        image_path = default_storage.path(os.path.join(parking_images_dir, image_name))

        # Check if the image file exists
        if not os.path.exists(image_path):
            return Response({"error": "Image not found."}, status=status.HTTP_404_NOT_FOUND)

        # Read the image file and encode it to Base64
        try:
            with open(image_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return Response({"error": "Failed to read or encode the image.", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get the spots data for the parking
        spots = parking_managers.get(parking.id, {}).get('spots', {})

        # Return the Base64-encoded image and spots data in the response
        return Response({
            "image_base64": encoded_image,
            "spots": spots
        }, status=status.HTTP_200_OK)