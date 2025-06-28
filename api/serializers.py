from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Project, Conversation, Message

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Optionally include more user info in the response
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = self.user.role
        return data

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', "member"),
        )
        return user


class ProjectSerializer(serializers.ModelSerializer):
    print("hi")
    creator = serializers.ReadOnlyField(source='creator.username')
    team_members = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(),
        required=False
    )
    roles = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'creator',
            'image',
            'stageColor',
            'category',
            'roles',
            'website',
            'teamSize',
            'team_members',
            'stage',
            'created_at',
            'updated_at'
        ]
class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['sender', 'timestamp']