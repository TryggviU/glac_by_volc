"""
Script used to:
 (1) Find documented eruptions of volcanoes within RGI regions.
 (2) Compute trends for the glaciers around the volcanoes.
The user must first have successfully run the 'volc_in_rgi.py' script.

Input:
Data file* from GVP - https://volcano.si.edu/search_eruption.cfm and outputs from previous scripts.
*file must be converted from .xml to .csv prior to usage.


Output:
.csv file(s) with the stats for each volcano, stored in the "results" subdirectory.
"""

# System
import os
# Basic
import numpy as np
import pandas as pd
# Arguments
import argparse
# Geospatial data
import geopandas as gpd
# Modules
import geo.geo_processing as geo_proc
import glacvolc.glacvolc_processing as gv_proc
import tools.tools as tools
import stats.fit as fit


# Set the root directory as the project directory.
dir_root = tools.set_root(path=os.getcwd(), name="glac_by_volc")
# Data directories.
dir_data = os.path.join(dir_root, "data")
dir_data_proc = os.path.join(dir_root, "data_processed")
dir_results = tools.mkdir_ifnot_exist(
    path=os.path.join(dir_root, "results"),
    path_proj=dir_root
)

# The RGI version code/phrase (e.g. RGI2000-v7.0).
RGI_v = os.path.basename(
    tools.find_files_within_path(
        path=os.path.join(dir_data, "RGI"),
        filename="RGI"
    )[0]
)[0:12]

# Initiate the argument parser.
parser = argparse.ArgumentParser()
# Add arguments.
parser.add_argument("-r", "--radius", action="store", nargs="*", type=float, default=[5, 10, 20, 40],
                    help="Maximum radial distance, in kilometres, of search buffer for glaciers surrounding volcano.")
parser.add_argument("-x", "--exogenous", action="store", nargs="*", type=str, default=["distance"],
                    help="The explanatory (exogenous) variable(s).")
parser.add_argument("-y", "--endogenous", action="store", nargs="*", type=str, default=["dzmed"],
                    help="The target (endogenous) variable.")
parser.add_argument("-n", "--n_min", action="store", nargs="*", type=int, default=4,
                    help="The minimum number of glaciers to be used when fitting results.")
parser.add_argument("-a", "--years", action="store", nargs=2, type=int, default=[1990, 2010],
                    help="The years that set the time period that should be checked for eruptions.")
# Read arguments from the command line
args = parser.parse_args()


def read_gvp_regional(RGI_id):
    return gpd.read_file(
        tools.find_files_within_path(
            path=dir_data_proc,
            filename=f"{RGI_v}-V-{RGI_id}.shp"
        )[0],
        crs="EPSG:4326"
    )


def eruption_id(gdf):
    """
    Create ID numbers for eruptions as 'YYYYMMDD - GVP_ID'

    :param gdf: GeoDataFrame containing GPV eruption info.
    :return: the input GeoDataFrame with a column of eruption IDs.
    """

    def nan2zero(a):
        a[np.isnan(a)] = 0
        return a.astype(int)

    sy = gdf["Start Year"].to_numpy(dtype=int)
    sm = nan2zero(gdf["Start Month"].to_numpy())
    sd = nan2zero(gdf["Start Day"].to_numpy())
    vn = gdf["Volcano Name"].to_list()

    def date2str(y, m, d, n):
        if d == 0 and m != 0:
            m = f"0{m}"[-2:]
            return f"{y}{m} - {n}"
        elif m == 0:
            return f"{y} - {n}"
        else:
            m = f"0{m}"[-2:]
            d = f"0{d}"[-2:]

            return f"{y}{m}{d} - {n}"

    gdf["id"] = [
        date2str(y, m, d, n) for y, m, d, n in zip(sy, sm, sd, vn)
    ]

    return gdf


def find_glacvolc_eruptions(radius):
    """
    Find all GVP eruptions that happened within 'radius' of a glacier.

    :param radius: The search radius between volcanoes and glacier.
    :return: .csv file of all the eruptions that took place within 'radius' of a glacier.
    """

    print(f"Radius: {radius}km")

    # Read in the GVP volcanic eruptions as a GeoDataFrame.
    gvp_eruptions = gv_proc.read_gvp(
        tools.find_files_within_path(path=dir_data,
                                     filename="GVP_Eruption_Results.csv")[0]
    )

    # RGI regions with GVP.
    rgi_regions = [
        subdir.split("-")[-1] for subdir in os.listdir(os.path.join(dir_data_proc, "regional_files", f"{RGI_v}-GV"))
    ]

    # Initialise a dictionary to hold all regional glaciated volcanoes
    gvp_gv = []
    # Find all the glaciated volcanoes.
    for RGI_id in rgi_regions:
        # Read in the regional volcanoes as a DataFrame.
        try:
            gvp_gv += os.listdir(
                os.path.join(dir_data_proc, "regional_files", f"{RGI_v}-GV", f"{RGI_v}-GV-{RGI_id}",
                             f"{RGI_id}_{float(radius)}km")
            )
            print(f" - {RGI_id}")
        except FileNotFoundError:
            print(f" - {RGI_id}", f" - No volcanoes with glaciers within a {float(radius)}km radius.")

    gvp_gv = list(map(int, gvp_gv))

    # Isolate the glaciated volcanoes from the eruption list.
    for i in range(len(gvp_eruptions)):
        if gvp_eruptions.loc[i, "Volcano Number"] not in gvp_gv:
            gvp_eruptions = gvp_eruptions.drop(i)

    # Create a result directory.
    dir_GV = tools.mkdir_ifnot_exist(
        path=os.path.join(dir_data_proc, "global_files", f"{RGI_v}-GV"),
        path_proj=dir_root
    )

    gvp_eruptions.to_csv(
        os.path.join(dir_GV, f"GVP_GV_Eruptions_{float(radius)}km.csv"),
        index=False
    )

    gvp_eruptions = eruption_id(gdf=gvp_eruptions)

    # Create a GeoDataFrame.
    gvp = gpd.GeoDataFrame(
        gvp_eruptions["id"],
        geometry=gpd.points_from_xy(gvp_eruptions.Longitude, gvp_eruptions.Latitude),
        crs="EPSG:4326"
    )

    gvp.to_file(
        os.path.join(dir_GV, f"GVP_GV_Eruptions_{float(radius)}km.shp")
    )


def who_erupted(gvp, radius, ymin=None, ymax=None):
    """
    Find the volcanoes in the 'gvp' GeoDataFrame that erupted between the years of 'ymin' and 'ymax'.

    :param gvp: A GeoDataFrame of GVP volcanoes.
    :param radius: The search radius for glaciers around volcanoes.
    :param ymin: The minimum year.
    :param ymax: The maximum year.
    :return: The 'gvp' GeoDataFrame with an 'Erupted' column of 1s and 0s meaning it did or did not erupt, respectively.
    """

    # Add an eruption info column.
    gvp["Erupted"] = np.zeros(len(gvp), dtype=int)
    gvp["f_erupt"] = np.zeros(len(gvp), dtype=float)

    # Read in the GVP volcanic eruptions as a GeoDataFrame.
    gvp_eruptions = pd.read_csv(
        tools.find_files_within_path(
            path=dir_data_proc,
            filename=f"GVP_GV_Eruptions_{float(radius)}km.csv")[0],
        encoding='latin-1'
    )

    if not ymin:
        ymin = gvp_eruptions["Start Year"].min()

    if not ymax:
        ymax = gvp_eruptions["Start Year"].max()

    # Array of GVP IDs that have erupted during the period (IDs are repeated for each eruption).
    v_e = gvp_eruptions.loc[
        np.logical_and(gvp_eruptions["Start Year"] <= ymax, gvp_eruptions["Start Year"] >= ymin),
        "Volcano Number"
    ].to_numpy()
    # Array of GVP IDs that have erupted during the period (non-repeating).
    GVP_id_e = np.unique(v_e)

    for i in gvp.index:
        # Did the volcano erupt? Yes = 1, No = 0.
        if gvp.loc[i, "Volcano Number"] in GVP_id_e:
            gvp.loc[i, "Erupted"] = 1

        # Compute the frequency of eruptions per year.
        gvp.loc[i, "f_erupt"] = len(v_e[v_e == gvp.loc[i, "Volcano Number"]]) / (ymax - ymin)

    return gvp


def is_mostly_nan(df, cols, n_min=args.n_min):
    """
    Check if there are not enough variables to perform trend tests.

    :param df: DataFrame
    :param cols: The columns to be inspected.
    :param n_min: The minimum number of variables.
    :return: True or False
    """

    for col in cols:
        if np.isnan(df[col]).all():
            return True

        if len(df[col]) - np.isnan(df[col]).sum() < n_min:
            return True

    return False


def run_fit_analysis(df, col_x=args.exogenous[0], col_y=args.endogenous[0]):
    """
    Run the statistical fitting analysis of the data, using:
        LR: Simple Linear Regression
        MK: Mann-Kendall test
        SR: Spearman's Rho test
    :param df: DataFrame
    :param col_x: the explanatory variable.
    :param col_y: the target variable.
    :return:
    """

    df_res = pd.DataFrame(
        data={
            "LR_s": [np.nan],
            "LR_p": [np.nan],
            "LR_r": [np.nan],
            #"MK_t": [np.nan],
            "MK_s": [np.nan],
            "MK_p": [np.nan],
            "MK_r": [np.nan],
            "SR_r": [np.nan],
            "SR_p": [np.nan]
        }
    )

    # Check if any of the arrays mostly contains NaN's.
    if is_mostly_nan(df=df, cols=[col_x, col_y]):
        print(" - Not enough variables.")
        return df_res

    fit_LR = fit.SimpleLinearRegression(df=df, col_x=col_x, col_y=col_y)
    df_res["LR_s"] = fit_LR.slope
    df_res["LR_p"] = fit_LR.pvalue
    df_res["LR_r"] = fit_LR.rvalue

    fit_LR = fit.MultipleLinearRegression(df=df, col_x=[col_x], col_y=[col_y])
    df_res["LR_s"] = fit_LR.params[args.exogenous].values[0]
    df_res["LR_p"] = fit_LR.pvalues[args.exogenous].values[0]
    df_res["LR_r"] = np.sign(df_res["LR_s"]) * np.sqrt(fit_LR.rsquared)

    fit_MK = fit.MannKendallTest(df=df, col_x=col_x, col_y=col_y)

    df_res["MK_s"] = fit_MK.slope
    df_res["MK_p"] = fit_MK.p
    df_res["MK_r"] = fit_MK.Tau

    fit_SR = fit.SpearmanCorrelationCoefficient(df=df, col_x=col_x, col_y=col_y)
    df_res["SR_r"] = fit_SR.statistic
    df_res["SR_p"] = fit_SR.pvalue

    return df_res


def gvp_analysis(GVP_id, RGI_id, radius, rgi_shp):
    """
    Run the statistical analysis for a given volcano.

    :param GVP_id: Volcano ID number.
    :param RGI_id: RGI region ID number.
    :param radius: The search radius.
    :param rgi_shp: The path to the .shp file of the volcano's surrounding glaciers.
    :return: A DataFrame with the volcano info and stats.
    """

    # The RGI regional volcanoes.
    gvp = read_gvp_regional(RGI_id=RGI_id)

    # Read in the glaciers within the radial distance from the volcano.
    rgi = gpd.read_file(rgi_shp)

    # Add the Delta z_min/med/max as columns.
    for m in ["min", "med", "max"]:
        rgi[f"dz{m}"] = rgi[f"z{m}_m"] - rgi[f"z{m}_m"].mean()

    # Transform to UTM.
    rgi = rgi.to_crs(rgi.estimate_utm_crs())
    gvp_crs = gvp.to_crs(rgi.crs)

    # A GeoDataFrame of the volcano itself.
    volcano = gpd.GeoSeries(gvp_crs[gvp_crs["Volcano Nu"] == int(GVP_id)].geometry.to_list(), crs=rgi.crs)

    # Search for other close-by volcanoes.
    close_by_volcanoes = gvp_crs.clip(volcano.buffer(2 * radius * 1e3))
    # Exclude the volcano from the close-by ones.
    close_by_volcanoes = close_by_volcanoes[close_by_volcanoes["Volcano Nu"] != int(GVP_id)]

    # Compute the distance between the volcano and all the glaciers within the search radius.
    rgi = geo_proc.compute_distance(f1=volcano, f2=rgi, f3=close_by_volcanoes)

    # A DataFrame for the volcano.
    df_gvp = pd.DataFrame(
        data={
            "Volcano Number": [GVP_id],
            "Volcano Name": [gvp["Volcano Na"][gvp["Volcano Nu"] == GVP_id].values[0]],
            "rgi_region": [RGI_id],
            "Latitude": [gvp["Latitude"][gvp["Volcano Nu"] == GVP_id].values[0]],
            "Longitude": [gvp["Longitude"][gvp["Volcano Nu"] == GVP_id].values[0]],
            "r_km": [radius],
            "n_glac": [len(rgi)],
            "A_glac_km2": [rgi["area_km2"].sum()]
        }
    )

    # Run the statistical analysis for the glaciers around the volcano.
    return pd.concat([df_gvp, run_fit_analysis(df=rgi)], axis=1)


def main():
    """
    Find all volcanoes with glaciers within 'radius', and perform a statistical analysis on the volcanic glaciers.

    :return: .csv files with the statistics.
    """

    # Find all the glaciovolcanic eruptions.
    for radius in args.radius:
        find_glacvolc_eruptions(radius=radius)

    # Create a DataFrame for the results
    df = pd.DataFrame()

    # Iterate through all the different volcanoes and search radii.
    for path, dirs, files in os.walk(os.path.join(dir_data_proc, "regional_files", f"{RGI_v}-GV")):
        for file in files:
            if file.endswith("glaciers.shp"):
                # Get the GVP ID, RGI ID, and the search radius.
                GVP_id = int(file[0:6])
                RGI_id = path.split("\\")[-3].split("-")[-1]
                radius = float(file.split('_')[1].split('km')[0])

                print(f"Volcano nr: {GVP_id}, search radius: {radius} km")

                # Join each volcano's result to the final DataFrame.
                df = tools.join_df(
                    df1=df,
                    df2=gvp_analysis(
                        GVP_id=GVP_id,
                        RGI_id=RGI_id,
                        radius=radius,
                        rgi_shp=os.path.join(path, file)
                    )
                )

    # Export the results for each radius as a .csv file.
    for rad in df["r_km"].unique():
        # Isolate each radius from the data.
        df_rad = df.loc[df["r_km"] == rad].sort_values(by=["rgi_region", "Volcano Number"])
        # Drop the radius column
        df_rad.drop(columns=["r_km"], axis=1, inplace=True)

        # Add eruption info.
        df_rad = who_erupted(gvp=df_rad, radius=rad, ymin=args.years[0], ymax=args.years[1])

        # Write the .csv file.
        df_rad.to_csv(
            os.path.join(
                dir_results,
                f"{RGI_v}-GV-stats-{'-'.join(args.endogenous)}_{float(rad)}km.csv"),
            index=False
        )


if __name__ == "__main__":
    main()
