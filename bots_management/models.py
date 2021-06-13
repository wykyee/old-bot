from typing import Union

from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse


class Channel(models.Model):
    """
    Model for representing channel.
    Each channel has its own bots with own tokens.
    We can crete webhooks using slugs of each model.
    """
    name = models.CharField("Назва", max_length=128, unique=True)
    slug = models.SlugField("URL", max_length=128, unique=True)
    moderators = models.ManyToManyField(get_user_model(), blank=True,
                                        verbose_name="Модератори")

    is_media_allowed = models.BooleanField(
        "Дозволити обробку медія від користувача", default=True
    )
    is_geo_allowed = models.BooleanField(
        "Дозволити обробку геолокації від користувача", default=False
    )
    is_mailing_allowed = models.BooleanField(
        "Дозволити розсилку без підтвердження адміна", default=True
    )
    welcome_action = models.ForeignKey(
        to="keyboards.Action", on_delete=models.DO_NOTHING,
        verbose_name="Привітальне повідомлення", blank=True,
        null=True, default=None
    )
    description = models.CharField("Опис", max_length=250,
                                   blank=True, null=True)

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Канали"
        db_table = "channel"

    def __str__(self) -> str:
        return f"{self.name}"

    def get_absolute_url(self) -> str:
        return reverse("bots-management:channel-detail",
                       kwargs={"slug": self.slug})

    def get_full_detail_url(self) -> str:
        return reverse("bots-management:channel-full-detail",
                       kwargs={"slug": self.slug})

    def get_update_url(self) -> str:
        return reverse("bots-management:channel-update",
                       kwargs={"slug": self.slug})

    def get_delete_url(self) -> str:
        return reverse("bots-management:channel-delete",
                       kwargs={"slug": self.slug})

    @property
    def viber_token(self) -> Union[str, None]:
        return self.viber_bot.token if self.viber_bot else None
        # try:
        #     return self.bots.get(messenger="viber").token
        # except Bot.DoesNotExist:
        #     return

    @property
    def viber_bot(self) -> Union[object, None]:
        return self.bots.filter(messenger="viber").first()
        # try:
        #     return self.bots.get(messenger="viber")
        # except Bot.DoesNotExist:
        #     return

    @property
    def telegram_token(self) -> Union[str, None]:
        return self.telegram_bot.token if self.telegram_bot else None
        # try:
        #     return self.bots.get(messenger="telegram").token
        # except Bot.DoesNotExist:
        #     return

    @property
    def telegram_bot(self) -> Union[object, None]:
        return self.bots.filter(messenger="telegram").first()
        # try:
        #     return self.bots.get(messenger="telegram")
        # except Bot.DoesNotExist:
        #     return


class Bot(models.Model):
    """
    Model for representing bot.
    For now we work only with viber and telegram bots. If we
    want to add new messenger in the future, just add it in choices.
    """
    messengers = (
        ("telegram", "telegram"),
        ("viber", "viber"),
    )
    channel = models.ForeignKey(
        to=Channel, on_delete=models.CASCADE,
        related_name="bots", verbose_name="Назва каналу"
    )
    messenger = models.CharField("Мессенджер", max_length=20,
                                 choices=messengers)
    token = models.CharField("Токен", max_length=150, unique=True)
    description = models.CharField("Опис", max_length=250,
                                   blank=True, null=True)

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боти"
        db_table = "bot"
        unique_together = [["channel", "messenger"]]

    def __str__(self) -> str:
        return f"{self.messenger.upper()} --- {self.channel.name}"

    def get_update_url(self) -> str:
        return reverse("bots-management:bot-update",
                       kwargs={"pk": self.pk,
                               "slug": self.channel.slug})
