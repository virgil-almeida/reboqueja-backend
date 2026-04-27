from rest_framework.pagination import PageNumberPagination


class HistoricoPagination(PageNumberPagination):
    page_size = 10
