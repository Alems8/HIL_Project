import sys
import ctypes
import random
import os
import pyautogui
import pandas as pd
import time
from calibration_ckeck import calibrate

abs_path = r"C:/Users/aleal/OneDrive/Documenti/Uni/GRENOBLE/HIL/ensimag_postwimp-main/ensimag_postwimp-main/optitrack"
dll_path = abs_path + r"\optitrack_sc.dll"
cLib = ctypes.CDLL(dll_path)
start_connection = cLib.start_connection


import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import ctypes
from PyQt5.QtTest import QTest

# x_min = -0.27
# x_max = 0.1
# y_max = 0.35
# y_min = 0.55

class MyWindow(QWidget):

    show_notification_signal = pyqtSignal(str)
    
    def __init__(self, x_min, y_min, x_max, y_max):
        
        super().__init__()
        self.x_min, self.y_min, self.x_max, self.y_max = x_min, y_min, x_max, y_max
        start_connection.argtypes = [ctypes.c_char_p]
        ip_address =b"169.254.210.95"
        start_connection(ip_address)
        self.track_finger = cLib.get_point
        self.testStarted=False
        self.press = False
        self.start_pos = 0
        self.start_time = 0
        self.it=0
        self.target_list = ['Netflix','Chili TV','HBOMax','home','Prime Video','profile','settings','Live TV','NBA TV', 'Rakuten TV', 'search', 'TF1','settings','home','Bein Sports','Apple Music','Juventus TV','Eurosport','Fox Sport', 'search', 'SKY','Youtube','RAI Play','Eurosport','Disney+','Chili TV','DAZN','profile','Fox Sport','Netflix']
        self.DataFrame = pd.DataFrame(columns=['Start position','End postion', 'Time'])
        self.DataFrame_list = []
        pyautogui.FAILSAFE = False

        # Screen range, used to map optitrack 
        self.range_x=QDesktopWidget().screenGeometry().width()
        self.range_y= QDesktopWidget().screenGeometry().height()

        main_layout=QHBoxLayout()
        
        self.sidebar = QWidget()
        self.buttons_widget = QWidget()
        
        v_layout = QVBoxLayout(self.sidebar)
        grid_layout = QGridLayout(self.buttons_widget)

        # Creating buttons
        num_rows = 4
        num_cols = 5
        num_buttons = num_rows * num_cols
        self.buttons = [QPushButton() for _ in range(num_buttons)]
        self.buttons_sidebar = [QPushButton() for j in range(4)]
        
        

        main_images_path = abs_path + r"\images\main"
        sidebar_images_path = abs_path + r"\images\sidebar"

        # Get a list of all files in the image folder
        sidebar_imgs = [p for p in os.listdir(sidebar_images_path) if os.path.isfile(os.path.join(sidebar_images_path, p))]
        image_files = [f for f in os.listdir(main_images_path) if os.path.isfile(os.path.join(main_images_path, f))]
        
        for i,side_but in enumerate(self.buttons_sidebar):
            
            image_path = os.path.join(sidebar_images_path, sidebar_imgs[i])

            # Button's name
            button_name = sidebar_imgs[i].split('.')[0] # remove extention
            side_but.setObjectName(button_name)

            # Insert icon
            icon = QIcon(image_path)
            side_but.setIcon(icon)

            # Setting icon size
            icon_size = QSize(side_but.size().width() // 11, side_but.size().height() // 11)
            side_but.setIconSize(icon_size)
            
            
            side_but.setObjectName(button_name)
            
            side_but.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            side_but.setMinimumSize(int(QDesktopWidget().screenGeometry().width()/40), int(QDesktopWidget().screenGeometry().height()/20))

            side_but.clicked.connect(self.button_clicked)
            
            v_layout.addWidget(side_but)
            
        
        v_layout.addStretch()
        self.sidebar.setLayout(v_layout)

        # Adding buttons to the grid layout
        for i, button in enumerate(self.buttons):

            # Icon set-up
            random_image = random.choice(image_files)
            image_path = os.path.join(main_images_path, random_image)

            # Button's name
            button_name = random_image.split('.')[0] # remove extention
            button.setObjectName(button_name)

            # Insert icon
            icon = QIcon(image_path)
            button.setIcon(icon)

            # Setting icon size
            icon_size = QSize(button.size().width() // 3, button.size().height() // 3)
            button.setIconSize(icon_size)
            image_files.remove(random_image)


            # Button's size
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            button.setMinimumSize(int(QDesktopWidget().screenGeometry().width()/num_cols)-50, int(QDesktopWidget().screenGeometry().height()/num_rows)-150)

            # Button's action
            button.clicked.connect(self.button_clicked)
            

            # Button's position
            row = i // num_cols
            col = i % num_cols

            # Adding button to the grid
            grid_layout.addWidget(button, row, col)
        
        
        # Add the grid layout to the main layout
        self.buttons_widget.setLayout(grid_layout)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.buttons_widget)


        # Connessione del timer all'aggiornamento
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(1)

        self.setLayout(main_layout)
        self.setWindowTitle('iTV menu')
        self.showMaximized()

    def update_position(self):
        # Cursor control
        points = (ctypes.c_float * 3)()
        self.track_finger(points)
        x, y, click = points
    
        cursor = QCursor()
        x_screen = ( (x - self.x_min) * self.range_x ) / ( self.x_max - self.x_min)
        y_screen = ( (y - self.y_min) * self.range_y ) / (self.y_max - self.y_min)
        cursor.setPos(int(x_screen), int(y_screen))


        if click and not self.press:
            self.press = True
            pyautogui.mouseDown()

        if not click and self.press:
            self.press = False
            pyautogui.mouseUp()

        
    def button_clicked(self):
        button_name = self.sender().objectName()
        if not self.testStarted:
            box_timer = QTimer(self)
            box_timer.setSingleShot(True)
            message_box = QMessageBox()
            message_box.setWindowTitle("Target Acquired!")
            message_box.setText(f"You opened {button_name}")
            message_box.show()
            box_timer.timeout.connect(lambda : message_box.close())
            box_timer.start(5000)
        else:
            print(button_name)
            print(self.target_list[self.it])
            if button_name == self.target_list[self.it]:
                print('target acquired')
                end_pos = QCursor.pos()
                end_time = time.time() - self.start_time
                self.DataFrame_list.append({'Start position':(self.start_pos.x(),self.start_pos.y()),'End postion':(end_pos.x(), end_pos.y()), 'Time':end_time})
                self.it+=1
                if self.it == len(self.target_list):
                    box_timer = QTimer(self)
                    box_timer.setSingleShot(True)
                    self.testStarted = False
                    message_box = QMessageBox()
                    message_box.setStandardButtons(message_box.Ok)
                    message_box.setIcon(message_box.Information)
                    message_box.setTextFormat(Qt.RichText)
                    message_box.setWindowTitle("Target Acquired!")
                    message_box.setText(f"<font size=24>This is the end of the test.<br> Thank you for your partecipation!</font>")
                    message_box.show()
                    print(self.DataFrame_list)
                    self.DataFrame = pd.concat([self.DataFrame, pd.DataFrame(self.DataFrame_list)], ignore_index=True)
                    self.DataFrame.to_excel("Results.xlsx")
                    box_timer.timeout.connect(lambda : message_box.close())
                    box_timer.start(10000)
                else:
                    box_timer = QTimer(self)
                    box_timer.setSingleShot(True)
                    print('next_target')
                    message_box = QMessageBox()
                    message_box.setTextFormat(Qt.RichText)
                    message_box.setStandardButtons(message_box.Ok)
                    message_box.setIcon(message_box.Information)
                    message_box.setWindowTitle("Target Acquired!")
                    message_box.setText(f"<font size=24>You opened {button_name}. <br> Your next target is {self.target_list[self.it]}<br> Press OK to start</font>")
                    message_box.buttonClicked.connect(lambda:setattr(self, 'start_pos', QCursor.pos()))
                    message_box.buttonClicked.connect(lambda:setattr(self, 'start_time',time.time()))
                    message_box.show()
                    box_timer.timeout.connect(lambda : message_box.close())
                    box_timer.start(10000)
            else:
                print('problemmmmmm')
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_A:
            self.testStarted=True
            box_timer = QTimer(self)
            box_timer.setSingleShot(True)
            message_box = QMessageBox()
            message_box.setStandardButtons(message_box.Ok)
            message_box.setIcon(message_box.Information)
            message_box.setTextFormat(Qt.RichText)
            message_box.setWindowTitle("Start of the Test")
            message_box.setText(f"<font size=24>Click on Netflix Icon. <br>Press OK to start</font>")
            message_box.buttonClicked.connect(lambda:setattr(self, 'start_pos', QCursor.pos()))
            message_box.buttonClicked.connect(lambda:setattr(self, 'start_time',time.time()))
            message_box.buttonClicked.connect(lambda:print('Click OK!'))
            message_box.show()
            box_timer.timeout.connect(lambda : message_box.close())
            box_timer.start(15000)
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow(*calibrate())
    sys.exit(app.exec_())
