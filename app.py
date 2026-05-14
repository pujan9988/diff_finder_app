
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImagePanel(tk.Frame):
    """
    A frame that displays an image, scaled to fit, optionally clickable.
    Initially shows "No image loaded".
    """
    def __init__(self, parent, title="", clickable=False, callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.clickable = clickable
        self.callback = callback
        self.original_pil = None
        self.display_image = None
        self.display_width = 0
        self.display_height = 0

        if title:
            title_label = tk.Label(self, text=title, font=('Arial', 10, 'bold'), bg='#2c3e50', fg='white')
            title_label.pack(side='top', pady=2, fill='x')

        self.image_label = tk.Label(self, bg='#ecf0f1', text="No image loaded", font=('Arial', 12))
        self.image_label.pack(expand=True, fill='both')

        if self.clickable:
            self.image_label.bind('<Button-1>', self._on_click)

        self.bind('<Configure>', self._on_frame_resize)
        self._resize_job = None
        self.configure(bg='#2c3e50')

    def update_image(self, pil_image):
        if pil_image is None:
            self.clear_image()
            return
        self.original_pil = pil_image.copy()
        self._resize_and_display()

    def clear_image(self):
        self.original_pil = None
        self.display_image = None
        self.image_label.config(image='', text="No image loaded")

    def _on_frame_resize(self, event):
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(50, self._resize_and_display)

    def _resize_and_display(self):
        if self.original_pil is None:
            return
        frame_w = self.winfo_width()
        frame_h = self.winfo_height()
        if frame_w <= 1 or frame_h <= 1:
            return

        orig_w, orig_h = self.original_pil.size
        scale = min(frame_w / orig_w, frame_h / orig_h)
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        self.display_width = new_w
        self.display_height = new_h

        resized = self.original_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(resized)
        self.image_label.config(image=self.display_image, text="")
        self.image_label.place(relx=0.5, rely=0.5, anchor='center')

    def _on_click(self, event):
        if not self.clickable or self.original_pil is None:
            return
        img_w = self.display_width
        img_h = self.display_height
        label_w = self.image_label.winfo_width()
        label_h = self.image_label.winfo_height()
        offset_x = (label_w - img_w) // 2
        offset_y = (label_h - img_h) // 2
        click_img_x = event.x - offset_x
        click_img_y = event.y - offset_y
        if click_img_x < 0 or click_img_x >= img_w or click_img_y < 0 or click_img_y >= img_h:
            return
        orig_w, orig_h = self.original_pil.size
        orig_x = int(click_img_x * orig_w / img_w)
        orig_y = int(click_img_y * orig_h / img_h)
        orig_x = max(0, min(orig_w - 1, orig_x))
        orig_y = max(0, min(orig_h - 1, orig_y))
        if self.callback:
            self.callback(orig_x, orig_y)


class WelcomeFrame(tk.Frame):
    """Colorful welcome screen with game rules and a start button."""
    def __init__(self, parent, start_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#1a252f')
        self.start_callback = start_callback

        # Title
        title = tk.Label(self, text="🔍 FIND THE DIFFERENCES", font=('Arial', 28, 'bold'), 
                         bg='#1a252f', fg='#f39c12')
        title.pack(pady=(50, 20))

        # Rules box
        rules_frame = tk.Frame(self, bg='#2c3e50', relief=tk.GROOVE, bd=2)
        rules_frame.pack(pady=20, padx=40, fill='both', expand=True)

        rules_text = """
        GAME RULES:

        • Two images will appear side by side.
        • The RIGHT image contains 5 hidden differences.
        • Click on the RIGHT image to find them.
        • You have only 3 mistakes per image.
        • Find all 5 to win the round!
        • Use the REVEAL button if you give up.
        • Load a new image anytime to keep playing.

        Good luck and have fun!
        """
        rules_label = tk.Label(rules_frame, text=rules_text, font=('Arial', 12), 
                               bg='#2c3e50', fg='white', justify='left')
        rules_label.pack(padx=20, pady=20)

        # Start button
        start_btn = tk.Button(self, text="LOAD IMAGE & START", font=('Arial', 14, 'bold'),
                              bg='#f39c12', fg='#1a252f', padx=20, pady=10,
                              command=self.start_callback)
        start_btn.pack(pady=30)

        # Footer
        footer = tk.Label(self, text="© 2025 Find the Differences Game", font=('Arial', 9),
                          bg='#1a252f', fg='#7f8c8d')
        footer.pack(side='bottom', pady=10)


class GameFrame(tk.Frame):
    """Frame containing the actual game (image panels and controls)."""
    def __init__(self, parent, click_callback, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#2c3e50')

        # Main container for images (side by side)
        main_frame = tk.Frame(self, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left panel (original)
        self.left_panel = ImagePanel(main_frame, title="📸 ORIGINAL", clickable=False)
        self.left_panel.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Right panel (modified, clickable)
        self.right_panel = ImagePanel(main_frame, title="🔍 MODIFIED (click here)", 
                                      clickable=True, callback=click_callback)
        self.right_panel.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        # Control panel at bottom
        control_frame = tk.Frame(self, bg='#34495e', relief=tk.RAISED, bd=2)
        control_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        self.load_btn = tk.Button(control_frame, text="📂 Load Another Image", 
                                  font=('Arial', 10), bg='#f39c12', fg='black')
        self.load_btn.pack(side='left', padx=5)

        self.reveal_btn = tk.Button(control_frame, text="🔎 Reveal", state='disabled',
                                    font=('Arial', 10), bg='#e74c3c', fg='black')
        self.reveal_btn.pack(side='left', padx=5)

        self.remaining_label = tk.Label(control_frame, text="✨ Remaining: --", 
                                        font=('Arial', 12, 'bold'), bg='#34495e', fg='white')
        self.remaining_label.pack(side='left', padx=20)

        self.mistakes_label = tk.Label(control_frame, text="❌ Mistakes: 0 / 3", 
                                       font=('Arial', 12), bg='#34495e', fg='white')
        self.mistakes_label.pack(side='left', padx=20)

        self.status_label = tk.Label(control_frame, text="Load an image to start", 
                                     font=('Arial', 10), bg='#34495e', fg='#1abc9c')
        self.status_label.pack(side='left', padx=20, expand=True)

    def get_controls(self):
        """Return control widgets so controller can modify them."""
        return {
            'load_btn': self.load_btn,
            'reveal_btn': self.reveal_btn,
            'remaining_label': self.remaining_label,
            'mistakes_label': self.mistakes_label,
            'status_label': self.status_label
        }

    def update_original_image(self, pil_image):
        self.left_panel.update_image(pil_image)

    def update_modified_image(self, pil_image):
        self.right_panel.update_image(pil_image)

    def clear_images(self):
        self.left_panel.clear_image()
        self.right_panel.clear_image()


class FindDifferenceApp(tk.Tk):
    """Main application with welcome and game frames."""
    def __init__(self):
        super().__init__()
        self.title("Find the Differences")
        self.geometry("1100x700")
        self.minsize(800, 600)
        self.configure(bg='#1a252f')

        # Container to hold either welcome or game frame
        self.container = tk.Frame(self, bg='#1a252f')
        self.container.pack(fill='both', expand=True)

        # Initially show welcome frame
        self.welcome_frame = WelcomeFrame(self.container, start_callback=self.show_game_frame)
        self.welcome_frame.pack(fill='both', expand=True)

        self.game_frame = None
        self.controller = None

    def show_game_frame(self):
        self.welcome_frame.pack_forget()
        if self.game_frame is None:
            self.game_frame = GameFrame(self.container, click_callback=self.on_game_click)
        self.game_frame.pack(fill='both', expand=True)

        # If controller is already set, connect the load button command
        if self.controller:
            ctrl = self.game_frame.get_controls()
            ctrl['load_btn'].config(command=self.controller.load_image_from_dialog)
            ctrl['reveal_btn'].config(command=self.controller.reveal)
            # Optionally, automatically open file dialog? But the user already clicked start, so we call load
            self.controller.load_image_from_dialog()
        else:
            self.game_frame.status_label.config(text="Controller not set – cannot load image")

    def set_controller(self, controller):
        self.controller = controller
        if self.game_frame:
            ctrl = self.game_frame.get_controls()
            ctrl['load_btn'].config(command=controller.load_image_from_dialog)
            ctrl['reveal_btn'].config(command=controller.reveal)

    def on_game_click(self, x, y):
        if self.controller:
            self.controller.handle_click(x, y)

    # Delegation methods for controller to update UI
    def update_score_display(self, remaining, mistakes):
        if self.game_frame:
            self.game_frame.remaining_label.config(text=f"✨ Remaining: {remaining}")
            self.game_frame.mistakes_label.config(text=f"❌ Mistakes: {mistakes} / 3")

    def set_status(self, message, is_error=False):
        if self.game_frame:
            color = '#e74c3c' if is_error else '#1abc9c'
            self.game_frame.status_label.config(text=message, fg=color)

    def enable_reveal_button(self, enabled=True):
        if self.game_frame:
            state = 'normal' if enabled else 'disabled'
            self.game_frame.reveal_btn.config(state=state)

    def show_message(self, title, message):
        messagebox.showinfo(title, message)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message)

    def update_original_image(self, pil_image):
        if self.game_frame:
            self.game_frame.update_original_image(pil_image)

    def update_modified_image(self, pil_image):
        if self.game_frame:
            self.game_frame.update_modified_image(pil_image)

    def clear_images(self):
        if self.game_frame:
            self.game_frame.clear_images()

    def show_game_over_dialog(self, try_again_callback, show_diff_callback):
        dialog = tk.Toplevel(self)
        dialog.title("Game Over")
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.configure(bg='#2c3e50')
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 350) // 2
        y = self.winfo_y() + (self.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        lbl = tk.Label(dialog, text="Game Over! No attempts left.", font=('Arial', 14, 'bold'), bg='#2c3e50', fg='white')
        lbl.pack(pady=25)
        
        btn_frame = tk.Frame(dialog, bg='#2c3e50')
        btn_frame.pack(pady=10)
        
        def on_try_again():
            dialog.destroy()
            try_again_callback()
            
        def on_show_diff():
            dialog.destroy()
            show_diff_callback()
            
        btn_try = tk.Button(btn_frame, text="Restart Game", font=('Arial', 10, 'bold'), command=on_try_again, bg='#3498db', fg='black', padx=10, pady=5)
        btn_try.pack(side='left', padx=15)
        
        btn_diff = tk.Button(btn_frame, text="Reveal Differences", font=('Arial', 10, 'bold'), command=on_show_diff, bg='#e74c3c', fg='black', padx=10, pady=5)
        btn_diff.pack(side='left', padx=15)

        dialog.wait_visibility()
        dialog.grab_set()