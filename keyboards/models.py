from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse


class Keyboard(models.Model):
    """
    Model for representing keyboard, that has global parameters for buttons.
    """
    name = models.CharField(max_length=120, verbose_name="Назва")
    channel = models.ForeignKey(
        to="bots_management.Channel", on_delete=models.CASCADE,
        verbose_name="Канал", related_name="keyboards"
    )
    description = models.CharField(
        max_length=240, verbose_name="Опис", null=True, blank=True
    )
    bg_color = models.CharField(
        verbose_name="Колір фону (тільки Viber)",
        null=True, blank=True, max_length=7
    )

    class Meta:
        verbose_name = "Клавіатура"
        verbose_name_plural = "Клавіатури"
        ordering = ["-channel__id", "pk"]
        unique_together = [["channel", "name"]]

    def __str__(self) -> str:
        return f"Клавіатура: {self.name}"

    def get_keyboard_params(self) -> dict:
        color = self.bg_color if self.bg_color else "#8074D6"
        data = {
            "Type": "keyboard",
            "DefaultHeight": False,
            "BgColor": color,
            "Buttons": self.get_viber_buttons()
        }
        return data

    def get_viber_buttons(self) -> list:
        all_buttons = self.get_sorted_by_position_buttons_list()
        buttons_with_params = [
            btn.get_viber_params() for btn in all_buttons
        ]
        return buttons_with_params

    def get_telegram_buttons(self) -> list:
        all_buttons = self.buttons.all()
        rows = set(all_buttons.values_list('tg_row', flat=True))
        buttons = []
        for i in rows:
            tmp = all_buttons.filter(tg_row=i)
            if tmp:
                tmp = sorted(tmp, key=lambda btn: btn.position)
                buttons.append(tmp)
        return buttons

    def get_sorted_by_position_buttons_list(self) -> list:
        return sorted(self.buttons.all(), key=lambda btn: btn.position)

    def get_absolute_url(self):
        return reverse(
            "bots-management:keyboards:keyboard-detail",
            kwargs={"slug": self.channel.slug,
                    "pk": self.pk})

    def get_update_url(self):
        return reverse(
            "bots-management:keyboards:keyboard-update",
            kwargs={"slug": self.channel.slug,
                    "pk": self.pk})

    def get_delete_url(self):
        return reverse(
            "bots-management:keyboards:keyboard-delete",
            kwargs={"slug": self.channel.slug,
                    "pk": self.pk})

    def get_create_button_url(self):
        return reverse(
            "bots-management:keyboards:button-create",
            kwargs={"slug": self.channel.slug,
                    "pk": self.pk})


class Action(models.Model):
    """
    Model for representing actions that have certain keyboards.
    Each button has its own action. When we press button we should
    get Action.text back to write it to user.
    Each action has its own keyboard that will be displayed after
    pressing button.
    """
    name = models.CharField(max_length=120, verbose_name="Назва")
    keyboard_to_represent = models.ForeignKey(
        to=Keyboard, on_delete=models.CASCADE,
        verbose_name="Клавіатура для відображення після дії"
    )
    ACTION_TYPES = (
        ("text", "text"),
        ("picture", "picture"),
        ("url", "url"),
        ("video", "video"),
        ("file", "file"),
        ("location", "location"),
        ("sticker", "sticker"),
        ("none", "none"),
    )
    action_type = models.CharField(
        verbose_name="Тип події", max_length=8, choices=ACTION_TYPES
    )
    text = models.TextField(
        verbose_name="Текст повідомлення користувачу",
        blank=True, null=True
    )
    picture = models.ImageField(
        upload_to="image", blank=True, null=True, verbose_name="Фотографія"
    )
    url = models.URLField(
        max_length=200, blank=True, null=True, verbose_name="URL"
    )
    video = models.FileField(
        upload_to="video", blank=True, null=True, verbose_name="Відео"
    )
    file = models.FileField(
        upload_to="file", blank=True, null=True, verbose_name="Файл"
    )
    location_latitude = models.FloatField(
        verbose_name="Широта", blank=True, null=True,
    )
    location_longitude = models.FloatField(
        verbose_name="Довгота", blank=True, null=True,
    )
    sticker_id = models.CharField(
        "ID стікеру(у форматі vider_st_id//telegram_st_id)",
        null=True, blank=True, max_length=150,
    )
    description = models.TextField("Опис", blank=True, null=True)
    is_menu_action = models.BooleanField(
        "Виступає, як подія, що відображає меню", default=False
    )

    class Meta:
        unique_together = [["keyboard_to_represent", "name"]]
        verbose_name = "Подія"
        verbose_name_plural = "Події"
        ordering = ["keyboard_to_represent__id", "name"]

    def __str__(self) -> str:
        return f"Подія: {self.name}"

    def get_absolute_url(self):
        return reverse(
            "bots-management:keyboards:action-detail",
            kwargs={"slug": self.keyboard_to_represent.channel.slug,
                    "pk": self.pk})

    def get_update_url(self):
        return reverse(
            "bots-management:keyboards:action-update",
            kwargs={"slug": self.keyboard_to_represent.channel.slug,
                    "pk": self.pk})

    def get_delete_url(self):
        return reverse(
            "bots-management:keyboards:action-delete",
            kwargs={"slug": self.keyboard_to_represent.channel.slug,
                    "pk": self.pk})


class Button(models.Model):
    """
    Model for representing button. Each keyboard can have
    lots of buttons and buttons can be same in different keyboards.
    """
    keyboard = models.ForeignKey(
        to=Keyboard, on_delete=models.CASCADE,
        verbose_name="Клавіатури", related_name="buttons"
    )
    action = models.ForeignKey(
        to=Action, on_delete=models.CASCADE,
        verbose_name="Подія, яка трапиться"
    )
    name = models.CharField(max_length=120, verbose_name="Назва")
    text = models.CharField(max_length=68, verbose_name="Текст кнопки")
    height = models.PositiveSmallIntegerField(
        verbose_name="Висота 1-2 (V)",
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        default=1
    )
    width = models.PositiveSmallIntegerField(
        verbose_name="Ширина 1-6 (V)",
        validators=[MinValueValidator(1), MaxValueValidator(6)],
        default=3
    )
    position = models.SmallIntegerField(
        verbose_name="Позиція кнопки", validators=[MinValueValidator(1)],
    )

    # for viber api
    V_ALIGN = (("top", "top"), ("middle", "middle"), ("bottom", "bottom"))
    H_ALIGN = (("left", "left"), ("center", "center"), ("right", "right"))
    TEXT_SIZE = (
        ("small", "small"),
        ("regular", "regular"),
        ("large", "large"),
    )
    ACTION_TYPE = (
        ("reply", "reply"),
        ("open-url", "open-url"),
        ("location-picker", "location-picker"),
        ("share-phone", "share-phone"),
        ("none", "none"),
    )
    text_v_align = models.CharField(
        verbose_name="(V) Вирівнювання по ветикалі", null=True, blank=True,
        choices=V_ALIGN, max_length=6
    )
    text_h_align = models.CharField(
        verbose_name="(V) Вирівнювання по горизонталі", null=True, blank=True,
        choices=H_ALIGN, max_length=6
    )
    text_size = models.CharField(
        verbose_name="(V) Розмір тексту ", null=True, blank=True,
        choices=TEXT_SIZE, max_length=7
    )
    bg_color = models.CharField(
        verbose_name="(V) Колір фону", null=True, blank=True, max_length=7
    )
    action_type = models.CharField(
        "Тип кнопки", choices=ACTION_TYPE,
        max_length=15, null=True, blank=True
    )

    description = models.CharField(
        max_length=256, verbose_name="Опис", null=True, blank=True
    )
    # for tg api
    tg_row = models.PositiveSmallIntegerField(
        verbose_name="№ рядка",
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        default=1
    )

    class Meta:
        verbose_name = "Кнопка"
        verbose_name_plural = "Кнопки"
        ordering = ["-keyboard__id", "position"]
        unique_together = [["keyboard", "position"], ["keyboard", "name"]]

    def __str__(self) -> str:
        return f"Кнопка: {self.name}"

    def get_viber_params(self) -> dict:
        """
        Returns dict with ViberAPI params for certain button.
        """
        data = {
            "Columns": self.width,
            "Rows": self.height,
            "Text": self.text,
            "ActionType": self.action_type if self.action_type else "reply",
            "ActionBody": self.text,
            "BgColor": self.bg_color if self.bg_color else "#FFFAFA",
            "TextVAlign": self.text_v_align if self.text_v_align else "middle",
            "TextHAlign": self.text_h_align if self.text_h_align else "center",
            "TextSize": self.text_size if self.text_size else "regular",
        }
        # TODO make it more flexible and customizable
        if self.action_type == "open-url":
            data["ActionBody"] = "tel:102"
            data["OpenURLType"] = "external"
            data["OpenURLMediaType"] = "not-media"
            data["InternalBrowser"] = {
                "Mode": "fullscreen",
                "CustomTitle": "Your Title",
            }

        return data

    def params_for_template(self) -> dict:
        if self.text_size:
            if self.text_size == "small":
                ts = 11
            elif self.text_size == "regular":
                ts = 15
            else:
                ts = 20
        else:
            ts = 18
        d = {
            "width": self.width * 2,
            "height": self.height * 40,
            "text_size": ts
        }
        return d

    def v_align_for_template(self) -> int:
        h = 0
        if self.text_v_align == "bottom":
            h = 40 if self.height == 2 else 10
        if self.text_v_align == "middle":
            h = 20 if self.height == 2 else 5
        return h

    def get_update_url(self):
        return reverse(
            "bots-management:keyboards:button-update",
            kwargs={"slug": self.keyboard.channel.slug,
                    "pk": self.keyboard.pk,
                    "pk_button": self.pk})

    def get_delete_url(self):
        return reverse("bots-management:keyboards:button-delete",
                       kwargs={"slug": self.keyboard.channel.slug,
                               "pk": self.keyboard.pk,
                               "pk_button": self.pk})


class IdFilesInMessenger(models.Model):
    """ Model for implement mass mailing media"""
    action = models.OneToOneField(
        to=Action, on_delete=models.CASCADE,
        verbose_name="Подія, з медіа"
    )
    path_media_tg = models.CharField(
        "Локальне місце зберігання",
        max_length=250
    )
    telegram_id = models.CharField(
        "Telegram id",
        max_length=150
    )
    token_tg = models.CharField(
        "Токен", max_length=150, default=None
    )