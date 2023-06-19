from django.contrib import admin, auth

from .models import Subscription, User


class UserAdmin(auth.admin.UserAdmin):
    list_display = ("pk", "username", "email", "first_name", "last_name")
    # fields = ('username', 'email', 'first_name',
    #           'last_name', 'password', 'is_active')
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": ("is_active", "is_staff", "is_superuser"),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "email",
                ),
            },
        ),
    )
    list_filter = ("email", "username")


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("pk", "subscriber", "author", "created")
    fields = ("subscriber", "author")


admin.site.register(User, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
