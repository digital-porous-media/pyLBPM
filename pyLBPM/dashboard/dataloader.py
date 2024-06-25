import pandas as pd
import numpy as np
import os
import re
import h5py
from pathlib import Path
import pyvista as pv
import argparse
from typing import Dict, Tuple
import xml.dom.minidom
from pyLBPM.lbpm_input_database import read_input_database, get_section
import matplotlib.pyplot as plt


def csv_reader(simulation_dir: Path, csv_file: str) -> pd.DataFrame:
    """
    Reads in a csv file produced by an LBPM simulation as a Pandas DataFrame.
    :param simulation_dir: Path to the simulation directory
    :param csv_file: Name of the simulation csv file
    :return: pd.DataFrame of the simulation csv file
    """
    # Check if there is a csv extension
    csv_file = _file_check(simulation_dir, csv_file, ".csv")

    df = pd.read_csv(os.path.join(simulation_dir, csv_file), delimiter=" ")
    df.insert(0, 'sim.step', np.arange(1, len(df) + 1))
    return df


def raw_reader(simulation_dir: Path, raw_file: str, img_shape: tuple[int, int, int], data_type: np.dtype = np.uint8):
    """
    Reads in a raw file produced by an LBPM simulation as a Numpy array.
    :param simulation_dir: path to the simulation directory
    :param raw_file: Name of the raw file
    :param img_shape:
    :param data_type:
    :return:
    """
    raw_file = _file_check(simulation_dir, raw_file, ".raw")

    img = np.fromfile(os.path.join(simulation_dir, raw_file), dtype=data_type).reshape(img_shape)
    return img





def _file_check(simulation_dir: Path, filename: str, extension:str) -> str:
    if not filename.lower().endswith(extension):
        filename += extension

    # Check that the simulation file exists
    if not os.path.isfile(os.path.join(simulation_dir, filename)):
        raise FileNotFoundError(f"File {filename} not found in {simulation_dir}")

    return filename


def _natural_sort(l: list[str]):
    """
    Sort a list of strings alphabetically and numerically.
    :param l: List of strings to be sorted
    :return:
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def _wrap_numpy_to_vtk(img):
    return pv.wrap(img)


def get_sim_dir() -> Path:
    parser = argparse.ArgumentParser(description="The LBPM Dashboard is a tool for monitoring and analyzing your LBPM simulations. https://github.com/JamesEMcClure/pyLBPM")
    parser.add_argument("--sim_dir", type=str, help="Path to the simulation directory")
    args = parser.parse_args()
    sim_dir = Path(fr"{args.sim_dir}")
    return sim_dir


def get_vis_fields(simulation_file: Path) -> list[str]:
    # TODO: Write better XML Parser
    img = h5py.File(simulation_file, 'r')
    domain = [domain_key for domain_key in [*img.keys()] if "domain" in domain_key]
    allowable_fields = ["Pressure", "Velocity_x", "Velocity_y", "Velocity_z", "phase"]
    return [key for key in [*img[domain[0]].keys()] if key in allowable_fields]


def _get_grid_names(xml_file_path: Path) -> Tuple[list, list]:
    """ XML parser to get the names of the grids for each rank

    :param xml_file_path: Path to the xml file
    :return: List of grid names, list of corresponding h5 filenames
    """
    domtree = xml.dom.minidom.parse(str(xml_file_path))
    group = domtree.documentElement

    domains = group.getElementsByTagName("Domain")
    grids = domains[0].getElementsByTagName("Grid")[2:]
    grid_names = []
    h5_names = []
    for grid in grids:
        grid_names.append(grid.getAttribute("Name"))
        h5_names.append(grid.getAttribute("Name").split('_')[1] + ".h5")
    return grid_names, h5_names


def _get_data_keys(xml_file_path: Path) -> list:
    """ XML parser to get the data keys for the 0th rank h5 file
    Later assumes all subsequent rank files contain the same keys

    :param xml_file_path: Path to the xml file
    :return: List of keys
    """
    domtree = xml.dom.minidom.parse(str(xml_file_path))
    group = domtree.documentElement

    domains = group.getElementsByTagName("Domain")
    grid_0 = domains[0].getElementsByTagName("Grid")[2]
    attributes = grid_0.getElementsByTagName("Attribute")

    data_keys = []
    for attr in attributes:
        data_keys.append(attr.getAttribute("Name"))
    return data_keys


def _get_grid_size(domains: list) -> Tuple[np.ndarray, float, float, float]:
    """ Get the global indices and side lengths (in voxels) of each subdomain

    :param domains: List of domain names
    :return: Tuple of the range indices and size of each subdomain
    """
    domain_ranges: np.ndarray = np.array([list(domain["range"]) for domain in domains], dtype=np.float64)
    nx, ny, nz = domain_ranges[:, 1].max(), domain_ranges[:, 3].max(), domain_ranges[:, -1].max()
    return domain_ranges, nx, ny, nz


def h5_reader(simulation_dir: Path, data_key: str, subdomain_num: list[str]=['all']) -> Dict:
    """ Get the fields from each h5 file.

    :param simulation_dir: Path to the parent directory containing .xmf and .h5 visualization files
    :param data_key: Data key to read. Defaults to vz.
    :param subdomain_num: Name of subdomain file to read. Defaults to 'all' but this may not scale well
    for large simulations.
    :param voxel_length: Voxel length in microns/voxel. Defaults to 1.00.
    :return: Dictionary of h5 fields as keys and their corresponding images.
    """

    # Read in the input database and extract the domain section
    db = read_input_database(simulation_dir.parent / "input.db")
    domain_db = get_section(db, "Domain")
    voxel_length = domain_db.voxel_length


    # if subdomain_num != "all":
    #     grid_names = [grid_name for grid_name in grid_names if f"{subdomain_num}" in grid_name]
    #     h5_names = [h5_name for h5_name in h5_names if f"{subdomain_num}" in h5_name]
    if "all" in subdomain_num:
        grid_names, h5_names = _get_grid_names(simulation_dir / "summary.xmf")
        h5_file_names = list(simulation_dir.glob("*.h5"))
        assert len(h5_file_names) == len(grid_names), "Number of h5 files does not match number of grid names"

        domains: list = [h5py.File(str(simulation_dir / f"{h5_file_name}"))[grid_name]
                         for h5_file_name, grid_name in zip(h5_names, grid_names)]

    else:
        if type(subdomain_num) is str:
            subdomain_num = [subdomain_num]
        h5_names = [subdomain.split("_")[-1] + ".h5" for subdomain in subdomain_num]
        domains: list = [h5py.File(str(simulation_dir / f"{h5_file_name}"), mode='r')[grid_name]
                         for h5_file_name, grid_name in zip(h5_names, subdomain_num)]

    # Get block ranges...
    # working with range properties of grid, so in floating point, absolute position
    domain_ranges, nz, ny, nx = _get_grid_size(domains)

    # Get the data (e.g. vx, vy, vz)
    # if data_key.lower() == 'all':
    #     data_keys = _get_data_keys(simulation_dir / "summary.xmf")
    #     if 'SignDist' in data_keys:
    #         signdist_idx = data_keys.index('SignDist')
    #         data_keys.pop(signdist_idx)

    # Initialize a Numpy array dictionary (images) and full image placeholder (image_tmp)
    image = np.zeros((int(nx / voxel_length),
                      int(ny / voxel_length),
                      int(nz / voxel_length)), dtype="<f8")
    for domain, r in zip(domains, domain_ranges):

        rr = np.array(r / voxel_length, dtype=np.uint64)
        image[rr[4]:rr[5], rr[2]:rr[3], rr[0]:rr[1]] = domain[data_key][:]

    return image

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    images = h5_reader(Path("C:/Users/bchan/Documents/lbpm_results/beadpack_test_vis/vis2000"),
              data_key='all', subdomain_num='all')

    plt.imshow(images['Velocity_z'][100, :, :], cmap='inferno')
    plt.colorbar()
    plt.show()
