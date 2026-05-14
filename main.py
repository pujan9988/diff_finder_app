from app import FindDifferenceApp
from game_controller import GameController

if __name__ == "__main__":
    app = FindDifferenceApp()
    controller = GameController(app)
    app.set_controller(controller)
    app.mainloop()