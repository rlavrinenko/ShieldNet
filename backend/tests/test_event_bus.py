import unittest

from app.core.events import Event, EventBus, EventDispatchError


class EventBusTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.bus = EventBus()
        await self.bus.start()

    async def asyncTearDown(self) -> None:
        await self.bus.stop()

    async def test_publish_delivers_to_named_and_wildcard_subscribers(self) -> None:
        received: list[str] = []

        async def named(event: Event) -> None:
            received.append(f"named:{event.name}")

        def wildcard(event: Event) -> None:
            received.append(f"wildcard:{event.name}")

        await self.bus.subscribe("guild.created", named)
        await self.bus.subscribe("*", wildcard)
        await self.bus.publish(Event(name="guild.created", payload={"guild_id": 1}))

        self.assertEqual(
            sorted(received),
            ["named:guild.created", "wildcard:guild.created"],
        )
        snapshot = await self.bus.snapshot()
        self.assertEqual(snapshot.published, 1)
        self.assertEqual(snapshot.delivered, 2)
        self.assertEqual(snapshot.failed, 0)

    async def test_duplicate_subscription_is_ignored(self) -> None:
        calls = 0

        async def handler(_: Event) -> None:
            nonlocal calls
            calls += 1

        await self.bus.subscribe("test", handler)
        await self.bus.subscribe("test", handler)
        await self.bus.publish(Event(name="test"))

        self.assertEqual(calls, 1)

    async def test_handler_failure_can_be_raised(self) -> None:
        async def broken(_: Event) -> None:
            raise ValueError("broken")

        await self.bus.subscribe("test", broken)

        with self.assertRaises(EventDispatchError):
            await self.bus.publish(Event(name="test"), raise_on_error=True)

        snapshot = await self.bus.snapshot()
        self.assertEqual(snapshot.failed, 1)

    async def test_publish_before_start_is_rejected(self) -> None:
        bus = EventBus()
        with self.assertRaises(RuntimeError):
            await bus.publish(Event(name="test"))


if __name__ == "__main__":
    unittest.main()
