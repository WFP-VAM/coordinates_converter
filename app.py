# https://stackoverflow.com/questions/7861196/check-if-a-geopoint-with-latitude-and-longitude-is-within-a-shapefile
import shapefile
import os
import pandas as pd
from shapely.geometry import shape, Point
from flask import Flask, request, render_template, make_response
from werkzeug.utils import secure_filename
app = Flask(__name__, instance_relative_config=True)


def converter_func(shapefile, lat, lon):

    for shp in shapefile.shapeRecords():
        # build a shapely polygon from your shape
        polygon = shape(shp.shape)

        point = Point(lon, lat)

        if polygon.contains(point):
            print('bingo! -> {}'.format(shp.record))
            return shp.record

    print('cooridnates not in shapefile. Maybe at sea?')
    return [None, None, None, None]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def covert():

    # admin level
    adm_level = request.form.get('adm_level_select')

    # coordinates
    coordinates = request.files['file']
    df = pd.read_csv(coordinates)
    print(df.head())

    # shapefile
    if 'shfile' not in request.files:
        # use local shapefile
        shapefile_path = 'data/global_adm1.shp'
        shpf = shapefile.Reader(shapefile_path)
    else:
        shfile = request.files['shfile']
        filename = secure_filename(shfile.filename)
        shfile.save('data/'+filename)
        shpf = shapefile.Reader('data/'+filename)

    for ix, row in df.iterrows():
        print('finding coordinates {} {}'.format(row.Latitude, row.Longitude))
        df.loc[ix, 'ADM{}_ID'.format(adm_level)], df.loc[ix, 'ADM{}'.format(adm_level)], \
        df.loc[ix, 'ADM0_ID'], df.loc[ix, 'ADM0'] =\
            converter_func(shpf, row.Latitude, row.Longitude)

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