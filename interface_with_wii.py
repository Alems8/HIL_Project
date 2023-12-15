import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QPushButton,
    QMessageBox,
    QDesktopWidget,
    QGridLayout,
    QSizePolicy
)
from PyQt5.QtCore import QThread, pyqtSignal, QElapsedTimer
from evdev import InputDevice, ecodes, list_devices
import time
import evdev

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

        # Inizializza il cronometro all'avvio dell'app
        self.elapsed_timer = QElapsedTimer()
        self.elapsed_timer.start()

    def initUI(self):
        main_layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        buttons_widget = QWidget()
        self.grid_layout = QGridLayout(buttons_widget)

        # Creating buttons
        self.buttons = [QPushButton(f'Button {i+1}') for i in range(12)]

        # Adding buttons to the grid layout
        for i, button in enumerate(self.buttons):
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            button.setMinimumSize(int(QDesktopWidget().screenGeometry().width()/3)-15, int(QDesktopWidget().screenGeometry().height()/2)-100)
            row = i // 6
            col = i % 6
            self.grid_layout.addWidget(button, row, col)

        # Set initial focus on the first button
        self.current_button_index = 0
        self.buttons[self.current_button_index].setFocus()
        # Cambia il colore di sfondo del nuovo pulsante corrente
        self.buttons[self.current_button_index].setStyleSheet("background-color: blue;")

        # Add the grid layout to the main layout
        buttons_widget.setLayout(self.grid_layout)
        self.scroll_area.setWidget(buttons_widget)

        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

        self.setWindowTitle('Grid of Buttons')
        self.showMaximized()  # Show the window maximized

    def handle_wii_button(self, direction):
        # Rimuovi il focus dal pulsante corrente
        self.buttons[self.current_button_index].clearFocus()

        # Cambia il colore di sfondo del pulsante corrente
        self.buttons[self.current_button_index].setStyleSheet("")

        # Imposta l'indice del pulsante corrente dopo lo spostamento
        if direction == "UP" and self.current_button_index - 6 >= 0:
            self.current_button_index -= 6
        elif direction == "DOWN" and self.current_button_index + 6 < len(self.buttons):
            self.current_button_index += 6
        elif direction == "LEFT" and self.current_button_index - 1 >= 0:
            self.current_button_index -= 1
        elif direction == "RIGHT" and self.current_button_index + 1 < len(self.buttons):
            self.current_button_index += 1

        # Imposta il focus sul nuovo pulsante corrente
        self.buttons[self.current_button_index].setFocus()

        # Cambia il colore di sfondo del nuovo pulsante corrente
        self.buttons[self.current_button_index].setStyleSheet("background-color: blue;")

        # Mostra il tempo trascorso dall'ultima interazione quando viene premuto A
        if direction == "A":
            elapsed_time = self.elapsed_timer.elapsed() / 1000  # Converti in secondi
            QMessageBox.critical(None, "Interazione", f"You completed your task (selecting Button {self.current_button_index + 1}) in {elapsed_time:.2f} s.", QMessageBox.Retry | QMessageBox.Cancel)
            # Azzera il cronometro
            self.elapsed_timer.restart()
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    wiimote = find_wiimote()
    if not wiimote:
        print("No Wii controller found.")
        sys.exit()

    window = MyWindow(wiimote)
    sys.exit(app.exec_())
