# -*- coding: utf-8 -*-
# Created by DoSun on 2017/3/19
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtWidgets
import re
import sqlite3
import math
import codecs

ITEM_BOX_OFFSET = 1205996  # 道具箱第一格在存档中的位置


class Ui_mhxx(object):
    def setupUi(self, mhxx):
        mhxx.setObjectName("mhxx")
        mhxx.resize(400, 478)
        mhxx.setStyleSheet("QWidget{font-family: \"微软雅黑\";}")
        self.itemsTable = QtWidgets.QTableWidget(mhxx)
        self.itemsTable.setGeometry(QtCore.QRect(10, 10, 261, 461))
        self.itemsTable.setMinimumSize(QtCore.QSize(261, 0))
        self.itemsTable.setRowCount(2500)
        self.itemsTable.setColumnCount(2)
        self.itemsTable.setObjectName("itemsTable")
        self.readButton = QtWidgets.QPushButton(mhxx)
        self.readButton.setGeometry(QtCore.QRect(280, 10, 111, 61))
        self.readButton.setObjectName("readButton")
        self.saveButton = QtWidgets.QPushButton(mhxx)
        self.saveButton.setGeometry(QtCore.QRect(280, 340, 111, 61))
        self.saveButton.setObjectName("saveButton")
        self.quitButton = QtWidgets.QPushButton(mhxx)
        self.quitButton.setGeometry(QtCore.QRect(280, 410, 111, 61))
        self.quitButton.setObjectName("quitButton")
        self.textLabel = QtWidgets.QLabel(mhxx)
        self.textLabel.setGeometry(QtCore.QRect(280, 80, 111, 91))
        self.textLabel.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.textLabel.setWordWrap(True)
        self.textLabel.setObjectName("textLabel")

        self.retranslateUi(mhxx)
        QtCore.QMetaObject.connectSlotsByName(mhxx)

    def retranslateUi(self, mhxx):
        _translate = QtCore.QCoreApplication.translate
        mhxx.setWindowTitle(_translate("mhxx", "mhxx存档修改器 --DoSun"))
        self.itemsTable.setSortingEnabled(False)
        self.readButton.setText(_translate("mhxx", "读取system文件"))
        self.saveButton.setText(_translate("mhxx", "保存修改"))
        self.quitButton.setText(_translate("mhxx", "退出"))
        self.textLabel.setText(_translate("mhxx", "  简单的mhxx道具箱修改,现在默认是只读取第一个存档的"))


class Ui_changeWindow(object):
    def setupUi(self, changeWindow):
        changeWindow.setObjectName("changeWindow")
        changeWindow.resize(333, 102)
        self.itemChosen = QtWidgets.QComboBox(changeWindow)
        self.itemChosen.setGeometry(QtCore.QRect(10, 10, 251, 31))
        self.itemChosen.setObjectName("itemChosen")
        self.numChosen = QtWidgets.QSpinBox(changeWindow)
        self.numChosen.setGeometry(QtCore.QRect(270, 10, 51, 31))
        self.numChosen.setObjectName("numChosen")
        self.quitBtn = QtWidgets.QPushButton(changeWindow)
        self.quitBtn.setGeometry(QtCore.QRect(220, 50, 100, 41))
        self.quitBtn.setObjectName("quitBtn")
        self.changeBtn = QtWidgets.QPushButton(changeWindow)
        self.changeBtn.setGeometry(QtCore.QRect(110, 50, 100, 41))
        self.changeBtn.setObjectName("changeBtn")

        self.retranslateUi(changeWindow)
        QtCore.QMetaObject.connectSlotsByName(changeWindow)

    def retranslateUi(self, changeWindow):
        _translate = QtCore.QCoreApplication.translate
        changeWindow.setWindowTitle(_translate("changeWindow", "修改该道具栏"))
        self.quitBtn.setText(_translate("changeWindow", "取消"))
        self.changeBtn.setText(_translate("changeWindow", "确定"))


class MyWindow(QWidget, Ui_mhxx):
    def __init__(self):
        """窗口初始化"""
        super(MyWindow, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setFixedSize(self.width(), self.height())
        self.initTable()
        self.blinding()

        self.ITEMS_LIST = []
        self.item_index = 0
        self.haveLoaded = False
        self.changedItem = []
        self.originalItem = []
        self.filename = b''
        self.fp = ''
        self.fp_list = []

        self.getItemsInfo()

    def initTable(self):
        """初始化表单窗口"""
        self.itemsTable.setHorizontalHeaderLabels(['道具', '个数'])
        self.itemsTable.setColumnWidth(0, 150)
        self.itemsTable.setColumnWidth(1, 57)
        self.itemsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.itemsTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.itemsTable.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def blinding(self):
        """各种动作的绑定"""
        self.readButton.pressed.connect(self.readFile)
        self.saveButton.pressed.connect(self.saveFile)
        self.quitButton.pressed.connect(self.close)
        self.itemsTable.cellDoubleClicked[int, int].connect(self.cellChange)

    def readFile(self):
        """读取system文件"""
        self.filename = QFileDialog.getOpenFileName()[0]
        if not self.filename:
            return
        self.readItems()
        self.haveLoaded = True

    def saveFile(self):
        """保存进行的修改"""
        if not self.changedItem:
            return
        rewrite = []
        for i in self.changedItem:
            packNum = math.floor(i[0] / 8)
            packBin = self.originalItem[packNum][1][::-1]
            pos = self.originalItem[packNum][0]
            changedNum = bin(int(i[2])).replace('0b', '')
            if len(changedNum) != 7:
                changedNum = '0' * (7 - len(changedNum)) + changedNum
            changedId = bin(int(i[1])).replace('0b', '')
            if len(changedId) != 12:
                changedId = '0' * (12 - len(changedId)) + changedId
            changedBin = changedNum + changedId
            packBin[i[0] % 8] = changedBin
            rewrite_bin = ''
            for b in packBin[::-1]:
                rewrite_bin = rewrite_bin + b
            rewrite_bin_list = re.findall(r'.{8}', rewrite_bin)[::-1]
            rewrite_hex = []
            for bs in rewrite_bin_list:
                bs_list = re.findall(r'.{4}', bs)
                hex_block = ''
                for b in bs_list:
                    h = hex(int(b, 2)).replace('0x', '')
                    hex_block += h
                rewrite_hex.append(hex_block)
            rewrite.append([pos, rewrite_hex])
        self.fp_list = re.findall(r'\w{2}', self.fp.hex())
        for i in rewrite:
            self.replaceHex(i)
        refp = ''
        for i in range(len(self.fp_list)):
            refp += self.fp_list[i]
        look = codecs.lookup('hex')
        refp = look.decode(refp)[0]
        with open('system', 'wb') as f:
            f.write(refp)
        self.changedItem = []
        self.saveFinish()

    def saveFinish(self):
        info = QMessageBox.information(self, '', '保存成功', QMessageBox.Ok)
        if info == QMessageBox.Ok:
            return

    def replaceHex(self, hex_list):
        for i in range(len(hex_list[1])):
            self.fp_list[hex_list[0] + i] = hex_list[1][i]

    def cellChange(self, row, column):
        """单元格修改"""
        if not self.haveLoaded:
            return
        item_name = self.itemsTable.item(row, 0).text()
        item_num = self.itemsTable.item(row, 1).text()
        changeWindow = ChangeWindow(item_name, item_num, self.ITEMS_LIST)
        if changeWindow.exec_():
            self.itemsTable.setItem(row, 0, QTableWidgetItem(changeWindow.itemChosen.currentText()))
            self.itemsTable.setItem(row, 1, QTableWidgetItem(str(changeWindow.numChosen.value())))
            # 每次修改后changedItem列表会新增一个list 内容为修改的位置,物品id,个数(都为int型)
            self.changedItem.append([row,
                                     self.ITEMS_LIST.index(changeWindow.itemChosen.currentText()),
                                     changeWindow.numChosen.value()])
        changeWindow.destroy()

    def getItemsInfo(self):
        """获取全物品数据"""
        conn = sqlite3.connect('mhxx_item.db')
        cursor = conn.cursor()
        cursor.execute('SELECT NAME FROM MHXX')
        for i in cursor.fetchall():
            self.ITEMS_LIST.append(i[0])
        cursor.close()
        conn.close()

    def readItems(self):
        """读取system文件中的道具箱数据"""
        with open(self.filename, 'rb') as f:
            self.fp = f.read()
            f.seek(ITEM_BOX_OFFSET)
            while True:
                pos = f.tell()
                a = f.read(19)
                try:
                    result = int(a.hex(), 16)
                    if result == 0:
                        break
                except ValueError:
                    break
                b = re.findall(r'.{2}', a.hex())[::-1]
                bin_list = []
                for i in b:
                    bin_num = bin(int(i, 16))
                    bin_num = bin_num.replace('0b', '')
                    if len(bin_num) != 8:
                        bin_num = '0' * (8 - len(bin_num)) + bin_num
                    bin_list.append(bin_num)
                n = ''
                for i in bin_list:
                    n = n + i
                c = re.findall(r'.{19}', n)
                self.originalItem.append([pos, c])
                for i in c[::-1]:
                    item_num = str(int(i[:7], 2))
                    item_id = str(int(i[7:], 2))
                    self.addItem(item_id, item_num)
        # 创建备份文件
        with open(self.filename + '_bak', 'wb+') as f:
            f.write(self.fp)

    def addItem(self, id, num):
        """向表单中添加道具数据"""
        try:
            item_name = QTableWidgetItem(self.ITEMS_LIST[int(id)])
        except IndexError:
            item_name = QTableWidgetItem('???')

        self.itemsTable.setItem(self.item_index, 0, item_name)
        self.itemsTable.setItem(self.item_index, 1, QTableWidgetItem(num))
        self.item_index += 1


class ChangeWindow(QDialog, Ui_changeWindow):
    def __init__(self, item_name, item_num, item_list):
        """初始化窗口"""
        super(ChangeWindow, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.blinding()

        self.itemChosen.setEditable(False)
        self.itemChosen.setMaxVisibleItems(25)
        self.itemChosen.addItems(item_list)
        self.itemChosen.setCurrentText(item_name)

        self.numChosen.setValue(int(item_num))

    def blinding(self):
        """动作绑定"""
        self.changeBtn.pressed.connect(self.accept)
        self.quitBtn.pressed.connect(self.reject)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    sys.exit(app.exec_())
