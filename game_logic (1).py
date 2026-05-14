import random

class DifferenceRegion:
    def __init__(self, x, y, w, h, alteration_type):
        self.rect = (x, y, w, h)
        self.alteration_type = alteration_type
        self.found = False
        self.center = (x + w//2, y + h//2)

    def contains_point(self, px, py, tolerance=10):
        x, y, w, h = self.rect
        # Expand rectangle by tolerance
        return (x - tolerance <= px <= x + w + tolerance and
                y - tolerance <= py <= y + h + tolerance)

class DifferenceManager:
    def __init__(self, image_width, image_height, num_differences=5, max_mistakes=3):
        self.width = image_width
        self.height = image_height
        self.num_differences = num_differences
        self.max_mistakes = max_mistakes
        self.differences = []
        self.mistakes = 0
        self.game_active = True

    def generate_random_regions(self, alteration_classes, min_size=40, max_size=60):
        """Generate non-overlapping random rectangles."""
        regions = []
        attempts = 0
        max_attempts = 1000
        while len(regions) < self.num_differences and attempts < max_attempts:
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x = random.randint(0, self.width - w)
            y = random.randint(0, self.height - h)
            rect = (x, y, w, h)
            # Check overlap with existing regions
            overlap = False
            for (ex, ey, ew, eh) in regions:
                if not (x + w < ex or ex + ew < x or y + h < ey or ey + eh < y):
                    overlap = True
                    break
            if not overlap:
                regions.append(rect)
            attempts += 1
        # Fallback: if still not enough, place them in a grid pattern
        if len(regions) < self.num_differences:
            # simple grid fallback
            cols = 2
            rows = (self.num_differences + cols - 1) // cols
            cell_w = self.width // cols
            cell_h = self.height // rows
            for i in range(self.num_differences):
                row = i // cols
                col = i % cols
                x = col * cell_w + 10
                y = row * cell_h + 10
                w = min(max_size, cell_w - 20)
                h = min(max_size, cell_h - 20)
                regions.append((x, y, w, h))
        return regions

    def setup_new_game(self, alteration_classes):
        """Create differences with random alteration types."""
        # Get available alteration classes (not instances)
        self.differences = []
        regions = self.generate_random_regions(alteration_classes)
        # For each region, pick random alteration type
        for rect in regions:
            alt_class = random.choice(alteration_classes)
            self.differences.append(DifferenceRegion(rect[0], rect[1], rect[2], rect[3], alt_class))
        self.mistakes = 0
        self.game_active = True
        return self.differences

    def check_click(self, x, y):
        """Return (is_hit, region_index) if click is within any unfound difference."""
        if not self.game_active:
            return False, None
        for idx, diff in enumerate(self.differences):
            if not diff.found and diff.contains_point(x, y):
                diff.found = True
                return True, idx
        # Miss
        self.mistakes += 1
        if self.mistakes >= self.max_mistakes:
            self.game_active = False
        return False, None

    def all_found(self):
        return all(diff.found for diff in self.differences)

    def get_unfound_regions(self):
        return [(diff.rect, diff.center) for diff in self.differences if not diff.found]

    def reset(self):
        self.differences = []
        self.mistakes = 0
        self.game_active = True