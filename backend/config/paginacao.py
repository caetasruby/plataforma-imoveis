from rest_framework.pagination import PageNumberPagination


class Paginacao(PageNumberPagination):
    """12 resultados por página; o cliente pode pedir até 100 com ?tamanho=."""
    page_size = 12
    page_size_query_param = "tamanho"
    max_page_size = 100
