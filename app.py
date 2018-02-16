import os
import pandas as pd
from shapely.geometry import Point
from flask import Flask, request, render_template, make_response
from werkzeug.utils import secure_filename
import geopandas as gp
from geopandas.tools import sjoin
app = Flask(__name__, instance_relative_config=True)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def covert():

    # coordinates
    coordinates = request.files['file']
    df = pd.read_csv(coordinates)

    # convert to geographic data
    tmp = df[['Longitude','Latitude']].dropna()
    print(tmp.head())
    geometry = [Point(xy) for xy in zip(tmp.Longitude, tmp.Latitude)]
    crs = {'init': 'epsg:2263'}  # http://www.spatialreference.org/ref/epsg/2263/
    geo_df = gp.GeoDataFrame(tmp, crs=crs, geometry=geometry)

    # shapefile
    if 'shfile' not in request.files:
        # use local shapefile
        shpf = gp.GeoDataFrame.from_file('data/global_adm2.shp')
    else:
        shfile = request.files['shfile']
        filename = secure_filename(shfile.filename)
        shfile.save('data/'+filename)
        shpf = gp.GeoDataFrame.from_file('data/'+filename)

    pointInPolys = sjoin(geo_df, shpf, how='left')

    output = pd.DataFrame(pointInPolys.drop('geometry', axis=1))

    df = df.merge(output, on=['Longitude','Latitude'], how='left')

    resp = make_response(df.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp


if __name__ == '__main__':

    # Preload our model
    print(("* Loading App..."
            "please wait until server has fully started"))

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)