
import streamlit as st
import pandas as pd
import numpy as np
import astropy.units as u
from astroquery.simbad import Simbad
from io import StringIO

st.set_page_config(
        page_title="Create TCS Cat",
        page_icon="",
        layout="wide",
    )

# sidebar_logo = 'images/Starcutout.png'
# st.logo(sidebar_logo, size='large')

c1,c2,c3 = st.columns(3)
with c2:
    st.write('## Magellan TCS Catalog Builder')
'''

Supply a list of Simbad-resolvable target names and produce a catalog for LCO TCS.  

Documentation for TCS catalog format: https://www.lco.cl/technical-documentation/observing-catalogs-format/.  This script takes in Simbad names of targets and retrieves from Simbad the parameters for fields 2--7. The observer needs to supply telescope setup parameters for fields 8--16.  The default settings given in the fields will be populated automatically if not changed. Alternately you can supply a csv file of target names and fields 8--16 parameters and generate a catalog from that. Or you can supply a csv file of all fields to generate a catalog.


Written by Logan Pearce, 2022, 2024
https://github.com/logan-pearce; http://www.loganpearcescience.com

'''
st.divider()
cols = st.columns(3)
with cols[1]:
    st.markdown('#### *Upload a csv of relevant parameters* ')
cols = st.columns(2)
with cols[0]:
    st.markdown('Example of supplying csv list of targets with varying TCS parameters')
    with open('Example1.csv') as f:
        st.download_button('Download example of basic csv input', f)

with cols[1]:
    st.markdown('Example of supplying csv list of targets with all parameters provided according to format')
    with open('Example2.csv') as f:
        st.download_button('Download example of full parameter csv input', f)


uploaded_file = st.file_uploader(r"$\textsf{\Large Upload csv}$")
if uploaded_file is not None:
# To convert to a string based IO:
    pdcat_uploaded = pd.read_csv(uploaded_file)
    st.write(pdcat_uploaded)

'''
Enter filename to save catalog as. Cat will save as "filename.cat" to your local downloads folder.'''

filename = st.text_input(r"$\textsf{\Large Filename}$", key='filenamecsv')

def doitwithcsv(pdcat_in):
    Names = pdcat_in['Name']
    Names = [Names[i].replace(" ","") for i in range(len(Names))]
    Names = [Names[i].replace("'","") for i in range(len(Names))]
    Names = [Names[i].replace("*","") for i in range(len(Names))]
    Names = [Names[i].replace("\n","") for i in range(len(Names))]
    if 'RA' in pdcat_in.columns:
        nums = np.arange(1,len(pdcat_in)+1,1)
        pdcat_out = pd.DataFrame({'num':nums, 'Name':Names})
        for col in pdcat_in.columns[1:]:
            pdcat_out[col] = pdcat_in[col]
        pdcat_out = pdcat_out.to_csv(index=False, sep='\t')
        return pdcat_out
    else:
        pdcat = pd.DataFrame(data={'Name':Names})
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
        pdcat_out['pmra'] = pdcat['pmra s/yr']
        pdcat_out['pmdec'] = pdcat['pmdec arcsec/yr'] 
        pdcat_out['Equinox'] = '2000'
        pdcat_out['rotang'] = pdcat_in['rotang'] 
        pdcat_out['rot_mode'] = pdcat_in['rot_mode'] 
        pdcat_out['RA_probe1'],pdcat_out['Dec_probe1'] = pdcat_in['RA_probe1'] ,  pdcat_in['Dec_probe1'] 
        pdcat_out['equinox'] = pdcat_in['equinox']
        pdcat_out['RA_probe2'],pdcat_out['Dec_probe2'] = pdcat_in['RA_probe2'] ,  pdcat_in['Dec_probe2']
        pdcat_out['equinox '] = pdcat_in['equinox ']
        pdcat_out['epoch'] = pdcat_in['epoch']
        pdcat_out = pdcat_out.to_csv(index=False, sep='\t')
        return pdcat_out

if st.button(r"$\textsf{\Large Generate TCS Catalog}$", key='generate1'):
    pdcat_out = doitwithcsv(pdcat_uploaded)
    st.write(':sparkles: Catalog Created :sparkles:')
else:
    pdcat_out = ''

st.download_button(label=r"$\textsf{\Large Save Cat}$", data = pdcat_out, file_name=filename+'.cat', key='save1')



def doit(Names, rotang, rot_mode, RA_probe1, DEC_probe1, eq1, RA_probe2, DEC_probe2, eq2, epoch, filename):
    Names = Names.split(',')
    Names = [Names[i].replace("'","") for i in range(len(Names))]
    Names = [Names[i].replace("*","") for i in range(len(Names))]
    Names = [Names[i].replace("\n","") for i in range(len(Names))]

    pdcat = pd.DataFrame(data={'Name':Names})

    pdcat['RA'], pdcat['DEC'], pdcat['pmra'], pdcat['pmdec'] = np.nan,np.nan,np.nan,np.nan
    customSimbad = Simbad()
    customSimbad.add_votable_fields('pmra','pmdec')


    pdcat['pmra s/yr'], pdcat['pmdec arcsec/yr'] = np.nan, np.nan

    from astropy.coordinates import Angle
    for i in range(len(pdcat)):
        try:
            r = customSimbad.query_object(pdcat['Name'][i])
            print(r)
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
        except:
            st.markdown('Could not find ' + pdcat['Name'][i])
            pass


    for i in range(len(pdcat)):
        pdcat.loc[i,'Name'] = pdcat.loc[i,'Name'].replace(' ','')
    pdcat['num'] = np.arange(1,len(pdcat)+1,1)

    pdcat_out = pdcat[['num']]
    pdcat_out['Name'] = pdcat['Name']
    pdcat_out['RA'] = pdcat['RA']
    pdcat_out['Dec'] = pdcat['DEC']

    # eq = eq.split(',')
    # if len(eq) == 1:
    #     pdcat_out.loc[:,'Equinox'] = eq[0]
    # else:
    #     try:
    #         pdcat_out['Equinox'] = np.array([str(e).replace(' ','') for e in eq])
    #     except:
    #         st.write('Enter RA/Dec equinox as one date or a list of dates as long as the number of names.')

    pdcat_out['pmra'] = pdcat['pmra s/yr']
    pdcat_out['pmdec'] = pdcat['pmdec arcsec/yr'] 

    rotang = rotang.split(',')
    if len(rotang) == 1:
        pdcat_out.loc[:,'rotang'] = str(rotang[0])
    else:
        try:
            pdcat_out['rotang'] = np.array([str(r) for r in rotang])
        except:
            st.write('Enter rotator angle as one date or a list of dates as long as the number of names.')

    rot_mode = rot_mode.split(',')
    if len(rot_mode) == 1:
        pdcat_out.loc[:,'rot_mode'] = str(rot_mode[0])
    else:
        try:
            pdcat_out['rot_mode'] = np.array([str(r) for r in rot_mode])
        except:
            st.write('Enter rotator mode as one date or a list of dates as long as the number of names.')

    RA_probe1 = RA_probe1.split(',')
    if len(RA_probe1) == 1:
        pdcat_out.loc[:,'RA_probe1'] = str(RA_probe1[0])
    else:
        try:
            pdcat_out['RA_probe1'] = np.array([str(r) for r in RA_probe1])
        except:
            st.write('Enter RA probe 1 as one date or a list of dates as long as the number of names.')

    DEC_probe1 = DEC_probe1.split(',')
    if len(DEC_probe1) == 1:
        pdcat_out.loc[:,'DEC_probe1'] = str(DEC_probe1[0])
    else:
        try:
            pdcat_out['DEC_probe1'] = np.array([str(r) for r in DEC_probe1])
        except:
            st.write('Enter DEC probe 1 as one date or a list of dates as long as the number of names.')

    eq1 = eq1.split(',')
    if len(eq1) == 1:
        pdcat_out.loc[:,'equinox'] = eq1[0]
    else:
        try:
            pdcat_out['equinox'] = np.array([str(e).replace(' ','') for e in eq1])
        except:
            st.write('Enter RA/Dec Probe 1 equinox as one date or a list of dates as long as the number of names.')


    RA_probe2 = RA_probe2.split(',')
    if len(RA_probe2) == 1:
        pdcat_out.loc[:,'RA_probe2'] = str(RA_probe2[0])
    else:
        try:
            pdcat_out['RA_probe2'] = np.array([str(r) for r in RA_probe2])
        except:
            st.write('Enter RA probe 2 as one date or a list of dates as long as the number of names.')

    DEC_probe2 = DEC_probe2.split(',')
    if len(DEC_probe2) == 1:
        pdcat_out.loc[:,'DEC_probe2'] = str(DEC_probe2[0])
    else:
        try:
            pdcat_out['DEC_probe2'] = np.array([str(r) for r in DEC_probe2])
        except:
            st.write('Enter DEC probe 2 as one date or a list of dates as long as the number of names.')

    eq2 = eq2.split(',')
    if len(eq2) == 1:
        pdcat_out.loc[:,'equinox '] = eq2[0]
    else:
        try:
            pdcat_out['equinox '] = np.array([str(e).replace(' ','') for e in eq2])
        except:
            st.write('Enter RA/Dec Probe 2 equinox as one date or a list of dates as long as the number of names.')

    epoch = epoch.split(',')
    if len(epoch) == 1:
        pdcat_out.loc[:,'epoch'] = epoch[0]
    else:
        try:
            pdcat_out['epoch'] = np.array([str(e).replace(' ','') for e in epoch])
        except:
            st.write('Enter epoch as one date or a list of dates as long as the number of names.')
    pdcat_out = pdcat_out.to_csv(index=False, sep='\t')
    return pdcat_out
    



st.divider()

cols = st.columns(3)
with cols[1]:
    st.write('#### *Manual Entry*:')
''' 
Enter list of Simbad-resolvable names separated by commas. Ex: alf Sco, HD 214810A, HD 218434. Or upload a text file of Simbad names separated by commas.'''

cols = st.columns([2,1])
with cols[0]:
    Names = st.text_input(r"$\textsf{\Large Names}$", key='names')
with cols[1]:
    uploaded_file = st.file_uploader(r"$\textsf{\Large Upload List of Names}$")
    if uploaded_file is not None:
    # To convert to a string based IO:
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        # To read file as string:
        Names = stringio.read()
        st.write(Names)
#Names = st.text_input(r"$\textsf{\Large Names}$", key='names')

''' Enter telescope set up parameters below.  If each target requires the same setup parameters, you only need to enter the value once. To apply different parameters for each target, enter the list into each field. The list length must be the same length as the list of names.  In the  below, four targets are provided, with one needing a different rotator mode and angle than the others, so a list of four modes and angles are entered in the relevant fields, with only one entry in each remaining field as those parameters are the same for all four targets.'''
#st.link_button("Manual Entry Example", "Manual-Example.png")

if 'show_text' not in st.session_state:
    st.session_state.show_text = False
def toggle_image():
    st.session_state.show_text = not st.session_state.show_text

st.button('Show/Hide Manual Entry Example', on_click=toggle_image)

if st.session_state.show_text:
    st.image("Manual-Example.png")

''' '''
''' '''

row_input = st.columns((1,1))
with row_input[0]:
    rotang = st.text_input(r"$\textsf{\Large Rotator Angle (default: 0)}$", '0',key='rotang')
with row_input[1]:
    rot_mode = st.text_input(r"$\textsf{\Large Rotator Mode (default: GRV)}$", 'GRV',key='rot_mode')

rows = st.columns([1,1])
with rows[0]:
    RA_probe1 = st.text_input(r"$\textsf{\Large RA Probe 1 (default: 00:00:00)}$", '00:00:00',key='RA_probe1')
    DEC_probe1 = st.text_input(r"$\textsf{\Large DEC Probe 1 (default: 00:00:00)}$", '00:00:00',key='DEC_probe1') 
    eq1 = st.text_input(r"$\textsf{\Large RA/DEC Probe 1 Equinox (default: 2000)}$", '2000',key='eq1')

with rows[1]:
    RA_probe2 = st.text_input(r"$\textsf{\Large RA Probe 2 (default: 00:00:00)}$", '00:00:00',key='RA_probe2')
    DEC_probe2 = st.text_input(r"$\textsf{\Large DEC Probe 2 (default: 00:00:00)}$", '00:00:00',key='DEC_probe2') 
    eq2 = st.text_input(r"$\textsf{\Large RA/DEC Probe 2 Equinox (default: 2000)}$", '2000',key='eq2')

epoch = st.text_input(r"$\textsf{\Large Epoch (default: 2000)}$", '2000',key='epoch')

'''
Enter filename to save catalog as. Cat will save as "filename.cat" to your local downloads folder.'''

filename = st.text_input(r"$\textsf{\Large Filename}$", key='filename')

if st.button(r"$\textsf{\Large Generate TCS Catalog}$", key='generate2'):
    pdcat_out = doit(Names, rotang, rot_mode, RA_probe1, DEC_probe1, eq1, RA_probe2, DEC_probe2, eq2, epoch, filename)
    st.write(':sparkles: Catalog Created :sparkles:')
else:
    pdcat_out = ''

st.download_button(label=r"$\textsf{\Large Save Cat}$", data = pdcat_out, file_name=filename+'.cat', key='save2')