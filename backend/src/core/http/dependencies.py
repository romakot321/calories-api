from src.core.http.client import IHttpClient, AsyncHttpClient


def get_http_client() -> IHttpClient:
    return AsyncHttpClient()
