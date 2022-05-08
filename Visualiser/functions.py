import numpy as np
from django.conf import settings
import os
import pandas as pd
from scipy.interpolate import UnivariateSpline

def load_data(in_txt, min_idx = 36, max_idx = 71):

    file1 = open(in_txt, 'r')
    count = 0
    
    # Dimension total matrix
    C = np.zeros((200,200,max_idx-min_idx+1))
    
    while True:
        count += 1
     
        # Get next line from file
        line = file1.readline()
    
        # if line is empty
        # end of file is reached
        if not line:
            break

        if count > 1 and count >= min_idx and count <= max_idx:
            img_file = line.strip()
            img_file = os.path.join(settings.DATA_DIR, img_file)
            A = np.fromfile(img_file, dtype=np.uint8,count=40000) # count=40000
            A.shape = (200,200)
            # Build a 200 x 200 x 108 matrix
            C[:,:,count-2-min_idx] = A[:,:]
     
    file1.close()
    return C


def extract_time_series(matrix, row, col):
    return matrix[row, col, :]

def get_all_coordinates():
    all_coordinates = []
    for r in range(10):
        for c in range(10):
            all_coordinates.append([r+1, c+1])

    return all_coordinates


def moving_average_ts(ts, n=3):
    out_ts = [float('nan')]*len(ts)
    out_ts[n-1:] = [np.mean(ts[i-n:i]) for i in range(n, len(ts)+1)]
    print(out_ts)
    return out_ts


def remove_outliers_mean(ts, max_tolerance):
    keep_mask = abs(ts - np.mean(ts)) < max_tolerance * np.std(ts)
    out_ts = [ts[k] if v is True else float('nan') for k, v in enumerate(keep_mask.tolist())]
    s = pd.Series(out_ts).interpolate(limit = len(ts), limit_direction = 'both').values.tolist()
    return s

def remove_outliers_median(ts, max_tolerance):
    keep_mask = abs(ts - np.median(ts)) < max_tolerance * np.std(ts)
    out_ts = [ts[k] if v is True else float('nan') for k, v in enumerate(keep_mask.tolist())]
    s = pd.Series(out_ts).interpolate(limit = len(ts), limit_direction = 'both').values.tolist()
    return s

def get_spline_formulation(ts, s=10000, k=3):
    y = np.array(ts)
    x = np.arange(len(y))
    spl = UnivariateSpline(x, y, k=k, s=s)
    return spl

def get_spline(spl, min_x, max_x, eval_points=1000):
    xs = np.linspace(min_x, max_x, eval_points)
    ys = spl(xs)
    return xs, ys

def get_season_start(ts):
    median = np.median(np.array(ts))
    increase_indexes = np.where(np.diff(ts) > 0)[0] + 1
    above_median = np.where(ts > median)[0] + 1
    already_intersected = np.where(ts < median)[0] + 1

    candidate_starts = [idx for idx, el in enumerate(ts) if idx in increase_indexes and idx in above_median and min(already_intersected) <= idx]

    if len(candidate_starts) > 0:
        season_start = candidate_starts[0]/len(ts)
    else:
        season_start = 0

    return season_start, median


def get_total_error(yspline, yts):
    err_sum = 0
    assert len(yspline) == len(yts)

    for idx, el in enumerate(yts):
        err_sum += abs(el - yspline[idx])/yspline[idx]

    return err_sum/len(yts)