from pyLBPM import lbpm_input_database

input_db=lbpm_input_database.read_database("tests")

Color=lbpm_input_database.get_section(input_db, "Color")
#GetDatabaseSection( input_db, "Color" )
#Domain=GetDatabaseSection( input_db, "Domain" )
#MRT=GetDatabaseSection( input_db, "MRT" )
