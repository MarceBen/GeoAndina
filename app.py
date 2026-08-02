from flask import Flask, render_template, request, redirect, url_for, session
from egm2008 import EGModel2008
from calculations import calculate_orthometric_height, dm_to_decimal, dms_to_decimal, calculate_ellipsoidal_height
from utm import utm_to_geodetic
from dotenv import load_dotenv
import os


MAX_QUANTITY = 1000
MIN_QUANTITY = 1

load_dotenv()

ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)

app.secret_key = SECRET_KEY

# Cargar el modelo una sola vez al iniciar la aplicación
model = EGModel2008()
model.load_model()

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("Logged") == True:
        return redirect(url_for("main_menu"))

    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        password = request.form.get("password")

        if password == ACCESS_PASSWORD:
            session["Logged"] = True
            return redirect(url_for("main_menu"))
        
        else:
            return render_template("login.html", error = "Contraseña Incorrecta")



@app.route("/main_menu", methods=["GET", "POST"])
def main_menu():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("main_menu.html")

    coordinate_type = request.form.get("CoordinateType")

    if coordinate_type == "Geodetic":
        return redirect(url_for("geodetic"))

    elif coordinate_type == "UTM":
        return redirect(url_for("utm_zone"))

    return render_template("main_menu.html")



@app.route("/geodetic", methods=["GET", "POST"])

def geodetic():

    if session.get("Logged") != True:
        return redirect(url_for("login"))
    

    results = None
    quantity = None

    if request.method == "POST":

        try:

            quantity = int(request.form.get("quantity", 1))
            action = request.form.get("action")

            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 1000")



            if action  == "generate":

                return render_template("geodetic.html", quantity=quantity)

            elif action == "calculate":

                results = []
            
                for i in range (quantity):
                    
                    calculation_type = request.form.get(f"CalculationType_{i}")
                    coordinate_format = request.form.get(f"CoordinateFormat_{i}")

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
            
                        latitude_degree = float(request.form.get(f"LatitudeDegreeDMS_{i}", 0 ))
                        latitude_minutes = float(request.form.get(f"LatitudeMinutesDMS_{i}", 0 ))
                        latitude_seconds = float(request.form.get(f"LatitudeSecondsDMS_{i}", 0 ))
            
                        latitude = dms_to_decimal(latitude_degree, latitude_minutes, latitude_seconds)
            
                        longitude_degree = float(request.form.get(f"LongitudeDegreeDMS_{i}", 0 ))
                        longitude_minutes = float(request.form.get(f"LongitudeMinutesDMS_{i}", 0 ))
                        longitude_seconds = float(request.form.get(f"LongitudeSecondsDMS_{i}", 0 ))
            
                        longitude = dms_to_decimal(longitude_degree, longitude_minutes, longitude_seconds)
            
                    else:
                        raise ValueError("Formato de coordenada no válido")

               

                    if calculation_type == "OrthometricHeight":
                                    
                        ellipsoidal_height = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                                    
                        orthometric_height = calculate_orthometric_height(model, latitude, longitude, ellipsoidal_height)
                                    
                    elif calculation_type == "EllipsoidalHeight":
                                    
                        orthometric_height = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                                        
                        ellipsoidal_height = calculate_ellipsoidal_height(model, latitude, longitude, orthometric_height)
                                    
                    else:
                        raise ValueError("Tipo de cálculo no válido")

                    

                    results.append ({
                            "CalculationType": calculation_type,
                            "latitude": latitude,
                            "longitude": longitude,
                            "orthometric_height": float(orthometric_height), 
                            "ellipsoidal_height": float(ellipsoidal_height)
                            })

                                    
                return render_template("geodetic.html", quantity = quantity, results=results) 
            
            else:
                raise ValueError("Accion Invalida")   

        except ValueError as e:
            return render_template("geodetic.html", quantity = quantity, results = results, error = str(e))

        except Exception as e:
            return render_template("geodetic.html", quantity = quantity, results = results, error = "Ocurrio un error inesperado")

    return render_template("geodetic.html", quantity = quantity, results = results)

@app.route("/utm_zone", methods=["GET", "POST"])
def utm_zone():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("utm_zone.html")

    if request.method == "POST":

        utm_zone = request.form.get("UTMZone")

        if utm_zone not in ["17", "18", "19"]:
            return render_template("utm_zone.html", error="Seleccione una zona válida.")

        session["UTMZone"] = int(utm_zone)

        return redirect(url_for("utm"))

@app.route("/utm", methods=["GET", "POST"])

def utm():

    if session.get("Logged") != True:
        return redirect(url_for("login"))

    results = None
    quantity = None

    if request.method == "POST":
         
        try:
        
            quantity = int(request.form.get("quantity", 1))
            action = request.form.get("action")
        
            if quantity > MAX_QUANTITY or quantity < MIN_QUANTITY:
                raise ValueError("La cantidad debe estar entre 1 y 1000")
        
            if action  == "generate":
        
                return render_template("utm.html", quantity=quantity)
        
            elif action == "calculate":
        
                        results = []
                    
                        for i in range (quantity):
                            
                            calculation_type = request.form.get(f"CalculationType_{i}")

                            east = float(request.form.get(f"East_{i}", 0))
                            north = float(request.form.get(f"North_{i}", 0))

                            utm_zone = session.get("UTMZone")

                            latitude, longitude = utm_to_geodetic(east, north, utm_zone)
                            
        
                            if calculation_type == "OrthometricHeight":
                                            
                                ellipsoidal_height = float(request.form.get(f"EllipsoidalHeight_{i}", 0 ))
                                            
                                orthometric_height = calculate_orthometric_height(model, latitude, longitude, ellipsoidal_height)
                                            
                            elif calculation_type == "EllipsoidalHeight":
                                            
                                orthometric_height = float(request.form.get(f"OrthometricHeight_{i}", 0 ))
                                                
                                ellipsoidal_height = calculate_ellipsoidal_height(model, latitude, longitude, orthometric_height)
                                            
                            else:
                                raise ValueError("Tipo de cálculo no válido")
        
                            
        
                            results.append ({
                                    "CalculationType": calculation_type,
                                    "latitude": latitude,
                                    "longitude": longitude,
                                    "orthometric_height": float(orthometric_height), 
                                    "ellipsoidal_height": float(ellipsoidal_height)
                                    })
        
                                            
                        return render_template("utm.html", quantity = quantity, results=results) 
                    
            else:
                raise ValueError("Accion Invalida")   
        
        except ValueError as e:
                    return render_template("utm.html", quantity = quantity, results = results, error = str(e))
        
        except Exception as e:
            return render_template("utm.html", quantity = quantity, results = results, error = "Ocurrio un error inesperado")
        
    return render_template("utm.html", quantity = quantity, results = results)
        
if __name__ == "__main__":
    app.run(debug=True)