from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                               QLabel, QListView, QProgressBar, QPushButton, QSizePolicy, QStackedWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 650)
        
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        
        # Main vertical layout
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Content Layout (Horizontal: Left list + Right panel)
        self.content_layout = QHBoxLayout()
        
        # Left side: Option list
        self.option_list = QListView(self.centralwidget)
        self.option_list.setObjectName(u"option_list")
        self.option_list.setFixedWidth(200)
        self.content_layout.addWidget(self.option_list)
        
        # Create a StackedWidget to toggle between the player and other views
        self.stacked_widget = QStackedWidget(self.centralwidget)
        self.stacked_widget.setObjectName(u"stacked_widget")
        
        self.content_layout.addWidget(self.stacked_widget)
        self.main_layout.addLayout(self.content_layout)
        
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"untitled overcomplicated rotational cd/vinyl player still on progress", None))

