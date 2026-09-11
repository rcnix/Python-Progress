from collections import *


class RegistrarQueue:

    def __init__(self, prefix="REG"):
        self.prefix = prefix
        self._next_number = 1
        self._tickets = deque()

    def generate_number(self):
        ticket = f"{self.prefix}-{self._next_number:03d}"
        self._next_number += 1
        self._tickets.append(ticket)
        return ticket

    def serve_next(self):
        if not self._tickets:
            return None
        return self._tickets.popleft()

    def peek(self):
        if not self._tickets:
            return None
        return self._tickets[0]

    def clear(self):
        self._tickets.clear()

    def tickets(self):
        return tuple(self._tickets)

    def __len__(self):
        return len(self._tickets)