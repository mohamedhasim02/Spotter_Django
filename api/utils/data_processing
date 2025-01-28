import os
import pandas as pd

from api.services.geo_service import get_lat_lon

df = pd.read_csv("./fuel-prices-for-be-assessment.csv")
df = df.head(100)

df = df.dropna()

df = df.drop_duplicates()

df['Retail Price'] = pd.to_numeric(df['Retail Price'], errors='coerce')

df.columns = df.columns.str.strip()


## COMPUTING (LAT,LONG) FROM ADDRESS |-----------------------------------
df['Full_Address'] = df['Address'] + ', ' + df['City'] + ', ' + df['State']

opencage_api_key = os.getenv("OPENROUTE_SERVICE_KEY")
df['Latitude'], df['Longitude'] = zip(*df['Full_Address'].apply(lambda x: get_lat_lon(x, opencage_api_key)))

df['Geocoding_Status'] = df.apply(lambda row: 'Failed' if pd.isna(row['Latitude']) or pd.isna(row['Longitude']) else 'Success', axis=1)

df.to_csv("cleaned_file.csv", index=False)

print(df.head(100))
