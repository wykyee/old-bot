import logging
import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    ListView, DetailView, UpdateView, CreateView, DeleteView,
)

from telegram_api.api import (
    get_bot_info as tg_bot_info,
    get_webhook_info as tg_webhook_info,
    set_webhook_ajax as tg_set_webhook_ajax,
    unset_webhook_ajax as tg_remove_webhook_ajax

)
from telegram_api.handlers import (
    event_handler_tg
)
from viber_api.api import (
    get_bot_info as v_bot_info,
    set_webhook_ajax as v_set_webhook_ajax,
    remove_webhook_ajax as v_remove_webhook_ajax
)
from viber_api.handlers import (
    event_handler
)
from .forms import (
    BotUpdateForm, BotAddForm, SuperuserChannelForm,
    ModeratorChannelForm, ChannelFrontForm
)
from .mixins import ModeratorRequiredMixin, SuperuserRequiredMixin
from .models import Channel, Bot
from .services import (
    get_channel_by_slug, get_all_related_bots,
    get_all_available_channels_to_moderator,
    get_channel_to_json, extract_data,
    get_moderators_to_json,
)
from keyboards.services import get_actions_related_to_channel_by_obj


logger = logging.getLogger(__name__)


def root_view(request):
    return redirect("bots-management:channel-list")


def notfound(request, exception=None):
    """
    redirect to channel list if something raises Http404 or
    to login page, if user isn't logged in
    IF DEBUG = False
    """
    # TODO create normal 404 page to render it
    return redirect("bots-management:channel-list")


class ChannelListView(LoginRequiredMixin, ListView):
    """
    Only related to user channels will be displayed
    """
    model = Channel
    template_name = "bots_management/channel_list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        user = self.request.user
        context["channels"] = get_all_available_channels_to_moderator(user)
        return context


class ChannelDetailView(ModeratorRequiredMixin, DetailView):
    """
    Get info can only moderator or superuser.
    """
    model = Channel
    template_name = "bots_management/channel_details.html"
    context_object_name = "channel"

    def get_context_data(self, **kwargs) -> dict:
        context = super(ChannelDetailView, self).get_context_data()
        context["bots"] = get_all_related_bots(self.object)

        # show response of action with webhook
        show_webhook = self.request.GET.get("show_webhook", None)
        if show_webhook == "true":
            messenger = self.request.GET.get("messenger", None)

            if messenger == "viber":
                info = v_bot_info(self.object.viber_token)
                keys = ["status", "status_message"]
                webhook_info = {x: info[x] for x in keys}
                event_types = info.get("event_types")
                if event_types:
                    webhook_info["event_types"] = event_types
                else:
                    webhook_info["event_types"] = "webhook removed"
                context["webhook_info"] = webhook_info

            elif messenger == "telegram":
                webhook_info = tg_webhook_info(
                    self.object.telegram_token
                )
                if not webhook_info:
                    webhook_info = {"ok": False,
                                    "error_code": 404,
                                    "description": "Not Found"}
                context["webhook_info"] = webhook_info
        return context


class ChannelFullDetailView(ModeratorRequiredMixin, DetailView):
    """
    Get full info can only moderator or superuser.
    """
    model = Channel
    template_name = "bots_management/channel_details.html"
    context_object_name = "channel"

    def get_context_data(self, **kwargs) -> dict:
        context = super(ChannelFullDetailView, self).get_context_data(**kwargs)

        tg_token = self.object.telegram_token
        v_token = self.object.viber_token

        context["bots"] = get_all_related_bots(self.object)

        if v_token:
            context["viber_info"] = v_bot_info(v_token)

        if tg_token:
            context["telegram_info"] = tg_bot_info(tg_token)
            context["telegram_webhook"] = tg_webhook_info(tg_token)
        return context


class ChannelCreateView(LoginRequiredMixin, CreateView):
    """
    Channel can create anyone.
    """
    model = Channel
    template_name = "bots_management/channel_add.html"

    def get_form(self, *args, **kwargs):
        user = self.request.user
        if user.is_superuser:
            return SuperuserChannelForm(**self.get_form_kwargs())
        return ModeratorChannelForm(**self.get_form_kwargs(), user=user)

    def get_success_url(self):
        return reverse_lazy("bots-management:channel-detail", kwargs={
            "slug": self.request.POST["slug"]
        })


class ChannelUpdateView(ModeratorRequiredMixin, UpdateView):
    """
    Channel can update only moderator or superuser.
    """
    model = Channel
    template_name = "bots_management/channel_update.html"

    def get_form(self, *args, **kwargs):
        user = self.request.user
        if user.is_superuser:
            form = SuperuserChannelForm(**self.get_form_kwargs())
        else:
            form = ModeratorChannelForm(**self.get_form_kwargs(), user=user)
        actions = get_actions_related_to_channel_by_obj(self.object)
        if actions:
            form.fields["welcome_action"].queryset = actions
        return form

    def get_success_url(self):
        return reverse_lazy("bots-management:channel-detail", kwargs={
            "slug": self.request.POST["slug"]
        })


class ChannelDeleteView(SuperuserRequiredMixin, DeleteView):
    """
    Channel can delete only superuser.
    """
    model = Channel
    template_name = "bots_management/channel_delete.html"
    success_url = reverse_lazy("bots-management:channel-list")


class BotUpdateView(ModeratorRequiredMixin, UpdateView):
    """
    Bot can update only moderator or superuser.
    """
    model = Bot
    template_name = "bots_management/bot_update.html"

    def get_success_url(self):
        return reverse_lazy(
            "bots-management:channel-detail",
            kwargs={"slug": self.object.channel.slug}
        )

    def get_form(self, *args, **kwargs):
        channel = get_channel_by_slug(self.kwargs["slug"])
        if channel:
            return BotUpdateForm(**self.get_form_kwargs(), channel=channel)
        else:
            raise Http404


class BotCreateView(ModeratorRequiredMixin, CreateView):
    """
    Channel can create only moderator or superuser.
    """
    model = Bot
    template_name = "bots_management/bot_add.html"

    def get_success_url(self):
        return reverse_lazy(
            "bots-management:channel-detail",
            kwargs={"slug": self.object.channel.slug}
        )

    def get_form(self, form_class=None):
        channel = get_channel_by_slug(self.kwargs["slug"])
        if channel:
            return BotAddForm(**self.get_form_kwargs(), channel=channel)
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super(BotCreateView, self).get_context_data(**kwargs)
        context["channel"] = get_channel_by_slug(self.kwargs["slug"])

        return context


@csrf_exempt
def telegram_index(request, slug):
    """
        telegram request dispatcher
    """
    if request.method == "POST":
        incoming_data: dict = json.loads(request.body.decode("utf-8"))
        if settings.DEBUG:
            logger.warning(
                f"""\n {incoming_data} \n"""
            )
        event_handler_tg(incoming_data=incoming_data, channel_slug=slug)
        return HttpResponse(status=200)

    return HttpResponse(status=404)


@csrf_exempt
def viber_index(request, slug):
    """
        viber request dispatcher
    """
    if request.method == "POST":
        incoming_data: dict = json.loads(request.body.decode("utf-8"))
        if settings.DEBUG:
            logger.warning(
                f"""\n {incoming_data} \n"""
            )
        event_handler(incoming_data=incoming_data, channel_slug=slug)
        return HttpResponse(status=200)
    return HttpResponse(status=404)


def ajax_channels_update(request):
    """
        Create or update channel with ajax
    """
    if request.is_ajax() and request.method == "POST":
        data = extract_data(request)
        channel_id = data.pop('id')
        if channel_id:
            Channel.objects.update_or_create(
                id=channel_id,
                defaults=data,
            )
        else:
            Channel(**data).save()
        return HttpResponse(get_channel_to_json())
    else:
        raise Http404


def ajax_get_channels(request):
    """
        Get list of channels
    """
    if request.is_ajax():
        return HttpResponse(get_channel_to_json())
    return Http404


def channel_list_view(request):
    """
        Template for new front
    """
    form = ChannelFrontForm()
    return render(request, "bots_management/channels_new.html", {"form": form})


def ajax_webhook(request):
    """
        set webhook for messengers
    """
    if request.is_ajax():
        token = request.POST.get('token')
        host = request.META['HTTP_HOST']
        slug = request.POST.get('channel_url')
        messenger = request.POST.get('messenger')
        response = 'Оберіть месенджер'
        if messenger == 'viber':
            response = v_set_webhook_ajax(slug, host, token)
        elif messenger == 'telegram':
            response = tg_set_webhook_ajax(slug, host, token)
        return HttpResponse(json.dumps(response))
    return Http404


def ajax_unset_webhook(request):
    """
        unset webhook for messengers
    """
    if request.is_ajax():
        token = request.POST.get('token')
        messenger = request.POST.get('messenger')
        response = 'Оберіть месенджер'
        if messenger == 'viber':
            response = v_remove_webhook_ajax(token)
        elif messenger == 'telegram':
            response = tg_remove_webhook_ajax(token)
        return HttpResponse(json.dumps(response))
    return Http404


def ajax_get_moderators(request):
    """
        Get list of channels
    """
    if request.is_ajax():
        return HttpResponse(get_moderators_to_json())
    return Http404


def keyboards_constructor_view(request):
    """
        Template for new front
    """
    form = ChannelFrontForm()
    return render(
        request,
        "bots_management/keyboards_constructor.html",
        {"form": form}
    )


def statistics_view(request):
    """
        Template for new front
    """
    form = ChannelFrontForm()
    return render(request, "bots_management/statistics.html", {"form": form})
