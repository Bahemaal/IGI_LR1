"""
Lab Work #4
Task 5: NumPy Matrix Operations
Variant 2

Description:
Generate matrix, find elements greater than mean,
compute standard deviation using NumPy and manually.
"""

import numpy as np


class MatrixAnalysis:
    """Class for matrix operations"""

    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.matrix = np.random.randint(1, 100, (n, m))

    def show_matrix(self):
        print("Matrix A:")
        print(self.matrix)

    def elements_above_mean(self):
        mean_value = np.mean(self.matrix)
        print("Mean value:", round(mean_value, 2))

        elements = self.matrix[self.matrix > mean_value]
        print("Elements above mean:", elements)

        return elements

    # ===== NumPy method =====
    def std_numpy(self, elements):
        return round(np.std(elements), 2)

    # ===== Manual method =====
    def std_manual(self, elements):
        mean = sum(elements) / len(elements)

        variance = sum((x - mean) ** 2 for x in elements) / len(elements)

        std = variance ** 0.5
        return round(std, 2)


# ================= MAIN =================

def main():
    try:
        n = int(input("Enter number of rows: "))
        m = int(input("Enter number of columns: "))

        if n <= 0 or m <= 0:
            print("Matrix size must be positive.")
            return

        analysis = MatrixAnalysis(n, m)

        analysis.show_matrix()

        elements = analysis.elements_above_mean()

        if len(elements) == 0:
            print("No elements above mean.")
            return

        print("\nStandard deviation (NumPy):", analysis.std_numpy(elements))
        print("Standard deviation (Manual):", analysis.std_manual(elements))

    except ValueError:
        print("Invalid input.")


if __name__ == "__main__":
    main()