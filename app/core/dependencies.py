"""Dependency injection container for loose coupling"""

from typing import Dict, Any, Optional, Type, TypeVar
from abc import ABC, abstractmethod
import asyncio

T = TypeVar('T')

class DIContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T):
        """Register a singleton service"""
        key = interface.__name__
        self._singletons[key] = implementation
    
    def register_factory(self, interface: Type[T], factory: callable):
        """Register a factory function"""
        key = interface.__name__
        self._factories[key] = factory
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance"""
        key = interface.__name__
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check factories
        if key in self._factories:
            return self._factories[key]()
        
        raise ValueError(f"Service {key} not registered")

# Global container instance
container = DIContainer()

# Service interfaces
class ITerminologyRepository(ABC):
    @abstractmethod
    async def search_codes(self, query: str, limit: int) -> list: pass

class ICacheService(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any: pass
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> bool: pass

class IConfigService(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any: pass