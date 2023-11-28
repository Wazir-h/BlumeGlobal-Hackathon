import pandas as pd
import pickle 
import os

def distance_matrix_writer(data,region_dict):
  data = data.drop('LOCATIONS',axis=1)
  for j in range(len(data)):
    for i in range(len(data)):
      data.iloc[j,i] = data.iloc[i,j]
  
  data = pd.DataFrame(data,dtype = int)
  distance_matrix_dict = {}

  for r in region_dict:
    distance_matrix_dict[r] = distance_matrix_sieve(data,region_dict[r])
  
  return distance_matrix_dict

def distance_matrix_sieve(distance_matrix,region):
  distance = pd.DataFrame()

  t = pd.DataFrame()
  for i,j in enumerate(region):
    t.insert(i,i,distance_matrix[::][j])
  t = t.T
  for i,j in enumerate(region):
    distance.insert(i,j,t[::][j-1])
  
  return distance

def location_array(data):
  regions = []

  for i,j in enumerate(data['TYPE'],1):
    if(j == 'Warehouse'):
      regions.append(i)

  region_locn = {}
  for r in regions:
    region_locn[r] = [r]
    for x,y in enumerate(data['SOURCED_FROM'],1):
      if(y == r):
        region_locn[r].append(x)
    
  return regions,region_locn


def update_data(filepath):

  data = pd.read_excel(filepath, sheet_name=None)
  regions, region_arr = location_array(data['LOCATIONS'])

  warehouse_data = distance_matrix_writer(data['DISTANCE MATRIX'],region_arr)
  for i in warehouse_data:
    warehouse_data[i] = [warehouse_data[i].to_numpy(dtype=int).tolist()]

  for i in regions:
    t = data['LOCATIONS'].loc[data['LOCATIONS']['ID'] == i]
    warehouse_data[i] += [int(t.iloc[0,-2]), int(t.iloc[0,-1])]
    warehouse_data[i] += [region_arr[i]]
  warehouse_data['time'] = os.stat(filepath).st_mtime
  with open('warehouse_data.dat','wb') as file:
    pickle.dump(warehouse_data,file)