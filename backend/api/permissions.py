from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    "Разрешение на редактирование объекта только в случае,"
    "когда user является владельцем или суперпользователем."

    # Проверка только на уровне объекта, т.к. в RecipeViewSet данные разрешения
    # используются только в случае обновления или удаления рецепта.
    # В других случах используется
    # permission_classes = IsAuthenticatedOrReadOnly.

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.is_superuser:
            return True
        return request.user == obj.author
