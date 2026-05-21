"""
Lab Work #4
Task 3: Series Approximation and Statistics
Variant 2

Description:
Compute function using Taylor series and math module,
calculate statistics and plot graphs.
"""

import math
import statistics
import matplotlib.pyplot as plt


class FunctionAnalysis:
    """Class for analyzing function values"""

    def __init__(self, x_values, n_terms):
        self.x_values = x_values
        self.n_terms = n_terms
        self.series_values = []
        self.math_values = []

    # Taylor series for sin(x)
    def taylor_sin(self, x):
        result = 0
        for n in range(self.n_terms):
            result += ((-1) ** n) * (x ** (2 * n + 1)) / math.factorial(2 * n + 1)
        return result

    def calculate(self):
        for x in self.x_values:
            self.series_values.append(self.taylor_sin(x))
            self.math_values.append(math.sin(x))


    def mean(self):
        return statistics.mean(self.series_values)

    def median(self):
        return statistics.median(self.series_values)

    def mode(self):
        try:
            return statistics.mode(self.series_values)
        except:
            return "No unique mode"

    def variance(self):
        return statistics.variance(self.series_values)

    def std_dev(self):
        return statistics.stdev(self.series_values)


    def plot(self):
        plt.figure()

        plt.plot(self.x_values, self.series_values, label="Taylor Series")
        plt.plot(self.x_values, self.math_values, label="math.sin(x)")

        plt.xlabel("x")
        plt.ylabel("y")
        plt.title("Function Comparison")
        plt.legend()
        plt.grid()

        plt.savefig("graph.png")


    def print_stats(self):
        print("Mean:", self.mean())
        print("Median:", self.median())
        print("Mode:", self.mode())
        print("Variance:", self.variance())
        print("Std Dev:", self.std_dev())

    def print_table(self):
        indices = [0, 4, 9]

        print(f"| {'X':^10} | {'n':^6} | {'Taylor F(x)':^15} | {'math.sin(x)':^15} | {'Разница':^12} |")
        print("-" * 80)

        for i in indices:
            x = self.x_values[i]
            taylor = self.series_values[i]
            real = self.math_values[i]
            diff = abs(taylor - real)

            print(f"| {x:^10.2f} | {self.n_terms:^6} | {taylor:^15.8f} | {real:^15.8f} | {diff:^12.2e} |")

        print("-" * 80)
        print(f"Всего точек: {len(self.x_values)} | Членов ряда: {self.n_terms}")
        print("=" * 80)

# ================= MAIN =================

def main():
    # generate x values
    x_values = [i * 0.5 for i in range(-10, 11)]
    n_terms = 10

    analysis = FunctionAnalysis(x_values, n_terms)

    analysis.calculate()
    analysis.print_stats()
    analysis.plot()
    analysis.print_table()


if __name__ == "__main__":
    main()