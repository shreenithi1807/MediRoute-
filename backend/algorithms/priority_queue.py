import heapq
import itertools


class EmergencyPriorityQueue:

    def __init__(self):
        self.heap = []
        self.counter = itertools.count()

    def push(self, emergency):
        severity = int(emergency["severity"])

        # heapq is a min heap.
        # Negative severity means severity 5 comes before severity 4.
        priority = -severity

        # Counter means older emergencies win ties.
        order = next(self.counter)

        heapq.heappush(
            self.heap,
            (
                priority,
                order,
                emergency["id"],
                emergency
            )
        )

    def pop(self):
        while self.heap:
            _, _, _, emergency = heapq.heappop(self.heap)

            if emergency.get("status") == "waiting":
                return emergency

        return None

    def peek(self):
        while self.heap:
            _, _, _, emergency = self.heap[0]

            if emergency.get("status") == "waiting":
                return emergency

            heapq.heappop(self.heap)

        return None

    def __len__(self):
        return len(self.heap)