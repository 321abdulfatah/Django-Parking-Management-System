from django.urls import path
from .views import (RegisterView, LoginView, ParkingListView, 
                    CheckAnnotationsView, CreateAnnotationView, 
                    UserParkingView, UserParkingImageView,
                    ProcessImageView, MobileRegisterView,
                    MobileLoginView, ParkingImageView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Check annotation existence
    path('check-annotations/', CheckAnnotationsView.as_view(), name='check-annotations'),
    # Create new annotation
    path('create-annotations/', CreateAnnotationView.as_view(), name='create-annotations'),
    
    path('my-parking/', UserParkingView.as_view(), name='user-parking'),
    path('my-parking/image/', UserParkingImageView.as_view(), name='user-parking-image'),

    path('process-image/', ProcessImageView.as_view(), name='process-image'),

    ## Mobile Section
    path('register-mobile/', MobileRegisterView.as_view(), name='register-mobile'),
    path('login-mobile/', MobileLoginView.as_view(), name='login-mobile'),
    path('parking/', ParkingListView.as_view(), name='parking-list'),
    path('parking/image/', ParkingImageView.as_view(), name='parking-image'),

]