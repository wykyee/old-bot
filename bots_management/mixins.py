from django.contrib.auth.mixins import AccessMixin

from bots_management.services import get_channel_by_slug


class ModeratorRequiredMixin(AccessMixin):
    """
    Raises 403 if user not in channel's moderators list and
    is not a superuser.
    """
    def dispatch(self, request, *args, **kwargs):
        channel = get_channel_by_slug(kwargs.get("slug"))

        if channel:
            if all([not request.user.is_superuser,
                    request.user not in channel.moderators.all()]):
                return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class SuperuserRequiredMixin(AccessMixin):
    """
    Raises 403 if user isn't a superuser.
    """
    def dispatch(self, request, *args, **kwargs):
        channel = get_channel_by_slug(kwargs.get("slug"))

        if channel:
            if not request.user.is_superuser:
                return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
