"""
文件操作工具
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
import aiofiles
import aiofiles.os

from core.logger import logger


class FileTool:
    """
    文件操作工具
    支持读写、目录操作、文件搜索
    """

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def _resolve_path(self, path: str) -> Path:
        """解析路径"""
        p = Path(path)
        if not p.is_absolute():
            p = self.base_path / p
        return p.resolve()

    async def read_file(
        self,
        file_path: str,
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """
        读取文件

        Args:
            file_path: 文件路径
            encoding: 编码

        Returns:
            读取结果
        """
        path = self._resolve_path(file_path)

        try:
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()

            logger.debug(f"Read file: {path}")
            return {
                "success": True,
                "content": content,
                "path": str(path),
                "size": len(content)
            }
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return {"success": False, "error": str(e)}

    async def write_file(
        self,
        file_path: str,
        content: str,
        encoding: str = 'utf-8',
        mode: str = 'w'
    ) -> Dict[str, Any]:
        """
        写入文件

        Args:
            file_path: 文件路径
            content: 内容
            encoding: 编码
            mode: 写入模式 ('w' 覆盖, 'a' 追加)

        Returns:
            写入结果
        """
        path = self._resolve_path(file_path)

        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(path, mode, encoding=encoding) as f:
                await f.write(content)

            logger.debug(f"Wrote file: {path}")
            return {
                "success": True,
                "path": str(path),
                "size": len(content)
            }
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return {"success": False, "error": str(e)}

    async def read_json(self, file_path: str) -> Dict[str, Any]:
        """读取JSON文件"""
        result = await self.read_file(file_path)
        if result["success"]:
            try:
                result["content"] = json.loads(result["content"])
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON: {e}"}
        return result

    async def write_json(
        self,
        file_path: str,
        data: Any,
        indent: int = 2
    ) -> Dict[str, Any]:
        """写入JSON文件"""
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            return await self.write_file(file_path, content)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """删除文件"""
        path = self._resolve_path(file_path)

        try:
            await aiofiles.os.remove(path)
            logger.debug(f"Deleted file: {path}")
            return {"success": True, "path": str(path)}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return {"success": False, "error": str(e)}

    async def list_directory(
        self,
        dir_path: str = ".",
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """
        列出目录内容

        Args:
            dir_path: 目录路径
            pattern: 匹配模式

        Returns:
            目录内容
        """
        path = self._resolve_path(dir_path)

        try:
            items = list(path.glob(pattern))
            files = [str(f.relative_to(path)) for f in items if f.is_file()]
            dirs = [str(d.relative_to(path)) for d in items if d.is_dir()]

            return {
                "success": True,
                "path": str(path),
                "files": files,
                "directories": dirs,
                "total_files": len(files),
                "total_dirs": len(dirs)
            }
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            return {"success": False, "error": str(e)}

    async def create_directory(self, dir_path: str) -> Dict[str, Any]:
        """创建目录"""
        path = self._resolve_path(dir_path)

        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
            return {"success": True, "path": str(path)}
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return {"success": False, "error": str(e)}

    async def delete_directory(
        self,
        dir_path: str,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """删除目录"""
        path = self._resolve_path(dir_path)

        try:
            if recursive:
                shutil.rmtree(path)
            else:
                await aiofiles.os.rmdir(path)

            logger.debug(f"Deleted directory: {path}")
            return {"success": True, "path": str(path)}
        except Exception as e:
            logger.error(f"Failed to delete directory {path}: {e}")
            return {"success": False, "error": str(e)}

    async def copy_file(
        self,
        src: str,
        dst: str
    ) -> Dict[str, Any]:
        """复制文件"""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)

        try:
            shutil.copy2(src_path, dst_path)
            logger.debug(f"Copied file: {src_path} -> {dst_path}")
            return {
                "success": True,
                "src": str(src_path),
                "dst": str(dst_path)
            }
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return {"success": False, "error": str(e)}

    async def move_file(
        self,
        src: str,
        dst: str
    ) -> Dict[str, Any]:
        """移动文件"""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)

        try:
            shutil.move(str(src_path), str(dst_path))
            logger.debug(f"Moved file: {src_path} -> {dst_path}")
            return {
                "success": True,
                "src": str(src_path),
                "dst": str(dst_path)
            }
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return {"success": False, "error": str(e)}

    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        path = self._resolve_path(file_path)
        return await aiofiles.os.path.exists(path)

    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        path = self._resolve_path(file_path)

        try:
            stat = await aiofiles.os.stat(path)
            return {
                "success": True,
                "path": str(path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
