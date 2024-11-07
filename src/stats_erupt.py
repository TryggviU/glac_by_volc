"""
Script used to find documented eruptions of volcanoes within RGI regions.
The user must first have successfully run the 'volc_in_rgi.py' script.
Input: Data file* from GVP - https://volcano.si.edu/search_eruption.cfm
Output:

*file must be converted from .xml to .csv prior to usage.
"""

import os
import numpy as np
import geopandas as gpd
# Arguments
import argparse
# Modules.
import glacvolc.glacvolc_processing as gv_proc
import tools.tools as tools

# Set the root directory as the project directory.
dir_root = tools.set_root(path=os.getcwd(), name="glac_by_volc")
# Data directories.
dir_data = os.path.join(dir_root, "data")
dir_data_proc = os.path.join(dir_root, "data_processed")

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
# Read arguments from the command line
args = parser.parse_args()


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
    dir_results = tools.mkdir_ifnot_exist(
        path=os.path.join(dir_data_proc, "global_files", f"{RGI_v}-GV"),
        path_proj=dir_root
    )

    gvp_eruptions.to_csv(
        os.path.join(dir_results, f"GVP_GV_Eruptions_{float(radius)}km.csv"),
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
        os.path.join(dir_results, f"GVP_GV_Eruptions_{float(radius)}km.shp")
    )


def main():
    for radius in args.radius:
        find_glacvolc_eruptions(radius=radius)


if __name__ == "__main__":
    main()
