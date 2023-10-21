from httpx import AsyncClient
import pytest


class TestHelloWorld:
    @pytest.mark.anyio
    async def test_hello_world(self, async_client: AsyncClient):
        response = await async_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"msg": "Hello World"}
