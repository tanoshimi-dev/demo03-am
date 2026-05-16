from django.utils import timezone

from .models import Account, AccountSession


class PortalSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.account = None
        if request.user.is_authenticated:
            try:
                request.account = request.user.account
            except Account.DoesNotExist:
                request.account = None

        response = self.get_response(request)

        account = getattr(request, "account", None)
        if account is not None:
            now = timezone.now()
            Account.objects.filter(pk=account.pk).update(last_seen_at=now)
            session_key = request.session.session_key
            if session_key:
                AccountSession.objects.filter(
                    session_key=session_key,
                    account=account,
                    ended_at__isnull=True,
                ).update(last_seen_at=now)

        return response
