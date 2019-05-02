
# vke_car_new
VKE Demo Car-side program
.../car_new/LipoMonitor/

LipoMonTest.py

car_main.py: NEM KELL

/etc/systemd/system/lipomon.service !!
sudo systemctl daemon-reload

"""
Calibration register values were calculated with following method:
	Current_LSB 	= MAX_CURRENT / 32768
	CAL 		= 0.00512 / (Current_LSB * RShunt)
	MAX_CURRENT 	= 5
	R_SHUNT 	= 0.1
	Current_LSB 	= 152 * 10-6 #higher LSB => smaller rounding error
	CAL 		= 336.8421 (337) ===> 0x151
Reconversion of received data: Y -> X
The value of 0 can be used for b for both current and power measurements with very little loss in accuracy
because the offset for power and current measurements is very low.
	b = 0
The voltage LSB for bus voltage and shunt voltage are fixed at 1.25 mV/bit and 2.5 µV/bit.
	m = 8 and m = 4
	R = 2 and R = 5
	X = (1 / m) * (Y * 10^[-R]  - b)
Calculating m,R for current measurement:
	m = 1 / Current_LSB
	m : move decimal point to maximize value, but stay in [-32767,32767] interval
	#this minimizes rounding errors!
	if *10 => R = -1 	(m shifted right)
	if /10 => R = 1 	(m shifted left)
Calculating m,R for power measurement:
	m = 1 / (25 * Current_LSB)
	rest is same as with current!
	X = (1 / m) * (Y * 10^[-R]  - b)
  """
