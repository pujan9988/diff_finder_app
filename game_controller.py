from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
from img_processor import ImageProcessor, ColorShiftAlteration, BlurAlteration, NoiseAlteration, HSVShiftAlteration, InpaintAlteration
from game_logic import DifferenceManager

class GameController:
    def __init__(self, app):
        self.app = app
        self.image_processor = ImageProcessor()
        self.diff_manager = None
        self.alteration_classes = [ColorShiftAlteration, BlurAlteration, NoiseAlteration, HSVShiftAlteration, InpaintAlteration]
        self.current_image_path = None

    def load_image_from_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not file_path:
            return
        self.load_image(file_path)

    def load_image(self, file_path):
        try:
            self.current_image_path = file_path
            # Load original image
            original_pil = self.image_processor.load_image(file_path)
            # Clone for modified
            self.image_processor.clone_original()
            # Get image dimensions
            w, h = original_pil.size
            # Setup difference manager
            self.diff_manager = DifferenceManager(w, h, num_differences=5, max_mistakes=3)
            # Generate random differences
            differences = self.diff_manager.setup_new_game(self.alteration_classes)
            # Prepare alterations list for image processor
            alterations = []
            for diff in differences:
                # Create instance of the alteration class
                alt_instance = diff.alteration_type()
                alterations.append((diff.rect, alt_instance))
            # Apply alterations to get modified image
            self.image_processor.apply_alterations(alterations)
            # Update GUI with both images
            self.app.update_original_image(self.image_processor.original_pil)
            self.app.update_modified_image(self.image_processor.modified_pil)
            # Reset UI state
            self.app.update_score_display(self.diff_manager.num_differences, 0)
            self.app.set_status(f"Loaded: {file_path.split('/')[-1]} - Find 5 differences!")
            self.app.enable_reveal_button(True)
        except Exception as e:
            self.app.set_status(f"Error loading image: {e}", is_error=True)

    def restart_game(self):
        """Restart the game by prompting the user to upload a new image."""
        self.load_image_from_dialog()

    def handle_click(self, x, y):
        if self.diff_manager is None:
            self.app.set_status("No image loaded. Please load an image first.", is_error=True)
            return
        if not self.diff_manager.game_active:
            self.app.set_status("Game over! Load a new image to play again.", is_error=True)
            return
        hit, idx = self.diff_manager.check_click(x, y)
        if hit:
            # Mark difference as found: draw red circle on both images
            diff = self.diff_manager.differences[idx]
            center = diff.center
            # Draw on original image (left)
            orig_cv = self.image_processor.get_original_cv()
            self.image_processor.draw_circle(orig_cv, center, radius=20, color=(255,0,0), thickness=3)
            self.image_processor.original_pil = Image.fromarray(orig_cv)
            # Draw on modified image (right)
            mod_cv = self.image_processor.get_modified_cv()
            self.image_processor.draw_circle(mod_cv, center, radius=20, color=(255,0,0), thickness=3)
            self.image_processor.modified_pil = Image.fromarray(mod_cv)
            # Update GUI
            self.app.update_original_image(self.image_processor.original_pil)
            self.app.update_modified_image(self.image_processor.modified_pil)
            remaining = sum(1 for d in self.diff_manager.differences if not d.found)
            mistakes = self.diff_manager.mistakes
            self.app.update_score_display(remaining, mistakes)
            self.app.set_status(f"Found a difference! {remaining} remaining.")
            if self.diff_manager.all_found():
                self.app.show_message("Congratulations!", "You found all 5 differences!")
                self.app.set_status("All differences found! Load a new image to continue.")
                self.app.enable_reveal_button(False)
        else:
            # Mistake
            mistakes = self.diff_manager.mistakes
            remaining = sum(1 for d in self.diff_manager.differences if not d.found)
            self.app.update_score_display(remaining, mistakes)
            if not self.diff_manager.game_active:
                self.app.set_status(f"You made {mistakes} mistakes! Game over.", is_error=True)
                self.app.enable_reveal_button(False)
                self.app.show_game_over_dialog(self.restart_game, self.show_differences)
            else:
                self.app.set_status(f"Mistake! {3 - mistakes} attempts left.", is_error=True)

    def reveal(self):
        """Reveal unfound differences during active gameplay (toolbar button)."""
        if self.diff_manager is None or not self.diff_manager.game_active:
            return
        self.show_differences()

    def show_differences(self):
        """Show all differences: found in red, unfound in blue.
        Works regardless of game_active state (used by game-over dialog)."""
        if self.diff_manager is None:
            return
        orig_cv = self.image_processor.get_original_cv()
        mod_cv = self.image_processor.get_modified_cv()
        for diff in self.diff_manager.differences:
            center = diff.center
            if diff.found:
                # Already-found differences shown in red
                color = (255, 0, 0)
            else:
                # Unfound differences shown in blue
                color = (0, 0, 255)
            self.image_processor.draw_circle(orig_cv, center, radius=20, color=color, thickness=3)
            self.image_processor.draw_circle(mod_cv, center, radius=20, color=color, thickness=3)
        self.image_processor.original_pil = Image.fromarray(orig_cv)
        self.image_processor.modified_pil = Image.fromarray(mod_cv)
        self.app.update_original_image(self.image_processor.original_pil)
        self.app.update_modified_image(self.image_processor.modified_pil)
        self.app.set_status("Red = found, Blue = unfound. Load a new image to play again.")
        self.app.enable_reveal_button(False)
        # Disable further clicks
        self.diff_manager.game_active = False
