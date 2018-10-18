import smbus
from math import atan2, pi, degrees

class LIS3MDL(object):
    register = {
        'WHO_AM_I'          : 0x0F,
        'CTRL_REG1'		    : 0x20,
        'CTRL_REG2'			: 0x21,
        'CTRL_REG3'			: 0x22,
        'CTRL_REG4'			: 0x23,
        'CTRL_REG5'			: 0x24,
        'STATUS_REG'        : 0x27,
        'OUT_X_L'			: 0x28,
        'OUT_X_H'			: 0x29,
        'OUT_Y_L'			: 0x2A,
        'OUT_Y_H'			: 0x2B,
        'OUT_Z_L'			: 0x2C,
        'OUT_Z_H'			: 0x2D,
        'TEMP_OUT_L'        : 0x2E,
        'TEMP_OUT_H'        : 0x2F,
        'INT_CFG'			: 0x30,
        'INT_SRC'			: 0x31,
        'INT_THS_L'			: 0x32,
        'INT_THS_H'			: 0x33,
    }

    range_fs = (
        '4_GAUSS',
        '8_GAUSS',
        '12_GAUSS',
        '16_GAUSS',)

    adr_fs_conf = {
        '4_GAUSS'           : 0b00000000,
        '8_GAUSS'           : 0b00100000,
        '12_GAUSS'          : 0b01000000,
        '16_GAUSS'          : 0b01100000,
    }

    sens_fs = {
        '4_GAUSS'           : 6842,
        '8_GAUSS'           : 3421,
        '12_GAUSS'          : 2281,
        '16_GAUSS'          : 1711,
    }

    axis_operation_mode = {
        'LOW_POWER'         : 0b00000000,      # Low-power mode
        'MEDIUM_PERF'       : 0b00100000,      # Medium-performance mode
        'HIGH_PERF'         : 0b01000000,      # High-performance mode
        'ULTRA_HIGH_PERF'   : 0b01100000,      # Ultra-High-performance mode
    }

    configuration = {
        'ODR_0625'          : 0b0000000,      # 0.625 Hz
        'ODR_125'           : 0b0000100,      # 1.25  Hz
        'ODR_25'            : 0b0001000,      # 2.5   Hz
        'ODR_5'             : 0b0001100,      # 5     Hz
        'ODR_10'            : 0b0010000,      # 10    Hz
        'ODR_20'            : 0b0010100,      # 20    Hz
        'ODR_40'            : 0b0011000,      # 40    Hz
        'ODR_80'            : 0b0011100,      # 80    Hz
    }

    temperature_measure = {'C',
                           'K',
                           'F',
                           }

    # Default
    I2C_DEFAULT_ADDRESS = 0b0011100
    I2C_IDENTITY = 0x3d

    # Additional constants
    DEFAULT_TEMPERATURE_MEASURE = 'C'
    CELSIUS_TO_KELVIN_OFFSET = 273.15



    _mult = sens_fs[range_fs[0]]
    _ctrlReg1 = 0
    _ctrlReg2 = 0
    _ctrlReg3 = 0
    _ctrlReg4 = 0
    _ctrlReg5 = 0

    _calibration_matrix = [[0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0]]

    _bias = [0.0, 0.0, 0.0]

    def __init__(self, port=1,
                 address=I2C_DEFAULT_ADDRESS,
                 sens_range=range_fs[0],
                 temperature_sensor_enable=True,
                 axis_operation_mode=axis_operation_mode['ULTRA_HIGH_PERF'],
                 output_data_rate=configuration['ODR_80']
                 ):
        
        self.wire = smbus.SMBus(port)
        
        self._address = address
        
        self.soft_reset()
        
        self.set_range(sens_range)
        
        self.enable()
        
        self.temperature_sensor(temperature_sensor_enable)
        # Ultra High Performance Mode Selected for XY Axis
        self.operation_mode_xy_axis(axis_operation_mode)
        # Ultra High Performance Mode Selected for Z Axis
        self.operation_mode_z_axis(axis_operation_mode)
        # Output Data Rate of 80 Hz Selected
        self.output_data_rate(output_data_rate)

    def identity(self):
        return self.wire.read_byte_data(self._address, self.register['WHO_AM_I']) == self.I2C_IDENTITY

    # Register 1 operations
    # TEMP_EN OM1 OM0 DO2 DO1 DO0 FAST_ODR ST
    # Temperature sensor enable. Default value: 0
    # (0: temperature sensor disabled; 1: temperature sensor enabled)
    def temperature_sensor(self, enable=False):
        if enable:
            self._ctrlReg1 |= (1 << 7)
        else:
            self._ctrlReg1 &= ~(1 << 7)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG1'], self._ctrlReg1)

    # X and Y axes operative mode selection. Default value: 00
    def operation_mode_xy_axis(self, mode=axis_operation_mode['LOW_POWER']):
        self._ctrlReg1 |= mode
        self.wire.write_byte_data(self._address, self.register['CTRL_REG1'], self._ctrlReg1)

    # Output data rate selection. Default value: 100
    def output_data_rate(self, rate=configuration['ODR_10']):
        self._ctrlReg1 |= rate
        self.wire.write_byte_data(self._address, self.register['CTRL_REG1'], self._ctrlReg1)

    # FAST_ODR enables data rates higher than 80 Hz. Default value: 0
    # (0: Fast_ODR disabled; 1: FAST_ODR enabled)
    def fast_odr(self, enable=False):
        if enable:
            self._ctrlReg1 |= (1 << 1)
        else:
            self._ctrlReg1 &= ~(1 << 1)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG1'], self._ctrlReg1)

    # Self-test enable. Default value: 0 (0: self-test disabled; 1: self-test enabled)
    def self_test(self, enable=False):
        if enable:
            self._ctrlReg1 |= (1 << 0)
        else:
            self._ctrlReg1 &= ~(1 << 0)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG1'], self._ctrlReg1)

    # Register 2 operations
    # 0 FS1 FS0 0 REBOOT SOFT_RST 0 0
    # Full-scale configuration. Default value: 00
    def set_range(self, sens_range=range_fs[0]):
        if sens_range in self.range_fs:
            self._ctrlReg2 = self.adr_fs_conf[sens_range]
            self._mult = self.sens_fs[sens_range]
            self.wire.write_byte_data(self._address, self.register['CTRL_REG2'], self._ctrlReg2)

    def soft_reset(self):
        # Configuration registers and user register reset function. (0: Default value; 1: Reset operation)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG2'], self._ctrlReg2 | (1 << 2))

    def reboot(self):
        # Reboot memory content. Default value: 0 (0: normal mode; 1: reboot memory content)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG2'], self._ctrlReg2 | (1 << 3))

    # Register 3 operations
    # 0 0 LP 0 0 SIM MD1 MD0
    # Low-power mode configuration. Default value: 0
    def low_power(self):
        self._ctrlReg3 |= (1 << 5)
        self._ctrlReg1 |= self.configuration['ODR_0625']
        self.wire.write_byte_data(self._address, self.register['CTRL_REG3'], self._ctrlReg3)

    # Power-Down mode
    def enable(self, power=True):
        if not power:
            self._ctrlReg3 |= (3 << 0)
        else:
            self._ctrlReg3 &= ~(3 << 0)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG3'], self._ctrlReg3)

    # Register 4 operations
    # 0 0 0 0 OMZ1 OMZ0 BLE 0
    # X and Y axes operative mode selection. Default value: 00
    def operation_mode_z_axis(self, mode=axis_operation_mode['LOW_POWER']):
        self._ctrlReg4 |= (mode >> 3)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG4'], self._ctrlReg4)

    # Register 5 operations
    # FAST_READ BDU 0 0 0 0 0 0
    def fast_read(self, enable=False):
        if enable:
            self._ctrlReg5 |= (1 << 7)
        else:
            self._ctrlReg5 &= ~(1 << 7)
        self.wire.write_byte_data(self._address, self.register['CTRL_REG5'], self._ctrlReg5)

    # Getting data operations
    def read_axis(self, reg):
        # assert MSB to enable register address auto increment
        return self.signed_int32(self.wire.read_word_data(self._address, reg | (1 << 7)))

    def read_xyz(self):
        # assert MSB to enable register address auto increment
        values = self.wire.read_i2c_block_data(self._address, self.register['OUT_X_L'] | (1 << 7), 6)
        return (self.signed_int32(values[1] << 8 | values[0]),
                self.signed_int32(values[3] << 8 | values[2]),
                self.signed_int32(values[5] << 8 | values[4]))

    def read_gauss_x(self):
        return self.read_axis(self.register['OUT_X_L']) / self._mult

    def read_gauss_y(self):
        return self.read_axis(self.register['OUT_Y_L']) / self._mult

    def read_gauss_z(self):
        return self.read_axis(self.register['OUT_Z_L']) / self._mult

    def read_gauss_xyz(self):
        gauss = self.read_xyz()
        return gauss[0] / self._mult, gauss[1] / self._mult, gauss[2] / self._mult

    def read_calibrate_xyz(self):
        return self.calibrate()

    def read_calibrate_gauss_xyz(self):
        calibrate_gauss = self.read_calibrate_xyz()
        return calibrate_gauss[0] / self._mult, calibrate_gauss[1] / self._mult, calibrate_gauss[2] / self._mult

    def calibrate(self):
        calibrated_values = []
        uncalibrated_values = []
        read_values = self.read_xyz()
        for i in range(0, 3):
            uncalibrated_values.append(read_values[i] - self._bias[i])

        for i in range(0, 3):
            result = 0
            for j in range(0, 3):
                result += self._calibration_matrix[i][j] * uncalibrated_values[j]
            calibrated_values.append(result)
        return calibrated_values

    def calibrate_matrix(self, calibration_matrix, bias):
        self._bias = bias
        self._calibration_matrix = calibration_matrix
        return None

    def read_azimut(self):
        if (self._bias[0] + self._bias[1] + self._bias[2]) != 0 and self._calibration_matrix[0][0] != 0:
            sensor = self.calibrate()
        else:
            print("please, calibrate your sensor first")
            return 0
        two_pi = 2 * pi
        heading = atan2(sensor[1], sensor[0])
        if heading < 0:
            heading += two_pi
        elif heading > two_pi:
            heading -= two_pi
        return degrees(heading)

    # Temperature read data
    def read_temperature_raw(self):
        # assert MSB to enable register address auto increment
        return self.signed_int32(self.wire.read_word_data(self._address, self.register['TEMP_OUT_L'] | (1 << 7)))

    def read_temperature(self, measure=DEFAULT_TEMPERATURE_MEASURE):
        self._temperature = self.read_temperature_raw()
        if measure in self.temperature_measure and self._temperature:
            return self._temperature / 8.0 + 25.0

    def read_temperature_k(self):
        return self.read_temperature_raw() / 8.0 + 25.0 + self.CELSIUS_TO_KELVIN_OFFSET

    def read_temperature_f(self):
        return self.read_temperature_raw() / 8.0 * 1.8 + 108.5

    @staticmethod
    def signed_int32(number):
        if number & (1 << 15):
            return number | ~65535
        else:
            return number & 65535
class TroykaIMU(object):
    def __init__(self):
        self.magnetometer = LIS3MDL()
		
imu = TroykaIMU()
print(imu.magnetometer.read_xyz())
