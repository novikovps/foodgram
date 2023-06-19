from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(
        max_length=150,
    )
    last_name = models.CharField(
        max_length=150,
    )
    email = models.EmailField(
        unique=True,
    )
    password = models.CharField(
        max_length=150,
    )

    REQUIRED_FIELDS = [
        "email",
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-pk"]

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, related_name="subscriber", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="author", on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.CheckConstraint(
                check=~models.Q(author=models.F("subscriber")),
                name="prevent_self_subscribe",
            ),
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscribe",
            ),
        ]
