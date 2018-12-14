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

TIME_FORMAT = '%H:%M:%S'

class TroykaIMU(object):
    def __init__(self):
        self.magnetometer = LIS3MDL()
        self.accelerometer = LIS331DLH()

class SimpleRequest:

    url = ""
    dataAccelerometer = []
    dataMagnetometer = []
    dataGyro = []
    # For synchronization
    canRead = True

    def __init__(self, url="http://localhost:8080"):
        self.url = url

    def collectAccelerometer(self, ax, ay, az, label, metainfo, peopleId, typeSensor):
        while (self.canRead):
            a = 1
        req = {
            'dateCreated':datetime.now().isoformat(),
            'label':label,
            'metaInfo':metainfo,
            'peopleId':peopleId,
            'typeSensor':typeSensor,
            'ax':ax,
            'ay':ay,
            'az':az,
            'time': datetime.now().date().isoformat(),
        }
        self.dataAccelerometer.append(req)

    def collectMagnetometer(self, x, y, z, label, metainfo, peopleId, typeSensor):
        while (self.canRead):
            a = 1
        req = {
            'x':x,
            'y':y,
            'z':z,
            'dateCreated':datetime.now().isoformat(),
            'label':label,
            'metaInfo':metainfo,
            'peopleId':peopleId,
            'typeSensor':typeSensor,
            'time': datetime.now().date().isoformat(),
        }
        self.dataMagnetometer.append(req)

    def collectGyro(self, x, y, z, label, metainfo, peopleId, typeSensor):
        while(self.canRead):
            a = 1
        req = {
            'x': x,
            'y': y,
            'z': z,
            'dateCreated': datetime.now().isoformat(),
            'label': label,
            'metaInfo': metainfo,
            'peopleId': peopleId,
            'typeSensor': typeSensor,
            'time': datetime.now().date().isoformat(),
        }
        self.dataGyro.append(req)

    def sendData(self):
        # If we copy information about that
        while(self.canRead == False):
            a = 1
        self.canRead = False
        dataAcc = self.dataAccelerometer.copy()
        self.dataAccelerometer.clear()
        dataMag = self.dataMagnetometer.copy()
        self.dataMagnetometer.clear()
        dataGyro = self.dataGyro.copy()
        self.dataGyro.clear()
        self.canRead = True
        response = requests.post(url=self.url + "/api/accelerometer", data=json.dumps(self.dataAccelerometer), headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print("Acc Responce: " + response.content.decode("utf-8"))
        if (response.ok == False):
            print("an error occupied by you")

        # Do not change
        self.dataAccelerometer.clear()

        response = requests.post(url=self.url + "/api/magnetometer", data=json.dumps(self.dataMagnetometer), headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print(json.dumps(self.dataMagnetometer))
        print("Mag Responce: " + response.content.decode("utf-8"))
        if (response.ok == False):
            print("an error occurred in you")
        # Do not change
        self.dataMagnetometer.clear()

        response = requests.post(url=self.url + "/api/magnetometer", data=json.dumps(self.dataGyro),
                                 headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        print(json.dumps(self.dataGyro))
        print("Mag Responce: " + response.content.decode("utf-8"))
        if (response.ok == False):
            print("an error occurred in you")
        self.dataGyro.clear();


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timestep_detect', type=float, default=0.5)
    parser.add_argument('--timestep_send', type=float, default=10)
    parser.add_argument('--max_time', type=float, default=60)
    parser.add_argument('--verbose', type=bool, default=True)
    parser.add_argument('--send_data', type=bool, default=True)
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
    label = args.label
    peopleId = args.peopleId
    meta = args.meta
    send_data = args.send_data

    batch_size = int(timestep_send / timestep_detect)  # Количество измерений в одной отправке
    n_batches = int(max_time / timestep_send) # Количество отправок

    imu = TroykaIMU()  # Troyka card

    simple_request = SimpleRequest(url="http://smart-chair-iot-dev.us-east-1.elasticbeanstalk.com")

    for n_batch in range(n_batches):

        for n_measurement in range(batch_size):
            data_magnetometer = imu.magnetometer.read_xyz()
            data_accelerometer = imu.accelerometer.read_xyz()

            if verbose:
                print('Magnetometer data: ', data_magnetometer)
                print('Accelerometer data: ', data_accelerometer)

            if send_data:
                ax, ay, az = data_magnetometer
                simple_request.collectMagnetometer(ax, ay, az, label, meta, peopleId, 'magnetometer')

                ax, ay, az = data_accelerometer
                simple_request.collectAccelerometer(ax, ay, az, label, meta, peopleId, 'accelerometer')

            time.sleep(timestep_detect)

        simple_request.sendData()

    print('---------------------------')
    print('----End of measurements----')
    print('---------------------------')






