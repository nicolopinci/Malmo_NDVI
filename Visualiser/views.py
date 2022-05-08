from django.http import HttpResponse
from . import functions
from django.conf import settings
import os
from django.shortcuts import render
import json
import math
import numpy as np
import scipy as sp
import scipy.ndimage


def index(request):
    return render(request, 'index.html', dict())

def visualize_map(request):

    min_lat = float(request.GET.get('min_lat', '0'))
    max_lat = float(request.GET.get('max_lat', '20'))

    min_lon = float(request.GET.get('min_lon', '-20'))
    max_lon = float(request.GET.get('max_lon', '0'))

    lat_elements = 200
    lon_elements = 200

    lat = request.GET.get('lat', '100')
    lon = request.GET.get('lon', '100')
    display_plot = request.GET.get('display', "none")

    list_images_file = os.path.join(settings.DATA_DIR, 'ndvilistwa.txt')
    m = functions.load_data(list_images_file)
    ts = []

    lat = float(lat)
    lon = float(lon)

    row_matrix =  round(lat_elements/(min_lat-max_lat)*(lat-max_lat))
    col_matrix = round(lon_elements / (min_lon - max_lon) * (lon - max_lon))
    
    if col_matrix < 0 or col_matrix >= lon_elements or row_matrix < 0 or row_matrix >= lat_elements:
        row_matrix, col_matrix = 100, 100

    center_lat = (min_lat-max_lat)/lat_elements*row_matrix + max_lat
    center_lon = (min_lon-max_lon)/lon_elements*col_matrix + max_lon

    ts = functions.extract_time_series(m, row_matrix, col_matrix)
    ts_out_mean = functions.remove_outliers_mean(ts, 2)
    ts_out_median = functions.remove_outliers_median(ts, 2)
    ts_ma = functions.moving_average_ts(ts_out_median, n=3)
    spl = functions.get_spline_formulation(ts_out_median)
    xts_spline, yts_spline = functions.get_spline(spl, 0, len(ts), 1000)
    xts_ldspline, yts_ldspline = functions.get_spline(spl, 0, len(ts), len(ts))
    
    err = functions.get_total_error(yts_ldspline, ts)
    
    season_start, median = functions.get_season_start(yts_spline.tolist())
    season_start = round(season_start*len(ts))

    context = dict()
    context['ts'] = json.dumps(ts.tolist())
    context['ts_ma'] = json.dumps(ts_ma)
    context['ts_out_mean'] = json.dumps(ts_out_mean)
    context['ts_out_median'] = json.dumps(ts_out_median)
    context['xts_spline'] = json.dumps(xts_spline.tolist())
    context['yts_spline'] = json.dumps(yts_spline.tolist())
    context['season_start'] = json.dumps(season_start)
    context['median'] = json.dumps(median)

    # Generate all the coordinates
    all_coordinates = functions.get_all_coordinates()

    context['all_coordinates'] = json.dumps(all_coordinates)
    context['lat'] = round(center_lat, 3)
    context['lon'] = round(center_lon, 3)
    context['dp'] = display_plot
    context['delta_lat'] = (max_lat-min_lat)/lat_elements
    context['delta_lon'] = (max_lon-min_lon)/lon_elements

    return render(request, 'map.html', context)


def get_season_start(request):
    max_allowed_error = float(request.GET.get('remove_above', '0.2'))
    sigma = float(request.GET.get('sigma', '1.0'))

    list_images_file = os.path.join(settings.DATA_DIR, 'ndvilistwa.txt')
    matrix = functions.load_data(list_images_file)
    season_starts = np.zeros(matrix.shape[:2])
    for r in range(len(matrix)):
        for c in range(len(matrix[0])):
            ts = functions.extract_time_series(matrix, r, c)
            ts_out_median = functions.remove_outliers_median(ts, 2)
            spl = functions.get_spline_formulation(ts_out_median)
            xts_spline, yts_spline = functions.get_spline(spl, 0, len(ts), len(ts))
            season_start, median = functions.get_season_start(yts_spline.tolist())
            error = functions.get_total_error(yts_spline, ts)

            if season_start < 0 or error >= max_allowed_error:
                season_starts[r][c] = None
            else:
                #season_start = round(season_start * len(ts))
                season_start = season_start * len(ts)
                season_starts[r][c] = season_start

    context = dict()

    season_starts = sp.ndimage.filters.gaussian_filter(season_starts, [sigma, sigma], mode='constant')

    context['season_starts'] = json.dumps(season_starts.tolist())
    return render(request, 'season_start_plot.html', context)


def get_errors(request):

    list_images_file = os.path.join(settings.DATA_DIR, 'ndvilistwa.txt')
    matrix = functions.load_data(list_images_file)
    errors = np.zeros(matrix.shape[:2])
    for r in range(len(matrix)):
        for c in range(len(matrix[0])):
            ts = functions.extract_time_series(matrix, r, c)
            ts_out_median = functions.remove_outliers_median(ts, 2)
            spl = functions.get_spline_formulation(ts_out_median)
            xts_spline, yts_spline = functions.get_spline(spl, 0, len(ts), len(ts))
            errors[r][c] = functions.get_total_error(yts_spline.tolist(), ts.tolist())

    context = dict()

    context['errors'] = json.dumps(errors.tolist())
    return render(request, 'error_plot.html', context)


