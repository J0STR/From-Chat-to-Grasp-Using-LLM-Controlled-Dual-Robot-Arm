import numpy as np

def rot_x(angle):
    matrix = np.array([[1,              0,              0,       0],
                       [0,  np.cos(angle),  -np.sin(angle),      0],
                       [0,  np.sin(angle),   np.cos(angle),      0],
                       [0,              0,               0,      1]])
    
    return matrix

def rot_y(angle):
    matrix = np.array([[np.cos(angle),  0,   np.sin(angle),      0],
                       [0,              1,               0,      0],
                       [-np.sin(angle), 0,   np.cos(angle),      0],
                       [0,              0,               0,      1]])
    
    return matrix

def rot_z(angle):
    matrix = np.array([[np.cos(angle),  -np.sin(angle), 0,       0],
                       [np.sin(angle),   np.cos(angle), 0,       0],
                       [0,                           0, 1,       0],
                       [0,                           0, 0,       1]])
    
    return matrix

def trans_x(d_trans):
    matrix = np.array([[1,              0,              0,  d_trans],
                       [0,              1,              0,        0],
                       [0,              0,              1,        0],
                       [0,              0,              0,        1]])
    
    return matrix

def trans_y(d_trans):
    matrix = np.array([[1,              0,              0,        0],
                       [0,              1,              0,  d_trans],
                       [0,              0,              1,        0],
                       [0,              0,              0,        1]])
    
    return matrix

def trans_z(d_trans):
    matrix = np.array([[1,              0,              0,        0],
                       [0,              1,              0,        0],
                       [0,              0,              1,  d_trans],
                       [0,              0,              0,        1]])
    
    return matrix