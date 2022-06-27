# Import libs
import os
import tempfile
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from pathlib import Path

# Import sorting functions
from CC_dominant import start_dominant_colors
from CC_PCA import start_PCA

# Import gui converted to code
from ui import main



class Ui_MainWindow(main.Ui_MainWindow, QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui_MainWindow, self).__init__()
        self.setupUi(self)
        self.icon_path = QtGui.QIcon(str((Path(__file__).parent).resolve())+'\\icon\\cc_icon.ico')
        self.init_label_text = self.label.text()
        self.setWindowIcon(self.icon_path)
        self.set_default_paths()
        self.msgbox_handler()
        self.buttons_handler()
        self.dir_tree_viewer()    

    def set_default_paths(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = None
        self.output_path = None
        self.PCA_map = False


    def set_input_path(self):
        self.input_path = str(Path(self.model.filePath(self.treeView.currentIndex())).resolve())


    def set_ouput_path(self):
        self.output_path = str(Path(QFileDialog.getExistingDirectory(self, "Выберите каталог", 'C:\\')).resolve()) 
        

    def msgbox_handler(self):
        self.error_msg = QMessageBox()
        self.error_msg.setWindowTitle('Ошибка!')
        self.error_msg.setIcon(QMessageBox.Warning)
        self.error_msg.setWindowIcon(self.icon_path)
        self.error_msg.setStandardButtons(QMessageBox.Ok)

        self.result_msg = QMessageBox()
        self.result_msg.setWindowTitle('Сортировка')
        self.result_msg.setWindowIcon(self.icon_path)
        self.result_msg.setStandardButtons(QMessageBox.Ok)
        self.result_msg.setText('Сортировка выполнена успешно!')


    def buttons_handler(self):
        self.pushButton.clicked.connect(self.start_sorting)
        self.pushButton_2.clicked.connect(self.set_ouput_path)
        self.pushButton_3.clicked.connect(self.print_pca_map)
        self.pushButton_4.clicked.connect(self.print_donut_chart)
        
        self.menu_action = QAction("Инструкция", self)
        self.menu_action.triggered.connect(self.show_help)
        self.menu.addAction(self.menu_action)
        self.menu.triggered.connect(self.show_help)

    def show_help(self):
        self.label.clear
        self.label.setStyleSheet('color:#000000')
        self.label.setStyleSheet('background-color:#c4e2ec')
        self.label.setText(str(self.init_label_text))

    # Directory viewer
    def dir_tree_viewer(self):
        path = r''
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.context_menu)
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath((QtCore.QDir.rootPath()))
        self.model.setFilter(QtCore.QDir.AllDirs|QtCore.QDir.NoDotAndDotDot)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(path))
        self.treeView.setColumnHidden(1, True)
        self.treeView.setColumnHidden(2, True)
        self.treeView.setColumnHidden(3, True)
        self.treeView.setSortingEnabled(True)
        
    # RMB context menu
    def context_menu(self):
        cx_menu = QtWidgets.QMenu()
        open = cx_menu.addAction("Выбрать папку")        
        open.triggered.connect(self.set_input_path)
        cursor = QtGui.QCursor()
        cx_menu.exec_(cursor.pos())
        
    # Resize event filter
    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.Resize and
            widget is self.label):
            self.label.setPixmap(self.pix.scaled(
                self.label.width(), self.label.height(),
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            return True
        return QMainWindow.eventFilter(self, widget, event)


    def print_pca_map(self):
        if self.PCA_map == True:
            self.pca_map_img
            self.pix = QtGui.QPixmap(self.pca_map_img).scaled(self.label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.label.installEventFilter(self)
            self.label.setPixmap(self.pix) 
        else:
            self.error_msg.setText('Отсутствует карта насыщенности')
            self.error_msg.exec_()
            return


    def print_donut_chart(self):
        img = QFileDialog.getOpenFileName(self, "Open File", "", "(*.jpg);;(*.png);;(*.webp);;(*jpeg)")
        img = str(Path(img[0]).resolve())
        donut_plot = start_dominant_colors(img, self.temp_dir.name, self.temp_dir.name, mode = 1)
        self.pix = QtGui.QPixmap(donut_plot).scaled(self.label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.label.installEventFilter(self)
        self.label.setPixmap(self.pix)


    def start_sorting(self):
        # Error msg if clicked 
        if self.input_path is None:
            self.error_msg.setText('Не выбран входной каталог!')
            self.error_msg.exec_()
            return
        if self.output_path is None:
            self.error_msg.setText('Не выбран выходной каталог!')
            self.error_msg.exec_()
            return
        # Count valid images
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        folder_elem_count = len([name for name in os.listdir(self.input_path) if (os.path.join(self.input_path, name)).endswith(valid_extensions)])
        if folder_elem_count == 0:
            self.error_msg.setText('Доступные изображения отсутствуют в каталоге!')
            self.error_msg.exec_()
            return
        try:
            # Check current Combo Box element (0 - dominant colors; 1 - PCA)
            self.comboBox_mode = self.comboBox.currentIndex()
            if self.comboBox_mode == 0:
                start_dominant_colors(self.input_path, self.output_path, self.temp_dir.name)
                self.result_msg.exec_()
            if self.comboBox_mode == 1:
                # Min element in folder for clusterisation - 3
                if folder_elem_count < 3:
                    self.error_msg.setText('Минимальное количество изображений для PCA режима - 3!')
                    self.error_msg.exec_()
                    return
                else:
                    try:
                        self.pca_map_img = start_PCA(self.input_path, self.output_path, self.temp_dir.name)
                        self.PCA_map = True
                    except Exception: 
                        self.PCA_map = False
                        self.error_msg.setText('Обнаружены битые изображения, не удалось создать карту насыщенности!')
                        self.error_msg.exec_()
                        return

        except Exception: 
            self.error_msg.setText('Обнаружена непредвиденная ошибка!')
            self.error_msg.setIcon(QMessageBox.Critical)
            self.error_msg.exec_()
            self.error_msg.setIcon(QMessageBox.Warning)
            return

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    mwindow = Ui_MainWindow()
    mwindow.show()
    app.exec_()