from IRSensor import IRSensor as ir

MFR_CALIBRATION = 0xD4
address = 0x45



bus=ir.bus
print(bus.read_word_data(address,MFR_CALIBRATION))

