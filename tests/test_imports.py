"""Smoke tests for package layout."""

import importlib

import richman


def test_package_metadata() -> None:
    assert richman.__app_name__ == "richman"
    assert richman.__version__ == "0.1.0"


def test_planned_module_packages_are_importable() -> None:
    modules = [
        "richman.domain",
        "richman.board",
        "richman.rules",
        "richman.player",
        "richman.engine",
        "richman.render",
        "richman.render.ports",
    ]

    for module in modules:
        assert importlib.import_module(module)
