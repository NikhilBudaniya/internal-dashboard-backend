import numpy as np
from numpy.core.fromnumeric import reshape

class Heatmap():
    def __init__(self, res_x=100, res_y=100, range_x=[0,100], range_y=[0,100]):
        """
        @res_x: resolution<x> of heatmap
        @res_y: resolution<y> of heatmap
        @range_x: x-size of heatmap area  
        @range_y: y-size of heatmap area  
        """
        # create map
        self.res_x = res_x
        self.res_y = res_y
        self.range_x = range_x
        self.range_y = range_y
        self.size_x = self.range_x[1] - self.range_x[0]
        self.size_y = self.range_y[1] - self.range_y[0]
        self.map = np.zeros((res_x, res_y), dtype=np.float32)

        # some settings
        self.max = 100

    def add_value(self, pos_x, pos_y, intensity=1):
        x = int(pos_x * (self.res_x / self.size_x))
        y = int(pos_y * (self.res_y / self.size_y))

        # 
        if x < self.range_x[0] or x > self.range_x[1]:
            raise ValueError("x value out of range")
        if y < self.range_x[0] or y > self.range_x[1]:
            raise ValueError("y value out of range")

        # add value
        if self.map[x, y] <= self.max:
            self.map[x, y] += intensity

    def get_value(self, x, y):
        return self.map[x, y]

    def get_map(self):
        return self.map