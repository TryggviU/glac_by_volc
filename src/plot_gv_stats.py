# System
import os
# Basic
import numpy as np
import pandas as pd
# Arguments
import argparse
# Plotting
import proplot as pplt
import seaborn as sns
# Geospatial data
import geopandas as gpd
import contextily as cx
# Modules
import geo.geo_processing as geo_proc
import glacvolc.glacvolc_processing as gv_proc
import tools.tools as tools
import tkn.tkn as tkn
import stats.fit as sfit

pplt.rc.update({'mathtext.fontset': 'stixsans', 'mathtext.default': 'it',
                'legend.fontsize': 'xx-large', 'legend.title_fontsize': 'xx-large',
                'title.size': 20})

# Set the root directory as the project directory.
dir_root = tools.set_root(path=os.getcwd(), name="glac_by_volc")
# Data directories.
dir_data = os.path.join(dir_root, "data")
dir_data_proc = os.path.join(dir_root, "data_processed")
# Create a temporary directory for temporary results.
dir_temp = tools.mkdir_ifnot_exist(
    path=os.path.join(dir_data_proc, "temp", "stats"),
    path_proj=dir_root
)
# Result figures directory
dir_figs = os.path.join(dir_root, "figs", "glacvolc_stats")
tools.mkdir_ifnot_exist(path=dir_figs, path_proj=dir_root)
dir_dzmed = tools.mkdir_ifnot_exist(
    path=os.path.join(dir_figs, "dzmed"),
    path_proj=dir_root
)

# The RGI version code/phrase (e.g. RGI2000-v7.0).
RGI_v = os.path.basename(
    tools.find_files_within_path(
        path=os.path.join(dir_data, "RGI"),
        filename="RGI"
    )[0]
)[0:12]
# Read in the RGI region codes/names.
RGI_regions = gv_proc.read_rgi(
    path=tools.find_files_within_path(
        path=dir_data,
        filename="o1regions-summary.csv"
    )[0]
)["long_code"].drop_duplicates().tolist()
RGI_regions.remove('20_antarctic_mainland')

# Initiate the argument parser.
parser = argparse.ArgumentParser()
# Add arguments.
parser.add_argument("-r", "--radius", action="store", nargs="*", type=float, default=[5, 10, 20, 40],
                    help="Maximum radial distance, in kilometres, of search buffer for glaciers surrounding volcano.")
parser.add_argument("-s", "--stat", action="store", nargs="*", type=str, default=["dzmed"],
                    help="The target (endogenous) variable.")
parser.add_argument("-f", "--fit", action="store", nargs="*", type=str, default=["LR", "MK", "SR"],
                    help="The fitting method used to evaluate trends.")
parser.add_argument("-p", "--pvalue", action="store", nargs="*", type=float, default=[1],
                    help="The maximum p-value that should be plotted.")
parser.add_argument("-c", "--compute", action="store", type=bool, default=True,
                    help="Whether to compute from scratch or read results from previous run.")
# Read arguments from the command line
args = parser.parse_args()


def gv_distance(RGI_id, radius):
    """
    Compute the distance of all glaciers from the nearest volcano.

    :param RGI_id: the RGI regional code.
    :param radius: The search radius around each volcano.

    :return: A GeoDataFrame containing all the glaciers within the search radius of a volcano,
    with their exact distance as an attribute.
    """
    print(RGI_id)

    # The RGI regional volcanoes.
    gvp = gpd.read_file(
        tools.find_files_within_path(
            path=dir_data_proc,
            filename=f"{RGI_v}-V-{RGI_id}.shp"
        )[0],
        crs="EPSG:4326"
    )

    # The data directory.
    try:
        subdir = tools.find_subdirs_within_path(
            path=dir_data_proc,
            dirname=f"{RGI_id}_{round(float(radius), 1)}"
        )[0]
    except FileNotFoundError:
        # Terminate the function if no volcanoes contain glaciers within the search radius.
        print(f" - No glaciers within {float(radius)}km from volcanoes in RGI region: {RGI_id}")
        return gpd.GeoDataFrame()

    # Initialise a GeoDataFrame for all glaciers within the given radius from volcanoes.
    rgi_gvp = gpd.GeoDataFrame()

    # Iterate through all the regional volcanoes.
    for GVP_id in os.listdir(subdir):
        # Read in the glaciers within the radial distance from each volcano.
        rgi_v = gpd.read_file(
            os.path.join(subdir, GVP_id, f"{GVP_id}_{round(float(radius), 1)}km-glaciers.shp")
        )
        # Transform to UTM.
        rgi_v = rgi_v.to_crs(rgi_v.estimate_utm_crs())
        gvp_crs = gvp.to_crs(rgi_v.crs)

        # A GeoDataFrame of the volcano itself.
        volcano = gpd.GeoSeries(gvp_crs[gvp_crs["Volcano Nu"] == int(GVP_id)].geometry.to_list(), crs=rgi_v.crs)

        # Search for other close-by volcanoes.
        close_by_volcanoes = gvp_crs.clip(volcano.buffer(2 * radius * 1e3))
        # Exclude the volcano from the close-by ones.
        close_by_volcanoes = close_by_volcanoes[close_by_volcanoes["Volcano Nu"] != int(GVP_id)]

        # Compute the distance between the volcano and all the glaciers within the search radius.
        rgi_v = geo_proc.compute_distance(f1=volcano, f2=rgi_v, f3=close_by_volcanoes)

        # Add the GVP ID as a column to the glacier GeoDataFrame.
        rgi_v["Volcano Nu"] = int(GVP_id)

        # Add the Delta z_med/min/max as columns.
        rgi_v["dzmed"] = rgi_v["zmed_m"] - rgi_v["zmed_m"].mean()
        rgi_v["dzmin"] = rgi_v["zmin_m"] - rgi_v["zmin_m"].mean()
        rgi_v["dzmax"] = rgi_v["zmax_m"] - rgi_v["zmax_m"].mean()

        rgi_gvp = tools.join_df(df1=rgi_gvp, df2=rgi_v.to_crs(gvp.crs))

    return rgi_gvp


def gv_glaciers(radius, compute=True):
    """
    Find all glaciers within a 'radius' from volcanoes.

    :param radius: The search radius for glaciers around volcanoes.
    :param compute: Whether to compute stats from scratch or read previous run from file.

    :return: A GeoDataFrame of all the glaciers within the 'radius' and their statistics.
    """

    if compute:
        # RGI regions with GVP.
        rgi_regions = [
            subdir.split("-")[-1] for subdir in os.listdir(os.path.join(dir_data_proc, "regional_files", f"{RGI_v}-GV"))
        ]

        # Initialise a GeoDataFrame for all results for a specific radius.
        rgi_rad = gpd.GeoDataFrame()

        # Find all the glaciers within the give radius of volcanoes.
        for RGI_id in rgi_regions:
            rgi_regional = gv_distance(RGI_id=RGI_id, radius=radius)

            rgi_rad = tools.join_df(df1=rgi_rad, df2=rgi_regional)

        # Save the results to the 'temp' directory.
        rgi_rad.to_file(os.path.join(dir_temp, f"rgi_{float(radius)}km.shp"))

    else:
        if os.path.exists(os.path.join(dir_temp, f"rgi_{float(radius)}km.shp")):
            rgi_rad = gpd.read_file(os.path.join(dir_temp, f"rgi_{float(radius)}km.shp"))
        else:
            rgi_rad = gv_glaciers(radius=radius)

    return rgi_rad


def read_GVP_trend_data(stat, radius):
    # Get the volcano trend data.
    gvp = pd.read_csv(
        tools.find_files_within_path(
            path=dir_root,
            filename=f"{RGI_v}-GV-stats-{stat}_{float(radius)}km.csv"
        )[0]
    )
    return gpd.GeoDataFrame(
        data=gvp,
        geometry=gpd.points_from_xy(gvp.Longitude, gvp.Latitude),
        crs="EPSG:4326"
    )


def plot_world_trends(stat, radius, fit, p):
    # Get the volcano trend data.
    gvp = read_GVP_trend_data(stat=stat, radius=radius)

    # Only include the volcanoes with appropriate p-values.
    gvp = gvp[gvp[f"{fit}_p"] <= p]

    # Plot the results.
    fig, ax = pplt.subplots(nrows=1, ncols=1, figsize=(8, 6.75), tight=True)
    ax.format(xlim=(-180, 180), ylim=(-85, 85),
              xticks=[-180, -120, -60, 0, 60, 120, 180], yticks=[-60, -30, 0, 30, 60], ticklabelsize=12,
              xminorlocator=5, yminorlocator=5,
              xformatter="deglon", yformatter="deglat")

    gvp[gvp[f"{fit}_r"] > 0].plot(ax=ax, facecolor="tab:blue", edgecolor="black", alpha=0.5, markersize=20)
    gvp[gvp[f"{fit}_r"] < 0].plot(ax=ax, facecolor="tab:red", edgecolor="black", alpha=0.5, markersize=20)

    hs = tkn.intermediate_scatterplot(
        info_dict={
            "labels": ["Rising MGE", "Lowering MGE"],
            "facecolors": ["tab:red", "tab:blue"],
            "edgecolors": ["black", "black"],
            "markers": ["o", "o"],
            "markersize": [20, 20]
        }
    )
    ax.legend(hs, loc="ll", ncols=1)

    cx.add_basemap(ax=ax, zoom=4, source=cx.providers.Esri.WorldPhysical, crs="EPSG:4326", attribution=False)

    fig.format(aspect="equal")
    fig.savefig(os.path.join(dir_figs, f"trend_map_{stat}-{fit}_{round(float(radius), 1)}km.png"))
    pplt.close(fig)


def raincloudplot(df, x, y, figname, **kwargs):
    fig, ax = pplt.subplots(nrows=1, ncols=1, figsize=(12, 6.75), tight=True)
    ax.format(labelsize=20, yminorlocator="null", linewidth=1, tickwidth=1, ticklabelsize=16,
              **kwargs)

    # sns.violinplot(
    #     data=df, x=x, y=y, hue=y, palette=colors, orient="h", legend=False, split=True,
    #     fill=True, alpha=0.25, linewidth=0, common_norm=True, inner=None
    # )
    sns.violinplot(
        data=df, x=x, y=y, split=True, hue=1, hue_order=[1, 2, 3], dodge=True, legend=False,
        fill=True, alpha=0.25, linewidth=0, common_norm=True, inner=None
    )

    sns.stripplot(
        data=df, x=x, y=y, size=4, palette="dark:black", legend=False, dodge=True, hue=1, hue_order=[3, 2, 1]
    )

    sns.boxplot(
        data=df, x=x, y=y,
        width=0.3, showfliers=False, fill=False,
        linewidth=3, palette="dark:#0072b2",
        legend=False, hue=1, hue_order=[3, 2, 1], dodge=True
    )

    ax.format(**kwargs)

    fig.savefig(os.path.join(dir_figs, figname))  # , transparent=True)
    pplt.close(fig)


def plot_fit_stats(stat, radius):
    # Get the volcano trend data.
    gvp = read_GVP_trend_data(stat=stat, radius=radius)

    df = pd.DataFrame()

    fit_name = ["LR", "MK", "SR"]

    for i, fit in enumerate(["LR", "MK", "SR"]):
        df2 = gvp[[
            "Volcano Number", "Volcano Name", "rgi_region", "Latitude", "Longitude",
            "n_glac", "A_glac_km2", "Erupted", "f_erupt"
        ]].copy()
        df2["fit"] = fit_name[i]
        df2["fit_r"] = gvp[f"{fit}_r"]
        df2["fit_p"] = gvp[f"{fit}_p"]

        df = tools.join_df(df1=df, df2=df2)

    # Check if eruption frequency plays part in this.
    # df["lim_f"] = [1 if df.loc[i, "f_erupt"] > 0.2 else 0 for i in range(len(df))]

    # bsv2(df=df, x="fit", y="fit_r", hue="Erupted",
    #     figname=f"trend_stats-r_{float(radius)}km.png",
    #     xlabel="Fitting method", ylabel="Correlation coefficient",
    #     ylim=[-1, 1], yticks=[-1, -0.5, 0, 0.5, 1])

    raincloudplot(
        df=df, x="fit_r", y="fit",
        figname=f"trend_stats-r_{float(radius)}km.png",
        ylabel="Trend test", xlabel="Correlation coefficient",
        xlim=[-1, 1], xticks=[-1, -0.5, 0, 0.5, 1]
    )


def plot_dz_scatter(compute=True):
    radii = [5, 10, 20, 40]
    pplt.rc.update({'legend.fontsize': 'large'})

    fig, axs = pplt.subplots([[1, 2, 3], [4, 4, 4]], figsize=(12, 6.75),
                             refnum=1, wratios=[radii[i] / radii[0] for i in range(1, len(radii))],
                             tight=True, share=True, spanx=True)
    axs.format(xlabel="Distance from volcanoes [km]", ylabel="Relative glacier elevations [m]", labelsize=20,
               linewidth=1, tickwidth=1, ticklabelsize=16,
               abc=True, abcloc="ul", abcbbox=False, abcsize="xx-large")

    colors = ["black", "black", "black"]
    linestyles = ["dotted", "--", "-"]

    for i, radius in enumerate(radii):
        rgi_rad = gv_glaciers(radius=radius, compute=compute)
        rgi_rad["distance"] *= 1e-3

        sns.scatterplot(
            ax=axs[i], data=rgi_rad, x="distance", y="dzmed", marker=".",
            color="tab:blue", alpha=0.3,
        )

        # Compute the linear trend within 5 km of volcanoes.
        trend = sfit.SimpleLinearRegression(df=rgi_rad[rgi_rad["distance"] <= 5], col_x="distance", col_y="dzmed")
        print(trend)
        # Plot the trend within 5 km of volcanoes and add a legend with the trend.
        sns.lineplot(ax=axs[i], x=[0, 5], y=[trend.intercept, trend.intercept + 5 * trend.slope],
                     color="red", linewidth=2, legend=False)
        axs[i].legend(
            tkn.intermediate_lineplot(
                colors=["red"],
                labels=[f"${int(np.round(trend.slope))}\pm{int(np.ceil(trend.stderr))}$ m/km"]
            ),
            loc="lower left"
        )

        for j, dz in enumerate(["dzmin", "dzmax", "dzmed"]):
            df = tools.df_moving_average(data=rgi_rad, x="distance", y=dz, xmin=0, xmax=radius, dx=0.1)
            for k in range(1):
                df[dz] = df[dz].rolling(4, min_periods=1).mean()

            sns.lineplot(
                ax=axs[i], data=df, x="distance", y=dz, color=colors[j], linestyle=linestyles[j], legend=False
            )

        axs[i].format(xlim=[0, radius])

    axs[3].legend(
        tkn.intermediate_lineplot(
            colors=colors,
            labels=["Maximum", "Median", "Minimum"],
            linestyles=["--", "-", "dotted"]
        ),
        ncols=1, loc="upper right", fontsize="xx-large"
    )

    fig.savefig(os.path.join(dir_figs, f"global_dzmed_scatter.png"))  # , transparent=True)
    pplt.close(fig)


def main():
    # plot_dz_scatter(compute=False)

    for radius in args.radius:
        for stat in args.stat:
            for fit in args.fit:
                for p in args.pvalue:
                    plot_world_trends(
                        stat=stat,
                        radius=radius,
                        fit=fit,
                        p=p
                    )

                    plot_fit_stats(stat=stat, radius=radius)


if __name__ == "__main__":
    main()
