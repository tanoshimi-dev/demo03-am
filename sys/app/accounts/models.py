from django.contrib.auth.models import User
from django.db import models


class AppRole(models.Model):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="account")
    portal_subject = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    email = models.EmailField()
    is_portal_active = models.BooleanField(default=True)
    roles = models.ManyToManyField(AppRole, blank=True, related_name="accounts")
    last_handover_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_name", "portal_subject"]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.portal_subject})"


class AccountSession(models.Model):
    SOURCE_DEV_HEADER = "dev-header"
    SOURCE_PORTAL_HEADER = "portal-header"
    SOURCE_PORTAL_JWT = "portal-jwt"
    SOURCE_CHOICES = [
        (SOURCE_DEV_HEADER, "Dev header"),
        (SOURCE_PORTAL_HEADER, "Portal header"),
        (SOURCE_PORTAL_JWT, "Portal JWT cookie"),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, unique=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    user_agent = models.CharField(max_length=255, blank=True)
    remote_addr = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_seen_at"]

    def __str__(self) -> str:
        return f"{self.account.display_name} [{self.session_key}]"
