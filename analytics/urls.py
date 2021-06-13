from django.urls import path

from analytics.views import (
    BotAnalyticsView, GeneralAnalyticsView, download_analytics
)

app_name = "analytics"

urlpatterns = [
    path("bot_analytics/", BotAnalyticsView.as_view(), name="bot-analytics"),
    path("general_analytics/",
         GeneralAnalyticsView.as_view(),
         name="general-analytics"),
    path("download_analytics/",
         download_analytics,
         name="download-analytics"),
]
