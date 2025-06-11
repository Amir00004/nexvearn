from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.conf import settings



class User(AbstractUser):
    ROLE_CHOICES = (
        ('creator', 'Project Creator'),
        ('member', 'Team Member'),
        ('admin', 'Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
    

class Project(models.Model):
    STAGE_CHOICES = [
        ('brainstorming', 'Brainstorming'),
        ('development', 'Development'),
        ('launch', 'Launch'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_projects'
    )
    
    image = models.CharField(max_length=100)
    stageColor = models.CharField(max_length=20, default='blue')
    roles = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    website = models.URLField(blank=True, null=True)
    teamSize = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=100)
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        blank=True
    )
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='brainstorming')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class Conversation(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='conversations_started', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='conversations_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"Conversation between {self.user1} and {self.user2}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"