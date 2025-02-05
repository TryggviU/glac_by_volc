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

crs = "EPSG:4326"

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
          xticks=[-180, -120, -60, 0, 60, 120, 180], yticks=[-60, -30, 0, 30, 60], ticklabelsize=16,
          xminorlocator=5, yminorlocator=5,
          xformatter="deglon", yformatter="deglat", grid=False)

rgi.plot(ax=ax, facecolor="white", edgecolor="none", alpha=0.25)

# Read in the RGI glaciers as a GeoDataFrame.
for RGI_id in RGI_ids:
    rgi_regional = gpd.read_file(
       tools.find_files_within_path(
           path=dir_data,
           filename=f"{RGI_v}-G-{RGI_id}.shp"
       )[0]
    )
    rgi_regional.to_crs(crs)
    rgi_regional.plot(ax=ax, edgecolor="midnightblue", linewidth=1)

rgi.plot(ax=ax, linewidth=0.5, facecolor="none", edgecolor="black")

# Read in the GVP volcanoes as a GeoDataFrame.
gvp_attributes = gv_proc.read_gvp(
    tools.find_files_within_path(path=dir_data,
                                 filename="GVP_Volcano_List_Holocene.csv")[0]
)
gvp = gpd.GeoDataFrame(
    gvp_attributes,
    geometry=gpd.points_from_xy(gvp_attributes.Longitude, gvp_attributes.Latitude),
    crs="EPSG:4326"
)
gvp.plot(ax=ax, facecolor="tab:red", edgecolor="none", markersize=2)

gv.iloc[::-1].plot(ax=ax, column="radius", legend=False, categorical=True, cmap="autumn", edgecolor="k", marker="^",
                   legend_kwds={"labels": ["  5km", "10km", "20km", "40km"], "loc": "lower center", "ncol": 4})

# Add a background basemap.
cx.add_basemap(ax=ax, zoom=4, source=cx.providers.Esri.WorldPhysical, crs=crs, attribution=False)

fig.format(aspect="equal")
fig.savefig(os.path.join(dir_root, "figs", "rgi_gvp.png"))
pplt.close(fig)
