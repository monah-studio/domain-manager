"""Provider registry — discover and manage all providers."""

import importlib
import pkgutil
import os

from . import BaseProvider

_registry = {}


def discover():
    """Load all provider modules and build registry."""
    global _registry
    _registry = {}

    pkg_dir = os.path.dirname(__file__)
    for importer, modname, ispkg in pkgutil.iter_modules([pkg_dir]):
        if modname.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f".{modname}", __package__)
            if hasattr(mod, "Provider"):
                inst = mod.Provider()
                _registry[inst.name] = inst
        except Exception as e:
            pass  # skip broken providers gracefully

    return _registry


def get_provider(name):
    """Get a provider by name, or None."""
    if not _registry:
        discover()
    return _registry.get(name)


def list_providers():
    """Return dict of {name: provider_instance}."""
    if not _registry:
        discover()
    return dict(_registry)


def list_configured():
    """Return providers with valid credentials."""
    return {n: p for n, p in list_providers().items() if p.configured}
