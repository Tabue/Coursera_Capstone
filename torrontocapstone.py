#!/usr/bin/env python
# coding: utf-8

# In[22]:


from bs4 import BeautifulSoup


# In[23]:


import requests as requests


# In[24]:


import pandas as pd


# Parsing and formatting  start

# In[25]:


url='https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M'


# In[26]:


url=requests.get(url).text


# In[27]:


soup=BeautifulSoup(url,'lxml')
print(soup)


# In[28]:


#get table
table=soup.find('table',{'class':'wikitable sortable'})


# In[29]:


#get rows in table
rows = table.findAll('tr')
parsed_table_data=[]


# In[30]:


#exctracting values from rows
for row in rows:
    children = row.findChildren(recursive=False)
    row_text = []
    for child in children:
        clean_text = child.text
                    #This is to discard reference/citation links
        clean_text = clean_text.split('&#91;')[0]
                    #This is to clean the header row of the sort icons
        clean_text = clean_text.split('&#160;')[-1]
        clean_text = clean_text.strip()
        row_text.append(clean_text)
    parsed_table_data.append(row_text)


# In[31]:


#creating df
parsed_table_data
df=pd.DataFrame(parsed_table_data)
df


# In[32]:


#dropping 1st row
df=df.drop([0],axis=0)
df


# In[33]:


#setting columns' name
df.rename(columns={0:"Postcode",1:"Borough",2:"Neighbourhood"},inplace=True)
df


# In[34]:


#getting rid of not assigned boroughs
df=df[df['Borough']!='Not assigned']


# In[35]:


#reset indexes for correct numeration
df=df.reset_index(drop=True)
dfn=df


# Parsing end

# In[36]:


df


# In[37]:


#giving names of boroughs to not assigned neibourhoods
df['Neighbourhood']=df['Neighbourhood'].replace('Not assigned', df['Borough'])


# In[38]:


#groupping by postcode+shape
df= df.groupby(['Postcode','Borough'])['Neighbourhood'].apply(', '.join).reset_index()
df.shape


# parsing and formatting end

# In[39]:


import json # library to handle JSON files

get_ipython().system("conda install -c conda-forge geopy --yes # uncomment this line if you haven't completed the Foursquare API lab")
from geopy.geocoders import Nominatim # convert an address into latitude and longitude values

import requests # library to handle requests
from pandas.io.json import json_normalize # tranform JSON file into a pandas dataframe

# Matplotlib and associated plotting modules
import matplotlib.cm as cm
import matplotlib.colors as colors

# import k-means from clustering stage
from sklearn.cluster import KMeans

get_ipython().system("conda install -c conda-forge folium=0.5.0 --yes # uncomment this line if you haven't completed the Foursquare API lab")
import folium # map rendering library

print('Libraries imported.')


# In[40]:


#get coord file
df_Coord = pd.read_csv("http://cocl.us/Geospatial_data")


# In[41]:


df = df.merge(df_Coord,how ='left',left_on='Postcode',right_on='Postal Code')
df.drop('Postal Code',axis=1,inplace=True)
df.head()


# In[42]:


#get the lat and long for Torronto
address = 'Toronto'

geolocator = Nominatim(user_agent="ny_explorer")
location = geolocator.geocode(address)
TR_latitude = location.latitude
TR_longitude = location.longitude
print('The geograpical coordinate of Torronto are {}, {}.'.format(TR_latitude, TR_longitude))


# In[45]:


# mapping
map_Torronto = folium.Map(location=(TR_latitude, TR_longitude), zoom_start=10)


for lat, lng, borough, neighborhood in zip(df['Latitude'], df['Longitude'], df['Borough'], df['Neighbourhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='blue',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_Torronto)  
    
map_Torronto


# In[46]:


#lets explore the neighborhood which starts with Torronto
df_neigh = (df[df['Borough'].str.contains('East Tor')]).reset_index(drop=True)
df_neigh.head()


# In[47]:


#credentials fro 4sq
CLIENT_ID = 'IMLONDKEC4X3GRL4DV43GRXLQK0YWDI4AYFJ2YMSCYYQIH24' # your Foursquare ID
CLIENT_SECRET = 'CTVTE3SVUR45XDJ4L3FH4YUNWOHREK2PVIPIYDHE3TK3VSWO' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version
LIMIT=100


# In[49]:


#loop through all boroughs
def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        #print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[51]:


Torronto_venues = getNearbyVenues( names=df_neigh['Neighbourhood'],
                                   latitudes=df_neigh['Latitude'],
                                   longitudes=df_neigh['Longitude']
                                 )


# In[52]:


Torronto_venues.head()


# In[53]:


Torronto_grouped = Torronto_venues.groupby('Venue Category').count()
Torronto_grouped.head()


# In[54]:


Toronto_format = pd.get_dummies(Torronto_venues[['Venue Category']], prefix="", prefix_sep="")
Toronto_format['Neighborhood'] = Torronto_venues['Neighborhood'] 
fixed_columns = [Toronto_format.columns[48]] + list(Toronto_format.columns[:-1])
Toronto_format = Toronto_format[fixed_columns]

Toronto_format.head()


# In[56]:


# set number of clusters
kclusters = 5

Cluster = Toronto_format.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(Cluster)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10]


# In[57]:


# add clustering labels
Torronto_venues.insert(0, 'Cluster Labels', kmeans.labels_)
Torronto_venues_Cluster = Torronto_venues
Torronto_venues_Cluster.head(15)


# In[58]:


Torronto_venues_Cluster.loc[Torronto_venues_Cluster['Cluster Labels'] == 0, Torronto_venues_Cluster.columns[[1] + list(range(5, Torronto_venues_Cluster.shape[1]))]]


# In[ ]:




