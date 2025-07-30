

from It1_interfaces import EventBus


def test_event_bus():
    em = EventBus()
    result = []

    def on_event(data):
        result.append(data)

    em.subscribe("test", on_event)
    em.publish("test", {"x": 1})
    assert result == [{"x": 1}]
