import folium

def create_route_map(route, start_coords , end_coords):
    '''
        coords in this format : [long , lat]
    '''
    m = folium.Map(location=[start_coords[0], start_coords[1]], zoom_start=6, tiles='CartoDB dark_matter')

    folium.GeoJson(route, name="Route").add_to(m)

    folium.Marker([start_coords[0], start_coords[1]], popup="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([end_coords[0], end_coords[1]], popup="End", icon=folium.Icon(color="red")).add_to(m)
    return m
