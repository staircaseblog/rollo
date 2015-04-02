

#!/usr/bin/python

from Subfact_ina219 import INA219

ina = INA219()
result = ina.getBusVoltage_V()

ina.getShuntVoltage_mV()
ina.getBusVoltage_V()
ina.getCurrent_mA()
