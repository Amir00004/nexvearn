from django.shortcuts import render
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, ConversationSerializer, MessageSerializer, ProjectSerializer, UserRegisterSerializer
from .models import Project, Conversation, Message
from django.conf import settings
from django.shortcuts import redirect
from urllib.parse import urlencode
from rest_framework.decorators import api_view, permission_classes
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import HttpResponseRedirect

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return Response({"error": "Missing authorization code"}, status=400)

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_res = requests.post(token_url, data=token_data)
    token_json = token_res.json()

    if "id_token" not in token_json:
        return Response({"error": "Google token exchange failed", "details": token_json}, status=400)

    try:
        id_info = id_token.verify_oauth2_token(
            token_json["id_token"],
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except Exception as e:
        return Response({"error": "Invalid Google ID token", "details": str(e)}, status=400)

    email = id_info.get("email")
    name = id_info.get("name", "")

    if not email:
        return Response({"error": "Email is required from Google account"}, status=400)

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": name,
            "first_name": name,
            "role": "creator",  # default role
        }
    )

    if created:
        user.set_unusable_password()
        user.save()

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    # Create response with redirect
    response = HttpResponseRedirect("http://localhost:3000/home")  # update as needed

    # Set cookies (secure=True only in HTTPS)
    response.set_cookie(
        key="access_token",
        value=str(access),
        httponly=True,
        secure=False,  # Set to True in production
        samesite="Lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=False,  # Set to True in production
        samesite="Lax"
    )

    return response

@csrf_exempt
def google_login_redirect(request):
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    print(f"Redirecting to Google OAuth2: {base_url}?{urlencode(params)}")
    return redirect(f"{base_url}?{urlencode(params)}")


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            data = response.data
            refresh = data.get("refresh")
            access = data.get("access")

            # Set HttpOnly cookies
            response.set_cookie(
                key='access_token',
                value=access,
                httponly=True,
                secure=True,  # Use False for local dev (http), True for production (https)
                samesite='Lax',
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh,
                httponly=True,
                secure=True,
                samesite='Lax',
            )
        return response

from pprint import pprint

class ProjectListCreateView(generics.ListCreateAPIView):
    print("ProjectListCreateView initialized")
    def post(self, request, *args, **kwargs):
        print("\n===== DEBUGGING REQUEST =====")
        print("METHOD:", request.method)
        print("PATH:", request.path)
        print("HEADERS:")
        pprint(dict(request.headers))
        print("BODY (raw):", request.body)
        print("DATA (parsed):", request.data)
        print("USER:", request.user)
        print("COOKIES:", request.COOKIES)
        print("=============================\n")
        if request.user.is_authenticated:
            print("User is authenticated:", request.user.username)  
        return super().post(request, *args, **kwargs)
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class ProjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)