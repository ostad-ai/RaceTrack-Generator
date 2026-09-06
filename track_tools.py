import json
import math

class RaceTrack:
    def __init__(self, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.center_line = data.get("center_line", [])
        self.inner_line = data.get("inner_line", [])
        self.outer_line = data.get("outer_line", [])
        self.length = self._calculate_length(self.center_line)

    def _calculate_length(self, line):
        total = 0.0
        for i in range(len(line) - 1):
            x1, y1 = line[i]
            x2, y2 = line[i+1]
            total += math.hypot(x2 - x1, y2 - y1)
        if len(line) > 2:
            x1, y1 = line[-1]
            x2, y2 = line[0]
            total += math.hypot(x2 - x1, y2 - y1)
        return total

    def get_nearest_point(self, x, y):
        best_dist = float('inf')
        best_idx = 0
        for i, (px, py) in enumerate(self.center_line):
            dist = math.hypot(px - x, py - y)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return best_idx, best_dist

    def get_lookahead_point(self, x, y, look_ahead_count=3, direction=1):
        """Finds the nearest point, then looks ahead OR behind for steering."""
        idx, _ = self.get_nearest_point(x, y)
        # direction = 1 for forward, -1 for reverse
        target_idx = int((idx + (look_ahead_count * direction)) % len(self.center_line))
        return self.center_line[target_idx]