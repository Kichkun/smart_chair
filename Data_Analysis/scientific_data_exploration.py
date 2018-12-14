import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import itertools
from scipy.interpolate import splev, splrep
import json
from datetime import datetime
import dateutil.parser

plt.interactive(True)
pd.options.display.max_columns = 15
pic_prefix = '../pic/'
data_path = '../CSV'

folders = os.listdir(data_path)
folders = [f"{data_path}/{folder}" for folder in folders if not folder.startswith('.')]

def normalize_MPU9250_data(df, coefs_dict=None):
    df = df.copy()

    if coefs_dict is None:
        coefs_dict = {
            'gyro_coef': 250.0/32768.0,
            'acc_coef': 2.0/32768.0,
            'mag_coef': 4912.0/32760.0,  # Actually it depends on x, y, z
        }

    acc_columns = [column for column in df.columns if column.startswith('acc')]
    gyro_columns = [column for column in df.columns if column.startswith('gyro')]
    mag_columns = [column for column in df.columns if column.startswith('mag')]

    df.loc[:, acc_columns] = df.loc[:, acc_columns] * coefs_dict['acc_coef']
    df.loc[:, gyro_columns] = df.loc[:, gyro_columns] * coefs_dict['gyro_coef']
    df.loc[:, mag_columns] = df.loc[:, mag_columns] * coefs_dict['mag_coef']  # Actually it depends on x, y, z

    return df

data_dict_dict = {}

chair_data_columns = ['time', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'mag_x', 'mag_y', 'mag_z']

for folder in folders:
    data_dict = {}
    name = folder.split('/')[-1]

    files = os.listdir(folder)
    files_shortnames = [file.split('_')[0] for file in files]  # There are might be repetitions

    for file, file_shortname in zip(files, files_shortnames):
        try:
            df = pd.read_csv(folder + '/' + file)

            if file_shortname in data_dict:  # If already in dict it's appended
                new_df = pd.concat([data_dict[file_shortname], df], axis=0).reset_index(drop=True)
                data_dict[file_shortname] = new_df
            else:
                data_dict[file_shortname] = df
        except:
            pass

    ### It was about processing data to the same format
    # if ('schairlog' in data_dict):
    #     acc_columns = [column for column in data_dict['schairlog'].columns if column.startswith('acc')]
    #     acc_columns = sorted(acc_columns, key=lambda x: x[-1])
    #     gyro_columns = [column for column in data_dict['schairlog'].columns if column.startswith('gyro')]
    #     gyro_columns = sorted(gyro_columns, key=lambda x: x[-1])
    #     mag_columns = [column for column in data_dict['schairlog'].columns if column.startswith('mag')]
    #     mag_columns = sorted(mag_columns, key=lambda x: x[-1])
    #
    #     all_columns = acc_columns + gyro_columns + mag_columns# + [time_column]
    #     rename_dict = dict(zip(all_columns, chair_data_columns[1:]))
    #     data_dict['schairlog'].rename(columns=rename_dict, inplace=True)
    #
    #     if (data_dict['schairlog']['acc_x'].dtype == int):
    #         data_dict['schairlog'] = normalize_MPU9250_data(data_dict['schairlog'])
    #         time_column = 'time'
    #     else: # if (data_dict['schairlog']['acc_x'].dtype == float):
    #         # data_dict['schairlog'] = normalize_MPU9250_data(data_dict['schairlog'])
    #         time_column = 'datetime_now'
    #
    #     data_dict['schairlog'].rename(columns={time_column: 'time'}, inplace=True)
    #     data_dict['schairlog']['time'] = pd.to_datetime(data_dict['schairlog']['time']).apply(lambda x: x.isoformat())
    #     data_dict['schairlog'] = data_dict['schairlog'].loc[:, chair_data_columns]
    #
    #     folder_new = folder.replace('CSV', 'NEW')
    #     os.mkdir(folder_new)
    #
    #     datetime_str = '99'
    #
    #     for file in files:
    #         if file.split('_')[0] == 'schairlog':
    #             datetime_str_candidate = '_'.join(file.split('_')[1:3])[:-4]
    #             if datetime_str_candidate < datetime_str:
    #                 datetime_str = datetime_str_candidate
    #
    #     data_dict['schairlog'].to_csv(folder_new + f'/schairlog_{datetime_str}.csv', index=False)

    data_dict_dict[name] = data_dict

chair_data_dict = {}

for key, value in data_dict_dict.items():
    key = key.replace('\t', ' ')
    if 'schairlog' in value:
        df_chair = value['schairlog']
        chair_data_dict[key] = df_chair
        print(len(df_chair))

class ChairAnalyser:

    def __init__(self,
                 df,
                 measurement_interval,
                 pic_prefix,
                 measurements_per_batch=1000,
                 name=None,
                 ):
        self.df_total = df
        self.measurement_interval = measurement_interval
        self.pic_prefix = pic_prefix
        self.measurements_per_batch = measurements_per_batch
        if name is not None:
            self.name = name
        else:
            self.name = folder.split('/')[-1]

        self.means, self.stds = self.create_mean_stds()


    def plot_measurements_timeline(
            self,
            sensors=('acc', 'gyro', 'mag'),
            axes=('x', 'y', 'z'),
    ):
        df = self.df_total
        name = self.name
        measurement_interval = self.measurement_interval

        n_cols = len(sensors)
        n_rows = len(axes)

        fig, ax = plt.subplots(n_rows, n_cols, sharex='col', figsize=(19, 11))

        for n_row, n_col in itertools.product(range(n_rows), range(n_cols)):
            ax_instance = ax[n_row, n_col]

            column_name = sensors[n_col] + '_' + axes[n_row]
            data2plot = df.loc[:, column_name].values

            ax_instance.plot(data2plot)

            if n_row == 0:
                title = sensors[n_col]
                ax_instance.set_title(title)

            if n_col == 0:
                title = axes[n_row]
                ax_instance.set_ylabel(title)

        suptitle = f'measurement_interval = {measurement_interval}'

        if 'mag' in sensors:
            zeros_portions = self.get_zeros_portion()
            mag_zeros_portion = zeros_portions[['mag_x', 'mag_y', 'mag_z']].mean()
            mag_zeros_string = f'Mag zeros portion = {round(mag_zeros_portion, 3)}'
            suptitle = suptitle + ', ' + mag_zeros_string

        plt.suptitle(suptitle)
        fig.tight_layout(rect=[0, 0.00, 1, 0.97])
        plt.savefig(pic_prefix + f'measurements_timeline_{name}.png')
        plt.close()

    def create_mean_stds(self, columns=('acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z')):
        df_chair = self.df_total.loc[:, columns]
        # df_chair = df_chair.loc[:, columns]
        # medians, lower_bounds, upper_bounds = np.percentile(df_chair, [50, percentile2crop, 100 - percentile2crop], axis=0)

        means = df_chair.mean(axis=0)
        stds = df_chair.std(axis=0)

        return means, stds

    def get_nonstationary_values_portion(self, n_sigma=3):
        means = self.means
        stds = self.stds

        columns = stds.index

        lower_bounds = means - n_sigma * stds
        upper_bounds = means + n_sigma * stds

        low_values_means = (df_chair[columns] < lower_bounds).mean()
        high_values_means = (df_chair[columns] > upper_bounds).mean()

        nonstationary_values_portion = low_values_means + high_values_means
        nonstationary_values_portion.index = [colname + '__nonstationary_portion' for colname in nonstationary_values_portion.index]

        return nonstationary_values_portion

    # def get_lean_back_portion(acc_z, means_stds=means_stds, n_sigma=5):
    def get_lean_back_portion(self, acc_z, acc_z_mean=-15910, acc_z_std=30, n_sigma=3):
        #     result = {}
        # acc_z_mean = means_stds.loc['Acc_z', 'mean']
        # acc_z_std = means_stds.loc['Acc_z', 'std']

        acc_z_min = acc_z_mean - n_sigma * acc_z_std
        acc_z_max = acc_z_mean + n_sigma * acc_z_std

        lean_back_portion = (acc_z < acc_z_min).mean()
        #     result['lean_back_portion'] = lean_back_portion

        #     return result
        return lean_back_portion

    def get_mess_mask_acc(self, acc_data, percentile2crop=10, n_sigma=10):
        lower_bound, upper_bound, median = np.percentile(acc_data, [percentile2crop, 100 - percentile2crop, 50])
        acc_data_filtered = acc_data[(lower_bound < acc_data) & (acc_data < upper_bound)]
        std = np.std(acc_data_filtered)
        oscillation = std / (25 * n_sigma)

        # Calculating bound for calm state
        calm_state_lower_bound = median - n_sigma * std
        calm_state_upper_bound = median + n_sigma * std

        mask_calm = ((calm_state_lower_bound < acc_data) & (acc_data < calm_state_upper_bound)).values
        #     mess_portion = 1 - np.mean(mask_calm)

        #     return mess_portion
        return mask_calm, oscillation

    def get_mess_mask_mag(self, mag_data, w=0.05, max_calm_derivative=30):
        # Spline approximation
        y = mag_data.values
        x = np.arange(len(y))
        splines = splrep(x, y, w=w * np.ones_like(y))
        points = splev(x, splines, der=0)
        derivatives = splev(x, splines, der=1)

        mask_calm = abs(derivatives) < max_calm_derivative

        #     return points, derivatives
        return mask_calm

    def get_mess_mask_mag4graph(self, mag_data, w=0.05, max_calm_derivative=30):
        # Spline approximation
        y = mag_data.values
        x = np.arange(len(y))
        splines = splrep(x, y, w=w * np.ones_like(y))
        points = splev(x, splines, der=0)
        derivatives = splev(x, splines, der=1)

        mask_calm = abs(derivatives) < max_calm_derivative

        return points, derivatives

    def get_chair_stats(self):
        df_total = self.df_total
        # results_list = []

        mask_calm_acc_x, oscillation_acc_x = self.get_mess_mask_acc(df_total['Acc_x'])
        mask_calm_acc_y, oscillation_acc_y = self.get_mess_mask_acc(df_total['Acc_y'])
        mask_calm_acc_z, oscillation_acc_z = self.get_mess_mask_acc(df_total['Acc_z'])

        mess_portion_acc_x = 1 - mask_calm_acc_x.mean()
        mess_portion_acc_y = 1 - mask_calm_acc_y.mean()
        mess_portion_acc_z = 1 - mask_calm_acc_z.mean()

        mess_portion_acc = (oscillation_acc_x + oscillation_acc_y + oscillation_acc_z) / 3

        mask_calm_acc = mask_calm_acc_x & mask_calm_acc_y & mask_calm_acc_z
        mess_portion_acc = 1 - mask_calm_acc.mean()

        mask_calm_mag_x = self.get_mess_mask_mag(df_total['Mag_x'])
        mask_calm_mag_y = self.get_mess_mask_mag(df_total['Mag_y'])
        mask_calm_mag_z = self.get_mess_mask_mag(df_total['Mag_z'])

        mess_portion_mag_x = 1 - mask_calm_mag_x.mean()
        mess_portion_mag_y = 1 - mask_calm_mag_y.mean()
        mess_portion_mag_z = 1 - mask_calm_mag_z.mean()

        mask_calm_mag = mask_calm_mag_x & mask_calm_mag_y & mask_calm_mag_z
        mess_portion_mag = 1 - mask_calm_mag.mean()

        lean_back_portion = self.get_lean_back_portion(df_total['Acc_z'])
        result = {
            # 'people_id': people_id,
            'mess_portion_acc_x': mess_portion_acc_x,
            'mess_portion_acc_y': mess_portion_acc_y,
            'mess_portion_acc_z': mess_portion_acc_z,
            'mess_portion_acc': mess_portion_acc,
            'lean_back_portion': lean_back_portion,
            'mess_portion_mag_x': mess_portion_mag_x,
            'mess_portion_mag_y': mess_portion_mag_y,
            'mess_portion_mag_z': mess_portion_mag_z,
            'mess_portion_mag': mess_portion_mag,
            'oscillation_acc_x': oscillation_acc_x,
            'oscillation_acc_y': oscillation_acc_y,
            'oscillation_acc_z': oscillation_acc_z,
            'oscillation_acc': oscillation_acc_z,
            # 'stress': stress,
        }
        # results_list.append(result)

        # return results_list
        return result

    def get_chair_stats_truncated(self):
        # self.get_df_total()
        self.plot_measurements_timeline()
        chair_stats_detailed = self.get_chair_stats()

        rename_dict = {
            'mess_portion_acc': 'Momentum',
            'mess_portion_mag': 'Rotational movement',
            'lean_back_portion': 'Lean back',
            'oscillation_acc': 'Oscillation',
        }

        chair_stats_detailed_truncated = {rename_dict[key]: chair_stats_detailed[key] for key in rename_dict if
                                          key in rename_dict}

        return chair_stats_detailed_truncated

    def plot_measurement_times(self):  # , filename='time_wrt_step.png'):
        df = self.df_total
        pic_prefix = self.pic_prefix
        measurement_interval = self.measurement_interval
        measurements_per_batch = self.measurements_per_batch
        n_measurements = len(df)
        n_batches = n_measurements // self.measurements_per_batch
        name = self.name

        timestamp_start = df['time'].min().timestamp()
        time_passed = df['time'].apply(lambda x: x.timestamp() - timestamp_start)

        # index2drop = range(measurements_per_batch, n_measurements, measurements_per_batch)
        # time_passed_truncated = time_passed.drop(index2drop, axis=0)

        time_between_batches_array = time_passed[measurements_per_batch::measurements_per_batch].values - \
                                     time_passed[measurements_per_batch - 1:-1:measurements_per_batch].values
        time_between_batches = time_between_batches_array.mean()

        timediff_total = time_passed.iloc[-1]
        timediff_because_of_measurements = timediff_total - time_between_batches_array.sum()
        n_measurements_without_batch = n_measurements - n_batches
        time_between_measurements = timediff_because_of_measurements / n_measurements_without_batch

        plt.close()
        plt.figure(figsize=(16, 12))
        plt.plot(time_passed)
        plt.xlabel('n_step')
        plt.ylabel('Time passed, s')
        title = f'Measurement interval = {round(measurement_interval, 3)}, ' + \
                f'Time Between Measurements = {round(time_between_measurements, 3)}, ' + \
                f'Time Between Batches = {round(time_between_batches, 3)}'
        plt.title(title, fontsize=16)
        plt.tight_layout()
        # plt.savefig(pic_prefix + filename)
        plt.savefig(pic_prefix + f'time_wrt_step_{name}.png')

    def get_zeros_portion(self):
        df = self.df_total.drop('time', axis=1)
        zeros_portions = (df == 0).mean(axis=0)

        return zeros_portions

    @staticmethod
    def parse_string_iso_format(s):
        d = dateutil.parser.parse(s)
        return d

if __name__ == "__main__":
    pic_prefix = '../pic/'

    nonstationary_values_portion_list = []
    for name, df_chair in chair_data_dict.items():
        chair_analyser = ChairAnalyser(df_chair, 0.01, pic_prefix)
        nonstationary_values_portion = chair_analyser.get_nonstationary_values_portion()
        nonstationary_values_portion.name = name
        nonstationary_values_portion_list.append(nonstationary_values_portion)

    df_nonstationary_values_portion = pd.DataFrame(nonstationary_values_portion_list)
    df_nonstationary_values_portion.reset_index(inplace=True)
    df_nonstationary_values_portion.rename(columns={'index': 'player_name'}, inplace=True)

    df_players = pd.read_csv('../data/participants2_fixed.csv', sep=';')

    df_players['player_name'] = df_players[['First Name', 'Last Name']].apply(lambda x: ' '.join(x), axis=1)

    df_players.rename(columns={
        ' What experience do u have in shooter games (Counter-Strike, Doom, Battlefield, etc.)?': 'Skill'
        },
        inplace=True,
    )

    df_players = df_players[['player_name', 'Skill']]
    skill_is_none = df_players['Skill'] == 'None'
    df_players.loc[skill_is_none, 'Skill'] = 'Small'
    df_players['Skill'].value_counts()


    df_players.to_csv('../data/clean/df_players.csv', index=False)
    df_nonstationary_values_portion.to_csv('../data/clean/df_nonstationary_values_portion.csv', index=False)

    pd.read_csv('../data/clean/df_nonstationary_values_portion.csv')


    df_merged = df_players.merge(df_nonstationary_values_portion, how='inner', on='player_name')
    df_merged.to_csv('../data/clean/df_merged.csv', index=False)



# data_dict['key']['key'].unique()  # Keyboard
#
# data_dict['envibox']['als']  # Enviroment params
#
# data_dict['schairlog']  # Chair. Why int, not float?
#
# data_dict['datalog']  # What is it?
#
# data_dict['mxy']  # Mouse scroll
#
# data_dict['mkey']['mouse_key'].value_counts()  # Mouse keys
#
# data_dict['hrm']  # Heart rate
#
# data_dict['imulog']  # What is it?

