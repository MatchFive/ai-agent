"""
路由模块
"""

from .auth import router as auth_router
from .admin import router as admin_router
from .admin_tools import router as admin_tools_router

__all__ = ["auth_router", "admin_router", "admin_tools_router"]
