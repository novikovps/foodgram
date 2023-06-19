from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    "Ограничение на количество элементов на странице."

    page_size_query_param = "limit"
