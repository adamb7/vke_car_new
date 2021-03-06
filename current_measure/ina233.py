""" ina233.py: Commands for INA233 """

"""" manual: https://hu.mouser.com/ProductDetail/Texas-Instruments/INA233AIDGST?qs=sGAEpiMZZMvEn2pkGav3bMtYv3jXcK%2Fs675Gz1CmKpPA31zMfaD9iw%3D%3D  """

CLEAR_FAULTS 		    = 0x03
RESTORE_DEFAULT_ALL 	= 0x12
CAPABILITY 		        = 0x19
IOUT_OC_WARN_LIMIT	    = 0x4A
VIN_OV_WARN_LIMIT	    = 0x57
VIN_UV_WARN_LIMIT	    = 0x58
PIN_OP_WARN_LIMIT	    = 0x6B
STATUS_BYTE		        = 0x7B
STATUS_WORD		        = 0x79
STATUS_IOUT		        = 0x7B
STATUS_INPUT		    = 0x7C
STATUS_CML		        = 0x7E
STATUS_MFR_SPECIFIC	    = 0x80
READ_EIN		        = 0x86
READ_VIN		        = 0x88
READ_IN			        = 0x89
READ_VOUT		        = 0x8B
READ_IOUT		        = 0x8C
READ_POUT		        = 0x96
READ_PIN		        = 0x97
MFR_ID			        = 0x99
MFR_MODEL		        = 0x9A
MFR_REVISION		    = 0x9B
MFR_ADC_CONFIG		    = 0xD0
MFR_READ_VSHUNT		    = 0xD1
MFR_ALERT_MASK		    = 0xD2
MFR_CALIBRATION		    = 0xD4
MFR_DEVICE_CONFIG	    = 0xD5
CLEAR_EIN		        = 0xD6
TI_MFR_ID		        = 0xE0
TI_MFR_MODEL		    = 0xE1
TI_MFR_REVISION         = 0xE2