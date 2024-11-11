
import streamlit as st
import pandas as pd
import numpy as np
import astropy.units as u
from astroquery.simbad import Simbad
import astropy.units as u
from streamlit import session_state
from io import StringIO

st.set_page_config(
        page_title="Create TCS Cat",
        page_icon="",
        layout="wide",
    )

# sidebar_logo = 'images/Starcutout.png'
# st.logo(sidebar_logo, size='large')


'''
### targets_into_TCScat.py

Supply a list of Simbad-resolvable target names and produce a catalog for LCO TCS.  

To run:

#### *Names*: 
Enter list of Simbad-resolvable names with quotes around each in text box. Ex: 'alf Sco', 'HD 214810A', 'HD 218434' 

#### OR 

Upload a text file of the list with quotes around each. '''
with open('images/Example-catalog-entry') as f:
    st.download_button('Download example entry file',f)
'''

#### *Filename*: 
Enter filename to save catalog as. Cat will save as "filename.cat" to your local downloads folder.

Dependencies:
astropy, astroquery, numpy, pandas

Written by Logan Pearce, 2022
https://github.com/logan-pearce; http://www.loganpearcescience.com
'''

def doit(Names, filename):
    Names = Names.split(',')
    Names = [Names[i].replace("'","") for i in range(len(Names))]
    Names = [Names[i].replace("*","") for i in range(len(Names))]
    Names = [Names[i].replace("\n","") for i in range(len(Names))]

    pdcat = pd.DataFrame(data={'Name':Names})
    # for i in range(1,len(Names)):
    #     data = pd.Series({'Name':Names[i]})
    #     #pdcat = pdcat.append(data,ignore_index=True)
    #     pdcat = pd.concat([pdcat,data],ignore_index=True, axis=1)
        

    pdcat['RA'], pdcat['DEC'], pdcat['pmra'], pdcat['pmdec'] = np.nan,np.nan,np.nan,np.nan
    customSimbad = Simbad()
    customSimbad.add_votable_fields('pmra','pmdec')


    pdcat['pmra s/yr'], pdcat['pmdec arcsec/yr'] = np.nan, np.nan

    from astropy.coordinates import Angle
    for i in range(len(pdcat)):
        r = customSimbad.query_object(pdcat['Name'][i])
        pdcat.loc[i,'RA'], pdcat.loc[i,'DEC'] = r['RA'][0],r['DEC'][0]
        pdcat.loc[i,'pmra'], pdcat.loc[i,'pmdec'] = r['PMRA'][0],r['PMDEC'][0]
        pdcat.loc[i,'RA'], pdcat.loc[i,'DEC'] = pdcat.loc[i,'RA'].replace(' ',':'), \
            pdcat.loc[i,'DEC'].replace(' ',':')
        
        
        # Create an astropy angle object:
        a = Angle(pdcat.loc[i,'pmra'],u.mas)
        # Convert to hms:
        a2 = a.hms
        # add up the seconds (a2[0] and a2[1] are most likely 0 but just in case):
        a3 = a2[0]*u.hr.to(u.s) + a2[1]*u.min.to(u.s) + a2[2]
        # put into table:
        pdcat.loc[i,'pmra s/yr'] = a3
        
        # Dec is easier:
        a = pdcat.loc[i,'pmdec']*u.mas.to(u.arcsec)
        # put into table:
        pdcat.loc[i,'pmdec arcsec/yr'] = a
        
    for i in range(len(pdcat)):
        pdcat.loc[i,'Name'] = pdcat.loc[i,'Name'].replace(' ','')
    pdcat['num'] = np.arange(1,len(pdcat)+1,1)

    pdcat_out = pdcat[['num']]
    pdcat_out['Name'] = pdcat['Name']
    pdcat_out['RA'] = pdcat['RA']
    pdcat_out['Dec'] = pdcat['DEC']
    pdcat_out['Equinox'] = '2000'
    pdcat_out['pmra'] = pdcat['pmra s/yr']
    pdcat_out['pmdec'] = pdcat['pmdec arcsec/yr'] 
    pdcat_out['rotang'] = '0'
    pdcat_out['rot_mode'] = 'GRV'
    pdcat_out['RA_probe1'],pdcat_out['Dec_probe1'] = '00:00:00.00',  '+00:00:00.0'
    pdcat_out['equinox'] = '2000'
    pdcat_out['RA_probe2'],pdcat_out['Dec_probe2'] = '00:00:00.00',  '+00:00:00.0'
    pdcat_out['equinox '] = '2000'
    pdcat_out['epoch'] = '2000'
    pdcat_out = pdcat_out.to_csv(index=False, sep='\t')
    return pdcat_out
    
left_co, right_co = st.columns(2)
with left_co:
    Names = st.text_input(r"$\textsf{\Large Names}$", key='names')
with right_co:
    uploaded_file = st.file_uploader(r"$\textsf{\Large Upload List or Names}$")
    if uploaded_file is not None:
    # To convert to a string based IO:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        # To read file as string:
        Names = stringio.read()
        st.write(Names)

filename = st.text_input(r"$\textsf{\Large Filename}$", key='filename')

if st.button(r"$\textsf{\Large Generate TCS Catalog}$"):
    pdcat_out = doit(Names, filename)
    st.write(':sparkles: Catalog Created :sparkles:')
else:
    pdcat_out = ''

st.download_button(label=r"$\textsf{\Large Save Cat}$", data = pdcat_out, file_name=filename+'.cat')