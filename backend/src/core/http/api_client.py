import json as json_lib
from io import BytesIO
from typing import Type, Literal, TypeVar, Callable, Awaitable
from urllib.parse import urljoin

import aiohttp
from loguru import logger
from pydantic import BaseModel, ValidationError

from src.core.http.client import IHttpClient
from src.core.http.exceptions import HttpApiRequestException, HttpApiResponseException

T = TypeVar("T", bound=BaseModel)


class AuthMixin:
    token: str | None

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}


class ApiResponse(BaseModel):
    cookies: dict
    data: dict | list
    headers: dict


class HttpApiClient(AuthMixin):
    def __init__(
        self,
        client: IHttpClient,
        source_url: str,
        headers: dict | None = None,
        cookies: dict | None = None,
        token: str | None = None,
    ):
        self.token = token
        self.client = client
        self.source_url = source_url
        self.headers = {**(headers or {}), **self.auth_headers}
        self.cookies = cookies or {}

    def validate_response(self, response: dict, validator: Type[T]) -> T:
        try:
            return validator.model_validate(response)
        except ValidationError as e:
            raise HttpApiResponseException(e) from e

    async def request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        **kwargs,
    ) -> ApiResponse:
        headers = headers or {}
        cookies = cookies or {}
        request_params = {
            "url": urljoin(self.source_url, endpoint),
            "headers": {**self.headers, **headers},
            "json": json,
            "params": params,
            "cookies": {**self.cookies, **cookies},
            **kwargs,
        }

        func: Callable[..., Awaitable[aiohttp.ClientResponse]] = getattr(self.client, method.lower())
        response = await func(**request_params)
        if not response.ok:
            raise HttpApiRequestException(await response.text())

        try:
            data = await response.json()
        except aiohttp.ContentTypeError as e:
            try:
                data = json_lib.loads(await response.text())
            except json_lib.JSONDecodeError:
                raise HttpApiResponseException("Empty response") from e

        response_data = ApiResponse(
            data=data,
            cookies=dict(response.cookies.items()),
            headers=dict(response.headers.items()),
        )

        if len(str(response_data)) > 1000:
            logger.debug(f"Get api response to {endpoint}: <truncated>")
        else:
            logger.debug(f"Get api response to {endpoint}: {response_data}")
        return response_data

    async def multipart_request(
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        endpoint: str,
        data: dict | None = None,
        files: list[tuple[str, BytesIO]] | None = None,
        params: dict | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        **kwargs,
    ) -> ApiResponse:
        """
        Send multipart/form-data request with JSON data encoded as form fields.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Dictionary with form data (will be encoded as JSON strings)
            files: List of tuples (field_name, file_object) for file uploads
            params: Query parameters
            headers: Additional headers
            cookies: Additional cookies
            **kwargs: Additional parameters for aiohttp request

        Returns:
            ApiResponse with parsed JSON response
        """
        headers = headers or {}
        cookies = cookies or {}

        # Create multipart form data
        form_data = aiohttp.FormData()

        # Add JSON data as form fields (encode as JSON strings)
        if data:
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    # Encode complex objects as JSON strings
                    form_data.add_field(key, json_lib.dumps(value), content_type="application/json")
                else:
                    # Add simple values as strings
                    form_data.add_field(key, str(value))

        # Add files
        if files:
            for field_name, file_obj in files:
                file_obj.seek(0)
                form_data.add_field(field_name, file_obj, filename="image.jpg")

        request_params = {
            "url": urljoin(self.source_url, endpoint),
            "headers": {**self.headers, **headers},
            "data": form_data,
            "params": params,
            "cookies": {**self.cookies, **cookies},
            **kwargs,
        }

        func: Callable[..., Awaitable[aiohttp.ClientResponse]] = getattr(self.client, method.lower())
        response = await func(**request_params)
        if not response.ok:
            raise HttpApiRequestException(await response.text())

        try:
            response_data = await response.json()
        except aiohttp.ContentTypeError as e:
            try:
                response_data = json_lib.loads(await response.text())
            except json_lib.JSONDecodeError:
                raise HttpApiResponseException("Empty response") from e

        api_response = ApiResponse(
            data=response_data,
            cookies=dict(response.cookies.items()),
            headers=dict(response.headers.items()),
        )

        if len(str(api_response)) > 1000:
            logger.debug(f"Get multipart response to {endpoint}: <truncated>")
        else:
            logger.debug(f"Get multipart response to {endpoint}: {api_response}")
        return api_response
