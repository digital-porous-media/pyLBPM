import re
import os
import numpy as np
import matplotlib.pyplot as plt

def create_input_database(filename, content):
    with open(filename,'w') as infile:
        infile.write(content)

def write_input_database(filename, content):
    with open(filename, 'a') as infile:
        infile.write(content)

def read_input_database(filepath):
    """Read input database file content.

    :param filepath: Path to the input database file (e.g., 'input.db')
    :return: String content of the file
    """
    with open(filepath, 'r') as infile:
        content = infile.read()
    return content


def lbpm_input_string_from_list( listValues ):
    string_values = str(list(listValues))
    string_values = string_values.strip("[]")
    return string_values

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
        open_section = 1
        for index in range(len(section)):
             if section[index] in '{}':
                open_section = (open_section + 1) if section[index] == '{' else (open_section - 1)
             if not open_section:
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
        try:
            # split into key - value pairs
            key=re.sub('\(','',line.split(":")[0])
            value=re.sub('\)','',line.split(":")[1]).strip()
            items=value.count(",")+1
        except IndexError:
            continue
        #handle vectors
        if (items > 1):
            vector=value
            #print(np.fromstring(re.sub('\)','',value),sep=","))
            value=np.fromstring(re.sub('\)','',value),sep=",")
            value=vector
        elif (value.isnumeric()):
            value=int(value)
        elif (is_float(value)):
            value=float(value)
            #print(key+str(np.fromstring(re.sub('\)','',value),sep=",")))
        else :
            pass
        # Assign keys to python class
        key=key[1:-1]  #remove quotes from key
        setattr(A,key,value)

    return (A)

def get_section( File, Section ):
    ReturnSection=ConvertDatabaseFormat(ExtractDatabaseSection(File,Section))
    return ReturnSection

def read_database(simulation_directory, input_filename="input.db"):
    """Read input database from a simulation directory.

    :param simulation_directory: Path to the simulation directory
    :param input_filename: Name of the input database file (default: "input.db")
    :return: String content of the database file
    """
    input_file = os.path.join(simulation_directory, input_filename)
    with open(input_file, "r") as input_db:
        content = input_db.read()
    return content


def get_database_section_names( File ):
    File = re.sub('//.*?\n','\n', File)  # strip C/C++ style comments
    section_start_idx = [s.start() for s in re.finditer(r'\{', File)]
    section_end_idx = [s.start() for s in re.finditer(r'\}', File)]
    section_end_idx.insert(0, -1)
    section_end_idx.pop(-1)
    section_names = [File[s_end+1:s_start] for s_end, s_start in zip(section_end_idx, section_start_idx)]
    section_names = [s.strip() for s in section_names]

    return section_names

