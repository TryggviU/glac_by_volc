# System
import os
# Basic
import proplot as pplt
import pandas as pd
# Geospatial data
import geopandas as gpd
import contextily as cx
# Modules.
import glacvolc.glacvolc_processing as gv_proc
import geo.geo_processing as geo_proc
import tools.tools as tools
import tkn.tkn as tkn

pplt.rc.update({'mathtext.fontset': 'stixsans', 'mathtext.default': 'it',
                'legend.fontsize': 20, 'legend.title_fontsize': 20, 'title.size': 20})

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

# Read in the RGI region codes/names.
RGI_ids = gv_proc.read_rgi(
    path=tools.find_files_within_path(
        path=dir_data,
        filename="o1regions-summary.csv"
    )[0]
)["long_code"].drop_duplicates().tolist()
# Drop Antarctic Mainland from the RGI list.
if "20_antarctic_mainland" in RGI_ids:
    RGI_ids.remove("20_antarctic_mainland")

# The desired GCS.
crs = "EPSG:4326"
# The areas for zoom-in.
df = pd.DataFrame(
    data={
        "xlim": [(-180, -115), (155, 165), (-25, -13), (-84, -64)],
        "ylim": [(35, 65), (50, 59.5), (63, 67), (-57, 10)],
        "rgi": [
            ["01_alaska", "02_western_canada_usa"],
            ["10_north_asia"],
            ["06_iceland"],
            ["16_low_latitudes", "17_southern_andes"]]
    }
)
df["geometry"] = [
    geo_proc.create_box(
        minx=roi.xlim[0], miny=roi.ylim[0],
        maxx=roi.xlim[1], maxy=roi.ylim[1],
        crs=crs
    ).geometry[0] for i, roi in df.iterrows()
]
sgdf = gpd.GeoDataFrame(df, geometry="geometry")

# Read in the glaciated volcanoes.
gv = gpd.GeoDataFrame()
for radius in [5, 10, 20, 40]:
    for rgi_id in RGI_ids:
        try:
            df = pd.read_csv(
                tools.find_files_within_path(
                    path=dir_data_proc,
                    filename=f"{rgi_id}_{float(radius)}km-attributes.csv"
                )[0],
                encoding='latin-1'
            )
        except FileNotFoundError:
            subdir_rgi = os.path.join(dir_data_proc, "regional_files", f"{RGI_v}-GV", f"{RGI_v}-GV-{rgi_id}")

            if os.path.exists(os.path.join(subdir_rgi, f"{rgi_id}_{float(radius)}km")):
                csvs = tools.find_files_within_path(
                    path=os.path.join(subdir_rgi, f"{rgi_id}_{float(radius)}km"),
                    filename="-attributes.csv"
                )
                df = pd.concat(
                    map(pd.read_csv, csvs), ignore_index=True
                )
                df.to_csv(os.path.join(subdir_rgi, f"{rgi_id}_{float(radius)}km-attributes.csv"))
            else:
                continue

        gdf = gpd.GeoDataFrame(
            data=df,
            geometry=gpd.points_from_xy(df.Longitude, df.Latitude),
            crs=crs
        )

        gdf["radius"] = radius

        if len(gv) != 0:
            for i in gdf.index:
                if gdf.loc[i, "Volcano Nu"] in gv["Volcano Nu"].to_list():
                    gdf.drop(index=i, inplace=True)

        gv = tools.join_df(df1=gv, df2=gdf)

# Read in shape file of the RGI regions as a GeoDataFrame.
rgi = gpd.read_file(
    tools.find_files_within_path(path=dir_data,
                                 filename="o1regions.shp")[0]
)

fig, ax = pplt.subplots(nrows=1, ncols=1, figsize=(16, 9), tight=True)
ax.format(xlim=(-180, 180), ylim=(-85, 85),
          xticks=[-180, -120, -60, 0, 60, 120, 180], yticks=[-60, -30, 0, 30, 60], ticklabelsize=20,
          xminorlocator=5, yminorlocator=5,
          xformatter="deglon", yformatter="deglat", grid=False)

# Plot the RGI regions.
rgi.plot(ax=ax, facecolor="white", edgecolor="none", alpha=0.25)
rgi.plot(ax=ax, linewidth=0.5, facecolor="none", edgecolor="black")

# Plot the subplot regions.
sgdf.plot(ax=ax, linewidth=1, facecolor="none", edgecolor="k", linestyle="dashed")#(0, (5, 10)))

# Read in the RGI glaciers as a GeoDataFrame.
for RGI_id in RGI_ids:
    rgi_regional = gpd.read_file(
       tools.find_files_within_path(
           path=dir_data,
           filename=f"{RGI_v}-G-{RGI_id}.shp"
       )[0]
    )
    rgi_regional.to_crs(crs)
    rgi_regional.plot(ax=ax, facecolor="midnightblue", edgecolor="midnightblue", linewidth=1)


# Read in the GVP volcanoes as a GeoDataFrame.
gvp_attributes = gv_proc.read_gvp(
    tools.find_files_within_path(path=dir_data,
                                 filename="GVP_Volcano_List_Holocene.csv")[0]
)
gvp = gpd.GeoDataFrame(
    gvp_attributes,
    geometry=gpd.points_from_xy(gvp_attributes.Longitude, gvp_attributes.Latitude),
    crs=crs
)
gvp.plot(ax=ax, facecolor="tab:red", edgecolor="none", markersize=2)

gv.iloc[::-1].plot(ax=ax, column="radius", legend=False, categorical=True, cmap="autumn", edgecolor="k", marker="^",
                   legend_kwds={"labels": ["  5km", "10km", "20km", "40km"], "loc": "lower center", "ncol": 4})

# Add a background basemap.
cx.add_basemap(ax=ax, zoom=4, source=cx.providers.Esri.WorldPhysical, crs=crs, attribution=False)

rgi_txt = [
    [-138, 51],  # 01
    [-109, 68],  # 02
    [-120, 75],  # 03
    [-85, 59],  # 04
    [-31, 60],  # 05
    [-18, 53],  # 06
    [-5, 76],  # 07
    [29, 60],  # 08
    [39, 71],  # 09
    [61, 48],  # 10
    [22, 45],  # 11
    [37, 31],  # 12
    [100, 40],  # 13
    [60, 27],  # 14
    [110, 27],  # 15
    [-96, -24],  # 16
    [-78, -31],  # 17
    [168, -40],  # 18
    [150, -55],  # 19
    [150, -80],  # 20
]
for i, point in enumerate(rgi_txt):
    ax.annotate(text=f"{1+i:02d}", xy=[point[0], point[1]], ha="center", fontsize=20)#, fontweight="bold")

sub_txt = [[-150, 30], [160, 62], [-19, 68], [-60, 0]]
for i, point in enumerate(sub_txt):
    ax.annotate(text="abcdefg"[i], xy=[point[0], point[1]], ha="center", fontsize=20, fontweight="bold")


fig.format(aspect="equal")

ax.legend(
    tkn.intermediate_scatterplot(
        info_dict={
            "facecolors": pplt.Colormap("autumn")([0, 0.33, 0.66, 1]).tolist(),
            "edgecolors": ["k", "k", "k", "k"],
            "markers": ["^", "^", "^", "^"],
            "labels": ["5 km", "10 km", "20 km", "40 km"],
        }
    ),
    loc="b",
    ncol=4,
    markersize=200,
    title="Glacierised volcanoes",
    pad=0,
    frame=False
)

ax.legend(
    tkn.intermediate_scatterplot(
        info_dict={
            "facecolors": ["red", "midnightblue"],
            "edgecolors": ["none", "none"],
            "markers": ["o", "o"],
            "labels": ["Holocene volcanoes", "Glaciers"],
        }
    ),
    loc="ll",
    ncol=1,
    markersize=200,
    edgecolor="none"
)

fig.savefig(os.path.join(dir_root, "figs", "rgi_gvp.png"))
pplt.close(fig)

##################################
# --- The zoomed-in subplots --- #
##################################

fig, axs = pplt.subplots(
    [[1, 1, 1, 4], [1, 1, 1, 4], [2, 3, 3, 4]], refnum=4, figsize=(9, 6.5), tight=True, share=False, span=False
)
axs.format(abc=True, abcloc='ul', abcbbox=False, abcsize=16, xticks=[], yticks=[])

for i, ax in enumerate(axs):
    ax.format(xlim=sgdf.iloc[i].xlim, ylim=sgdf.iloc[i].ylim)

    for RGI_id in sgdf.loc[i, "rgi"]:
        rgi_regional = gpd.read_file(
               tools.find_files_within_path(
                   path=dir_data,
                   filename=f"{RGI_v}-G-{RGI_id}.shp"
               )[0]
            )
        rgi_regional.to_crs(crs)
        rgi_regional.plot(ax=ax, color="midnightblue")

    gvp_roi = gvp.clip(sgdf.iloc[i].geometry)
    gv_roi = gv.clip(sgdf.iloc[i].geometry)

    gvp_roi.plot(ax=ax, facecolor="tab:red", edgecolor="none", markersize=2)

    gv_roi.iloc[::-1].plot(
        ax=ax, column="radius", legend=False, categorical=True, cmap="autumn", edgecolor="k", marker="^"
    )

    # Add a basemap, but keep the aspect ratio.
    aspect = ax.get_aspect()
    cx.add_basemap(ax=ax, zoom=8, source=cx.providers.Esri.WorldPhysical, crs=crs, attribution=False) # max zoom 8
    ax.set_aspect(aspect)

fig.savefig(os.path.join(dir_root, "figs", f"rgi_gvp_zoom.png"))
pplt.close(fig)
