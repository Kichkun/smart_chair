# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime
import sys
import time
import argparse
import FaBo9Axis_MPU9250
import time
import sys
import joblib
import os

sys.path.append('../')

# TIME_FORMAT = '%H:%M:%S'
TIME_FORMAT = '%H-%M-%S'

mpu9250 = FaBo9Axis_MPU9250.MPU9250()


class SimpleRequest:
    url = ""
    dataAccelerometer = []
    dataMagnetometer = []
    dataGyroscope = []

    def __init__(self, url="http://localhost:8080"):
        self.url = url

    def collectAccelerometer(self, ax, ay, az, label, metainfo, peopleId, typeSensor):
        req = {
            'dateCreated': datetime.now().isoformat(),
            'label': label,
            'metaInfo': metainfo,
            'peopleId': peopleId,
            'typeSensor': typeSensor,
            'ax': ax,
            'ay': ay,
            'az': az,
            # 'time': datetime.now().time().strftime(TIME_FORMAT),
            # 'timestep_detect': timestep_detect
        }
        self.dataAccelerometer.append(req)

    def collectMagnetometer(self, x, y, z, label, metainfo, peopleId, typeSensor):
        req = {
            'x': x,
            'y': y,
            'z': z,
            'dateCreated': datetime.now().isoformat(),
            'label': label,
            'metaInfo': metainfo,
            'peopleId': peopleId,
            'typeSensor': typeSensor,
            # 'time': datetime.now().time().strftime(TIME_FORMAT),
        }
        self.dataMagnetometer.append(req)

    def collectGyroscope(self, x, y, z, label, metainfo, peopleId, typeSensor):
        req = {
            'x': x,
            'y': y,
            'z': z,
            'dateCreated': datetime.now().isoformat(),
            'label': label,
            'metaInfo': metainfo,
            'peopleId': peopleId,
            'typeSensor': typeSensor,
            # 'time': datetime.now().time().strftime(TIME_FORMAT),
        }
        self.dataGyroscope.append(req)

    def sendData(self):
        # Accelerometer
        response = requests.post(url=self.url + "/api/accelerometer", data=json.dumps(self.dataAccelerometer),
                                 headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print("Acc Responce: " + response.content.decode("utf-8"))
        if (response.ok == False):
            print("an error occupied by you")

        self.dataAccelerometer.clear()
        # self.dataAccelerometer = []

        # Magnetometer
        response = requests.post(url=self.url + "/api/magnetometer", data=json.dumps(self.dataMagnetometer),
                                 headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print(json.dumps(self.dataMagnetometer))
        print("Mag Responce: " + response.content.decode("utf-8"))
        if (response.ok == False):
            print("an error occurred in you")

        self.dataMagnetometer.clear()
        # self.dataMagnetometer = []

        # Gyroscope
        response = requests.post(url=self.url + "/api/gyroscope", data=json.dumps(self.dataAccelerometer),
                                 headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print("Acc Responce: " + response.content.decode("utf-8"))
        if (response.ok == False):
            print("an error occupied by you")

        self.dataAccelerometer.clear()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timestep-detect', type=float, default=0.01)
    parser.add_argument('--timestep-send', type=float, default=10)
    parser.add_argument('--max-time', type=float, default=60)
    parser.add_argument('--verbose', type=bool, default=False)
    parser.add_argument('--send-data', type=bool, default=True)
    parser.add_argument('--save-data', type=bool, default=True)
    parser.add_argument('--label', type=str, default='')
    parser.add_argument('--meta', type=str, default='')
    parser.add_argument('--person-id', type=str, default='')
    parser.add_argument('--folder', type=str, default=None)
    parser.add_argument('--synchronize-time', type=bool, default=False)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    timestep_detect = args.timestep_detect  # timestep between measurements
    timestep_send = args.timestep_send  # 60  #  timestep between sendings
    max_time = args.max_time  # 30 * 60  # total time of measurement
    verbose = args.verbose
    label = args.label
    person_id = args.person_id
    meta = args.meta
    send_data = args.send_data
    save_data = args.save_data
    folder = args.folder
    synchronize_time = args.synchronize_time

    batch_size = int(timestep_send / timestep_detect)  # Количество измерений в одной отправке
    n_batches = int(max_time / timestep_send)  # Количество отправок

    # simple_request = SimpleRequest(url="http://smart-chair-iot-dev.us-east-1.elasticbeanstalk.com")

    time_start = datetime.now().strftime(TIME_FORMAT)

    if folder is None:
        folder = time_start

    os.mkdir('../data/' + folder)  # Here we will store data in batches
    prefix = '../data/' + folder + '/'

    # It's time to synchronize time!
    # Meybe you should use 'sudo python' instead of 'python' when running the script because of this command
    if synchronize_time:
        os.system('sudo ntpdate ntp1.stratum1.ru')

    for n_batch in range(n_batches):

        results_list = []

        for n_measurement in range(batch_size):
            accel = mpu9250.readAccel()
            gyro = mpu9250.readGyro()
            mag = mpu9250.readMagnet()

            if verbose:
                print('accel: ', accel)
                print('gyro: ', gyro)
                print('mag: ', mag)

            result = {
                'datetime_now': datetime.now(),
                'accel_x': accel['x'],
                'accel_y': accel['y'],
                'accel_z': accel['z'],
                'gyro_x': gyro['x'],
                'gyro_y': gyro['y'],
                'gyro_z': gyro['z'],
                'mag_x': mag['x'],
                'mag_y': mag['y'],
                'mag_z': mag['z'],
            }

            # if send_data:
            #     ax, ay, az = data_magnetometer
            #     simple_request.collectMagnetometer(ax, ay, az, label, meta, person_id, 'magnetometer')
            #
            #     ax, ay, az = data_accelerometer
            #     simple_request.collectAccelerometer(ax, ay, az, label, meta, person_id, 'accelerometer')

            results_list.append(result)

            time.sleep(timestep_detect)

        joblib.dump(results_list, prefix + str(n_batch))
        # simple_request.sendData()

    print('---------------------------')
    print('----End of measurements----')
    print('---------------------------')
