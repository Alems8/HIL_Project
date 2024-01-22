import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import * 
from PyQt5.QtGui import *
import ctypes

abs_path = r"C:/Users/aleal/OneDrive/Documenti/Uni/GRENOBLE/HIL/ensimag_postwimp-main/ensimag_postwimp-main/optitrack"
dll_path = abs_path + r"\optitrack_sc.dll"
cLib = ctypes.CDLL(dll_path)
start_connection = cLib.start_connection
track_finger = cLib.get_point


class CalibrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        screen_geometry = QDesktopWidget().screenGeometry()

        # screen size
        self.x_screen_delta = screen_geometry.width()
        self.y_screen_delta = screen_geometry.height()

        # target 1 and 2 position
        self.target_1 = { 
            "x" : screen_geometry.topLeft().x(), 
            "y" : screen_geometry.topLeft().y(),
        }
        self.target_2 = {
            "x" : screen_geometry.bottomRight().x() - 50,
            "y" : screen_geometry.bottomRight().y() - int(50*1.41),
        }
        
        self.target_delta_x = self.target_1["x"] - self.target_2["x"]
        self.target_delta_y = self.target_1["y"] - self.target_2["y"]

        self.init_ui()

    def init_ui(self):

        # Declaration
        btn1 = QPushButton('1', self)
        btn2 = QPushButton('2', self)
        
        # Names
        btn1.setObjectName("FIRST")
        btn1.setObjectName("SECOND")

        # Size
        btn_size = 50
        btn1.setFixedSize(btn_size, btn_size)
        btn2.setFixedSize(btn_size, btn_size)

        # Color
        btn1.setStyleSheet('background-color: red;')
        btn2.setStyleSheet('background-color: red;')

        # Position
        btn1.move(self.target_1["x"], self.target_1["y"] )
        btn2.move(self.target_2["x"], self.target_2["y"] )

        # Action on click
        btn1.clicked.connect(self.on_click)
        btn2.clicked.connect(self.on_click)

        # Impostazione delle dimensioni della finestra pari a quelle dello schermo
        self.setGeometry(0, 0, self.x_screen_delta, self.y_screen_delta)

        # Impostazione del titolo della finestra
        self.setWindowTitle('Calibration')

    def on_click(self):
        pass
    
    def user_feedback(self,msg : str):
        message_box = QMessageBox()
        message_box.setWindowTitle("Coordinates Acquired!")
        message_box.setText(msg)

        # Message box immage
        icon_path = abs_path + r"\done.png"
        icon = QIcon(icon_path)
        message_box.setWindowIcon(icon)

        # At most 3 second on the screen
        box_timer = QTimer(self)
        box_timer.setSingleShot(True)
        box_timer.timeout.connect(lambda : message_box.close())

        # Show box and timer
        message_box.show()
        box_timer.start(3000)
    
def calibrate() -> dict : 

    # User coordinates
    min = { "x" : 0, "y" : 0}
    max = { "x" : 0, "y" : 0}
    
    # start connection
    start_connection.argtypes = [ctypes.c_char_p]
    ip_address =b"169.254.210.95"
    start_connection(ip_address)

    calwin = CalibrationWindow()
    calwin.showMaximized()
    # acquisition buffer
    points = (ctypes.c_float * 3)()

    # Firs point acquisition
    click = {"press" : False, "release" : False}
    while not click["press"] :
        QApplication.processEvents()
        track_finger(points)
        click["press"] = ( points[2] == 1 ) 

    # Points acquired on the first click.
    min["x"] = points[0]; min["y"] = points[1]

    # Waiting for release
    while not click["release"]:
        QApplication.processEvents()
        track_finger(points)
        click["release"] = ( points[2] == 0 )
    
    print(f"Point one acquired: ", min)

    # SECOND point acquisition
    click = {"press" : False, "release" : False}
    while not click["press"] :
        QApplication.processEvents()
        track_finger(points)
        click["press"] = ( points[2] == 1 ) 

    # Points acquired on the first click.
    max["x"] = points[0]; max["y"] = points[1]

    # Waiting for release
    while not click["release"]:
        QApplication.processEvents()
        track_finger(points)
        click["release"] = ( points[2] == 0 )

    print("Point two acquired: ", max)

    # # Calibrate
    # user_range_x = (calwin.x_screen_delta / calwin.target_delta_x)*(user_p1["x"]- user_p2["x"])
    # user_range_y = (calwin.y_screen_delta / calwin.target_delta_y)*(user_p1["x"]- user_p2["y"])
    # user_x_min = user_p1["x"] - (user_range_x / calwin.x_screen_delta)*calwin.target_1["x"]
    # user_y_min = user_p1["y"] - (user_range_y / calwin.y_screen_delta)*calwin.target_1["y"]
    
    return min["x"], min["y"], max["x"], max["y"]
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # open interface
    calibrate()
    # chek no wait --> print("Arriva qui")
    sys.exit(app.exec_())
