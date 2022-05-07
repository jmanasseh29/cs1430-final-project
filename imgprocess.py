import math
import cv2
import numpy as np
from skimage.color import rgb2gray
from sklearn.cluster import MiniBatchKMeans
from sklearn.neighbors import NearestNeighbors

DEGREE = np.pi/180

'''
handles the actual computer vision part
'''

# gets intersections between two lines
def get_line_intersection(line1, line2):
    rho1 = line1[0]
    theta1 = line1[1]
    rho2 = line2[0]
    theta2 = line2[1]
    A = np.array([
        [np.cos(theta1), np.sin(theta1)],
        [np.cos(theta2), np.sin(theta2)]
    ])
    b = np.array([[rho1], [rho2]])
    if (np.linalg.det(A) != 0):
        x0, y0 = np.linalg.solve(A, b)
        x0, y0 = int(np.round(x0)), int(np.round(y0))
        return np.array([x0, y0])
    return None

# gets the intersection points of all the lines
def get_intersection_points(horizontals, verticals):
    intersections = []
    for line1 in horizontals:
        for line2 in verticals:
            point = get_line_intersection(line1, line2)
            if point is not None:
                intersections.append(point)
    return np.array(intersections)

def separate_lines(lines, threshold = DEGREE * 20):
    horizontals = []
    verticals = []
    for line in lines:
        theta = line[1]
        if theta <= threshold/2 or theta - DEGREE*180 >= -threshold/2:
            verticals.append(line)
        elif abs(theta - DEGREE*90) <= threshold:
            horizontals.append(line)
    return np.array(horizontals + verticals), np.array(horizontals), np.array(verticals)


def combine_lines(lines, rho_threshold=30, theta_threshold=np.pi/6):
    best_lines = np.zeros((18, 2))
    count = 0
    for i in range(lines.shape[0]):
        rho = lines[i][0]
        theta = lines[i][1]
        if i == 0:
            best_lines[count] = lines[i]
            count += 1
        else:
            if rho < 0:
                rho *= -1
                lines[i][0] *= -1
                theta -= np.pi
                lines[i][1] -= np.pi
            closeness_rho = np.isclose(rho, best_lines[0:count, 0], atol=rho_threshold)
            closeness_theta = np.isclose(theta, best_lines[0:count, 1], atol=theta_threshold)
            closeness = np.all([closeness_rho, closeness_theta], axis=0)
            if not any(closeness) and count < best_lines.shape[0]:
                best_lines[count] = lines[i]
                count += 1

    return best_lines
    
def cluster_points(intersections):
    features = np.array(intersections)
    kmeans = MiniBatchKMeans(n_clusters=81, max_iter=500).fit(features)
    return np.ndarray.tolist(kmeans.cluster_centers_)

def get_lines(img):
    # convert to grayscale, blur, then get canny edges
    img = np.uint8(255 * rgb2gray(img))
    img = cv2.blur(img, (5, 5))
    edges = cv2.Canny(img, 50, 200)

    # get hough transform lines
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 100, None)
    return np.squeeze(lines, axis=1)

def plot_lines(img, lines, color=(255, 0, 0)):
    img = np.array(img)
    for i in range(0, len(lines)):
        rho = lines[i][0]
        theta = lines[i][1]
        a = math.cos(theta)
        b = math.sin(theta)
        x0 = a * rho
        y0 = b * rho
        pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
        pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
        cv2.line(img, pt1, pt2, color, 1, cv2.LINE_AA)
    
    return img

def plot_points(img, points):
    for i in points:
        x0 = i[0]
        y0 = i[1]
        
        img = np.array(img)
        cv2.circle(img, (int(x0), int(y0)), radius=5, color=(0, 255, 0), thickness=-1)
        cv2.circle(img, (int(x0), int(y0)), radius=5, color=(0, 0, 255), thickness=2)
    
    return img

def get_intersection_matrix(points):
    points = points[points[:, 1].argsort()]
    matrix = np.reshape(points, (9, 9, 2))
    for i in range(matrix.shape[0]):
        matrix[i, :, :] = matrix[i, :, :][matrix[i, :, :][:, 0].argsort()]
    return matrix

def warp_image(img, matrix):
    orig_coords = np.float32([matrix[0, 0, :], matrix[0, -1, :], matrix[-1, 0, :], matrix[-1, -1, :]])
    new_coords = np.float32([[0, 0], [img.shape[0], 0], [0, img.shape[1]], [img.shape[0], img.shape[1]]])
    transform_mat = cv2.getPerspectiveTransform(orig_coords, new_coords)
    warped_img = cv2.warpPerspective(img, transform_mat, img.shape[:2])
    
    #just for a sanity check, checking to see where the matrix points get mapped... not working atm
    warped_mtx = np.zeros((9, 9, 2))
    for i in range(9):
        for j in range(9):
            print(np.delete(np.reshape(np.matmul(transform_mat, np.reshape(np.pad(matrix[i, j, :], (0, 1)), (3, 1))), (3)), 2, 0))
            warped_mtx[i, j, :] = np.delete(np.reshape(np.matmul(transform_mat, np.reshape(np.pad(matrix[i, j, :], (0, 1)), (3, 1))), (3)), 2, 0)
    
    return warped_img, warped_mtx

def get_features(img, matrix):
    warped_img, warped_mtx = warp_image(img, matrix)
    for i in range(8):
        for j in range(8):
            p1 = matrix[i, j, :]
            p2 = matrix[i, j+1, :]
            p3 = matrix[i+1, j, :]
            p4 = matrix[i+1, j+1, :]
            center = (p1 + p2 + p3 + p4) / 4

            (np.abs(p1 - center) + np.abs(p2 - center) + np.abs(p3 - center) + np.abs(p4 - center)) / 4

def get_board_corners(img):
    lines = get_lines(img)
    if lines is not None:
        plot = plot_lines(img, lines)
        lines = combine_lines(lines)
        lines, horizontals, verticals = separate_lines(lines)
        intersections = get_intersection_points(horizontals, verticals)
        intersections = np.array(list(filter(lambda point : point[0] >= 0 and point[0] < img.shape[1] and point[1] >= 0 and point[1] < img.shape[0], intersections)))
        # corners = cluster_points(intersections)
        intersection_matrix = get_intersection_matrix(intersections)
        # features = get_features(img, intersection_matrix)
        plot = plot_points(plot_lines(plot, lines, color=(255, 255, 255)), intersections)
        # warped_img, warped_mtx = warp_image(img, intersection_matrix)
        # plot = plot_points(warped_img, np.reshape(warped_mtx, (-1, 2)))
        return plot
    return None
