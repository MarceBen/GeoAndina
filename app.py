from flask import Flask, render_template, request
from egm2008 import EGModel2008
from calculations import calculate_orthometric_height, dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height
from utm import utm_to_geodetic

MAX_QUANTITY = 50
MIN_QUANTITY = 1

app = Flask(__name__)

# Cargar el modelo una sola vez al iniciar la aplicación
model = EGModel2008()
model.load_model()


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        try:
            quantity = int(request.form.get("Quantity", 1))

            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 50")

            coordinate_type = request.form.get("CoordinateType")
            calculation_type = request.form.get("CalculationType")

            results = []

            for i in range (quantity):
                if coordinate_type == "UTM":

                    east = float(request.form.get(f"East_{i}", 0 ))
                    north = float(request.form.get(f"North_{i}", 0 ))
                    utm_zone = int(request.form.get(f"UTMZone_{i}", 18 ))

                    if utm_zone < 17 or utm_zone > 19:
                        raise ValueError("La zona UTM debe estar entre 17 y 19")

                    latitude, longitude = utm_to_geodetic(east, north, utm_zone)

                else:

                    coordinate_format = request.form.get("CoordinateFormat")

                    if coordinate_format == "DD":

                        latitude = float(request.form.get(f"Latitude_{i}", 0 ))
                        longitude = float(request.form.get(f"Longitude_{i}", 0 ))

                    elif coordinate_format == "DM":

                        latitude_degree = float(request.form.get(f"LatitudeDegree_{i}", 0 ))
                        latitude_minutes = float(request.form.get(f"LatitudeMinutes_{i}", 0 ))

                        latitude = dm_to_decimal(latitude_degree, latitude_minutes)

                        longitude_degree = float(request.form.get(f"LongitudeDegree_{i}", 0 ))
                        longitude_minutes = float(request.form.get(f"LongitudeMinutes_{i}", 0 ))

                        longitude = dm_to_decimal(longitude_degree, longitude_minutes)


                    elif coordinate_format == "DMS":

                        latitude_degree = float(request.form.get(f"LatitudeDegree_{i}", 0 ))
                        latitude_minutes = float(request.form.get(f"LatitudeMinutes_{i}", 0 ))
                        latitude_seconds = float(request.form.get(f"LatitudeSeconds_{i}", 0 ))

                        latitude = dms_to_decimal(latitude_degree, latitude_minutes, latitude_seconds)

                        longitude_degree = float(request.form.get(f"LongitudeDegree_{i}", 0 ))
                        longitude_minutes = float(request.form.get(f"LongitudeMinutes_{i}", 0 ))
                        longitude_seconds = float(request.form.get(f"LongitudeSeconds_{i}", 0 ))

                        longitude = dms_to_decimal(longitude_degree, longitude_minutes, longitude_seconds)

                       

                       
                        






                
            
            

        except ValueError as e:
            return render_template("index.html",error=str(e))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)