"""
Lab Work #4
Task 6: Pandas Data Analysis
Variant 2

Description:
Basic Pandas operations using Iris dataset.
"""
import pathlib

import pandas as pd


class IrisAnalysis:
    """Class for Iris dataset analysis"""

    def __init__(self, filename):
        self.df = pd.read_csv(filename)

    # ================= TASK A =================

    def create_series(self):
        petal_length = pd.Series(
            self.df['PetalLengthCm'].head(5).values,
            index=[1, 2, 3, 4, 5]
        )

        print("Series petal_length:")
        print(petal_length)

        print("\nThird element (.iloc):")
        print(petal_length.iloc[2])

        print("\nElement with index 4 (.loc):")
        print(petal_length.loc[4])

    # ================= TASK B =================

    def statistics(self):

        # Mean sepal length for Iris-setosa
        setosa_mean = self.df[
            self.df['Species'] == 'Iris-setosa'
        ]['SepalLengthCm'].mean()

        print("\nMean Sepal Length (Iris-setosa):")
        print(round(setosa_mean, 2))

        # Mean petal width
        virginica_mean = self.df[
            self.df['Species'] == 'Iris-virginica'
        ]['PetalWidthCm'].mean()

        versicolor_mean = self.df[
            self.df['Species'] == 'Iris-versicolor'
        ]['PetalWidthCm'].mean()

        ratio = virginica_mean / versicolor_mean

        print("\nRatio:")
        print(round(ratio, 2))


# ================= MAIN =================

def main():
    parent = pathlib.Path(__file__).parent
    try:
        input_file = parent / "Iris.csv"
        analysis = IrisAnalysis(input_file)

        analysis.create_series()

        analysis.statistics()

    except FileNotFoundError:
        print("Dataset file not found.")

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()