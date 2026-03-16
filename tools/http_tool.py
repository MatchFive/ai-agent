"""
HTTP请求工具
"""

from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin
import httpx

from core.logger import logger


class HttpTool:
    """
    HTTP请求工具
    基于httpx实现的异步HTTP客户端
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.default_headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送HTTP请求

        Args:
            method: HTTP方法
            url: URL
            params: 查询参数
            headers: 请求头
            json_data: JSON数据
            data: 表单数据
            **kwargs: 其他参数

        Returns:
            响应结果
        """
        client = await self._get_client()

        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=headers,
                json=json_data,
                data=data,
                **kwargs
            )

            logger.debug(f"HTTP {method} {url} -> {response.status_code}")

            # 尝试解析JSON
            try:
                body = response.json()
            except Exception:
                body = response.text

            return {
                "success": response.is_success,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body,
                "url": str(response.url),
            }
        except httpx.TimeoutException:
            logger.error(f"HTTP request timeout: {url}")
            return {"success": False, "error": "Request timeout"}
        except httpx.RequestError as e:
            logger.error(f"HTTP request error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"HTTP unexpected error: {e}")
            return {"success": False, "error": str(e)}

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """GET请求"""
        return await self.request("GET", url, params=params, headers=headers, **kwargs)

    async def post(
        self,
        url: str,
        json_data: Optional[Any] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """POST请求"""
        return await self.request(
            "POST", url,
            json_data=json_data,
            data=data,
            headers=headers,
            **kwargs
        )

    async def put(
        self,
        url: str,
        json_data: Optional[Any] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """PUT请求"""
        return await self.request(
            "PUT", url,
            json_data=json_data,
            data=data,
            headers=headers,
            **kwargs
        )

    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """DELETE请求"""
        return await self.request("DELETE", url, headers=headers, **kwargs)

    async def patch(
        self,
        url: str,
        json_data: Optional[Any] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """PATCH请求"""
        return await self.request(
            "PATCH", url,
            json_data=json_data,
            data=data,
            headers=headers,
            **kwargs
        )

    async def download(
        self,
        url: str,
        save_path: str,
        chunk_size: int = 8192
    ) -> Dict[str, Any]:
        """
        下载文件

        Args:
            url: 文件URL
            save_path: 保存路径
            chunk_size: 块大小

        Returns:
            下载结果
        """
        import aiofiles
        from pathlib import Path

        client = await self._get_client()

        try:
            async with client.stream("GET", url) as response:
                if not response.is_success:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                    }

                # 确保目录存在
                path = Path(save_path)
                path.parent.mkdir(parents=True, exist_ok=True)

                total_size = 0
                async with aiofiles.open(path, 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size):
                        await f.write(chunk)
                        total_size += len(chunk)

                logger.info(f"Downloaded {url} -> {save_path} ({total_size} bytes)")
                return {
                    "success": True,
                    "path": save_path,
                    "size": total_size,
                }

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return {"success": False, "error": str(e)}
