"""Compatibility shim for hosts that auto-detect gammaan.wsgi from the GitHub org name."""

from config.wsgi import application

__all__ = ["application"]
