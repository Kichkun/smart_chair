# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime
import sys
import time
import argparse

sys.path.append('../')

from accel import LIS331DLH
from magnet import LIS3MDL

class TroykaIMU(object):
    def __init__(self):
        self.magnetometer = LIS3MDL()
        self.accelerometer = LIS331DLH()

class SimpleRequest:

    url = ""
    dataAccelerometer = []
    dataMagnetometer = []

    def __init__(self, url="http://localhost:8080"):
        self.url = url

    def collectAccelerometer(self, ax, ay, az, label, metainfo, peopleId, typeSensor):
        req = {'dateCreated':datetime.now().date().isoformat(),'label':label,'metaInfo':metainfo,'peopleId':peopleId,
               'typeSensor':typeSensor,'ax':ax,'ay':ay,'az':az}
        self.dataAccelerometer.append(req)

    def collectMagnetometer(self, ax, ay, az, label, metainfo, peopleId, typeSensor):
        req = {'linX':0.0,'linY':0.0,'linZ':0.0,
               'dateCreated':datetime.now().date().isoformat(),'label':label,'metaInfo':metainfo,'peopleId':peopleId,
               'typeSensor':typeSensor,'ax':ax,'ay':ay,'az':az}
        self.dataMagnetometer.append(req)

    def sendData(self):
        response = requests.post(url=self.url + "/api/accelerometer", data=json.dumps(self.dataAccelerometer), headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print(response.content)
        if (response.ok == False):
            print("an error occupied by you")

        # self.dataAccelerometer.clear()
        self.dataAccelerometer = []

        response = requests.post(url=self.url + "/api/magnetometer", data=json.dumps(self.dataMagnetometer), headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print(response.content)
        if (response.ok == False):
            print("an error occurred in you")

        # self.dataMagnetometer.clear()
        self.dataMagnetometer = []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timestep_detect', type=int, default=1)
    parser.add_argument('--timestep_send', type=float, default=3)
    parser.add_argument('--max_time', type=float, default=9)
    parser.add_argument('--verbose', type=bool, default=True)
    parser.add_argument('--label', type=str, default='')
    parser.add_argument('--meta', type=str, default='')
    parser.add_argument('--peopleId', type=str, default='')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    timestep_detect = args.timestep_detect  # timestep between measurements
    timestep_send = args.timestep_send #  60  #  timestep between sendings
    max_time = args.max_time #  30 * 60  # total time of measurement
    verbose = args.verbose

    batch_size = timestep_send // timestep_detect  # Количество измерений в одной отправке
    n_batches = max_time // timestep_send  # Количество отправок

    imu = TroykaIMU()  # Troyka card

    simple_request = SimpleRequest(url="http://smart-chair-iot-dev.us-east-1.elasticbeanstalk.com")

    for n_batch in range(n_batches):

        for n_measurement in range(batch_size):
            data_magnetometer = imu.magnetometer.read_xyz()
            data_accelerometer = imu.accelerometer.read_xyz()

            if verbose:
                print('Magnetometer data: ', data_magnetometer)
                print('Accelerometer data: ', data_accelerometer)

            ax, ay, az = data_magnetometer
            simple_request.collectMagnetometer(ax, ay, az, 'LaBeL', 'meta-meta', 'peopleID', 'magnetometer')

            ax, ay, az = data_accelerometer
            simple_request.collectAccelerometer(ax, ay, az, 'LaBeL', 'meta-meta', 'peopleID', 'accelerometer')

            time.sleep(timestep_detect)

        simple_request.sendData()

    print('---------------------------')
    print('----End of measurements----')
    print('---------------------------')






