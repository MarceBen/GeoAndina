from egm2008 import EGModel2008
from scipy.spatial import KDTree
class LocalModel(EGModel2008):
    def __init__(self, points):

        super().__init__()

        self.points = points
        self.kdtree = None

    def buildkd_tree(self):

        points = []

        for point in self.points:
            points.append((point["East"], point["North"]))

        self.kdtree = KDTree(points)

    def find_nearest_points(self, east, north, k):

        distance, indexes = self.kdtree.query(((east, north)), k=k)

        nearest_points = []

        for index in indexes:

            nearest_points.append(self.points[index])

        return nearest_points

        


    

    