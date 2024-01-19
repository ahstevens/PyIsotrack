import serial
from enum import Enum

class PolhemusData:
    px = py = pz = 0
    qx = qy = qz = 0
    qw = 1
    
    def __init__(self, name):
        self.name = name
    
    def set(self, px, py, pz, qx, qy, qz, qw):
        self.px = float(px)
        self.py = float(py)
        self.pz = float(pz)
        self.qx = float(qx)
        self.qy = float(qy)
        self.qz = float(qz)
        self.qw = float(qw)

class IsotrakCommands:
    def __init__(self):
        self.ALIGN_REF_FRAME					= 'A'
        self.ALIGN_REF_FRAME_RESET			= 'R'
        self.BORESIGHT						= 'B'
        self.UNBORESIGHT						= 'b'
        self.CONTINUOUS_PRINT_OUTPUT_ENABLE	= 'C'
        self.CONTINUOUS_PRINT_OUTPUT_DISABLE	= 'c'
        self.DIGITIZER_MODE_ENABLE			= 'Y'
        self.DIGITIZER_RUN_MODE_ENABLE		= 'e'
        self.DIGITIZER_POINT_MODE_ENABLE		= 'E'
        self.DIGITIZER_TRACK_MODE_SET		= 'i'
        self.DIGITIZER_TRACK_MODE_END		= chr(5)
        self.FORMAT_OUTPUT_ASCII				= 'F'
        self.FORMAT_OUTPUT_BINARY			= 'f'
        self.HEMI_OF_OPERATION				= 'H'
        self.DEFINE_INCREMENT				= 'I'
        self.QUIET_MODE_ENABLE				= 'K'
        self.QUIET_MODE_DISABLE				= 'm'
        self.ACTIVE_STATION_STATE			= 'l'
        self.DEFINE_TIP_OFFSETS				= 'N'
        self.OUTPUT_DATA_LIST				= 'O'
        self.OUTPUT_SINGLE_RECORD			= 'P'
        self.TRANS_MOUNTING_FRAME			= 'r'
        self.SYS_STATUS						= 'S'
        self.EXT_CONFIG						= 't'
        self.TRACKER_COMMANDS				= 'T'
        self.UNITS_IN						= 'U'
        self.UNITS_CM						= 'u'
        self.POS_OP_ENV						= 'V'
        self.ATT_FILTER_PARAMS				= 'v'
        self.POS_FILTER_PARAMS				= 'x'
        self.REINITIALIZE					= chr(25)
        self.COMPAT_MODE						= chr(4)
        self.SUSPEND_XMIT					= chr(19)
        self.RESUME_XMIT						= chr(17)
        self.CRLF							= chr(13) + chr(10)
    

class OutputCodes:
    def __init__(self):# OUTPUT FORMAT	| DESCRIPTION    
        self.SPACE = '0'			# A1			| ASCII space character
        self.CRLF = '1'			# A2			| ASCII carriage return, line feed pair
        self.XYZ = '2'			# 3(Sxxx.xx)	| x,y,z Cartesian coordinates of position
        self.XYZ_REL = '3'			# 3(Sxxx.xx)	| relative movement, x,y,z Cartesian coordinates of position; i.e., the difference in position from the last output. This item should only be selected if the specified station's Increment is = 0.0. See the "I" command
        self.EULER = '4'			# 3(Sxxx.xx)	| azimuth, elevation, roll Euler orientation angles
        self.COSX = '5'			# 3(Sx.xxxx)	| x-axis direction cosines
        self.COSY = '6'			# 3(Sx.xxxx)	| y-axis direction cosines
        self.COSZ = '7'			# 3(Sx.xxxx)	| z-axis direction cosines
        self.RAWX = '8'			#				| x-axis receiver data (factory use only)
        self.RAWY = '9'			#				| y-axis receiver data (factory use only)
        self.RAWZ = '10'			#				| z-axis receiver data (factory use only)
        self.QUAT = '11'			# 4(Sx.xxxx)	| orientation quaternion (components ordered wxyz)

class IsotrakServer:
    def __init__(self):
        self.port = '/dev/ttyUSB0'
        self.baudrate = 115200
        self.timeout = None # wait for EOL
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        self.rtscts = 0
        self.tracker = PolhemusData('Tracker1')
        self.ser = serial.Serial()
        self.outputcodes = OutputCodes()
        self.commands = IsotrakCommands()
                
    def connect(self):
        if not self.ser.is_open:
            self.ser.baudrate = self.baudrate
            self.ser.port = self.port
            self.ser.timeout = self.timeout
            self.ser.bytesize = self.bytesize
            self.ser.parity = self.parity
            self.ser.stopbits = self.stopbits
            self.ser.rtscts = self.rtscts
            try:
                self.ser.open()
            except (serial.serialutil.SerialException) as e:
                print(e)
        return self.ser.is_open

    def disconnect(self):
        if self.ser.is_open:
            self.ser.close()

    def initialize(self):
        cmd = self.commands.CONTINUOUS_PRINT_OUTPUT_ENABLE
        cmd = cmd + self.commands.UNITS_CM
        cmd += self.commands.OUTPUT_DATA_LIST
        cmd += self.outputcodes.XYZ + ',' + self.outputcodes.QUAT + ',' + self.outputcodes.CRLF
        cmd += self.commands.CRLF

        if self.ser.is_open:
            self.ser.write(cmd.encode('UTF-8')) # set output to position and quaternion
            
    def update(self):
        self.ser.write(self.commands.OUTPUT_SINGLE_RECORD.encode('UTF-8'))
        data = self.ser.readline()
        if data == b'' or len(data) != 54:
            return False
            
        self.tracker.set(data[3:10], data[10:17], data[17:24],
                    data[24:31], data[31:38], data[38:45], data[45:52])
        
        return True

    def print(self):
        fmt = "{0:0.2f}"
        output = self.tracker.name + ": ("
        output += fmt.format(self.tracker.px) + ", "
        output += fmt.format(self.tracker.py) + ", "
        output += fmt.format(self.tracker.pz)
        output += ") | ("
        output += fmt.format(self.tracker.qx) + ", "
        output += fmt.format(self.tracker.qy) + ", "
        output += fmt.format(self.tracker.qz) + ", "
        output += fmt.format(self.tracker.qw)
        output += ")"
        print(output)

    def getTrackerData(self):
        fmt1 = "{0:0.2f}"
        fmt2 = "{0:0.4f}"
        output = self.tracker.name + ","
        output += fmt1.format(self.tracker.px) + ","
        output += fmt1.format(self.tracker.py) + ","
        output += fmt1.format(self.tracker.pz) + ","
        output += fmt2.format(self.tracker.qx) + ","
        output += fmt2.format(self.tracker.qy) + ","
        output += fmt2.format(self.tracker.qz) + ","
        output += fmt2.format(self.tracker.qw)
        return output

            
    def createCommands(self):
        self.commands = {
            "Alignment Reference Frame" : "A",			# Get: A1<>
            											# Set: A1,[Ox],[Oy],[Oz],[Xx],[Xy],[Xz],[Yx],[Yy],[Yz]<>
            "Reset Alignment Reference Frame" : "R",	# R1<>
            "Boresight" : "B",							# Bstation<>
            "Unboresight" : "b",						# bstation<>
            "Continuous Print Output" : "C",
            "Disable Continuous Printing" : "c",
            "Enable Digitizer Mode" : "Y",
            "Enable Run Digitizer Mode" : "e",
            "Enable Point Digitizer Mode" : "E",
            "Set Track Digitizer Mode" : "i",
            "Enable ASCII Output Format" : "F",
            "Enable Binary Output Format" : "f",
            "Hemisphere of Operation" : "H",			# Get: H<>
            											# Set: Hstation,[p1],[p2],[p3]<>
            "Define Increment" : "I",					# Get: I<>
            											# Set: I[distance]<>
            "Enable Quiet Mode" : "K",
            "Active Station State" : "l",				# Get: l<>
            											# Set: lstation<>
            "Disable Quiet Mode" : "m",
            "Define Tip Offsets" : "N",					# Get: N<>
            											# Set: N,xoff,yoff,zoff<>
            "Output Data List" : "O",					# O[code#],[code#],...,[code#]<>
            "Single Data Record Output" : "P",
            "Transmitter Mounting Frame" : "r",			# Get: r1,r<>
            											# Set: r1,r,[A],[E],[R]<>
            "System Status Record" : "S",
            "Extended Configuration" : "t",
            "Tracker Commands" : "T",
            "English Conversion Units" : "U",
            "Metric Conversion Units" : "u",
            "Position Operational Envelope" : "V",		# Get: Vs<>
            											# Set: Vs,[xmax],[ymax],[zmax],[xmin],[ymin],[zmin]<>
            "Attitude Filter Parameters" : "v",			# Get: v<>
            											# Set: v[F],[FLOW],[FHIGH],[FACTOR]<>
            "Position Filter Parameters" : "x",			# Get: x<>
            											# Set: x[F],[FLOW],[FHIGH],[FACTOR]<>
            "Reinitialize System" : chr(25),				# Ctrl-Y
            "Compatibility Mode" : chr(4),				# Ctrl-D
            "End Track Mode" : chr(5),					# Ctrl-E
            "Suspend Data Transmission" : chr(19),		# Ctrl-S
            "Resume Data Transmission" : chr(17)		# Ctrl-Q
        }
