"""
Lab Work #4
Task 4: Geometry Classes
Variant 2 – Rhombus by diagonals

Description:
Implements abstract shape, color class and rhombus.
Draws shape and saves it to file.
"""

from Task4.Rhombus import Rhombus


#input

def input_values():
    while True:
        try:
            d1 = float(input("Enter diagonal d1: "))
            d2 = float(input("Enter diagonal d2: "))

            if d1 <= 0 or d2 <= 0:
                print("Values must be positive.")
                continue

            color = input("Enter color: ")

            return d1, d2, color

        except ValueError:
            print("Invalid input. Try again.")



def main():
    d1, d2, color = input_values()

    rhombus = Rhombus(d1, d2, color)

    print("\n--- RHOMBUS INFO ---")
    rhombus.rhombus_print()
    print(rhombus.get_info())
    rhombus.draw()


if __name__ == "__main__":
    main()