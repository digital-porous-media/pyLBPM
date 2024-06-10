import re
import os
import numpy as np
import matplotlib.pyplot as plt

def create_input_database(filename, content):
    infile = open(filename,'w')
    infile.write(content)
    infile.close()

def write_input_database(filename, content):
    infile = open(filename,'a')
    infile.write(content)
    infile.close()

def read_input_database(filename):
    infile = open(filename,'r')
    content = infile.read()
    return content

def lbpm_input_string_from_list( listValues ):
    string_values = str(list(listValues))
    string_values = string_values.strip("[]")
    return string_values

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

class color_db:

    def __init__(self, domain):
        # Domain should be initialized from 3D numpy array
        # set up default values for input parameters
        self.Dm = domain
        self.protocols = [ 'fractional flow',
                          'centrifuge', 
                          'core flooding', 
                          'image sequence'
                         ]
        self.protocol = "user specified"
        self.restart = False
        self.BC = 0
        self.useProtocol = False
        self.timestepMax = 10000000
        self.tauA = 0.7
        self.tauB = 0.7
        self.rhoA = 1.0
        self.rhoB = 1.0
        self.alpha = 0.01
        self.beta = 0.95
        self.F = [0.0, 0.0, 0.0]
        self.outletLayers = [0, 0, 5]
        self.inletLayers = [0, 0, 5]
        self.flux = 0.0
        self.capillary_number = 1.0e-5
        self.wetting_values = []
        for i in domain.solid_labels:
            self.wetting_values.append(1.0)
            
        print("Solid labels from domain: "
              + str(self.Dm.solid_labels)
             )
        print("Default wetting labels:   "
              + str(self.wetting_values)
              + " (change manually if desired)"
             )
    def set_protocol(self, string):
        self.useProtocol = False
        for option in self.protocols:
            if (option == string):
                self.protocol = option
                self.useProtocol = True
                print("Protocol selected: " + option)
                
                if (self.protocol == "fractional flow"):
                    self.F =  [0.0, 0.0, 1.0e-5]
                    self.outletLayers = [0, 0, 5]
                    self.inletLayers = [0, 0, 5]
                    self.target_capillary = 1.0e-5
                    self.BC = 0
                    
                elif (self.protocol == "fractional flow"):
                    #self.flux = capillary_number*interfacial_tension/(rho_w*nu_w)
                    print("not implemented")
                    
        if (self.useProtocol == False):
            print("Protocol not set. Please choose from the options below\n" 
                  + str(self.protocols))
                    
    def show_config_file(self):
        LBPM_input_file = "Domain {\n"
        LBPM_input_file += '   Filename = "'+str(self.Dm.name)+'"'+"\n"
        LBPM_input_file += '   ReadType ="8bit"'+"\n"
        LBPM_input_file += '   voxel_length = '+str(self.Dm.voxel_length)+"\n"
        LBPM_input_file += "   N = "+str(self.Dm.Nx)+", "+str(self.Dm.Ny)+", "+str(self.Dm.Nz)+"\n"
        LBPM_input_file += "   n = "+str(self.Dm.Nx)+", "+str(self.Dm.Ny)+", "+str(self.Dm.Nz)+"\n"
        LBPM_input_file += "   nproc = "+str(self.Dm.Nx)+", "+str(self.Dm.Ny)+", "+str(self.Dm.Nz)+"\n"
        LBPM_input_file += "   n = "+str(int(self.Dm.nx))+", "+str(int(self.Dm.ny))+", "+str(int(self.Dm.nz))+"\n"
        LBPM_input_file += "   nproc = "+str(int(self.Dm.npx))+", "+str(int(self.Dm.npy))+", "+str(int(self.Dm.npz))+"\n" 
        LBPM_input_file += "   ReadValues = " + lbpm_input_string_from_list(self.Dm.labels) +"\n"
        LBPM_input_file += "   WriteValues = " + lbpm_input_string_from_list(self.Dm.labels) +"\n"
        LBPM_input_file += "   ComponentLabels = " + lbpm_input_string_from_list(self.Dm.solid_labels) +"\n"
        LBPM_input_file += '}\n'
        LBPM_input_file += "Color {\n"
        if (self.useProtocol):
            LBPM_input_file += '   protocol = "'+str(self.protocol)+'"'+"\n"
            
        LBPM_input_file += '   Restart = '+str(self.restart)+"\n"
        LBPM_input_file += '   WettingConvention = "SCAL"'+"\n"
        LBPM_input_file += "   ComponentLabels = " + lbpm_input_string_from_list(self.Dm.solid_labels) +"\n"
        LBPM_input_file += "   ComponentAffinity = " + lbpm_input_string_from_list(self.wetting_values) +"\n"
        LBPM_input_file += '   timestepMax = '+str(self.timestepMax)+"\n"
        LBPM_input_file += '   tauA = '+str(self.tauA)+"\n"
        LBPM_input_file += '   tauB = '+str(self.tauB)+"\n"
        LBPM_input_file += '   rhoA = '+str(self.rhoA)+"\n"
        LBPM_input_file += '   rhoB = '+str(self.rhoB)+"\n"
        LBPM_input_file += '   alpha = '+str(self.alpha)+"\n"
        LBPM_input_file += '   beta = '+str(self.beta)+"\n"
        LBPM_input_file += '   capillary_number = '+str(self.capillary_number)+"\n"
        LBPM_input_file += "   F = " + lbpm_input_string_from_list(self.F) +"\n"
        LBPM_input_file += "   outletLayers = " + lbpm_input_string_from_list(self.outletLayers) +"\n"
        LBPM_input_file += "   inletLayers = " + lbpm_input_string_from_list(self.inletLayers) +"\n"
        LBPM_input_file += '}\n'
        LBPM_input_file += 'Visualization { \n'
        LBPM_input_file += '   save_8bit_raw = true \n'
        LBPM_input_file += '   write_silo = false \n'
        LBPM_input_file += '}\n'
        LBPM_input_file += 'Analysis { \n'
        LBPM_input_file += '   restart_file = "Restart"\n'
        LBPM_input_file += '   subphase_analysis_interval = 5000'+"\n"
        LBPM_input_file += '   analysis_interval = 1000'+"\n"
        LBPM_input_file += '}\n'
        LBPM_input_file += "FlowAdaptor {\n"
        if self.protocol == "fractional flow" :
            LBPM_input_file += '   max_steady_timesteps = 200000'+"\n"
            LBPM_input_file += '   min_steady_timesteps = 100000'+"\n"
            LBPM_input_file += '   fractional_flow_increment = 0.1'+"\n"
            LBPM_input_file += '   mass_fraction_factor = 0.0002'+"\n"
            LBPM_input_file += '   endpoint_threshold = 0.1'+"\n"
        LBPM_input_file += "}\n"
        write_input_database("input.db",LBPM_input_file)
        print(LBPM_input_file)
        
def is_float(element:any) -> bool:
    if element is None:
        return False
    try: 
        float(element)
        return True
    except ValueError:
        return False


def ExtractDatabaseSection( File, Section ):
    SectionKey= Section+" {"
    if SectionKey in File:
        section = File.split(SectionKey,1)[1]
        open = 1
        for index in range(len(section)):
             if section[index] in '{}':
                open = (open + 1) if section[index] == '{' else (open - 1)
             if not open:
                #return re.sub('[\s]',';',match[:index].replace("\n",""))
                return section[:index].strip()

def ConvertDatabaseFormat ( Section ):
    class A: 
        pass
    # Clean the text 
    SectionList=re.sub('//.*?\n','\n',Section)  # strip C/C++ style comments
    SectionList="(" + SectionList.replace("\n",");(") + ")"
    SectionList=SectionList.replace('(','("')
    SectionList=SectionList.replace('=','" :')
    SectionList=re.sub('[\s]','',SectionList)
    SectionList=SectionList.replace(',)',')')
    SectionList=SectionList.replace(');(',')\n(')
    for line in SectionList.split('\n'):
        #print(line)
        # split into key - value pairs
        key=re.sub('\(','',line.split(":")[0])
        value=re.sub('\)','',line.split(":")[1]).strip()
        items=value.count(",")+1
        #handle vectors
        if (items > 1):
            vector=value
            #print(np.fromstring(re.sub('\)','',value),sep=","))
            value=np.fromstring(re.sub('\)','',value),sep=",")
            print("Key "+key+" is vector:",value)
            value=vector 
        elif (value.isnumeric()):
            print("Key "+key+" is integer:",value)
            value=int(value)
        elif (is_float(value)):
            print("Key "+key+" is float:",value)
            value=float(value)
            #print(key+str(np.fromstring(re.sub('\)','',value),sep=",")))
        else :
            print("Key "+key+" is string:",value)
        # Assign keys to python class
        key=key[1:-1]  #remove quotes from key
        setattr(A,key,value)

    return (A)

def get_section( File, Section ):
    ReturnSection=ConvertDatabaseFormat(ExtractDatabaseSection(File,Section))

def read_database(simulation_directory):
    #simulation_directory="../lbpm/lrc32"
    input_file=os.path.join(simulation_directory,"input.db")
    input_db=open(input_file,"r")
    input=input_db.read()
    input_db.close()
    print(input)
    return(input)

