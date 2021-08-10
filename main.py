from PySide6.QtWidgets import *
from PySide6.QtCore import QThread, QObject, Signal
from main_window import Ui_MainWindow
from timetable_search import *
from blog_downloader import *

class Worker(QObject):
    finished = Signal(bool)
    progress = Signal(int)

    def search(self, search):
        data_list = get_anime_data(search)
        self.finished.emit()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, is_searching=0):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.search_btn_clicked)
        self.lineEdit.returnPressed.connect(self.search_btn_clicked)

    def search_btn_clicked(self):
        self.treeWidget.clear()
        search = self.lineEdit.text()

        if 'https:/' in search or 'http:/' in search:
            download(search)
        else:
            data_list = get_anime_data(search)

            if data_list:
                with ThreadPoolExecutor(max_workers=32) as executor:
                    executor.map(self.add_tree_item, data_list)
            else:
                tree_item = QTreeWidgetItem(['', '해당하는 작품을 찾지 못했습니다'])
                self.treeWidget.addTopLevelItem(tree_item)

    def add_tree_item(self, data):
        tree_item = QTreeWidgetItem([data[0] + ' ~ ' + data[1], data[3]])
        '''
        sub_data = get_sub_data(data)
        if sub_data:
            for sub_maker in sub_data:
                chapter = '  ' + str(int(sub_maker[2])) + '화'
                if chapter == '  9999화':
                    chapter = '  완결'
                child = QTreeWidgetItem([sub_maker[1], chapter])
                tree_item.addChild(child)
        else:
            child = QTreeWidgetItem(['', '  자막 제작자를 찾을 수 없습니다.'])
            tree_item.addChild(child)
        '''
        self.treeWidget.addTopLevelItem(tree_item)


if __name__ == '__main__':
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()