import os
import json
import logging
from logging.handlers import RotatingFileHandler

import numpy

from PySide6.QtCore import QSettings, Slot, QSize, QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSpacerItem,
    QSizePolicy, QGridLayout, QComboBox,
    QDoubleSpinBox, QMenuBar, QMenu, QMessageBox, QApplication,
    QStatusBar
)

from mywidgets import FovDisplay, FNumberBar, DofBar   

__version__ = '1.0.0'

APPDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

# Log
logger = logging.getLogger('MyLens')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%d/%m/%Y %H:%M:%S')
# Handler vers fichier :
file_handler = RotatingFileHandler(os.path.join(APPDIR, 'activity.log'), 'a', 1000000, 1, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
# Handler vers console :
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

try:
    with open('constants.json', 'rt', encoding='utf-8') as f:
        json_data = json.load(f)
        SENSOR_SIZES = json_data['SENSOR_SIZES']
        LENS_FOCALS = json_data['LENS_FOCALS']
except Exception as e:
    logger.error(str(e))
    raise


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initUi()
        self._sensor_size = (1.0, 1.0)
        self.set_confusion_dict()
        self.readSettings()
        self.on_sensor_changed(self.combo_sensors.currentText())
        self.set_confusion_dict()

    def initUi(self):
        self.setWindowTitle('Lenses')
        self.setGeometry(100, 100, 800, 480)


        centralwidget = QWidget(self)
        hLayout_MainWindow = QHBoxLayout(centralwidget)
        
        # ---------------------------------------------
        # Page principale
        # ---------------------------------------------

        main_page = QWidget()
        vLayout_main = QVBoxLayout(main_page)

        gLayout_camera = QGridLayout()
        gLayout_camera.setColumnStretch(0, 2)
        gLayout_camera.setColumnStretch(1, 2)
        gLayout_camera.setColumnStretch(2, 1)

        label1 = QLabel('Caméra/capteur :', main_page)
        gLayout_camera.addWidget(label1, 0, 0)
        self.combo_sensors = QComboBox(main_page)
        self.combo_sensors.addItems(SENSOR_SIZES.keys())
        self.combo_sensors.currentTextChanged.connect(self.on_sensor_changed)
        gLayout_camera.addWidget(self.combo_sensors, 1, 0)

        label2 = QLabel('Objectif :', main_page)
        gLayout_camera.addWidget(label2, 0, 1)
        self.combo_lenses = QComboBox(main_page)
        self.combo_lenses.addItems(LENS_FOCALS.keys())
        self.combo_lenses.currentTextChanged.connect(self.on_lens_changed)
        gLayout_camera.addWidget(self.combo_lenses, 1, 1)

        label3 = QLabel('Distance focale :', main_page)
        gLayout_camera.addWidget(label3, 0, 2)
        # self.focal_spin = QSpinBox(main_page)
        self.focal_spin = QDoubleSpinBox(main_page)
        self.focal_spin.setRange(1.0, 1000.0)
        self.focal_spin.setSuffix(' mm')
        self.focal_spin.setDecimals(1),
        self.focal_spin.valueChanged.connect(self.on_focal_changed)
        gLayout_camera.addWidget(self.focal_spin, 1, 2)

        vLayout_main.addLayout(gLayout_camera)

        gLayout_confusion = QGridLayout()
        gLayout_confusion.setColumnStretch(0, 2)
        gLayout_confusion.setColumnStretch(1, 1)
        gLayout_confusion.setColumnStretch(2, 2)

        label4 = QLabel('Cercle de confusion :', main_page)
        gLayout_confusion.addWidget(label4, 0, 0)
        self.combo_confusions = QComboBox(main_page)
        self.combo_confusions.addItems(('Photo numérique', 'Zeiss', 'Personnalisé...'))
        self.combo_confusions.currentTextChanged.connect(self.on_confusion_changed)
        gLayout_confusion.addWidget(self.combo_confusions, 1, 0)

        label5 = QLabel('Taille :', main_page)
        gLayout_confusion.addWidget(label5, 0, 1)
        self.confusion_spin = QDoubleSpinBox(main_page)
        self.confusion_spin.setRange(0.1, 100.0)
        self.confusion_spin.setSuffix(' μm')
        self.confusion_spin.setDecimals(1),
        self.confusion_spin.valueChanged.connect(self.on_confusion_spin_changed)
        gLayout_confusion.addWidget(self.confusion_spin, 1, 1)

        vLayout_main.addLayout(gLayout_confusion)

        label7 = QLabel('Distance de mise au point :', main_page)
        vLayout_main.addWidget(label7)
        self.dof_bar = DofBar(main_page)
        self.dof_bar.valueChanged.connect(self.on_distance_changed)
        vLayout_main.addWidget(self.dof_bar)
        self.label_dof = QLabel('→ profondeur de champ : ND', main_page)
        vLayout_main.addWidget(self.label_dof)

        label8 = QLabel('Ouverture :', main_page)
        vLayout_main.addWidget(label8)
        self.fnumber_bar = FNumberBar(main_page)
        self.fnumber_bar.valueChanged.connect(self.on_fnumber_changed)
        vLayout_main.addWidget(self.fnumber_bar)

        label6 = QLabel('Angle de champ :', main_page)
        vLayout_main.addWidget(label6)
        self.fov_view = FovDisplay(main_page)
        vLayout_main.addWidget(self.fov_view)

        vSpacer_helpBottom = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vLayout_main.addItem(vSpacer_helpBottom)

        hLayout_MainWindow.addWidget(main_page)
        self.setCentralWidget(centralwidget)

        # ---------------------------------------------
        # Menus
        # ---------------------------------------------
        menubar = QMenuBar(self)
        action_Quitter = QAction('&Quitter', self)
        action_Quitter.setShortcut('Ctrl+Q')
        action_Quitter.triggered.connect(self.close)
        
        menu_Fichier = QMenu('&Fichier', menubar)
        menu_Fichier.addAction(action_Quitter)

        menubar.addAction(menu_Fichier.menuAction())

        self.setMenuBar(menubar)

        # ---------------------------------------------
        # Barre d'état
        # ---------------------------------------------
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
        self.statusbar.hide()

    def _confusion_size(self, option='DIGITAL'):
        '''
        Retourne le diamètre du cercle de confusion pour une taille de capteur donnée.
        `sensor_size` : (l, h) en mm
        '''
        # Diagonale capteur (mm)
        w, h = self._sensor_size
        d = numpy.sqrt(w**2 + h**2)
        # Cercle de confusion (mm)
        if option.upper()=='ZEISS':
            c = d/1730 # Formule de Zeiss (plus sévère)
        else: # 'DIGITAL'
            c = d/1442 # Valeur en photo numérique
        return c # mm

    def set_confusion_dict(self): # , sensor_size
        c1 = self._confusion_size(option='DIGITAL')
        c2 = self._confusion_size(option='ZEISS')
        self._confusion_dict = {
            'Photo numérique ({:0.1f} μm)'.format(c1*1000): 'DIGITAL',
            'Zeiss ({:0.1f} μm)'.format(c2*1000): 'ZEISS',
            'Personnalisé...': 'CUSTOM'
        }
        keys = list(self._confusion_dict.keys())
        for i in range(self.combo_confusions.count()):
            self.combo_confusions.setItemText(i, keys[i])

    @staticmethod
    def format_distance_m(m, infinity_limit=1e6):
        abs_m = abs(m)
        if 0<=abs_m<0.001 and abs_m<infinity_limit:
            return ('{:0.3f} µm'.format(m*1e6))
        elif 0.001<=abs_m<0.01 and abs_m<infinity_limit:
            return ('{:0.3g} mm'.format(m*1000))
        elif 0.01<abs_m<1 and abs_m<infinity_limit:
            return ('{:0.3g} cm'.format(m*100))
        elif 1<=abs_m<1000 and abs_m<infinity_limit:
            return ('{:0.3g} m'.format(m))
        elif 1000<=abs_m<infinity_limit:
            return ('{:0.3g} km'.format(m/1000))
        else:
            return 'inf' if numpy.sign(m)==1 else '-inf'

    def _update_dof_string(self):
        dof = self.dof_bar.focusing_distance_far - self.dof_bar.focusing_distance_near
        formatted_dof = self.format_distance_m(dof, infinity_limit=999.5)
        if formatted_dof=='inf':
            text = '→ profondeur de champ : infinie'
        else:
            text = '→ profondeur de champ : {}'.format(formatted_dof)
        self.label_dof.setText(text)

    def set_focal_length(self, focal):
        self.fov_view.setFocalLength(focal)
        self.dof_bar.setFocalLength(focal)
        self._update_dof_string()
    
    def set_confusion_size(self, size):
        self.dof_bar.setConfusionSize(size)
        self._update_dof_string()
        self.fnumber_bar.setConfusionSize(size)

    @Slot(str)
    def on_sensor_changed(self, key):
        self._sensor_size = tuple(SENSOR_SIZES[key])
        self.fov_view.setSensorSize(self._sensor_size)
        self.dof_bar.setSensorSize(self._sensor_size)
        self._update_dof_string()
        self.fnumber_bar.setSensorSize(self._sensor_size)
        self.set_confusion_dict() # self._sensor_size
    
    @Slot(str)
    def on_confusion_changed(self, key):
        confusion_option = self._confusion_dict[key]
        if confusion_option=='CUSTOM':
            size = self.confusion_spin.value()/1000
        else:
            size = self._confusion_size(option=confusion_option)
            self.confusion_spin.blockSignals(True)
            self.confusion_spin.setValue(float(size*1000))
            self.confusion_spin.blockSignals(False)
        self.set_confusion_size(size)

    @Slot(float)
    def on_confusion_spin_changed(self, size):
        self.combo_confusions.blockSignals(True)
        self.combo_confusions.setCurrentIndex(int(len(self._confusion_dict)-1))
        self.combo_confusions.blockSignals(False)
        self.set_confusion_size(size/1000)

    @Slot(str)
    def on_lens_changed(self, key):
        if key=='' or key==list(LENS_FOCALS.keys())[-1]:
            focal = self.focal_spin.value()
        else:
            focal = LENS_FOCALS[key]
            self.focal_spin.blockSignals(True)
            self.focal_spin.setValue(float(focal))
            self.focal_spin.blockSignals(False)
        self.set_focal_length(focal)

    @Slot(float)
    def on_focal_changed(self, focal):
        self.combo_lenses.blockSignals(True)
        self.combo_lenses.setCurrentIndex(int(len(LENS_FOCALS)-1))
        self.combo_lenses.blockSignals(False)
        self.set_focal_length(focal)

    @Slot(int)
    def on_fnumber_changed(self, index):
        self.dof_bar.setFNumber(self.fnumber_bar.f_number)
        self._update_dof_string()

    @Slot(int)
    def on_distance_changed(self, index):
        self._update_dof_string()
        self.fov_view.setFocusDistance(self.dof_bar.focusing_distance)

    def closeEvent(self, event):
        msg = 'Êtes-vous sûr de vouloir quitter ?'
        icon = QMessageBox.Question
        
        closeMsg = QMessageBox(icon, 'Quitter', msg)
        closeMsg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        closeMsg.setDefaultButton(QMessageBox.No)
        closeMsg = closeMsg.exec()

        if closeMsg == QMessageBox.Yes:
            self.writeSettings()
            event.accept()
            logger.info('Fermeture de l’interface graphique.')
        else:
            event.ignore()

    def showEvent(self, event):
        logger.info('Affichage de l’interface graphique.')
        event.accept()

    def writeSettings(self):
        settings = QSettings('MyLens', 'GUI')

        settings.beginGroup('MainWindow')
        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())
        settings.endGroup()
        
        settings.beginGroup('CameraHelper')
        settings.setValue('sensor', self.combo_sensors.currentIndex())
        settings.setValue('lens', self.combo_lenses.currentIndex())
        settings.setValue('focal', self.focal_spin.value())
        settings.setValue('confusion', self.combo_confusions.currentIndex())
        settings.setValue('fnumber', self.fnumber_bar.f_number)
        settings.setValue('dof', self.dof_bar.focusing_distance)
        settings.endGroup()

    def readSettings(self):
        settings = QSettings('MyLens', 'GUI')

        settings.beginGroup('MainWindow')
        self.resize(settings.value('size', QSize(800, 600)))
        self.move(settings.value('pos', QPoint(200, 200)))
        settings.endGroup()
        
        settings.beginGroup('CameraHelper')
        self.combo_sensors.setCurrentIndex(settings.value('sensor', 1))
        focal_index = settings.value('lens', 1)
        focals = list(LENS_FOCALS.values())
        if focal_index>=len(focals):
            focal_index=len(focals)-1
        self.focal_spin.setValue(float(settings.value('focal', focals[focal_index])))
        self.combo_lenses.setCurrentIndex(focal_index)
        self.combo_confusions.setCurrentIndex(settings.value('confusion', 1))
        self.fnumber_bar.setFNumber(float(settings.value('fnumber', 5.6)))
        self.dof_bar.setFocusDistance(float(settings.value('dof', 3.5)))
        settings.endGroup()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setStyle('fusion')


    window = MainWindow()
    window.show()
    sys.exit(app.exec())
