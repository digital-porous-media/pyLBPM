import re
import os
import numpy as np
import matplotlib.pyplot as plt

from pyLBPM.lbpm_input_database import *

class domain_db:
    """
    Domain section for the input database

    Parameters:
        name: str
            The name of the domain.
        img: numpy.ndarray
            A 3D numpy array representing the domain image.
        voxlen: float, optional
            The length of a voxel in the domain (default is 1.0).
    """
    def __init__(self, name, img, voxlen=1.0):
        """Constructor method
        """
        # Domain should be initialized from 3D numpy array
        # set up the array in advance to match the simulation domain                                                     
        self.name = name
        self.image = img.astype(np.uint8)
        self.Nx, self.Ny, self.Nz = self.image.shape
        self.nx = self.Nx   # sub-domain sizes
        self.ny = self.Ny
        self.nz = self.Nz
        self.nproc = [1, 1, 1]        # process grid

        self.BoundaryCondition = 0    # default is periodic bC
        self.region = [0, 0, 0, self.Nx, self.Ny, self.Nz]
        self.voxel_length = voxlen
        self.labels = np.unique(img)
        self.label_count = self.labels.size
        self.write_labels = self.labels
        self.solid_labels = self.write_labels[self.write_labels<=0]
        print("Original image labels " + str(self.labels) )
        print("Simulation image labels " + str(self.write_labels) )
        print("Solid labels " + str(self.solid_labels) )
        
    # assign relabeling for LBPM convention
    #    non-negative labels are solid / immobile phase
    #    phase 1 is NWP
    #    phase 2 is WP
    def relabel(self, newlabels):
        """
        Relabel the domain image with new labels.

        Parameters
            newlabels: list or numpy.ndarray
                A list or array of new labels for the domain image.

        """
        if (len(newlabels) != len(self.labels)):
            print("Error assigning new labels, length must match!")
            print(self.labels)
        else :
            self.write_labels = np.array(newlabels)
            self.solid_labels = self.write_labels[self.write_labels<=0]
            print("Original image labels " + str(self.labels) )
            print("Simulation image labels " + str(self.write_labels) )
            print("Solid labels " + str(self.solid_labels)) 
        
    # crop the image
    def subregion(self, origin, size):
        """
        Define a subregion within the domain.

        Parameters
            origin: list or tuple
                The origin coordinates [x, y, z] of the subregion.
            size: list or tuple
                The size [x, y, z] of the subregion.

        """
        self.region[0:3] = origin
        self.region[3:6] = size
        print("Simulation region: ")
        print("    origin: " + str(self.region[0:3]))
        print("    size: " + str(self.region[3:6]))
        
    # basic domain decomposition with process grid [px, py, pz]
    def decomp(self, process_layout):
        """
        Decomposes the simulation domain into sub-domains based on the provided process layout.

        Parameters
            process_layout: tuple of ints, the layout of processes (e.g., (nx, ny, nz))
        """
        self.nproc = process_layout
        self.nx = np.int32(self.region[3] / self.nproc[0] )
        self.ny = np.int32(self.region[4] / self.nproc[1] )
        self.nz = np.int32(self.region[5] / self.nproc[2] )
        print("Process grid " + str(self.nproc))
        print("Sub-domain size " + str([self.nx, self.ny, self.nz]))

    def view(self, slice): 
        """
        Decomposes the simulation domain into sub-domains based on the provided process layout.

        Parameters
            process_layout: tuple of ints, the layout of processes (e.g., (nx, ny, nz)) 
        """
        plt.figure(1)
        plt.title('simulation domain')
        plt.pcolormesh(self.image[slice, :, :], cmap='hot')
        plt.grid(True)
        plt.axis('equal')
        plt.show()

    def add_section(self, LBPM_input_file):
        """ 
        Adds the domain parameters to the given LBPM input file string.

        Parameters
            LBPM_input_file: str, the LBPM input file content

        Returns
            str: The updated LBPM input file content with added domain parameters
        """
        LBPM_input_file = "Domain {\n"
        LBPM_input_file += '   Filename = "'+str(self.name)+'"'+"\n"
        LBPM_input_file += '   ReadType ="8bit"'+"\n"
        LBPM_input_file += '   voxel_length = '+str(self.voxel_length)+"\n"
        LBPM_input_file += "   N = "+str(self.Nx)+", "+str(self.Ny)+", "+str(self.Nz)+"\n"
        LBPM_input_file += "   offset = " + lbpm_input_string_from_list(self.region[0:3]) +"\n"
        LBPM_input_file += "   nproc = " + lbpm_input_string_from_list(self.nproc) +"\n"
        LBPM_input_file += "   n = "+str(self.nx)+", "+str(self.ny)+", "+str(self.nz)+"\n"
        LBPM_input_file += "   ReadValues = " + lbpm_input_string_from_list(self.labels) +"\n"
        LBPM_input_file += "   WriteValues = " + lbpm_input_string_from_list(self.write_labels) +"\n"
        LBPM_input_file += "   ComponentLabels = " + lbpm_input_string_from_list(self.solid_labels) +"\n"
        LBPM_input_file += "   BC = " + str(self.BoundaryCondition) + "\n"
        LBPM_input_file += '}\n'
        return(LBPM_input_file)
