"""
数据库操作工具
"""

from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, MetaData, Table
from sqlalchemy.orm import declarative_base

from core.config import settings
from core.logger import logger


class DatabaseTool:
    """
    数据库操作工具
    基于SQLAlchemy的异步数据库操作
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: Optional[bool] = None,
    ):
        self.database_url = database_url or settings.database.url
        self.echo = echo if echo is not None else settings.database.echo
        self._engine = None
        self._session_factory = None

    async def _get_engine(self):
        """获取数据库引擎"""
        if self._engine is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=self.echo,
            )
            logger.info(f"Database engine created: {self.database_url.split('@')[-1]}")
        return self._engine

    async def _get_session_factory(self):
        """获取会话工厂"""
        if self._session_factory is None:
            engine = await self._get_engine()
            self._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        return self._session_factory

    @asynccontextmanager
    async def session(self):
        """获取数据库会话上下文"""
        factory = await self._get_session_factory()
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行SQL语句

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            执行结果
        """
        try:
            async with self.session() as session:
                result = await session.execute(text(sql), params or {})

                # 判断是否有返回结果
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    data = [dict(zip(columns, row)) for row in rows]
                    return {
                        "success": True,
                        "data": data,
                        "rowcount": len(data),
                    }
                else:
                    return {
                        "success": True,
                        "rowcount": result.rowcount,
                    }

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def fetch_one(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """查询单条记录"""
        result = await self.execute(sql, params)
        if result["success"] and result.get("data"):
            result["data"] = result["data"][0] if result["data"] else None
        return result

    async def fetch_all(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """查询所有记录"""
        return await self.execute(sql, params)

    async def insert(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        插入数据

        Args:
            table: 表名
            data: 数据

        Returns:
            插入结果
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        return await self.execute(sql, data)

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: str,
        where_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        更新数据

        Args:
            table: 表名
            data: 更新数据
            where: WHERE条件
            where_params: WHERE参数

        Returns:
            更新结果
        """
        set_clause = ", ".join(f"{k} = :{k}" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"

        params = {**data, **(where_params or {})}
        return await self.execute(sql, params)

    async def delete(
        self,
        table: str,
        where: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        删除数据

        Args:
            table: 表名
            where: WHERE条件
            params: 参数

        Returns:
            删除结果
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        return await self.execute(sql, params)

    async def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        sql = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=:table_name
        """
        result = await self.fetch_one(sql, {"table_name": table_name})
        return result["success"] and result.get("data") is not None

    async def create_table(
        self,
        table_name: str,
        columns: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        创建表

        Args:
            table_name: 表名
            columns: 列定义 {"name": "TEXT", "age": "INTEGER"}

        Returns:
            创建结果
        """
        columns_def = ", ".join(f"{name} {dtype}" for name, dtype in columns.items())
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})"
        return await self.execute(sql)

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connection closed")
