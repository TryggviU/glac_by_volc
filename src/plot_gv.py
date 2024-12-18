# System
import os
# Arguments
import argparse

import matplotlib.pyplot as plt
# Plotting
import proplot as pplt
from cmap import Colormap
# Geospatial data
import geopandas as gpd
import contextily as cx
from matplotlib_scalebar.scalebar import ScaleBar
# Modules
import geo.geo_processing as geo_proc
import glacvolc.glacvolc_processing as gv_proc
import tools.tools as tools
import tkn.tkn as tkn

pplt.rc.update({'mathtext.fontset': 'stixsans', 'mathtext.default': 'it',
                'legend.fontsize': 'xx-large', 'legend.title_fontsize': 'xx-large',
                'title.size': 20})

# Set the root directory as the project directory.
dir_root = tools.set_root(path=os.getcwd(), name="glac_by_volc")
# Data directories.
dir_data = os.path.join(dir_root, "data")
dir_data_proc = os.path.join(dir_root, "data_processed")
# Result figures directory
dir_figs = os.path.join(dir_root, "figs", "glacvolc_stats", "dzmed")
tools.mkdir_ifnot_exist(path=dir_figs, path_proj=dir_root)

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
parser.add_argument("-v", "--GVP_ids", action="store", nargs="*", type=int, default=[313030],
                    help="Select GVP identification number(s) of volcano(s).")
parser.add_argument("-r", "--radius", action="store", nargs="*", type=float, default=[5, 10, 20, 40],
                    help="Maximum radial distance, in kilometres, of search buffer for glaciers surrounding volcano.")
parser.add_argument("-a", "--all", action="store", nargs=1, type=bool, default=False,
                    help="If set to True, then figs created for all volcanoes.")
parser.add_argument("-n", "--n_min", action="store", nargs="*", type=int, default=4,
                    help="The minimum number of glaciers to be used when fitting results.")
parser.add_argument("-z", "--zmax", action="store", type=int, default=500,
                    help="Select the maximum relative median elevation showed on graphs.")
# Read arguments from the command line
args = parser.parse_args()

if args.all:
    args.radius = [5, 10, 20, 40]
    args.GVP_ids = gv_proc.read_gvp(
        tools.find_files_within_path(
            path=dir_data,
            filename="GVP_Volcano_List_Holocene.csv"
        )[0]
    )["Volcano Number"].values


def gvp_regional(GVP_id, gdf):
    """
    Find all regional volcanoes close to the dataframe.

    :param GVP_id: Volcano ID number from the Global Volcanism Program.
    :param gdf: A GeoDataFrame
    :return: A GeoDataFrame containing all volcanoes within gdf
    """

    # Read in the GVP volcanoes as a GeoDataFrame.
    gvp_attributes = gv_proc.read_gvp(
        tools.find_files_within_path(
            path=dir_data,
            filename="GVP_Volcano_List_Holocene.csv"
        )[0]
    )
    gvp = gpd.GeoDataFrame(
        gvp_attributes,
        geometry=gpd.points_from_xy(gvp_attributes.Longitude, gvp_attributes.Latitude),
        crs="EPSG:4326"
    )
    # Return the volcanoes within the region.
    return tools.join_df(
        df1=gvp[gvp["Volcano Number"] == GVP_id],
        df2=geo_proc.shapes_within_gdf(
            gdf=geo_proc.bounding_box(gdf=gdf, padding=0.2),
            shapes=gvp[gvp["Volcano Number"] != GVP_id])[1]
    )
    # return geo_proc.shapes_within_rad(point=gvp[gvp["Volcano Number"] == GVP_id], shapes=gvp, rad=radius * 1.2e3)[1]


def gvp2rgi(GVP_id, radius):
    """
    Find which RGI region a volcano belongs to.

    :param GVP_id: Volcano ID number from the Global Volcanism Program.
    :param radius: Search radius
    :return: RGI regional code.
    """

    subdir = os.path.normpath(
        tools.find_files_within_path(
            path=dir_data_proc,
            filename=f"{GVP_id}_{float(radius)}km-glaciers.shp"
        )[0]
    ).split(os.sep)[-4]

    return subdir.split("-")[-1]


def in_n_out_glaciers(GVP_id, radius, padding=0.2):
    """
    Find glaciers within and outside the search radius.

    :param GVP_id: Volcano ID number from the Global Volcanism Program.
    :param radius: Search radius
    :param padding: Padding/buffer around the GeoDataFrame to be applied. Given as a fraction of width/height, so
        bbox_width/height = gdf_width/height * (1 + 2 * padding)
    :return:
    """

    # Read in the glaciers around the volcano.
    gdf = gpd.read_file(
        tools.find_files_within_path(
            path=dir_data_proc,
            filename=f"{GVP_id}_{float(radius)}km-glaciers.shp"
        )[0]
    )

    # Find all regional RGI glaciers within an enlarged bounding box.
    rgi = gpd.read_file(
        tools.find_files_within_path(
            path=dir_data,
            filename=f"{RGI_v}-G-{gvp2rgi(GVP_id, radius)}.shp"
        )[0]
    ).clip(geo_proc.bounding_box(gdf=gdf, padding=padding))

    # Remove the volcanic glaciers from the outer glaciers.
    for i in rgi.index:
        if rgi.loc[i, "rgi_id"] in gdf["rgi_id"].to_list():
            rgi.drop(index=i, inplace=True)

    return gdf, rgi


def plot_volc_dzmed(GVP_id, radius, cmap=Colormap('colorbrewer:RdYlBu_r').to_mpl(), vmin=-args.zmax, vmax=args.zmax):
    """
    A function that plots the relative median elevation of glaciers surrounding volcanoes.

    :param GVP_id: Volcano ID number from the Global Volcanism Program.
    :param radius: Search radius
    :param cmap: colormap to be used.
    :param vmin: minimum dzmed value
    :param vmax: maximum dzmed value
    :return:
    """

    # Read in the glaciers around the volcano.
    gdf, rgi = in_n_out_glaciers(GVP_id=GVP_id, radius=radius, padding=0.2)

    # Quit if too few glaciers.
    if len(gdf) < args.n_min:
        print(f" - Too few glaciers (n={len(gdf)}).")
        return

    # Read in the volcanoes.
    gvp = gvp_regional(GVP_id=GVP_id, gdf=gdf)

    # Compute the median of dz and add to the GeoDataFrame.
    gdf["dzmed_m"] = gdf["zmed_m"] - gdf["zmed_m"].mean()

    # Get the extent of the data for plotting.
    if len(gvp.clip(geo_proc.bounding_box(gdf=gdf))) == 0:  # ensure volcano is included in data extent.
        pv = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(gvp.Longitude, gvp.Latitude),
            crs="EPSG:4326"
        )
        pg = gpd.GeoDataFrame(
            geometry=gdf.geometry,
            crs="EPSG:4326"
        )
        xmin, ymin, xmax, ymax = geo_proc.bounding_box(gdf=tools.join_df(df1=pv, df2=pg), padding=0.1).total_bounds
    else:
        xmin, ymin, xmax, ymax = geo_proc.bounding_box(gdf=gdf, padding=0.1).total_bounds

    a = (xmax - xmin) / (ymax - ymin)
    if a > 2:
        a = 2

    fig, ax = pplt.subplots(nrows=1, ncols=1, tight=True, figsize=(a*9, 9))
    ax.format(labelsize=20, ticklabelsize=12, xformatter="deglon", yformatter="deglat",
              xlim=[xmin, xmax], ylim=[ymin, ymax])

    # Plot the glaciers
    gdf.plot(ax=ax, column="dzmed_m", cmap=cmap, vmin=vmin, vmax=vmax)  # Plot volcanic glaciers
    if len(rgi) > 0:
        rgi.plot(ax=ax, facecolor="none", edgecolor="dimgrey")  # Plot outer glaciers

    # Add all the volcanoes on top.
    gvp[gvp["Volcano Number"] == GVP_id].plot(ax=ax, facecolor="k", edgecolor="black", marker="*", markersize=300)
    if len(gvp) > 1:
        gvp[gvp["Volcano Number"] != GVP_id].plot(ax=ax, facecolor="k", edgecolor="none", marker="^", markersize=100)
        gvp = gvp[gvp["Volcano Number"] == GVP_id]

    # save the aspect of the figure for later.
    aspect = ax.get_aspect()

    # Add a grayscale background map.
    cx.add_basemap(ax=ax, crs=gdf.crs, alpha=0.5, zoom=12,
                   source=cx.providers.NASAGIBS.ASTER_GDEM_Greyscale_Shaded_Relief, attribution=False)
    # Reset the aspect to the original.
    ax.set_aspect(aspect)

    # Add the colorbar.
    ax.colorbar(
        tkn.intermediate_figure(cmap=cmap, vmin=vmin, vmax=vmax, levels=255),
        label=r"Relative median glacier elevation [m]",
        ticks=(vmax - vmin) / 4,
        loc="r",
        length=0.7,
        ticklabelsize=16,
        labelsize=20
    )

    # Add scale bar.
    ax.add_artist(ScaleBar(
        geo_proc.set_scalebar(N=gvp.geometry.y, E=gvp.geometry.x), font_properties={"size": "xx-large"}, box_alpha=0
    ))

    fig.savefig(os.path.join(dir_figs, f"{GVP_id}_{float(radius)}km-dzmed.png"))
    pplt.close(fig)


def main():
    for radius in args.radius:
        for GVP_id in args.GVP_ids:
            try:
                tools.find_files_within_path(
                    path=dir_data_proc,
                    filename=f"{GVP_id}_{float(radius)}km-glaciers.shp"
                )
            except FileNotFoundError:
                continue

            if os.path.exists(os.path.join(dir_figs, f"{GVP_id}_{float(radius)}km-dzmed.png")):
                continue

            print(f"{GVP_id}: {float(radius)} km")
            plot_volc_dzmed(GVP_id=GVP_id, radius=radius)


if __name__ == "__main__":
    main()
