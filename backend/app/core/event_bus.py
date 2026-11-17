"""
Alias module re-exporting EventBus and event streaming helpers.
"""

from backend.app.core.events import EventBus, event_bus, event_generator

__all__ = ["EventBus", "event_bus", "event_generator"]
