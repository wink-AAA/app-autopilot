"""Adapter registry for discovering and instantiating platform adapters."""

from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, Optional, Type

from app_autopilot.adapters.base import PlatformAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Central registry for platform adapters.

    Adapters can be registered explicitly (via ``register``) or discovered
    dynamically by module path (via ``create``).

    Example::

        registry = AdapterRegistry()
        registry.register("my_board", MyJobBoardAdapter)
        adapter = registry.create("my_board", config={"api_key": "..."})
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, Type[PlatformAdapter]] = {}

    def register(self, name: str, adapter_class: Type[PlatformAdapter]) -> None:
        """Register an adapter class under a given name.

        Args:
            name: Unique identifier for the adapter.
            adapter_class: A subclass of ``PlatformAdapter``.

        Raises:
            TypeError: If *adapter_class* is not a ``PlatformAdapter`` subclass.
        """
        if not (isinstance(adapter_class, type) and issubclass(adapter_class, PlatformAdapter)):
            raise TypeError(
                f"adapter_class must be a subclass of PlatformAdapter, "
                f"got {adapter_class!r}"
            )
        self._adapters[name] = adapter_class
        logger.info("Registered adapter: %s -> %s", name, adapter_class.__name__)

    def unregister(self, name: str) -> None:
        """Remove a registered adapter by name."""
        self._adapters.pop(name, None)

    def get(self, name: str) -> Optional[Type[PlatformAdapter]]:
        """Look up a registered adapter class by name."""
        return self._adapters.get(name)

    def list_adapters(self) -> Dict[str, str]:
        """Return a mapping of adapter names to their class names."""
        return {name: cls.__name__ for name, cls in self._adapters.items()}

    def create(self, name: str, config: Optional[Dict[str, Any]] = None) -> PlatformAdapter:
        """Instantiate a registered adapter.

        Args:
            name: The registered adapter name.
            config: Configuration dict passed to the adapter constructor.

        Returns:
            An instance of the adapter.

        Raises:
            KeyError: If no adapter is registered under *name*.
        """
        adapter_class = self._adapters.get(name)
        if adapter_class is None:
            raise KeyError(
                f"No adapter registered with name '{name}'. "
                f"Available: {list(self._adapters.keys())}"
            )
        return adapter_class()

    @staticmethod
    def load_from_module(module_path: str) -> Type[PlatformAdapter]:
        """Dynamically load an adapter class from a dotted module path.

        The module must contain exactly one subclass of ``PlatformAdapter``.

        Args:
            module_path: Dotted Python import path (e.g. ``"platforms.job_board_example"``).

        Returns:
            The adapter class found in the module.

        Raises:
            ImportError: If the module cannot be imported.
            ValueError: If no ``PlatformAdapter`` subclass is found.
        """
        module = importlib.import_module(module_path)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PlatformAdapter)
                and attr is not PlatformAdapter
            ):
                return attr
        raise ValueError(
            f"No PlatformAdapter subclass found in module '{module_path}'"
        )
