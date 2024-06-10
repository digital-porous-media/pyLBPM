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
        self.npx = 1        # process grid
        self.npy = 1
        self.npz = 1
        self.voxel_length = voxlen
        self.labels = np.unique(img)
        self.label_count = self.labels.size
        self.solid_labels = self.labels[self.labels<=0]
        print("Image labels " + str(self.labels) )
        print("Solid labels " + str(self.solid_labels) )
        
    # basic domain decomposition with process grid [px, py, pz]
    def decomp(self, px, py, pz):
        self.npx = px
        self.npy = py
        self.npz = pz
        self.nx = np.int32(self.Nx / px )
        self.ny = np.int32(self.Ny / py )
        self.nz = np.int32(self.Nz / pz )
        print("Process grid " + str([self.npx, self.npy, self.npz]))
        print("Sub-domain size " + str([self.nx, self.ny, self.nz]))

    def view(self, slice): 
        plt.figure(1)
        plt.title('simulation domain')
        plt.pcolormesh(ID[slice,:,:],cmap='hot')
        plt.grid(True)
        plt.axis('equal')
        plt.show()

