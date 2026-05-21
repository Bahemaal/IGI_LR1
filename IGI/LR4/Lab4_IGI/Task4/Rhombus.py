from Task4.Shape import Shape
from Task4.RhombusMixin import RhombusMixin
import matplotlib.pyplot as plt
from Task4.Color import Color

class Rhombus(Shape, RhombusMixin):
    """Rhombus defined by diagonals"""

    name = "Rhombus"

    def __init__(self, d1, d2, color):
        self.d1 = d1
        self.d2 = d2
        self.color_obj = Color(color)

    def area(self):
        return (self.d1 * self.d2) / 2

    def get_info(self):
        return "Shape: {}\nDiagonal1: {}\nDiagonal2: {}\nColor: {}\nArea: {:.2f}".format(
            self.name,
            self.d1,
            self.d2,
            self.color_obj.color,
            self.area()
        )

    def draw(self):
        # Coordinates of rhombus
        x = [0, self.d1/2, 0, -self.d1/2, 0]
        y = [self.d2/2, 0, -self.d2/2, 0, self.d2/2]

        plt.figure()
        plt.fill(x, y, color=self.color_obj.color)
        plt.plot(x, y)

        plt.text(0, 0, self.name, ha='center')

        plt.title("Rhombus")
        plt.grid()
        plt.axis('equal')

        plt.savefig("rhombus.png")
