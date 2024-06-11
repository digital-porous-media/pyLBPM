import re
import os
import numpy as np
import matplotlib.pyplot as plt

class domain_db:

    def __init__(self, name, img, voxlen = 1.0):
        # Domain should be initialized from 3D numpy array                                                                                   
        # set up the array in advance to match the simulation domain                                                                         
        self.name = name
        self.image = img.astype(np.uint8)
        self.Nx, self.Ny, self.Nz = self.image.shape
        self.nx = self.Nx   # sub-domain sizes                                                                                               
        self.ny = self.Ny
        self.nz = self.Nz
        self.nproc = [1, 1, 1]        # process grid                                                                                         
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
        self.region[0:3] = origin
        self.region[3:6] = size
        print("Simulation region: ")
        print("    origin: " + str(self.region[0:3]))
        print("    size: " + str(self.region[3:6]))
        
    # basic domain decomposition with process grid [px, py, pz]
    def decomp(self, process_layout):
        self.nproc = process_layout
        self.nx = np.int32(self.region[3] / self.nproc[0] )
        self.ny = np.int32(self.region[4] / self.nproc[1] )
        self.nz = np.int32(self.region[5] / self.nproc[2] )
        print("Process grid " + str(self.nproc))
        print("Sub-domain size " + str([self.nx, self.ny, self.nz]))

    def view(self, slice): 
        plt.figure(1)
        plt.title('simulation domain')
        plt.pcolormesh(ID[slice,:,:],cmap='hot')
        plt.grid(True)
        plt.axis('equal')
        plt.show()

