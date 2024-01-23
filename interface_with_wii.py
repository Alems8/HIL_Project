import random
import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from evdev import InputDevice, ecodes
import evdev
import time
import pandas as pd
import pyautogui

abs_path = r"/home/alessio/HIL/WII/HIL_Project"

def find_wiimote():
    devices = [InputDevice(fn) for fn in evdev.list_devices()]
    for device in devices:
        if "Nintendo" in device.name:
            return device
    return None

class WiiThread(QThread):
    wii_button_pressed = pyqtSignal(str)

    def __init__(self, device):
        super().__init__()
        self.device = device

    def run(self):
        for event in self.device.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:
                if event.code == ecodes.KEY_UP:
                    self.wii_button_pressed.emit("UP")
                elif event.code == ecodes.KEY_DOWN:
                    self.wii_button_pressed.emit("DOWN")
                elif event.code == ecodes.KEY_LEFT:
                    self.wii_button_pressed.emit("LEFT")
                elif event.code == ecodes.KEY_RIGHT:
                    self.wii_button_pressed.emit("RIGHT")
                elif event.code == ecodes.BTN_A:
                    self.wii_button_pressed.emit("A")
                elif event.code == ecodes.BTN_B:
                    self.wii_button_pressed.emit("B")

class MyWindow(QWidget):
    def __init__(self, wiimote):
        super().__init__()

        self.initUI()

        # Creare un thread per gestire gli eventi del controller Wii
        self.wii_thread = WiiThread(wiimote)
        self.wii_thread.wii_button_pressed.connect(self.handle_wii_button)
        self.wii_thread.start()

        self.current_focus = "main_buttons"  # "main_buttons" o "sidebar"

        self.current_button_index = 0  # Indice per i pulsanti principali
        self.sidebar_button_index = 0  # Indice per i pulsanti della barra laterale


    def initUI(self):
        main_layout = QHBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.sidebar = QWidget()
        self.buttons_widget = QWidget()
        
        v_layout = QVBoxLayout(self.sidebar)

        self.grid_layout = QGridLayout(self.buttons_widget)
        self.msgbox_open=False
        self.testStarted = False
        self.start_time = 0
        self.it=0
        self.target_list = ['Netflix','Chili TV','HBOMax','home','Prime Video','profile','settings','Live TV','NBA TV', 'Rakuten TV', 'search', 'TF1','settings','home','Bein Sports','Apple Music','Juventus TV','Eurosport','Fox Sport', 'search', 'SKY','Youtube','RAI Play','Eurosport','Disney+','Chili TV','DAZN','profile','Fox Sport','Netflix']
        self.DataFrame = pd.DataFrame(columns=['Time'])
        self.DataFrame_list = []

        # Creating buttons
        num_rows = 4
        num_cols = 5
        num_buttons = num_rows * num_cols
        self.buttons = [QPushButton() for _ in range(num_buttons)]
        self.buttons_sidebar = [QPushButton() for j in range(4)]

        images_path = abs_path + r"/images/main"
        sidebar_images_path = abs_path + r"/images/sidebar"

        # Get a list of all files in the image folder
        image_files = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]
        sidebar_imgs = [p for p in os.listdir(sidebar_images_path) if os.path.isfile(os.path.join(sidebar_images_path, p))]

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
            
            v_layout.addWidget(side_but)
            
        
        v_layout.addStretch()
        self.sidebar.setLayout(v_layout)

        # Adding buttons to the grid layout
        for i, button in enumerate(self.buttons):
            # Icon set-up
            random_image = random.choice(image_files)
            image_path = os.path.join(images_path, random_image)

            icon = QIcon(image_path)
            button.setIcon(icon)

            # Create a widget to contain both the button and the label
            container_widget = QWidget()

            # Layout for the container widget
            container_layout = QVBoxLayout(container_widget)
            container_layout.addWidget(button)

            # Add label below the button
            label = QLabel(button.objectName())
            label.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(label)


            icon_size = QSize(button.size().width() // 3, button.size().height() // 3)
            button.setIconSize(icon_size)
            image_files.remove(random_image)

            # Button's name
            button.setObjectName(random_image.split('.')[0])
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            # Button's size
            button.setMinimumSize(int(QDesktopWidget().screenGeometry().width() / num_cols) - 50,
                                  int(QDesktopWidget().screenGeometry().height() / num_rows) - 150)

            # Button's position
            row = i // num_cols
            col = i % num_cols

            # Adding button to the grid
            self.grid_layout.addWidget(button, row, col, Qt.AlignCenter)

        # Set initial focus on the first button
        self.current_button_index = 0
        self.buttons[self.current_button_index].setFocus()
        # Cambia il colore di sfondo del nuovo pulsante corrente
        self.buttons[self.current_button_index].setStyleSheet("background-color: blue;")

        # Add the grid layout to the main layout
        self.buttons_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidget(self.buttons_widget)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

        self.setWindowTitle('iTV')
        self.showMaximized()  # Show the window maximized


    def handle_wii_button(self, direction):
        if self.current_focus == "main_buttons":
            self.handle_main_buttons(direction)
        elif self.current_focus == "sidebar":
            self.handle_sidebar_buttons(direction)

    def handle_main_buttons(self, direction):
        if not self.msgbox_open:
            # Logica per i pulsanti principali

            # Rimuovi il focus dal pulsante corrente
            if self.current_button_index is not None:
                self.buttons[self.current_button_index].clearFocus()
                self.buttons[self.current_button_index].setStyleSheet("")

            num_cols = 5
            if direction == "UP" and self.current_button_index - num_cols >= 0:
                self.current_button_index -= num_cols
            elif direction == "DOWN" and self.current_button_index + num_cols < len(self.buttons):
                self.current_button_index += num_cols
            elif direction == "LEFT":
                if self.current_button_index % num_cols == 0:
                    # Se il cursore è nella prima colonna
                    # Imposta il focus sulla barra laterale
                    self.buttons_sidebar[0].setFocus()
                    self.current_button_index = None
                    # Imposta lo sfondo blu sul bottone della sidebar
                    self.buttons_sidebar[0].setStyleSheet("background-color: blue;")
                    self.current_focus = "sidebar"
                    return
                else:
                    self.current_button_index -= 1
            elif direction == "RIGHT" and self.current_button_index + 1 < len(self.buttons):
                self.current_button_index += 1

            # Imposta il focus sul nuovo pulsante corrente
            self.buttons[self.current_button_index].setFocus()
            self.buttons[self.current_button_index].setStyleSheet("background-color: blue;")

        # Mostra il tempo trascorso dall'ultima interazione quando viene premuto A
        if direction == "A":
            button_name = self.buttons[self.current_button_index].objectName()
            if not self.testStarted:
                if self.msgbox_open:
                    pyautogui.press('enter')
                    self.msgbox_open = False
                else:
                    box_timer = QTimer(self)
                    box_timer.setSingleShot(True)
                    message_box = QMessageBox()
                    message_box.setStandardButtons(message_box.Ok)
                    message_box.setIcon(message_box.Information)
                    message_box.setTextFormat(Qt.RichText)
                    message_box.setWindowTitle("Target Acquired!")
                    message_box.setText(f"<font size=24>You opened {button_name}")
                    message_box.show()
                    self.msgbox_open = True
                    box_timer.timeout.connect(lambda : message_box.close())
                    box_timer.start(10000)
            else:
                if self.msgbox_open:
                    pyautogui.press(['tab','enter'])
                    self.msgbox_open = False
                else:
                    print(button_name)
                    print(self.target_list[self.it])
                    if button_name == self.target_list[self.it]:
                        print('target acquired')
                        end_time = time.time() - self.start_time
                        self.DataFrame_list.append({'Time':end_time})
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
                            self.msgbox_open = True

                            for btn in self.buttons_sidebar:
                                btn.setEnabled(False)
                            for btn in self.buttons:
                                btn.setEnabled(False)

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
                            self.msgbox_open = True
                            box_timer.timeout.connect(lambda : message_box.close())
                            box_timer.start(10000)
                    else:
                        print('problemmmmmm')
            

            
    def handle_sidebar_buttons(self, direction):
        if not self.msgbox_open:
            # Logica per i pulsanti della barra laterale

            # Rimuovi il focus dal pulsante corrente
            if self.sidebar_button_index is not None:
                self.buttons_sidebar[self.sidebar_button_index].clearFocus()
                self.buttons_sidebar[self.sidebar_button_index].setStyleSheet("")
            
            # Numero di pulsanti nella barra laterale
            num_sidebar_buttons = len(self.buttons_sidebar)

            if direction == "UP":
                if self.sidebar_button_index >0:
                    self.sidebar_button_index = (self.sidebar_button_index - 1) % num_sidebar_buttons
                else:
                    self.sidebar_button_index = num_sidebar_buttons - 1

            elif direction == "DOWN":
                self.sidebar_button_index = (self.sidebar_button_index + 1) % num_sidebar_buttons
            elif direction == "RIGHT":
                # Torna ai pulsanti principali
                self.current_focus = "main_buttons"
                self.buttons[0].setFocus()
                self.buttons[0].setStyleSheet("background-color: blue;")
                self.current_button_index = 0
                return
            
            # Imposta il focus sul nuovo pulsante corrente
            self.buttons_sidebar[self.sidebar_button_index].setFocus()
            self.buttons_sidebar[self.sidebar_button_index].setStyleSheet("background-color: blue;")
                

        # Mostra il tempo trascorso dall'ultima interazione quando viene premuto A sulla barra laterale
        if direction == "A":

            button_name = self.buttons_sidebar[self.sidebar_button_index].objectName()
            if not self.testStarted:
                if self.msgbox_open:
                    pyautogui.press('enter')
                    self.msgbox_open = False
                else:
                    box_timer = QTimer(self)
                    box_timer.setSingleShot(True)
                    message_box = QMessageBox()
                    message_box.setStandardButtons(message_box.Ok)
                    message_box.setIcon(message_box.Information)
                    message_box.setTextFormat(Qt.RichText)
                    message_box.setWindowTitle("Target Acquired!")
                    message_box.setText(f"<font size=24>You opened {button_name}")
                    message_box.show()
                    self.msgbox_open = True
                    box_timer.timeout.connect(lambda : message_box.close())
                    box_timer.start(10000)
            else:
                if self.msgbox_open:
                    pyautogui.press('enter')
                    self.msgbox_open = False
                else:
                    print(button_name)
                    print(self.target_list[self.it])
                    if button_name == self.target_list[self.it]:
                        print('target acquired')
                        end_time = time.time() - self.start_time
                        self.DataFrame_list.append({'Time':end_time})
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
                            self.msgbox_open = True
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
            message_box.buttonClicked.connect(lambda:setattr(self, 'start_time',time.time()))
            message_box.buttonClicked.connect(lambda:print('Click OK!'))
            message_box.show()
            self.msgbox_open=True
            box_timer.timeout.connect(lambda : message_box.close())
            box_timer.start(15000)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    wiimote = find_wiimote()
    if not wiimote:
        print("No Wii controller found.")
        sys.exit()

    window = MyWindow(wiimote)
    sys.exit(app.exec_())
