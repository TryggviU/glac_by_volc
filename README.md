# Glaciers by volcanoes - `glac_by_volc`

Repository for code\* used to locate glaciers within a radial distance from volcanoes, and perform analysis on the geometries and dynamics of those glaciers. 

> \*The code will be made available upon publication of results.



## Methods

### Locating glaciers by volcanoes

We locate glaciers within the vicinity of volcanoes by comparing two databases: The ``Volcanoes of the World'' of the [Smithsonian Global Volcanism Program (GVP)](https://volcano.si.edu/volcanolist_holocene.cfm) -- a complete list of Earth's Holocene volcanoes; and the [Randolph Glacier Inventory (RGI) version 7.0](http://www.glims.org/rgi_user_guide/welcome.html) -- a dataset containing outlines and information for all glaciers in the World, excluding the ice sheets of Greenland and Antarctica, in the year 2000. We locate all RGI glacier geometries within a radial search area around each GVP volcano with Python scripts utilising the geospatial data package [GeoPandas](https://geopandas.org/). The code effectively accomplishes the same as that of [Edwards et al. (2020)](https://doi.org/10.1016/j.gloplacha.2020.103356) who used a search radius of 5 km, but does so automatically and allows the user to specify the search radius. In our study we use 5, 10, 20, and 40 km search radii. Besides downloading this repository and the data (see [Data](#data)), the code is fully automated, with optional user inputs.

First step - finding all GVP volcanoes within RGI regions:
```
..\glac_by_volc>python src\volc_in_rgi.py
```
Second step - find all glaciers within the search radius of each volcano:
```
..\glac_by_volc>python src\glac_by_volc.py -i RGI_IDs -r SEARCH_RADIUS -d DISPLAY
```


### Relative glacier elevations

We adopt the methodology of [Howcutt et al. (2023)](https://doi.org/10.1130/G51411.1), but adapt it to use the median glacier elevations, $\tilde{z}$, instead of ELAs. We compute the relative median elevation for each ($i$-th) individual glacier wtihin the locality, given by the search radius, of a volcano as

$$\Delta \tilde{z}\_{i} = \tilde{z}\_{i} - \overline{\tilde{{z}}},$$

where 

$$\overline{\tilde{z}} = \frac{1}{n} \sum_{i=1}^{n} \tilde{z}\_i$$

is the average median glacier elevation within the radial area, comprising of $n$ glaciers.

### Trend analysis

We use three trend tests to investigate how glacier elevations change with distance from volcanoes.
1. Linear regression using [SciPy](https://scipy.org/) and [statsmodels](https://www.statsmodels.org/stable/index.html)
2. Mann-Kendall trend test using [pyMannKendall](https://pypi.org/project/pymannkendall/)
3. Spearman's rho test using [SciPy](https://scipy.org/)
All three tests give a correlation coefficient/statistic $-1 \leq r \leq 1$, with $\pm 1$ indicating a perfect linear/monotonic trend where the sign denoting the direction (positive or negative) direction of the trend. If glacier elevations decrease away from volcanoes we would expect a coefficient $r < 0$.


## Data

### RGI and GPV

Prior to any analysis, it is assumed that the user has previously downloaded the global glacier and volcano datasets from:
 - [Randolphs Glacier Inventory (RGI)](http://www.glims.org/rgi_user_guide/welcome.html): The version used during the developement of the code is v7.0.
 - [Global Volcanism Program (GVP)](https://volcano.si.edu/volcanolist_holocene.cfm): The GVP data is downloaded as an Microsoft Excel file by default, and the user must convert it to a `.csv` file prior to executing scripts.

and stored the data within their respective subdirectories, [data/RGI](./data/RGI) and [data/GVP](./data/GVP). The resulting processed data is then stored within the subdirectory [data_processed](./data_processed).


