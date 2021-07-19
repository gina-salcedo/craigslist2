# -*- coding: utf-8 -*-
"""
Name: Gina Salcedo Lannin
CS602 Section 1
Data: Craigslist Used Cars

https://share.streamlit.io/gina-salcedo/craigslist2/main/Lannin_FinalProject.py

Description: 
    
    This Program allows individuals to view the distribution of craigslist car sales thorughout the US, providing visuals
    for comparison and understanding the supply differences by state and region.

"""


import streamlit as st
import pandas as pd
import statistics as stats
import pydeck as pdk
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from datetime import datetime, time
import numpy as np
import wikipedia
import xlrd

st.set_page_config(
     page_title='Craigslist Cars',
     layout="wide",
     initial_sidebar_state="expanded",
)

import base64

main_bg = "pexels-kelly-lacy-2402235_2.jpg"
main_bg_ext = "jpg"

side_bg = "pexels-kelly-lacy-2402235_2.jpg"
side_bg_ext = "jpg"

st.markdown(
    f"""
    <style>
    .reportview-container {{
        background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()})
    }}
   .sidebar .sidebar-content {{
        background-color:  #011839}})
    }}
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache #to avoid re-running the data collected


def load_data():

    filename = 'cl_used_cars_7000_sample.xls'
    
    df = pd.read_excel(filename)
    
    df.columns = ['Unnamed: 0', 'id', 'url', 'region', 'region_url', 'price', 'year',
       'manufacturer', 'model', 'condition', 'cylinders', 'fuel', 'odometer',
       'title_status', 'transmission', 'VIN', 'drive', 'size', 'category',
       'paint_color', 'image_url', 'description', 'state', 'lat', 'lon',
       'posting_date']


    df = df.dropna()
    
    df['region'] = df['region'].str.title()
    
    #dropping columns I don't want, OK to drop 'id' because VIN is a unique identifier
    df = df.drop(columns = ['Unnamed: 0', 'url', 'region_url', 'description', 'image_url', 'id'])

    

    df['state'] = df['state'].str.upper() 
    
    df.reset_index(inplace = True)
    
    df.drop(columns = ['index'], inplace = True)
    
    #add datetime component
    df['posting_date'] = [df['posting_date'][n][0:len(df['posting_date'][n])-5] for n in range(len(df))]
    df['DTstr'] = pd.Series(df['posting_date'], dtype='string')
    


    df['date'] = [datetime.strptime(df.loc[n,'DTstr'], "%Y-%m-%dT%H:%M:%S") for n in range(len(df))]
    
     
    return(df)

#This function helps the suer narrow down the possible options for each column
#It retunrs a sorted list of possibilities

def getChoices(df, column):
    col = df[column]
    choices = col.drop_duplicates()
        
    return(sorted(list(choices)))

################################## CHECK BOXES ##################################

# creates check boxes for one column of the dataframe 
# returns a list of what the user has selected in the check boxes
# this can later be used for filtering

def createCheckboxes(df, column):
    choices = getChoices(df, column)
    
    chosen = []
    
    st.sidebar.subheader(column.title())

    
    for choice in choices:
        choice = choice.title()

        if st.sidebar.checkbox(choice):
            chosen.append(choice)

             
    return(chosen)


# cycles through the columns for which we want check boxes
# calls on a function that creates check boxes and returns a table of the items the user selected
# creates a dictionary where the key is the column name and the values are the returned table

def generateDictChoices(state_df, checkBoxColumns):
    
    selectionsDict = {}
    
    for field in checkBoxColumns:      
        selectionsDict[field] = createCheckboxes(df = state_df, column=field)
       
    return(selectionsDict)

############################ MULTI SELECT BOXES ###########################


def createMultiSelect(df,column):

    choices = getChoices(df, column)
    default = choices[:]
    # default = choices[:3] 
   # user_choices = st.sidebar.multiselect(f'Select {column}', choices, default = default)
    user_choices = st.multiselect(f'Select {column}', choices, default = default)    
    return(user_choices)

def generateDictChoicesMulti(state_df, multiSelectColumns):
    
    selectionsDict = {}
    
    for field in multiSelectColumns:      
        selectionsDict[field] = createMultiSelect(df = state_df, column=field)
     #   print(selectionsDict[field])
      
  #  print(selectionsDict)
    return(selectionsDict)

################################## MAP ##################################

# This dataset had duplicate coordinates in some instances
# This function adds a tiny value to the coordinates that are duplicates to avoid a pydeck error
# The lon and lat values are then rounded elsewhere

def noDupCoors(df):
    
    df_coords = []
    dupes = []
    
    for i in range(len(df)):
        lon = df['lon'][i]
        lat = df['lat'][i]

    
        if [lat, lon] in df_coords:
            lon2 = df['lon'][i] + .0000000001
            lat2 = df['lat'][i] + .0000000001
            df_coords.append([lat2, lon2])
            dupes.append(i)
        else:
            lon2 = df['lon'][i] 
            lat2 = df['lat'][i] 
            df_coords.append([lat2, lon2])
    
    
    newdf = pd.DataFrame(df_coords, columns =['lat2', 'lon2']).reset_index()
    df1 = df.reset_index()
    df1 = df1.merge(newdf, how='left', on = 'index')
    

    return(df1)


# crateMap
# Uses df to plot all the points
# Uses state_df to get the view to zoom into the selected state (taking the mean lon and lat values)


def createMap(df, state_df):
    
    df =  noDupCoors(df) #creating coordinates without duplicates to allow the program to map them
    
    z = st.slider('Map: Zoom Factor', min_value = 0, max_value = 9, value =5)

    view_state = pdk.ViewState(
        latitude = state_df['lat'].mean(),
        longitude = state_df['lon'].mean(),
        zoom = z)
    
    #replacing the lat and lon values with de-duped versions 
    df['lon'] = df['lon2']
    df['lat'] = df['lat2']
    layer1 = pdk.Layer("ScatterplotLayer", 
                        data = df,
                        pickable = True,
                        opacity = 0.8,
                        stroked = True,
                     #   filled = True,
                        
                        get_position = ['lon', 'lat'],
                        get_radius = 15000, 
                        get_fill_color = [255, 140, 0])
    
    
    
    
    tool_tip = {"html": "<b>Region Name:</b>  {region} <br/><b> State: </b> {stateName} <br/><b>  Year   : </b> {year} <b> Price: </b> {price} <br/><b> Manufacturer: </b> {manufacturer} <br/> <b> Model: </b> {model} <br/>  <b> Posting Date: </b> {date}", 
                 "style": {"backgroundColor": "steelblue", "color": "white"}} #
    
    
    
    map_ = pdk.Deck(map_style ='mapbox://styles/mapbox/outdoors-v11',
                   layers = [layer1],
                   initial_view_state=view_state,
                   tooltip=tool_tip)

    st.pydeck_chart(map_)


############################### FILTERING #########################################

# Takes user-selected values and a dataframe (usually narrowed down by state)
# Checks which line items in the data frame are compatible with user selections
# One takes in values from the checkboxes, the other one takes in values from the multiselectio boxes

def updatedDf(df, selectionsDict):
    
    df_new = pd.DataFrame(columns = df.columns)

    if all(value == [] for value in selectionsDict.values()):
        return(df)
    
    for key in selectionsDict.keys():
        df_values = getChoices(df = df, column = key) #unique items in state df
        selec_values = selectionsDict[key] #boxes checked by user

        for item in df_values:

            if item.title() in selec_values:

                df_temp = df[df[key] == item]
                df_new = pd.concat([df_new, df_temp])
               
    final_df = df_new.drop_duplicates()
    

    return(final_df)



def updatedDf2(df, selectionsDict):
    
    df_new = pd.DataFrame(columns = df.columns)
    
    for key in selectionsDict.keys():
#        print(selectionsDict.values())
        df_values = getChoices(df = df, column = key) #unique items in state df
        selec_values = selectionsDict[key] #boxes checked by user

        for item in df_values:
#            print(item)

            if item in selec_values:
#                print(item)
                df_temp = df[df[key] == item]
                df_new = pd.concat([df_new, df_temp])
               
    final_df = df_new.drop_duplicates()
#    print(final_df)
    

    return(final_df)

###################################STATS###########################################    


#gets the quantitative metrics we want for a specific area (takes in a df that should encompass the entire area
# then we iterate to repeat this for each one)

def getStatsForArea(df):

    statDict = {}
    
    statDict['Sales Count'] = df['VIN'].count()
    
    statDict['Mean Price'] = round(stats.mean(df.price), 2)
    statDict['Median Price'] = round(stats.median(df.price), 2)

    
    
    statDict['Mean Mileage'] = round(stats.mean(df.odometer),2)
    statDict['Median Mileage'] = round(stats.median(df.odometer),2)

    
    statDict['Oldest Car Year'] = min(df.year)
    statDict['Newest Car Year'] = max(df.year)
    statDict['Median Car Year'] = stats.median(df.year)

    
    return(statDict)


def statsByState(df):
  
    stateChoices = getChoices(df, 'state')
    byState = {} 
    
    for state in stateChoices:
        state_df = df[df['state'] == state]
        byState[state] = getStatsForArea(state_df)

        
    stats_df = pd.DataFrame(byState)
    

 
    cm = sns.color_palette("flare", as_cmap=True)
    
 

    st.dataframe(stats_df.style.background_gradient(axis = 1, cmap = cm).format('{:.0f}'))    


################################# Pie Charts ##############################

#gathers percentages to build pie charts based on column and df
# depending on what we want, we would use state_df or just df (data comes in filtered)
def forPie(df, column):

    percentages = []
    labels = []
    choices = getChoices(df=df, column=column)
    
    for choice in choices:
        df_temp = df[df[column]== choice]
        percentage = df_temp.shape[0]/df.shape[0]    
        percentages.append(percentage)
        labels.append(choice)
        

    return(percentages, labels)

def createPie(df, column, title = 'Pie Chart'):

    percentages, labels = forPie(df, column = column)    

    
    fig1, ax = plt.subplots()

    explode = [0.05 for label in labels]
    print(explode)
    
    ax.pie(percentages,autopct='%1.1f%%', startangle=90, colors = cm, explode = explode)
    
    ax.legend(labels,
          title=column.title(),
          loc="center left",
          bbox_to_anchor=(1, 0, 0.5, 1))
    

    
    ax.axis('equal')
    ax.set_title(title, color = 'purple', size = 15)
   
    st.pyplot(fig1)    
    
################################# Box Plots ##############################

def createBoxPlot(df, title, qual, quant, horizontal = 0):
    
    
    if horizontal == 1:
        x = quant
        y = qual
    else:
        x= qual
        y = quant
    
    
    labels = getChoices(df, qual)



    fig2, ax2 = plt.subplots()

    df = df.sort_values(by = [qual, quant])

    ax2 = sns.boxplot(x=x, y=y, data=df, palette = cm)

    
    ax2.legend(labels,
          title=qual.title(),
          loc="upper left",
          bbox_to_anchor=(1, 0, 0.5, 1), labelcolor = cm)

    ax2.set_title(title, color = 'purple', size = 15)
   
    st.pyplot(fig2)    
  


############################### States Mapping ##############################

def abbrevToState(df):
    # United States of America Python Dictionary to translate States,
    # Districts & Territories to Two-Letter codes and vice versa.
    #
    # https://gist.github.com/rogerallen/1583593
    #
    # Dedicated to the public domain.  To the extent possible under law,
    # Roger Allen has waived all copyright and related or neighboring
    # rights to this code.
    
    
    us_state_abbrev = {
        'Alabama': 'AL',
        'Alaska': 'AK',
        'American Samoa': 'AS',
        'Arizona': 'AZ',
        'Arkansas': 'AR',
        'California': 'CA',
        'Colorado': 'CO',
        'Connecticut': 'CT',
        'Delaware': 'DE',
        'District of Columbia': 'DC',
        'Florida': 'FL',
        'Georgia': 'GA',
        'Guam': 'GU',
        'Hawaii': 'HI',
        'Idaho': 'ID',
        'Illinois': 'IL',
        'Indiana': 'IN',
        'Iowa': 'IA',
        'Kansas': 'KS',
        'Kentucky': 'KY',
        'Louisiana': 'LA',
        'Maine': 'ME',
        'Maryland': 'MD',
        'Massachusetts': 'MA',
        'Michigan': 'MI',
        'Minnesota': 'MN',
        'Mississippi': 'MS',
        'Missouri': 'MO',
        'Montana': 'MT',
        'Nebraska': 'NE',
        'Nevada': 'NV',
        'New Hampshire': 'NH',
        'New Jersey': 'NJ',
        'New Mexico': 'NM',
        'New York': 'NY',
        'North Carolina': 'NC',
        'North Dakota': 'ND',
        'Northern Mariana Islands':'MP',
        'Ohio': 'OH',
        'Oklahoma': 'OK',
        'Oregon': 'OR',
        'Pennsylvania': 'PA',
        'Puerto Rico': 'PR',
        'Rhode Island': 'RI',
        'South Carolina': 'SC',
        'South Dakota': 'SD',
        'Tennessee': 'TN',
        'Texas': 'TX',
        'Utah': 'UT',
        'Vermont': 'VT',
        'Virgin Islands': 'VI',
        'Virginia': 'VA',
        'Washington': 'WA',
        'West Virginia': 'WV',
        'Wisconsin': 'WI',
        'Wyoming': 'WY'
    }
    
    # thank you to @kinghelix and @trevormarburger for this idea
    abbrev_us_state = dict(map(reversed, us_state_abbrev.items()))

    dfNames = pd.DataFrame.from_dict(abbrev_us_state, orient = 'index')
    
    dfNames = dfNames.reset_index()
    
    dfNames.columns = ['abbrev', 'stateName']
    
    updated_df = df.merge(dfNames, how = 'left', left_on = 'state', right_on = 'abbrev')
    
    return(updated_df)
    
    


##################################################################################


def main():

    df = load_data()
    
    df = abbrevToState(df) #get state names
    
    
    global cm #universal color theme for app
    cm = sns.color_palette("flare") 
    
    #Setting up rows/columns to divide the space nicely
    row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.beta_columns(
    (.1, 2, .2, 1, .1))

   
    row0_1.title('Cars Sales on Craigslist')
    
    with row0_1:
        stateChoices = getChoices(df, 'state')
        defaultValue = stateChoices.index('MA')
        
        selectedState = st.selectbox("Select a state", stateChoices, index =defaultValue)
        st.sidebar.subheader(f'Selected State: {selectedState}')
        
   
    with row0_2:
        st.write('')
    

    row0_2.subheader(
       'A Web App by Gina Salcedo Lannin')

    
    row1_spacer1, row1_1, row1_spacer2 = st.beta_columns((.1, 3.2, .1))
    
    with row1_1:
        state_df = df[df['state'] == selectedState]

        stateName = df[df['state'] == selectedState]['stateName']
        
        result = wikipedia.summary(stateName, sentences = 4) 
    
        st.subheader(result)



    row2_spacer1, row2_1, row2_spacer2, row2_2, row2_spacer3 = st.beta_columns(
        (.1, 3, .1, 3, .01))    
    
    #sets up the option of seeing stats/distributions by region
    with row2_1:
        st.header('Statistics by United States Region')
        st.subheader('Check Boxes for Regions to view BoxPlot and Table')
    

    #equal spacing for check boxes
    row3_spacer1, row3_1, row3_spacer2, row3_2, row3_spacer3, row3_3, row3_spacer4 = st.beta_columns(
        (.2, 1, 1, 1, 1, 1, .1))
        
        
    with row3_1:

        #setting up tables for each retion with the states therein
        WEST =  ['WA', 'ID', 'MT', 'CO', 'UT', 'NV', 'OR', 'CA', 'WY', 'AK', 'HI']
        MIDWEST = ['ND', 'SD', 'NE', 'KS', 'MN', 'IA', 'MO', 'WI', 'IL', 'IN', 'OH', 'MI' ]
        SOUTHWEST = ['AZ', 'NM', 'OK', 'TX']
        SOUTHEAST = ['AR', 'LA', 'MS', 'AL', 'TN', 'KY', 'GA', 'FL', 'SC', 'NC', 'VA', 'WV']
        NORTHEAST = ['ME', 'NH', 'MA','VT', 'NY', 'NJ', 'PA', 'DE', 'MD', 'CT', 'RI']
        
        #creating data frame for each region
        df_w = df[df['state'].isin(WEST)]
        w = st.checkbox('Western US')
        
    #repeat this process for all regions
    with row3_spacer2:
        df_mw = df[df['state'].isin(MIDWEST)]
        mw = st.checkbox('Midwestern US')
        
        
    with row3_2:
        df_sw = df[df['state'].isin(SOUTHWEST)]
        sw = st.checkbox('Southwestern US')
        
    with row3_spacer3:    
        df_se = df[df['state'].isin(SOUTHEAST)]
        se = st.checkbox('Southeastern US')
    
    with row3_3:            
        df_ne = df[df['state'].isin(NORTHEAST)]
        ne = st.checkbox('Northeastern US')
        
    row4_spacer1, row4_1, row4_spacer2, row4_2, row4_spacer3 = st.beta_columns(
        (.2, 2, .1, 1.5, .1))  
   
    #takes input from above of whether the boxes are checked and if so creating a summary view for the selected region
    #repeated for each of the 5 regions
    
    with row4_1:
        if w:
            region1 = 'Western'
            createBoxPlot(df_w, qual = 'state', quant = 'price', title = f'Box Plot for States in {region1} United States', horizontal=1)           
            
            with row4_2:
                statsByState(df_w)
                st.subheader(f'About the {region1} United States Region')

                result = wikipedia.summary(f'{region1} United States', sentences = 3) 
                st.write(result)


        if sw:
            region2 = 'Southwestern'

            createBoxPlot(df_sw, qual = 'state', quant = 'price', title = f'Box Plot for States in {region2} United States', horizontal=1)           
            
            with row4_2:
                statsByState(df_w)
                st.subheader(f'About the {region2} United States Region')

                result = "The southeastern United States, also referred to as the American Southeast or simply the Southeast, is broadly the eastern portion of the southern United States and the southern portion of the eastern United States. It comprises at least a core of states on the lower East Coast of the United States and eastern Gulf Coast. Expansively, it includes everything south of the Mason–Dixon line, the Ohio River, the 36°30' parallel, and stretches far west as Arkansas and Louisiana.[1] There is no official U.S. government definition of the region, though various agencies and departments use different definitions."
                st.write(result)            


        if mw:
            region3 = 'Midwestern'

            
            createBoxPlot(df_mw, qual = 'state', quant = 'price', title = f'Box Plot for States in {region3} United States', horizontal=1)

            
            with row4_2:

                statsByState(df_mw)
                st.subheader(f'About the {region3} United States Region')

                result = wikipedia.summary(f'{region3} United States', sentences = 4) 
                st.write(result)

        if se:

            region4 = 'Southeastern'

            createBoxPlot(df_se, qual = 'state', quant = 'price', title = f'Box Plot for States in {region4} United States', horizontal=1)
            
            with row4_2:
                
                result = wikipedia.summary(f'{region4} United States', sentences = 4) 
                st.subheader(f'About the {region4} United States Region')

                st.write(result)
                statsByState(df_se)

        if ne:
            region5 = 'Northeastern'

            createBoxPlot(df_ne, qual = 'state', quant = 'price', title = f'Box Plot for States in {region5} United States', horizontal=1)
            
            with row4_2:
                statsByState(df_ne)        

                st.subheader(f'About the {region5} United States Region')
                
                result = wikipedia.summary(f'{region5} United States', sentences = 2) 
                st.write(result)

    #columns we want to be able to filter on using check boxes
    checkBoxColumns = ['fuel', 'drive', 'condition', 'cylinders', 'size']

    #options in check boxes will change based on state since we're passing in a dataframe filtered down by state
    
    selectionsDict = generateDictChoices(state_df = state_df, checkBoxColumns = checkBoxColumns)

    new_df = updatedDf(df = state_df, selectionsDict=selectionsDict)

    multiSelectColumns = ['paint_color', 'manufacturer']

    row6_spacer1, row6_1, row6_spacer2 = st.beta_columns((.1, 3.2, .1))
    
    with row6_1:
        selectionsDict_multi = generateDictChoicesMulti(new_df, multiSelectColumns)

    new_df2 = updatedDf2(df = new_df, selectionsDict=selectionsDict_multi)
    
    
    
    row5_spacer1, row5_1, row5_spacer2, row5_2, row5_spacer3, row5_3, row5_spacer4 = st.beta_columns(
        (.7, 1, .05, 1, .05, 1, .01))



    with row5_spacer1:
        columns = ['Fuel', 'Drive', 'Condition', 'Cylinders', 'Size']
        defaultValue = columns.index('Drive')
        st.subheader('Please Select Qualitative Category For Pie Charts')
        x = st.selectbox('Category', columns, index = defaultValue)
        
        columns1 = ['Price', 'Odometer', 'Year', 'Count']
        defaultValue_y = columns1.index('Price')
        st.subheader('Please Select Category For Boxplots')
        y = st.selectbox('Category', columns1, index = defaultValue_y)
        
        additional = st.checkbox("Compare Additional Quantitative Category")
        
        x= x.lower() # changing x and y so the program can serach for it since titles are in lowercase
        y= y.lower()
        
    with row5_1:
        createPie(new_df2, column = x, title = f'Pie Chart by  {x} category for {selectedState} - filtered')
        createBoxPlot(new_df2, qual = x, quant = y, title= f'Distribution of {y} by {x} for {selectedState} - filtered')

    with row5_2:
        createPie(state_df, column = x, title = f'Pie Chart by  {x} category for {selectedState}')
        createBoxPlot(state_df, qual = x, quant = y, title= f'Distribution of {y} by {x} for {selectedState}')
        
    with row5_3:
        createPie(df, column = x, title = f'Pie Chart by {x} category for the United States')
        createBoxPlot(df, qual = x, quant = y, title= f'Distribution of {y} by {x} for the United States')
        
    if additional:
        row6_spacer1, row6_1, row6_spacer2, row6_2, row6_spacer3, row6_3, row6_spacer4 = st.beta_columns(
        (.7, 1, .05, 1, .05, 1, .01))

    
        defaultValue3 = 0
        columns2 = columns1
        with row5_spacer1:
            y1 = st.selectbox('Second Category', columns2, index = defaultValue3)
            y1 = y1.lower()
        with row5_1:
            createBoxPlot(new_df2, qual = x, quant = y1, title= f'Distribution of {y1} by {x} for {selectedState} - filtered')
    
        with row5_2:
            createBoxPlot(state_df, qual = x, quant = y1, title= f'Distribution of {y1} by {x} for {selectedState}')
            
        with row5_3:
            createBoxPlot(df, qual = x, quant = y1, title= f'Distribution of {y1} by {x} for the United States')                      

        state_df.reset_index(inplace = True)
    

    


    #options in multi-select boxes will change based on state since we're passing in a dataframe filtered down by state

    #calling function to create map
    createMap(df = df, state_df = state_df)
    

    if st.checkbox('View Data'):
        st.subheader('All transactions in %s' %selectedState)
        st.dataframe(new_df2.style.set_properties(**{'background-color': 'lightsalmon', 'color': 'black'}))

    
    if st.checkbox('View Stats for All States'):
        statsByState(df)
    

main()
