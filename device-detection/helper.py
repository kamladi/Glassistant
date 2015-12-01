def min_distance(cr_list, x_pos):
    #Return (center, radius) of the circle thats closes to the center of monitor
    #cr_list = [(center, radius), (center, radius), ...]
    # print(cr_list)
    min_diff = abs(cr_list[0][0][0] - x_pos)
    min_diff_circle = cr_list[0]
    for (c, r) in cr_list:
        if (c[0] == x_pos):
            return (c, r)
        if abs(c[0] - x_pos) < min_diff:
            min_diff_circle = (c, r)
    return min_diff_circle

def on_linear_path(path_pt1, path_pt2, targ_pt1, targ_pt2, center):
    print (path_pt1, path_pt2)
    slope = -float((path_pt1[1] - path_pt2[1]))/(path_pt2[0] - path_pt1[0])

    print ((pt[0] * slope) - delta, pt[1])

    if ((pt[0] * slope) - delta) <= pt[1] <= ((pt[0] * slope) + delta):
        return True

    return False
