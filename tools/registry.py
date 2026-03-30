"""
工具注册表
提供装饰器注册、自动扫描、DB同步等能力
"""

import hashlib
import json
import inspect
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field

from core.logger import logger


@dataclass
class ToolRegistration:
    """工具注册信息"""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler_class_path: str   # e.g. "tools.gold_price_tool.GoldPriceTool"
    handler_method: str       # e.g. "get_current_price"
    category: str = "general"

    @property
    def version_hash(self) -> str:
        raw = (
            f"{self.name}|{self.description}|"
            f"{json.dumps(self.parameters, sort_keys=True)}|"
            f"{self.handler_class_path}|{self.handler_method}"
        )
        return hashlib.md5(raw.encode()).hexdigest()

    def get_instance(self):
        """获取或创建工具类实例（每个类路径缓存单例）"""
        if self.handler_class_path not in _instance_cache:
            parts = self.handler_class_path.rsplit(".", 1)
            if len(parts) != 2:
                raise ImportError(f"Invalid class path: {self.handler_class_path}")
            module_path, class_name = parts
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            _instance_cache[self.handler_class_path] = cls()
        return _instance_cache[self.handler_class_path]

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具方法（同时支持 async 和 sync）"""
        instance = self.get_instance()
        method = getattr(instance, self.handler_method)
        if inspect.iscoroutinefunction(method):
            return await method(**kwargs)
        else:
            return method(**kwargs)


# 工具类实例缓存
_instance_cache: Dict[str, Any] = {}


class ToolRegistry:
    """全局工具注册表"""

    _registrations: Dict[str, ToolRegistration] = {}

    @classmethod
    def register(cls, registration: ToolRegistration) -> None:
        cls._registrations[registration.name] = registration
        logger.info(
            f"Tool registered: {registration.name} "
            f"({registration.handler_class_path}.{registration.handler_method})"
        )

    @classmethod
    def get(cls, name: str) -> Optional[ToolRegistration]:
        return cls._registrations.get(name)

    @classmethod
    def get_all(cls) -> Dict[str, ToolRegistration]:
        return cls._registrations.copy()

    @classmethod
    def list_by_category(cls) -> Dict[str, List[ToolRegistration]]:
        result: Dict[str, List[ToolRegistration]] = {}
        for reg in cls._registrations.values():
            result.setdefault(reg.category, []).append(reg)
        return result

    @classmethod
    def clear(cls) -> None:
        cls._registrations.clear()


def register_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    category: str = "general",
    method_name: Optional[str] = None,
):
    """
    类级装饰器，用于单方法工具。

    用法:
        @register_tool(name="get_price", description="...", parameters={...})
        class MyTool:
            async def the_method(self, ...): ...
    """
    def decorator(cls):
        if method_name:
            handler_method = method_name
        else:
            candidates = [
                m for m in dir(cls)
                if not m.startswith("_")
                and callable(getattr(cls, m, None))
                and inspect.iscoroutinefunction(getattr(cls, m, None))
            ]
            if len(candidates) == 1:
                handler_method = candidates[0]
            elif len(candidates) == 0:
                raise ValueError(
                    f"{cls.__name__} 没有公开的 async 方法，请使用 @register_method_tool"
                )
            else:
                raise ValueError(
                    f"{cls.__name__} 有多个 async 方法 ({candidates})，"
                    f"请指定 method_name 或使用 @register_method_tool"
                )

        class_path = f"{cls.__module__}.{cls.__name__}"
        registration = ToolRegistration(
            name=name,
            description=description,
            parameters=parameters,
            handler_class_path=class_path,
            handler_method=handler_method,
            category=category,
        )
        ToolRegistry.register(registration)
        return cls

    return decorator


def register_method_tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    category: str = "general",
):
    """
    方法级装饰器，用于多方法工具。

    用法:
        class MyTool:
            @register_method_tool(name="read", description="...", parameters={...})
            async def read_file(self, ...): ...

            @register_method_tool(name="write", description="...", parameters={...})
            async def write_file(self, ...): ...
    """
    def decorator(method):
        method._tool_meta = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "category": category,
        }
        return method

    return decorator


def scan_classes_for_method_tools():
    """
    扫描已导入的 tools 模块，收集带 @register_method_tool 装饰器的方法。
    在所有工具模块导入完成后调用。
    """
    import sys

    for module_name in list(sys.modules.keys()):
        if not module_name.startswith("tools"):
            continue
        module = sys.modules[module_name]
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module_name:
                continue
            class_path = f"{cls.__module__}.{cls.__name__}"
            for attr_name in dir(cls):
                attr = getattr(cls, attr_name, None)
                if callable(attr) and hasattr(attr, "_tool_meta"):
                    meta = attr._tool_meta
                    registration = ToolRegistration(
                        name=meta["name"],
                        description=meta["description"],
                        parameters=meta["parameters"],
                        handler_class_path=class_path,
                        handler_method=attr_name,
                        category=meta["category"],
                    )
                    ToolRegistry.register(registration)
