def euclidian_distance(point1,point2):
    return ((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)**(0.5)

def rearrange_path(path,symbol):
    start_point = (path[0][0],(path[0][1]))
    end_point = (path[-1][0],(path[-1][1]))
    if euclidian_distance(symbol,start_point) > euclidian_distance(symbol,end_point):
        return path[::-1]
    else:
        return path