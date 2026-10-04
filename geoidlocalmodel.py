import math
from itertools import product

import numpy as np
from scipy.spatial import KDTree, Delaunay

from egm2008 import EGModel2008

MIN_CONTROL_POINTS = 4      # mínimo para formar una grilla
MAX_NEIGHBORS = 32          # tope de vecinos al ampliar la búsqueda
EXACT_POINT_TOLERANCE = 0.001   # m: el punto coincide con un punto de control
UV_TOLERANCE = 1e-9         # tolerancia numérica para puntos en el borde de la celda



class LocalModel(EGModel2008):
    def __init__(self, points):

        super().__init__()

        self.points = points
        self.kdtree = None
        self.triangulation = None

    def buildkd_tree(self):

        if not self.points:
            raise ValueError("No se encontraron puntos")

        if len(self.points) < MIN_CONTROL_POINTS:
            raise ValueError(f"El modelo local necesita al menos {MIN_CONTROL_POINTS} puntos de control.")

        points = []

        for point in self.points:
            points.append((point["East"], point["North"]))

        self.kdtree = KDTree(points)

        
        try:
            self.triangulation = Delaunay(np.array(points, dtype=float))
        except Exception:
            self.triangulation = None

    def find_nearest_points(self, east, north, k):

        if k < MIN_CONTROL_POINTS:
            raise ValueError("El numero de puntos debe ser mayor o igual a 4")

        k = min(k, len(self.points))

        distance, indexes = self.kdtree.query((east, north), k=k)

        nearest_points = []

        for index in indexes:

            nearest_points.append(self.points[index])

        return nearest_points

    def is_valid_grid(self, north_west, south_west, north_east, south_east, east, north):

        if north_west["East"] >= north_east["East"]:
            return False

        if south_west["East"] >= south_east["East"]:
            return False

        if south_west["North"] >= north_west["North"]:
            return False

        if south_east["North"] >= north_east["North"]:
            return False

        cross_1 = self.cross_product(north_west, north_east, south_east)
        cross_2 = self.cross_product(north_east, south_east, south_west)
        cross_3 = self.cross_product(south_east, south_west, north_west)
        cross_4 = self.cross_product(south_west, north_west, north_east)

        if cross_1 == 0 or cross_2 == 0 or cross_3 == 0 or cross_4 == 0:
            return False

        positive = cross_1 > 0 and cross_2 > 0 and cross_3 > 0 and cross_4 > 0
        negative = cross_1 < 0 and cross_2 < 0 and cross_3 < 0 and cross_4 < 0

        return positive or negative

    def find_grid(self, east, north, k):

        nearest_points = self.find_nearest_points(east, north, k)

        north_west = []
        south_west = []
        north_east = []
        south_east = []

        
        for point in nearest_points:

            point_east = point["East"]
            point_north = point["North"]

            is_west = point_east <= east
            is_east = point_east >= east
            is_south = point_north <= north
            is_north = point_north >= north

            if is_west and is_north:
                north_west.append(point)

            if is_east and is_north:
                north_east.append(point)

            if is_west and is_south:
                south_west.append(point)

            if is_east and is_south:
                south_east.append(point)

        for north_west_point, south_west_point, north_east_point, south_east_point in product(north_west, south_west, north_east, south_east):

            if self.is_valid_grid(north_west_point, south_west_point, north_east_point, south_east_point, east, north):

                if self.is_point_inside_grid(east, north, north_west_point, north_east_point, south_west_point, south_east_point):

                    return north_west_point, south_west_point, north_east_point, south_east_point

        return None

    def find_grid_adaptive(self, east, north, k):

        # Empieza con k vecinos y los duplica hasta encontrar una celda que rodee al punto.
        total = len(self.points)
        limit = min(MAX_NEIGHBORS, total)
        current = min(max(k, MIN_CONTROL_POINTS), limit)

        while True:

            grid = self.find_grid(east, north, current)

            if grid is not None:
                return grid

            if current >= limit:
                return None

            current = min(current * 2, limit)

    def is_point_inside_grid(self, east, north, nw, ne, sw, se):

        point = { "East": east, "North": north }

        cross_1 = self.cross_product(nw, ne, point)
        cross_2 = self.cross_product(ne, se, point)
        cross_3 = self.cross_product(se, sw, point)
        cross_4 = self.cross_product(sw, nw, point)

        positive = cross_1 >= 0 and cross_2 >= 0 and cross_3 >= 0 and cross_4 >= 0
        negative = cross_1 <= 0 and cross_2 <= 0 and cross_3 <= 0 and cross_4 <= 0

        return positive or negative

    def cross_product(self, point_a, point_b, point_c):

        vector_ab_x = point_b["East"] - point_a["East"]
        vector_ab_y = point_b["North"] - point_a["North"]

        vector_ac_x = point_c["East"] - point_a["East"]
        vector_ac_y = point_c["North"] - point_a["North"]

        return vector_ab_x * vector_ac_y - vector_ab_y * vector_ac_x

    def calculate_point_geoid(self, point):

        # Ondulación geoidal del punto de control: N = h - H, con los datos del propio archivo.
        N = point["EllipsoidalHeight"] - point["OrthometricHeight"]

        point["Geoid_Height"] = N

        return N

    def calculate_local_coordinates(self, east, north, nw, ne, sw, se):

        u = 0.5
        v = 0.5

        for _ in range(20):

            x = (sw["East"] * (1-u) * (1-v) + se["East"] * u * (1-v) + nw["East"] * (1-u) * v + ne["East"] * u * v)

            y = (sw["North"] * (1-u) * (1-v)+ se["North"] * u * (1-v)+ nw["North"] * (1-u) * v+ ne["North"] * u * v)

            error_x = east - x
            error_y = north - y

            if abs(error_x) < 0.000001 and abs(error_y) < 0.000001:

                if -UV_TOLERANCE <= u <= 1 + UV_TOLERANCE and -UV_TOLERANCE <= v <= 1 + UV_TOLERANCE:

                    return min(max(u, 0.0), 1.0), min(max(v, 0.0), 1.0)

                raise ValueError("El punto se encuentra fuera de la grilla")

            dx_du = ((se["East"] - sw["East"]) * (1-v) + (ne["East"] - nw["East"]) * v)

            dx_dv = ((nw["East"] - sw["East"]) * (1-u) + (ne["East"] - se["East"]) * u)

            dy_du = ((se["North"] - sw["North"]) * (1-v)+ (ne["North"] - nw["North"]) * v)

            dy_dv = ((nw["North"] - sw["North"]) * (1-u) + (ne["North"] - se["North"]) * u)

            determinant = dx_du * dy_dv - dx_dv * dy_du

            if determinant == 0:
                raise ValueError("No se puede calcular la posición dentro de la grilla.")

            delta_u = ((error_x * dy_dv - error_y * dx_dv) / determinant)

            delta_v = ((dx_du * error_y - dy_du * error_x) / determinant)

            u += delta_u
            v += delta_v

        raise ValueError("No se pudo calcular la posición dentro de la grilla.")

    def interpolate_local_geoid(self, u, v, nw, ne, sw, se):

        N = (sw["Geoid_Height"] * (1-u) * (1-v) + se["Geoid_Height"] * u * (1-v) + nw["Geoid_Height"] * (1-u) * v+ ne["Geoid_Height"] * u * v)

        return N

    def calculate_points_geoid(self, utm_zone=None):

        # utm_zone se conserva por compatibilidad con app.py; ya no se necesita.
        for point in self.points:

            self.calculate_point_geoid(point)

    def interpolate_triangle(self, east, north):

        if self.triangulation is None:
            return None

        simplex = int(self.triangulation.find_simplex((east, north)))

        if simplex < 0:
            return None

        transform = self.triangulation.transform[simplex]

        b = transform[:2].dot(np.array([east, north]) - transform[2])

        weights = (b[0], b[1], 1.0 - b[0] - b[1])

        vertices = self.triangulation.simplices[simplex]

        return float(sum(weight * self.points[int(vertex)]["Geoid_Height"] for weight, vertex in zip(weights, vertices)))

    def calculate_local_geoid(self, east, north, k):

        if self.kdtree is None:
            raise ValueError("El modelo local no está construido.")

        # Si el punto coincide con un punto de control, se devuelve su ondulación directamente.
        distance, index = self.kdtree.query((east, north), k=1)

        if distance <= EXACT_POINT_TOLERANCE:
            return self.points[index]["Geoid_Height"]

        grid = self.find_grid_adaptive(east, north, k)

        if grid is None:

            N = self.interpolate_triangle(east, north)

            if N is not None:
                return N

            raise ValueError(
                "El punto no está rodeado por puntos de control. "
                "Verifique que se encuentre dentro del área cubierta por el modelo local "
                "(se necesitan puntos de control a ambos lados, no alineados)."
            )

        nw, sw, ne, se = grid

        u, v = self.calculate_local_coordinates(east, north, nw, ne, sw, se)

        N = self.interpolate_local_geoid(u, v, nw, ne, sw, se)

        return N

    def calculate_height(self, height, geoid_height, calculation_type):

        if calculation_type == "OrthometricHeight":

            ellipsoidal_height = height
            orthometric_height = height - geoid_height

        elif calculation_type == "EllipsoidalHeight":

            orthometric_height = height
            ellipsoidal_height = height + geoid_height

        else:
            raise ValueError("Tipo de calculo inválido.")

        return orthometric_height, ellipsoidal_height

    def calculate_result(self, east, north, height, calculation_type, k):

        geoid_height = self.calculate_local_geoid(east, north, k)

        orthometric_height, ellipsoidal_height = self.calculate_height(height, geoid_height, calculation_type)

        return {
            "East": east,
            "North": north,
            "GeoidHeight": geoid_height,
            "OrthometricHeight": orthometric_height,
            "EllipsoidalHeight": ellipsoidal_height
        }