from django.urls import path, include

from .views import (
    telegram_index, viber_index, ChannelListView,
    ChannelDetailView, ChannelFullDetailView, ChannelCreateView,
    ChannelUpdateView, ChannelDeleteView, BotUpdateView,
    BotCreateView, root_view, ajax_channels_update,
    ajax_get_channels, channel_list_view,
    ajax_webhook, ajax_get_moderators, ajax_unset_webhook,
    keyboards_constructor_view, statistics_view
)

app_name = "bots-management"

urlpatterns = [
    path("", root_view, name="root"),
    path("ajax_get_channels/",
         ajax_get_channels,
         name='ajax_get_channels'),
    path("ajax_get_moderators/",
         ajax_get_moderators,
         name='ajax_get_moderators'),
    path("ajax_channels_update/",
         ajax_channels_update,
         name='ajax_channels_update'),
    path("channels_new/",
         channel_list_view,
         name="channel-list-new"),
    path("ajax_webhook/",
         ajax_webhook,
         name="ajax_webhook"),
    path("ajax_unset_webhook/",
         ajax_unset_webhook,
         name="ajax_unset_webhook"),


    path("channels/",
         ChannelListView.as_view(),
         name="channel-list"),
    path("channel/<str:slug>/",
         ChannelDetailView.as_view(),
         name="channel-detail"),
    path("channel_full/<str:slug>/",
         ChannelFullDetailView.as_view(),
         name="channel-full-detail"),
    path("channel_create/",
         ChannelCreateView.as_view(),
         name="channel-create"),
    path("channel_delete/<str:slug>/",
         ChannelDeleteView.as_view(),
         name="channel-delete"),
    path("channel_update/<str:slug>/",
         ChannelUpdateView.as_view(),
         name="channel-update"),
    path("channel/<str:slug>/bot_create/",
         BotCreateView.as_view(),
         name="bot-create"),
    path("channel/<str:slug>/bot_update/<int:pk>/",
         BotUpdateView.as_view(),
         name="bot-update"),
    path("keyboards_new",
         keyboards_constructor_view,
         name="keyboards-new"),
    path("statistics_new",
         statistics_view,
         name="statistics-new"),

    # actions with keyboards, related to certain channel
    path("channel/<str:slug>/",
         include("keyboards.urls", namespace="keyboards")),

    # bots and subscribers' analytics
    path("channel/<str:slug>/",
         include("analytics.urls", namespace="analytics")),

    # subscribers and messages
    path("subscribers/",
         include("subscribers.urls", namespace="subscribers")),

    # bots` mailings
    path("channel/<str:slug>/",
         include("bots_mailings.urls", namespace="mailings")),

    path("telegram_prod/<str:slug>/", telegram_index),
    path("viber_prod/<str:slug>/", viber_index),
]
