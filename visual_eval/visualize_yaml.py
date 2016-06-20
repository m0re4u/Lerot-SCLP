#!/usr/bin/env python

import argparse
import numpy as np
import gzip
import os
import yaml
from multiple_plots import multiple_plots


def visualize_yaml(evaluation, folder, x, y, max_bound, ymin=0, ymax=1,
                   title="plot", run_mean=1):
    """
    Visualize the specified evaluation from the folder given.
    Setting the mean flag will assume each file is one run, and take the
    average over runs.
    """

    x_data = []
    y_data = []
    y_pos = []
    z_labels = []

    if evaluation == "offline":
        evaluation = "offline_test"

    for filename in os.listdir(folder):
        x_data, y_data, y_pos, z_labels = open_file(
            evaluation, filename, folder, x_data, y, y_data, y_pos, z_labels
        )

    for i in range(len(y_data)):
        x_data[i] = x_data[i][:-run_mean]
        y_data[i] = running_mean(y_data[i], run_mean)[:-run_mean]
        if evaluation == "online":
            y_data[i] = calc_cumulative(y_data[i])
        if y_data[i][-1] > ymax:
            ymax = y_data[i][-1]
        y_pos.append(y_data[i][-1])

    multiple_plots(x_data, y_data, y_pos, max_bound-run_mean, ymin, ymax,
                   title, x, y, z_labels)


def running_mean(x, N):
    return np.convolve(x, np.ones((N,))/N)[(N-1):]


def open_file(evaluation, filename, folder, x_data, y, y_data, y_pos,
              z_labels):

    if os.path.isdir(os.path.join(folder, filename)):
        new_folder = os.path.join(folder, filename)
        temp_x = []
        temp_y = []
        temp_y_pos = []
        temp_z = []
        for file in os.listdir(new_folder):
            temp_x, temp_y, temp_y_pos, temp_z = open_file(
                evaluation, file, new_folder, temp_x, y, temp_y, temp_y_pos,
                temp_z
            )

        x_data.append(np.median(temp_x, axis=0))
        y_data.append(np.median(temp_y, axis=0))
        z_labels.append(filename.split('@')[0])
    else:
        data = None
        _, ext = os.path.splitext(filename)
        # Exclude some standard files that are normally in the folder generated
        # by an experiment(particularly LearningExperiment)
        if ext == '.gz' and not filename.startswith('_'):

            with gzip.open(os.path.join(folder, filename), 'r') as data_file:
                print("Reading " + str(filename))
                data = yaml.load(data_file.read())

            z_labels.append(filename.split("@")[0])

            for measure in data:
                if (evaluation in measure) and measure.endswith(y):
                    data = data[measure]

            y_data.append(data)
            x_data.append(list(range(1, len(data)+1)))

    return (x_data, y_data, y_pos, z_labels)


def calc_cumulative(y_data):
    """
    Turn data into cumulative vector.
    """

    summed = 0
    for i in range(len(y_data)):
        summed += y_data[i]
        y_data[i] = summed / (i + 1)

    return y_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
            Construct and run a set of learning experiments. Provide the
            name of the config file, and which parameter you want to be shifted
            between what range, with what steps""")
    parser.add_argument("-f", "--folder_name", help="name of folder with data")
    parser.add_argument("-m", "--measure", help="offline or online evaluation")
    parser.add_argument("-x", "--x_label", help="label for x-axis")
    parser.add_argument("-y", "--y_label", help="label for y-axis"
                        "(HAS TO BE EVALUATION MEASURE LIKE IN CONFIG)")
    parser.add_argument("-max_x", "--max_bound_x",
                        help="maximum number for x-axis", type=int)
    parser.add_argument("-max_y", "--max_bound_y",
                        help="maximum number for y-axis", type=float)
    parser.add_argument("-min_y", "--min_bound_y",
                        help="minimum number for y-axis", type=float)
    parser.add_argument("-title", help="title for image")
    parser.add_argument("-run_mean", help="parameter for running mean",
                        type=int)
    # parser.add_argument("-cum", "--cumulative",
    #                     help="boolean for want cumulative evaluation",
    #                     action=storetrue)
    args = parser.parse_args()

    visualize_yaml(args.measure, args.folder_name, args.x_label, args.y_label,
                   args.max_bound_x, args.min_bound_y, args.max_bound_y,
                   args.title, args.run_mean)
