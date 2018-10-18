import requests
import json
from datetime import datetime
import sys

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
        if (response.ok == False):
            print("an error occupied")

        # self.dataAccelerometer.clear()
        self.dataAccelerometer = []

        response = requests.post(url=self.url + "/api/magnetometer", data=json.dumps(self.dataMagnetometer), headers={'content-type': 'application/json', 'Accept-Charset': 'UTF-8'})
        if (response.ok == False):
            print("an error occupied")

        # self.dataMagnetometer.clear()
        self.dataMagnetometer = []


if __name__ == '__main__':
    imu = TroykaIMU()
    data_magnetometer = imu.magnetometer.read_xyz()
    data_accelerometer = imu.accelerometer.read_xyz()

    print('Magnetometer data')
    print(data_magnetometer)
    print('Accelerometer data')
    print(data_accelerometer)

    simple_request = SimpleRequest(url="http://smart-chair-iot-dev.us-east-1.elasticbeanstalk.com/")
    ax, ay, az = data_accelerometer
    simple_request.collectAccelerometer(ax, ay, az, 'LaBeL', 'meta-meta', 'peopleID', 'accelerometer')
    ax, ay, az = data_magnetometer
    simple_request.collectMagnetometer(ax, ay, az, 'LaBeL', 'meta-meta', 'peopleID', 'magnetometer')

    simple_request.sendData()






