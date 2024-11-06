import os
import pandas as pd


def read_rgi(path):
    # Read in the RGI attributes.
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        raise FileNotFoundError("RGI attributes file not recognised: {file}".format(file=path))


def read_gvp(path):
    # Read in the GVP global attributes.
    if os.path.exists(path):
        return pd.read_csv(path, header=1, encoding='latin-1')
    else:
        raise FileNotFoundError("GVP global attributes file not recognised: {file}.".format(file=path))
