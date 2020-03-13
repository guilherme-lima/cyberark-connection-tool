import os.path
import random
import sys
import yaml
import subprocess
from os import path
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Window(QMainWindow):
    home = os.path.dirname(os.path.realpath(__file__))

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remote CyberArk Connection")
        self.setWindowIcon(QIcon("cyberark.ico"))
        self.table_widget = TableWidget(self)
        self.setCentralWidget(self.table_widget)
        self.update_data()

    def update_data(self):
        with open(os.path.join(self.home, 'conf', 'config.yaml'), 'r') as config:
            items = yaml.full_load(config)
            last_protocol_index = items.__getitem__("lastProtocolIndex")
            last_protocol_index = (last_protocol_index, 1)[last_protocol_index is None]
            last_account = items.__getitem__("lastAccount")
            last_host = items.__getitem__("lastHost")
        self.table_widget.protocol_combo.setCurrentIndex(last_protocol_index)
        self.table_widget.account_line_edit.setText(last_account)
        self.table_widget.host_line_edit.setText(last_host)

    def closeEvent(self, event):
        with open(os.path.join(self.home, 'conf', 'config.yaml'), 'r') as config:
            vault_servers = yaml.full_load(config).get("vaultServers")
        last_protocol_index = self.table_widget.protocol_combo.currentIndex()
        last_account = self.table_widget.account_line_edit.text()
        last_host = self.table_widget.host_line_edit.text()
        new_config = {'lastProtocolIndex': last_protocol_index, 'lastAccount': last_account, 'lastHost': last_host,
                      'vaultServers': vault_servers}
        with open(os.path.join(self.home, 'conf', 'config.yaml'), 'w') as old_config:
            yaml.dump(new_config, old_config)


class TableWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.home = parent.home
        self.hostFilePath = os.path.join(self.home, 'conf', 'hosts')
        self.layout = QVBoxLayout(self)

        # Init screen
        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.config_tab = QWidget()

        # Add tabs
        self.tabs.addTab(self.main_tab, "Main")
        self.tabs.addTab(self.config_tab, "Config")

        # Connect button
        self.connect_button = QPushButton('Connect')
        self.connect_button.setToolTip('Click to connect')
        self.connect_button.clicked.connect(lambda: self.connect())

        # Erase button
        self.erase_button = QPushButton('⌫')
        self.erase_button.clicked.connect(lambda: self.erase())

        # Host line edit
        layout = QFormLayout()
        layout.addWidget(self.erase_button)
        layout.setContentsMargins(150, 0, 0, 0)

        self.host_line_edit = QLineEdit()
        self.completer = QCompleter(self.read_hosts_from_file())
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.host_line_edit.setCompleter(self.completer)
        self.host_line_edit.setMinimumWidth(200)
        self.host_line_edit.setPlaceholderText("hostname")
        self.host_line_edit.returnPressed.connect(lambda: self.connect())
        self.host_line_edit.setLayout(layout)

        # Account line edit
        self.account_line_edit = QLineEdit()
        self.account_line_edit.setPlaceholderText("username@address")
        self.account_line_edit.setMinimumWidth(200)
        self.account_line_edit.returnPressed.connect(lambda: self.connect())

        # Protocol combo box
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItem("SSH")
        self.protocol_combo.addItem("RDP")

        # MainTab form layout
        main_form_layout = QFormLayout()
        main_form_layout.addRow(QLabel("Protocol:"), self.protocol_combo)
        main_form_layout.addRow(QLabel("Account:"), self.account_line_edit)
        main_form_layout.addRow(QLabel("Host:"), self.host_line_edit)
        main_form_layout.addRow(self.connect_button)

        # Add main tab layout
        self.main_tab.setLayout(main_form_layout)

        # Width line edit
        self.width_line_edit = QLineEdit()
        self.width_line_edit.setPlaceholderText("1024")

        # Height line edit
        self.height_line_edit = QLineEdit()
        self.height_line_edit.setPlaceholderText("768")

        # ConfigTab form layout
        config_form_layout = QFormLayout()
        config_form_layout.addRow(QLabel("Width:"), self.width_line_edit)
        config_form_layout.addRow(QLabel("Height:"), self.height_line_edit)

        # Add config tab layout
        self.config_tab.setLayout(config_form_layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.host_line_edit.setFocus()

    def connect(self):
        host: str = self.host_line_edit.text().upper()
        if host:
            self.add_host_to_file(host)
            action = Action(self)
            action.command_callback()

    def erase(self):
        host: str = self.host_line_edit.text().upper()
        if host:
            with open(self.hostFilePath, 'r') as file_stream:
                lines = file_stream.readlines()
            with open(self.hostFilePath, 'w') as file_stream:
                for line in lines:
                    if line.rstrip() != host:
                        file_stream.write(line)
        self.refresh_completer()
        self.host_line_edit.clear()

    def add_host_to_file(self, host):
        access_type = ('x', 'a')[path.exists(self.hostFilePath)]
        with open(self.hostFilePath, 'r') as file_stream:
            for line in file_stream:
                if line.rstrip() == host:
                    return [None]

        file_stream = open(self.hostFilePath, access_type)
        file_stream.write("\n%s" % host)
        file_stream.close()
        self.refresh_completer()

    def refresh_completer(self):
        self.completer = QCompleter(self.read_hosts_from_file())
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.host_line_edit.setCompleter(self.completer)

    def read_hosts_from_file(self):
        if path.exists(self.hostFilePath):
            return [line.rstrip('\n') for line in open(self.hostFilePath)]
        return [None]


class Action:

    def __init__(self, parent):
        self.home = parent.home
        self.account = parent.account_line_edit.text()
        self.protocol = parent.protocol_combo.currentText()
        self.host = parent.host_line_edit.text()
        self.width = parent.width_line_edit.text();
        self.height = parent.height_line_edit.text();
        with open(os.path.join(self.home, 'conf', 'config.yaml'), 'r') as config:
            items = yaml.full_load(config)
            vault_servers = items.__getitem__("vaultServers")
            self.vault_server = random.choice(vault_servers)

    def command_callback(self):
        source_file_name = os.path.join(self.home, 'conf', 'template.rdp')
        dest_file_name = os.path.join(self.home, 'conf', 'temp.rdp')
        with open(source_file_name) as fileRDP:
            new_text = fileRDP.read().replace('#HOSTNAME#', str(self.host))
            new_text = new_text.replace('#PROTOCOL#', str(self.protocol))
            new_text = new_text.replace('#ACCOUNT#', self.account)
            new_text = new_text.replace('#VAULTSERVER#', str(self.vault_server))
            screen_mode = 0
            if self.width and self.height:
                width = self.width
                height = self.height
                screen_mode = 1
            else:
                if self.protocol == "RDP":
                    width = 0
                    height = 0
                elif self.protocol == "SSH":
                    width = 1024
                    height = 768
                    screen_mode = 1
                else:
                    width = 0
                    height = 0
            new_text = new_text.replace('#WIDTH#', str(width))
            new_text = new_text.replace('#HEIGHT#', str(height))
            new_text = new_text.replace('#SCREENMODE#', str(screen_mode))
        with open(dest_file_name, "w") as f:
            f.write(new_text)
        if sys.platform == "win32":
            subprocess.Popen('start ' + dest_file_name, shell=True)
        else:
            subprocess.Popen('open ' + dest_file_name, shell=True)


root = QApplication([])
app = Window()
app.show()
sys.exit(root.exec_())
