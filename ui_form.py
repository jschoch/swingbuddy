# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QListView, QPushButton, QSizePolicy,
    QSpacerItem, QTabWidget, QVBoxLayout, QWidget)

class Ui_SBW(object):
    def setupUi(self, SBW):
        if not SBW.objectName():
            SBW.setObjectName(u"SBW")
        SBW.resize(1468, 1016)
        self.verticalLayoutWidget_2 = QWidget(SBW)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(300, 640, 1081, 371))
        self.verticalLayout_4 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.widget = QWidget(self.verticalLayoutWidget_2)
        self.widget.setObjectName(u"widget")
        self.status_label = QLabel(self.widget)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setGeometry(QRect(10, 0, 1081, 21))
        self.horizontalLayoutWidget_2 = QWidget(self.widget)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(0, 20, 1081, 31))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.stop_btn = QPushButton(self.horizontalLayoutWidget_2)
        self.stop_btn.setObjectName(u"stop_btn")

        self.horizontalLayout_2.addWidget(self.stop_btn)

        self.add_btn = QPushButton(self.horizontalLayoutWidget_2)
        self.add_btn.setObjectName(u"add_btn")

        self.horizontalLayout_2.addWidget(self.add_btn)

        self.del_swing_btn = QPushButton(self.horizontalLayoutWidget_2)
        self.del_swing_btn.setObjectName(u"del_swing_btn")

        self.horizontalLayout_2.addWidget(self.del_swing_btn)

        self.sw_btn = QPushButton(self.horizontalLayoutWidget_2)
        self.sw_btn.setObjectName(u"sw_btn")

        self.horizontalLayout_2.addWidget(self.sw_btn)

        self.horizontalSpacer = QSpacerItem(1048, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.run_a_btn = QPushButton(self.horizontalLayoutWidget_2)
        self.run_a_btn.setObjectName(u"run_a_btn")

        self.horizontalLayout_2.addWidget(self.run_a_btn)

        self.gridLayoutWidget = QWidget(self.widget)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(0, 59, 1081, 311))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout_4.addWidget(self.widget)

        self.tabWidget = QTabWidget(SBW)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 640, 271, 261))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.out_msg = QLabel(self.tab)
        self.out_msg.setObjectName(u"out_msg")
        self.out_msg.setGeometry(QRect(10, 30, 49, 16))
        self.create_db_btn = QPushButton(self.tab)
        self.create_db_btn.setObjectName(u"create_db_btn")
        self.create_db_btn.setGeometry(QRect(10, 60, 75, 24))
        self.pop_btn = QPushButton(self.tab)
        self.pop_btn.setObjectName(u"pop_btn")
        self.pop_btn.setGeometry(QRect(10, 90, 181, 24))
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.frame = QFrame(SBW)
        self.frame.setObjectName(u"frame")
        self.frame.setGeometry(QRect(0, 30, 1451, 611))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayoutWidget = QWidget(self.frame)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 211, 601))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.verticalLayoutWidget)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout.addWidget(self.label_5)

        self.LM_data_lv = QListView(self.verticalLayoutWidget)
        self.LM_data_lv.setObjectName(u"LM_data_lv")

        self.verticalLayout.addWidget(self.LM_data_lv)

        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.swings_lv = QListView(self.verticalLayoutWidget)
        self.swings_lv.setObjectName(u"swings_lv")

        self.verticalLayout.addWidget(self.swings_lv)

        self.tabWidget_2 = QTabWidget(self.frame)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tabWidget_2.setGeometry(QRect(210, 0, 1241, 611))
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.horizontalLayoutWidget = QWidget(self.tab_3)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(10, 0, 1221, 581))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_2.addTab(self.tab_3, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.verticalLayoutWidget_4 = QWidget(self.tab_5)
        self.verticalLayoutWidget_4.setObjectName(u"verticalLayoutWidget_4")
        self.verticalLayoutWidget_4.setGeometry(QRect(0, 0, 1221, 581))
        self.verticalLayout_6 = QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_2.addTab(self.tab_5, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayoutWidget_3 = QWidget(self.tab_4)
        self.verticalLayoutWidget_3.setObjectName(u"verticalLayoutWidget_3")
        self.verticalLayoutWidget_3.setGeometry(QRect(20, 10, 531, 541))
        self.verticalLayout_5 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.tabWidget_2.addTab(self.tab_4, "")

        self.retranslateUi(SBW)
        self.stop_btn.clicked.connect(SBW.update)

        self.tabWidget.setCurrentIndex(0)
        self.tabWidget_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SBW)
    # setupUi

    def retranslateUi(self, SBW):
        SBW.setWindowTitle(QCoreApplication.translate("SBW", u"SBW", None))
        self.status_label.setText(QCoreApplication.translate("SBW", u"Analysis: charts, tabs, tables?", None))
        self.stop_btn.setText(QCoreApplication.translate("SBW", u"?", None))
        self.add_btn.setText(QCoreApplication.translate("SBW", u"Add Swing", None))
        self.del_swing_btn.setText(QCoreApplication.translate("SBW", u"Delete Swing ", None))
        self.sw_btn.setText(QCoreApplication.translate("SBW", u"Test Screenshot", None))
        self.run_a_btn.setText(QCoreApplication.translate("SBW", u"Run Analysis", None))
        self.out_msg.setText(QCoreApplication.translate("SBW", u"TextLabel", None))
        self.create_db_btn.setText(QCoreApplication.translate("SBW", u"CreateDB", None))
        self.pop_btn.setText(QCoreApplication.translate("SBW", u"Populate Test DB", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("SBW", u"Test crap", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("SBW", u"Tab 2", None))
        self.label_5.setText(QCoreApplication.translate("SBW", u"LM Data", None))
        self.label.setText(QCoreApplication.translate("SBW", u"Swings", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_3), QCoreApplication.translate("SBW", u"Video", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_5), QCoreApplication.translate("SBW", u"Swing", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_4), QCoreApplication.translate("SBW", u"Configuration", None))
    # retranslateUi

