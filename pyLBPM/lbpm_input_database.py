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

