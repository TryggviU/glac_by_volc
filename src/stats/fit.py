# Basic
import numpy as np
# Statistics
from scipy import stats
import statsmodels.api as sm
from patsy import dmatrices
import pymannkendall as mk


def SimpleLinearRegression(df, col_x, col_y):
    """
    Simple linear regression using Scipy's stats module.

    :param df: DataFrame
    :param col_x: The x data column.
    :param col_y: The y data column.
    :return: The fitted model.
    """

    # Filter out NaN values
    mask = ~np.isnan(df[col_x].to_numpy()) & ~np.isnan(df[col_y].to_numpy())

    return stats.linregress(
        x=df[col_x][mask],
        y=df[col_y][mask]
    )


def SpearmanCorrelationCoefficient(df, col_x, col_y):
    """
    Simple linear regression using Scipy's stats module.

    :param df: DataFrame
    :param col_x: The x data column.
    :param col_y: The y data column.
    :return: The fitted model.
    """

    mask = ~np.isnan(df[col_x].to_numpy()) & ~np.isnan(df[col_y].to_numpy())

    return stats.spearmanr(
        a=df[col_x][mask],
        b=df[col_y][mask]
    )


def MultipleLinearRegression(df, col_x, col_y):
    """
    Multiple linear regression (Ordinary-Least-Squares) using statsmodels package.

    :param df: DataFrame
    :param col_x: The x data column(s).
    :param col_y: The y data column(s).
    :return: The fitted model.
    """

    formula = " ~ ".join([" + ".join(col_y), " + ".join(col_x)])

    # Fit the model to the data.
    y, X = dmatrices(formula, data=df, return_type="dataframe")
    model = sm.OLS(y, X)
    return model.fit()


def MannKendallTest(df, col_x, col_y):
    """
    A Mann-Kendall trend detection test.

    :param df: DataFrame
    :param col_x: The x data column.
    :param col_y: The y data column.
    :return: The fitted model.
    """

    # Sort the y-data based on the x-data.
    df = df.sort_values(by=col_x, ascending=True)

    return mk.original_test(df[col_y])
