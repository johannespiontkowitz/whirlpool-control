import time


class _TimeAdapter:
    def ticks_ms(self):
        ticks_ms = getattr(time, "ticks_ms", None)
        if ticks_ms is not None:
            return ticks_ms()
        return int(time.monotonic() * 1000)

    def ticks_diff(self, current, previous):
        ticks_diff = getattr(time, "ticks_diff", None)
        if ticks_diff is not None:
            return ticks_diff(current, previous)
        return current - previous


class Button:
    def __init__(self, pin, pin_factory=None, time_source=None, active_low=True, pull_up=True):
        self._time = time_source or _TimeAdapter()
        self._active_low = active_low
        self._debounce_ms = 50
        self._pin = self._create_pin(pin, pin_factory, pull_up)

        initial_state = self._read_raw_state()
        self._stable_state = initial_state
        self._last_raw_state = initial_state
        self._last_change_ms = self._time.ticks_ms()
        self._pressed_event = False
        self._released_event = False

    def _create_pin(self, pin, pin_factory, pull_up):
        if hasattr(pin, "value"):
            return pin

        if pin_factory is None:
            from machine import Pin

            pin_factory = Pin

        mode = getattr(pin_factory, "IN", None)
        pull = getattr(pin_factory, "PULL_UP", None) if pull_up else None

        if mode is None:
            return pin_factory(pin)
        if pull is None:
            return pin_factory(pin, mode)
        return pin_factory(pin, mode, pull)

    def _read_raw_state(self):
        raw_value = self._pin.value()
        if self._active_low:
            return raw_value == 0
        return raw_value == 1

    def set_debounce_time(self, debounce_time_ms):
        self._debounce_ms = max(0, int(debounce_time_ms))

    def loop(self):
        self._pressed_event = False
        self._released_event = False

        now = self._time.ticks_ms()
        raw_state = self._read_raw_state()

        if raw_state != self._last_raw_state:
            self._last_raw_state = raw_state
            self._last_change_ms = now
            return

        if raw_state == self._stable_state:
            return

        if self._time.ticks_diff(now, self._last_change_ms) < self._debounce_ms:
            return

        self._stable_state = raw_state
        if self._stable_state:
            self._pressed_event = True
        else:
            self._released_event = True

    def is_pressed(self):
        return self._pressed_event

    def is_released(self):
        return self._released_event

    def get_state(self):
        return self._stable_state

    def is_down(self):
        return self._stable_state

    def is_up(self):
        return not self._stable_state