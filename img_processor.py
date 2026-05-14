import cv2
import numpy as np
from PIL import Image
import random

class Alteration:
    """Abstract base class for alterations."""
    def apply(self, img, region):
        raise NotImplementedError

class ColorShiftAlteration(Alteration):
    def apply(self, img, region):
        x, y, w, h = region
        roi = img[y:y+h, x:x+w].copy()
        
        # converting to HSV to make subtle adjustments to brightness, saturation, or hue
        hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV).astype(np.float32)
        
        choice = random.choice(['s', 'v', 'hue'])
        if choice == 's':
            # Slightly adjust saturation
            hsv[:,:,1] = np.clip(hsv[:,:,1] * random.uniform(0.7, 1.3), 0, 255)
        elif choice == 'v':
            # Slightly adjust brightness (value)
            hsv[:,:,2] = np.clip(hsv[:,:,2] * random.uniform(0.8, 1.2), 0, 255)
        else:
            # Subtle hue shift
            hsv[:,:,0] = np.mod(hsv[:,:,0] + random.uniform(-10, 10), 180)
            
        roi = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        img[y:y+h, x:x+w] = roi
        return img

class BlurAlteration(Alteration):
    def apply(self, img, region):
        x, y, w, h = region
        roi = img[y:y+h, x:x+w]
        
        # Use a smaller kernel and blend it with the original to make it less obvious
        blurred = cv2.GaussianBlur(roi, (3, 3), 1.0)
        blended = cv2.addWeighted(roi, 0.4, blurred, 0.6, 0)
        
        img[y:y+h, x:x+w] = blended
        return img

class NoiseAlteration(Alteration):
    def apply(self, img, region):
        x, y, w, h = region
        roi = img[y:y+h, x:x+w].copy()
        
        # Apply very light Gaussian noise instead of harsh uniform noise
        row, col, ch = roi.shape
        mean = 0
        sigma = 12  # Small variance for subtle effect
        gauss = np.random.normal(mean, sigma, (row, col, ch))
        
        noisy = np.clip(roi + gauss, 0, 255).astype(np.uint8)
        img[y:y+h, x:x+w] = noisy
        return img

class HSVShiftAlteration(Alteration):
    """Shifts the Hue or Value (brightness) channel in a region by a small
    amount (±15) to produce a subtle colour-tint or lighter/darker effect."""
    def apply(self, img, region):
        x, y, w, h = region
        roi = img[y:y+h, x:x+w].copy()

        # Converting ROI from RGB to HSV colour space
        hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV).astype(np.float32)

        # Randomly choose to shift Hue or Value channel
        channel = random.choice(['h', 'v'])
        shift = random.choice([-15, 15])

        if channel == 'h':
            # Hue channel (index 0) wraps around at 180
            hsv[:, :, 0] = np.mod(hsv[:, :, 0] + shift, 180)
        else:
            # Value/brightness channel (index 2), clamp to [0, 255]
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + shift, 0, 255)

        roi = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        img[y:y+h, x:x+w] = roi
        return img


class InpaintAlteration(Alteration):
    """Removes a small patch of content from the centre of the region
    using OpenCV inpainting and fills it with the surrounding texture."""
    def apply(self, img, region):
        x, y, w, h = region
        # Creating a mask the same size as the full image (inpaint needs it)
        mask = np.zeros(img.shape[:2], dtype=np.uint8)

        # Defining a small elliptical patch in the centre of the region
        center_x = x + w // 2
        center_y = y + h // 2
        # Patch covers roughly 40 % of the region dimensions
        axes = (max(5, w // 5), max(5, h // 5))
        cv2.ellipse(mask, (center_x, center_y), axes, 0, 0, 360, 255, -1)

        # Using Telea inpainting algorithm to fill the masked area
        # Converting from RGB to BGR for inpainting, then back to RGB
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        inpainted_bgr = cv2.inpaint(img_bgr, mask, inpaintRadius=3,
                                     flags=cv2.INPAINT_TELEA)
        inpainted_rgb = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)

        # Only copy the affected region back to preserve the rest of the image
        img[y:y+h, x:x+w] = inpainted_rgb[y:y+h, x:x+w]
        return img


class ImageProcessor:
    def __init__(self):
        self.original_cv = None
        self.modified_cv = None
        self.original_pil = None
        self.modified_pil = None

    def load_image(self, filepath):
        """Load image using OpenCV, convert to RGB and PIL."""
        self.original_cv = cv2.imread(filepath)
        if self.original_cv is None:
            raise ValueError("Could not load image")
        self.original_cv = cv2.cvtColor(self.original_cv, cv2.COLOR_BGR2RGB)
        self.original_pil = Image.fromarray(self.original_cv)
        return self.original_pil

    def clone_original(self):
        """Create a copy of original image for modification."""
        self.modified_cv = self.original_cv.copy()
        self.modified_pil = Image.fromarray(self.modified_cv)
        return self.modified_pil

    def apply_alterations(self, regions_with_alterations):
        """
        regions_with_alterations: list of (region, alteration_instance)
        region = (x, y, w, h)
        """
        for region, alteration in regions_with_alterations:
            self.modified_cv = alteration.apply(self.modified_cv, region)
        self.modified_pil = Image.fromarray(self.modified_cv)
        return self.modified_pil

    def draw_circle(self, img_cv, center, radius=15, color=(255,0,0), thickness=3):
        """Draw circle on OpenCV image (color in RGB)."""
        cv2.circle(img_cv, center, radius, color, thickness)
        return img_cv

    def get_original_cv(self):
        return self.original_cv

    def get_modified_cv(self):
        return self.modified_cv

    def update_modified_from_cv(self):
        self.modified_pil = Image.fromarray(self.modified_cv)
        return self.modified_pil