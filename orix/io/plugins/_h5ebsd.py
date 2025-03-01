# -*- coding: utf-8 -*-
# Copyright 2018-2022 the orix developers
#
# This file is part of orix.
#
# orix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# orix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with orix.  If not, see <http://www.gnu.org/licenses/>.

from h5py import File, Group
import numpy as np

from orix.crystal_map import CrystalMap


def hdf5group2dict(group, dictionary=None, recursive=False, dont_read=None):
    """Return a dictionary with values from datasets in a group in an
    opened HDF5 file.

    Parameters
    ----------
    group : h5py:Group
        HDF5 group object.
    dictionary : dict, optional
        To fill dataset values into. If None (default), a new dictionary
        is created.
    recursive : bool, optional
        Whether to add subgroups to dictionary. Default is False.
    dont_read : list of str, optional
        List of strings of names of HDF data sets to not read.

    Returns
    -------
    dictionary : dict
        Dataset values in group (and subgroups if recursive=True).
    """
    if dictionary is None:
        dictionary = {}
    if dont_read is None:
        dont_read = []
    for key, value in group.items():
        # Check whether to extract subgroup or write value the dictionary
        if isinstance(value, Group):
            if recursive:
                dictionary[key] = {}
                hdf5group2dict(
                    group=group[key], dictionary=dictionary[key], recursive=recursive
                )
            else:
                dictionary[key] = value
        elif key not in dont_read:
            value = value[()]
            # Prepare value for entry in dictionary
            if isinstance(value, np.ndarray) and len(value) == 1:
                value = value[0]
            if isinstance(value, bytes):
                value = value.decode("latin-1")
            dictionary[key] = value
    return dictionary


class H5ebsdFile:
    """Base class for HDF5 files in the h5ebsd format containing
    orientation data to be returned as a crystal map.
    """

    file = None
    data_dict = dict()
    header_dict = dict()
    sem_dict = dict()
    map_shape = (1, 1)
    rotations = None
    x = None
    y = None
    properties = None
    phase_id = None
    phase_list = None
    scan_unit = None

    def __init__(self, filename):
        self.filename = filename

    @property
    def map_size(self):
        """Number of map points."""
        return np.prod(self.map_shape)

    def open(self, **kwargs):
        """Open the HDF5 file."""
        mode = kwargs.pop("mode", "r")
        self.file = File(self.filename, mode=mode, **kwargs)

    def close(self):
        """Close the HDF5 file."""
        self.file.close()

    def get_dictionary(self, group_name, **kwargs):
        """Return a dictionary with values from datasets in a group
        within the file.

        Parameters
        ----------
        group_name : str
            Name of the group.
        kwargs
            Keyword arguments passed to
            :func:`~orix.io.plugins._h5ebsd.hdf5group2dict`.

        Returns
        -------
        dict

        See Also
        --------
        orix.io.plugins._h5ebsd.hdf5group2dict
        """
        return hdf5group2dict(self.file[group_name], **kwargs)

    def get_crystal_map(self):
        """Return a crystal map from instance properties.

        Returns
        -------
        CrystalMap
        """
        return CrystalMap(
            rotations=self.rotations,
            phase_id=self.phase_id,
            x=self.x,
            y=self.y,
            phase_list=self.phase_list,
            prop=self.properties,
            scan_unit=self.scan_unit,
        )

    def set_scan_group_names(self):
        """Set name of scan HDF5 groups in top group as a list of
        strings.
        """
        scan_groups = []
        f = self.file
        for key in f["/"].keys():
            if key.lstrip().lower() not in ["manufacturer", "version"]:
                scan_groups.append(key)
        self.scan_groups = scan_groups
