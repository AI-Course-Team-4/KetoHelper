"""
의존성 주입 컨테이너 구현
"""

from typing import TypeVar, Type, Callable, Dict, Any, Optional, get_type_hints
from abc import ABC, abstractmethod
import inspect
import asyncio
from functools import wraps

T = TypeVar('T')

class DIContainerError(Exception):
    """DI 컨테이너 관련 예외"""
    pass

class CircularDependencyError(DIContainerError):
    """순환 의존성 예외"""
    pass

class ServiceNotRegisteredError(DIContainerError):
    """서비스 미등록 예외"""
    pass

class ServiceLifetime:
    """서비스 라이프타임"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"

class ServiceDescriptor:
    """서비스 설명자"""

    def __init__(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        instance: Optional[T] = None,
        lifetime: str = ServiceLifetime.TRANSIENT
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime

        # 검증
        if sum(bool(x) for x in [implementation, factory, instance]) != 1:
            raise DIContainerError("Exactly one of implementation, factory, or instance must be provided")

class Container:
    """의존성 주입 컨테이너"""

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_services: Dict[str, Dict[Type, Any]] = {}
        self._resolution_stack: list = []
        self._current_scope: Optional[str] = None

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """싱글톤 서비스 등록"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON
        )
        self._services[interface] = descriptor
        return self

    def register_transient(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """일시적 서비스 등록"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT
        )
        self._services[interface] = descriptor
        return self

    def register_scoped(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None
    ) -> 'Container':
        """스코프 서비스 등록"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED
        )
        self._services[interface] = descriptor
        return self

    def register_instance(self, interface: Type[T], instance: T) -> 'Container':
        """인스턴스 직접 등록"""
        descriptor = ServiceDescriptor(
            interface=interface,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        self._services[interface] = descriptor
        self._singletons[interface] = instance
        return self

    def resolve(self, interface: Type[T]) -> T:
        """서비스 해결"""
        return asyncio.run(self.resolve_async(interface))

    async def resolve_async(self, interface: Type[T]) -> T:
        """비동기 서비스 해결"""
        # 순환 의존성 체크
        if interface in self._resolution_stack:
            raise CircularDependencyError(f"Circular dependency detected: {' -> '.join(str(t) for t in self._resolution_stack)} -> {interface}")

        self._resolution_stack.append(interface)

        try:
            service = await self._resolve_service(interface)
            return service
        finally:
            self._resolution_stack.remove(interface)

    async def _resolve_service(self, interface: Type[T]) -> T:
        """내부 서비스 해결 로직"""
        if interface not in self._services:
            # 인터페이스 자체가 구현체인 경우 자동 등록
            if not inspect.isabstract(interface):
                self.register_transient(interface, interface)
            else:
                raise ServiceNotRegisteredError(f"Service {interface} not registered")

        descriptor = self._services[interface]

        # 라이프타임에 따른 인스턴스 관리
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if interface in self._singletons:
                return self._singletons[interface]

            instance = await self._create_instance(descriptor)
            self._singletons[interface] = instance
            return instance

        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if self._current_scope is None:
                raise DIContainerError("No scope is active")

            if self._current_scope not in self._scoped_services:
                self._scoped_services[self._current_scope] = {}

            scope_dict = self._scoped_services[self._current_scope]
            if interface in scope_dict:
                return scope_dict[interface]

            instance = await self._create_instance(descriptor)
            scope_dict[interface] = instance
            return instance

        else:  # TRANSIENT
            return await self._create_instance(descriptor)

    async def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """인스턴스 생성"""
        if descriptor.instance is not None:
            return descriptor.instance

        if descriptor.factory is not None:
            if asyncio.iscoroutinefunction(descriptor.factory):
                return await descriptor.factory()
            else:
                return descriptor.factory()

        if descriptor.implementation is not None:
            return await self._create_with_injection(descriptor.implementation)

        raise DIContainerError(f"Cannot create instance for {descriptor.interface}")

    async def _create_with_injection(self, implementation: Type[T]) -> T:
        """생성자 주입으로 인스턴스 생성"""
        # 생성자 시그니처 분석
        init_signature = inspect.signature(implementation.__init__)
        init_params = {}

        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue

            # 타입 힌트에서 의존성 추론
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                # 타입 힌트가 없는 경우 기본값 사용
                if param.default != inspect.Parameter.empty:
                    init_params[param_name] = param.default
                else:
                    raise DIContainerError(f"Cannot resolve parameter '{param_name}' for {implementation}")
            else:
                # 의존성 주입
                dependency = await self.resolve_async(param_type)
                init_params[param_name] = dependency

        return implementation(**init_params)

    def create_scope(self, scope_name: str = None) -> 'ScopeContext':
        """스코프 생성"""
        if scope_name is None:
            import uuid
            scope_name = str(uuid.uuid4())

        return ScopeContext(self, scope_name)

    def dispose_scope(self, scope_name: str):
        """스코프 정리"""
        if scope_name in self._scoped_services:
            scope_dict = self._scoped_services[scope_name]

            # IDisposable 인터페이스를 구현한 서비스들 정리
            for service in scope_dict.values():
                if hasattr(service, 'dispose'):
                    try:
                        if asyncio.iscoroutinefunction(service.dispose):
                            asyncio.create_task(service.dispose())
                        else:
                            service.dispose()
                    except Exception:
                        pass  # 정리 중 예외는 무시

            del self._scoped_services[scope_name]

    def is_registered(self, interface: Type[T]) -> bool:
        """서비스 등록 여부 확인"""
        return interface in self._services

    def get_services(self) -> Dict[Type, ServiceDescriptor]:
        """등록된 서비스 목록 반환"""
        return self._services.copy()

class ScopeContext:
    """스코프 컨텍스트"""

    def __init__(self, container: Container, scope_name: str):
        self.container = container
        self.scope_name = scope_name
        self._previous_scope = None

    def __enter__(self):
        self._previous_scope = self.container._current_scope
        self.container._current_scope = self.scope_name
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.dispose_scope(self.scope_name)
        self.container._current_scope = self._previous_scope

    async def __aenter__(self):
        self._previous_scope = self.container._current_scope
        self.container._current_scope = self.scope_name
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.container.dispose_scope(self.scope_name)
        self.container._current_scope = self._previous_scope

# 데코레이터들
def injectable(container: Container):
    """클래스를 자동으로 컨테이너에 등록하는 데코레이터"""
    def decorator(cls):
        container.register_transient(cls, cls)
        return cls
    return decorator

def singleton(container: Container):
    """클래스를 싱글톤으로 등록하는 데코레이터"""
    def decorator(cls):
        container.register_singleton(cls, cls)
        return cls
    return decorator

def inject(container: Container):
    """함수/메서드에 의존성 주입하는 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 함수 시그니처 분석
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)

            for param_name, param in sig.parameters.items():
                if param_name not in bound_args.arguments and param.annotation != inspect.Parameter.empty:
                    try:
                        dependency = await container.resolve_async(param.annotation)
                        bound_args.arguments[param_name] = dependency
                    except ServiceNotRegisteredError:
                        if param.default == inspect.Parameter.empty:
                            raise
                        # 기본값이 있으면 그것을 사용

            if asyncio.iscoroutinefunction(func):
                return await func(**bound_args.arguments)
            else:
                return func(**bound_args.arguments)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

# 글로벌 컨테이너 인스턴스
container = Container()