# Glaciers by volcanoes - `glac_by_volc`

Repository for code used to locate glaciers within a radial distance from volcanoes, and perform analysis on the geometries and dynamics of those glaciers. 



## Data

### RGI and GPV

Prior to any analysis, it is assumed that the user has previously downloaded the global glacier and volcano datasets:
 - [Randolphs Glacier Inventory (RGI)](http://www.glims.org/rgi_user_guide/welcome.html): A dataset containing outlines and information for all glaciers in the World, excluding the ice sheets of Greenland and Antarctica, around the target year 2000. The version used during the developement of the code is v7.0.
 - [Smithsonian Global Volcanism Program (GVP)](https://volcano.si.edu/volcanolist_holocene.cfm): A complete list of Earth's [Holocene volcanoes](https://volcano.si.edu/volcanolist_holocene.cfm) and [eruptions](https://volcano.si.edu/search_eruption.cfm). The GVP data is downloaded as an Microsoft Excel file by default, and the user themselves must convert it to a `.csv` file prior to executing scripts.

Store the data within their respective subdirectories, [data/RGI](./data/RGI) and [data/GVP](./data/GVP). The resulting processed data is then saved to the subdirectory [data_processed](./data_processed).



## Methods and scripts

There are a few scripts that must be run to carry out the analysis of glaciers around volcanoes. Here are descriptions of what each script accomplishes as well as the methods it applies.

### Locating glaciers by volcanoes

We locate glaciers within the vicinity of volcanoes by comparing two databases: The ``Volcanoes of the World'' of the [Smithsonian Global Volcanism Program (GVP)](https://volcano.si.edu/volcanolist_holocene.cfm) ; and the [Randolph Glacier Inventory (RGI) version 7.0](http://www.glims.org/rgi_user_guide/welcome.html). We locate all RGI glacier geometries within a radial search area around each GVP volcano with Python scripts utilising the geospatial data package [GeoPandas](https://geopandas.org/). The code effectively accomplishes the same as that of [Edwards et al. (2020)](https://doi.org/10.1016/j.gloplacha.2020.103356) who used a search radius of 5 km, but does so automatically and allows the user to specify the search radius. In our study we use 5, 10, 20, and 40 km search radii as default. Besides downloading this repository and the data (see [Data](#data)), the code is fully automated, with optional user inputs.

1. Find all GVP volcanoes within RGI regions:
```python
..\glac_by_volc>python src\volc_in_rgi.py
```
2. Find all glaciers within the search radius of each volcano:
```python
..\glac_by_volc>python src\glac_by_volc.py -i RGI_IDs -r SEARCH_RADIUS -d DISPLAY
```
3. ***Not needed if the plot scripts below are used:*** Aggregate all regional results to a single `.csv` file for simplified analysis and viewing (this is written in Powershell not Python).
```bat
PS ..\ps1> .\tools\join_attributes.ps1
```

### Relative glacier elevations and trend analysis

We adopt the methodology of [Howcutt et al. (2023)](https://doi.org/10.1130/G51411.1), but adapt it to use the median glacier elevations, $\tilde{z}$, instead of ELAs. We compute the relative median elevation for each ($i$-th) individual glacier wtihin the locality, given by the search radius, of a volcano as

$$\Delta \tilde{z}\_{i} = \tilde{z}\_{i} - \overline{\tilde{{z}}},$$

where 

$$\overline{\tilde{z}} = \frac{1}{n} \sum_{i=1}^{n} \tilde{z}\_i$$

is the average median glacier elevation within the radial area, comprising of $n$ glaciers. The relative median glacier elevations are computed within the statistical trend analysis step.

We use three trend tests to investigate how glacier elevations change with distance from volcanoes.
1. Linear regression using [SciPy](https://scipy.org/) and [statsmodels](https://www.statsmodels.org/stable/index.html)
2. Mann-Kendall trend test using [pyMannKendall](https://pypi.org/project/pymannkendall/)
3. Spearman's rho test using [SciPy](https://scipy.org/)
All three tests give a correlation coefficient/statistic $-1 \leq r \leq 1$, with $\pm 1$ indicating a perfect linear/monotonic trend where the sign denoting the direction (positive or negative) direction of the trend. If glacier elevations decrease away from volcanoes we would expect a coefficient $r < 0$.

To run the trend analysis simply execute:
```python
..\glac_by_volc>python src\gv_stats.py -r RADIUS1 RADIUS2 ... -x EXOGENOUS -y ENDOGENOUS -n N_MINIMUM -a YEAR1 YEAR2
```

The results from the trend analysis are saved in the [results](https://github.com/TryggviU/glac_by_volc/tree/main/results) directory.



## Plotting results

A couple of scripts are included to plot the results.

### RGI and GVP plots

To plot the global distribution of volcanoes, glaciers, and glaciated volcanoes* run:
```python
..\glac_by_volc>python src\plot_rgi_gvp.py
```
*Note that the figure does not come with a legend or labels for the RGI region polygons.

![The world's glaciers, volcanoes, and glaciated volcanoes](/figs/rgi_gvp_lowres.png "The world's glaciers, volcanoes, and glaciated volcanoes.")

**Legend:** `(Blue poligons) Glaciers (red dots) Holocene volcanoes - (Triangles) Glaciated volcanoes (red) 5 km (dark orange) 10 km (light orange) 20 km (yellow) 40 km.`



### Relative glacier elevations and trend analysis

To plot the results from the statistical trend analysis run:
```python
..\glac_by_volc>python src\plot_gv_stats.py -r RADIUS -s STAT -f FIT -p P_VALUE -c COMPUTE
```

![Trend analysis of the world's glaciated volcanoes showing that 80% of volcanoes have higher median glacier elevations.](/figs/trend_map_dzmed-SR_5.0km_lowres.png "Trend analysis of the world's glaciated volcanoes showing that 80% of volcanoes have higher median glacier elevations.")

**Legend:** `The local trend of median glacier elevations (MGE) for 5 km around glacierised volcanoes. Red and blue dots denote rising and lowering, respectively, median glacier elevations towards volcanoes based on the Spearman's Rho test. Up to 80% of Earth's volcanoes demonstrate higher median glacier elevations closer to volcanoes.`

To plot the relative median glacier elevations around volcanoes run:
```python
..\glac_by_volc>python src\plot_gv.py -v GVP_IDs -r RADIUS -e EVERYTHING -n N_MINIMUM -z Z_MAX
```

![An example of higher median glacier elevations arround Mount Wrangell in Alaska.](/figs/315020_40.0km-dzmed_lowres.png "An example of higher median glacier elevations arround Mount Wrangell in Alaska.")

**Legend:** `An example of median glacier elevations rising towards Mount Wrangell volcano, Alaska. The glaciers within 40 km of Mount Wrangell are coloured according to their relative median elevation.`



## Script inputs

| Option | Variable | Default Input |
|-|-|-|
| `-r` | Radii (in km) | `5 10 20 40` |
| `-x` | Explanatory variable | `distance` |
| `-y` | Target variable | `dzmed` |
| `-n` | Minimum number of glaciers | `4` |
| `-a` | Target years | `1990 2010` |
| `-c` | Complete all volcanoes? | `False` |
| `-d` | Display intermediate results? | `False` |
| `-e` | Run every volcano? | `False` |
| `-z` | Max relative value to plot. | `500` |


