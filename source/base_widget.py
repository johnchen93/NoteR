
'''
base_widget.py is a wrapper that subclasses pyqt QWidget to create a empty template of a frameless window with basic interaction capabilities.

Copyright (C) 2018  John Chen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import sys
import widget_styles
#from fancy_scroll import fancy_scroll
#from noter_list_widget import noter_list

from PyQt5.QtWidgets import QWidget, QTextEdit,QVBoxLayout,QApplication, QComboBox, QTreeWidget, QTreeWidgetItem, QLabel, QTextBrowser, QAbstractItemView, QPushButton, QHBoxLayout, QSizePolicy, QLineEdit, QFrame, QSpacerItem, QSizeGrip, QStyleFactory, QMenu, QMenuBar, QScrollArea
from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QLinearGradient
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, pyqtSlot, QCoreApplication


class base_widget(QWidget):

    def __init__(self, title='Base Widget'):
        QWidget.__init__(self)

        # testing palette settings
        self.app = QCoreApplication.instance()
        print(QStyleFactory.keys())
        self.app.setStyle('Fusion')
        self.palettes = widget_styles.palette_selection()
        #self.app.setPalette(self.palettes.get_palette('matcha'))

        # general app settings
        # get the screen space and size the app accordingly
        desktop = QApplication.desktop()
        avail_desktop = desktop.availableGeometry()
        screen_width = avail_desktop.width()
        screen_height = avail_desktop.height()
        print('Detected available screen space, {} wide and {} tall'.format(screen_width, screen_height))

        default_height = 1040
        def_start_height = 950
        def_start_width = 700
        if screen_height < def_start_height:
            def_start_height = screen_height
        font_scale = screen_height / default_height
        if font_scale < 0.5:
            font_scale = 0.5
        elif font_scale > 1.5:
            font_scale = 1.5
        print('Font scale is {}'.format(font_scale))
        self.font_scale=font_scale

        # set default size
        self.setMinimumSize(400,400)

        # basic visual properties
        self.setAttribute(Qt.WA_TranslucentBackground)

        # font set up
        self.def_font_size = 12
        self.title_font_size = 16
        self.basefont = QFont()
        self.basefont.setPointSize(int(self.def_font_size*font_scale))
        self.setFont(self.basefont)
        self.titlefont = QFont()
        self.titlefont.setPointSize(int((self.title_font_size)*font_scale))
        self.titlefont.setBold(True)

        # set style sheets
        #self.setStyleSheet( 'QLineEdit, QTextEdit {border-radius: 4px; background-color: palette(base)}');

        # frameless window
        flags = Qt.WindowFlags(Qt.FramelessWindowHint) # | Qt.WindowStaysOnTopHint)
        self.setWindowFlags(flags)

        # frameless window movement
        self.draggable = True
        self.dragging_threshould = 5
        self.__mousePressPos = None
        self.__mouseMovePos = None

        # init layout
        self.layout = QVBoxLayout(self)

        # making the title bar, with minimize and close buttons
        title_bar = QHBoxLayout()
        title = QLabel(title)
        self.basefont.setBold(True)
        title.setFont(self.basefont)

        Exit = QPushButton("X")
        Exit.setFixedWidth(25)
        Exit.setFixedHeight(25)
        #Exit.clicked.connect(self.ExitM)
        Exit.clicked.connect(self.close)
        self.basefont.setPointSize(int(10*font_scale))
        Exit.setFont(self.basefont)

        Minimize = QPushButton("-")
        Minimize.setFixedWidth(25)
        Minimize.setFixedHeight(25)
        Minimize.clicked.connect(self.MinimizeM)
        self.basefont.setBold(False)
        self.basefont.setPointSize(int(20*font_scale))
        Minimize.setFont(self.basefont)

        title_bar.addWidget(title)
        title_bar.addStretch(1)
        title_bar.addWidget(Minimize, 0 ,Qt.AlignBottom | Qt.AlignRight)
        title_bar.addWidget(Exit, 0 ,Qt.AlignBottom | Qt.AlignRight)
        self.layout.addLayout(title_bar)

        #self.layout.addWidget(self.HLine())
        #verticalSpacer = QSpacerItem(30, 10, QSizePolicy.Minimum)#, QSizePolicy.Expanding)
        #self.layout.addItem(verticalSpacer)

        # resize tool at bottom
        lowest_lay = QHBoxLayout()
        self.sizegrip = QSizeGrip(self)
        lowest_lay.addStretch()
        lowest_lay.addWidget(self.sizegrip) #, 1, Qt.AlignBottom | Qt.AlignRight)
        self.layout.addLayout(lowest_lay)

    def append_layout(self, layout):
        self.layout.insertLayout(self.layout.count()-1,layout)

    def append_widget(self, widget):
        self.layout.insertWidget(self.layout.count()-1,widget)

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.setRenderHint( QPainter.HighQualityAntialiasing)
        painter.setPen(Qt.NoPen)
        shadow = QColor(50,50,50, 100)
        painter.setBrush(QColor(50,50,50, 100))
        painter.drawRoundedRect(self.rect().adjusted(4,4,0,0), 10, 10)
        painter.setBrush(QColor(160,160,160))
        painter.drawRoundedRect(self.rect().adjusted(0,0,-3,-3), 10.0, 10.0)
        painter.setBrush(self.palette().color(QPalette.Window))
        painter.drawRoundedRect(self.rect().adjusted(2,2,-5,-5), 10.0, 10.0)

    def MinimizeM(self):
        self.showNormal()
        self.showMinimized()

    def ExitM(self):
        #sys.exit(0)
        self.closeEvent()

    def mousePressEvent(self, event):
        if self.draggable and event.button() == Qt.LeftButton:
            self.__mousePressPos = event.globalPos()                # global
            self.__mouseMovePos = event.globalPos() - self.pos()    # local
        super(base_widget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draggable and event.buttons() & Qt.LeftButton and self.__mousePressPos is not None and self.__mouseMovePos is not None:
            globalPos = event.globalPos()
            moved = globalPos - self.__mousePressPos
            if moved.manhattanLength() > self.dragging_threshould:
                # move when user drag window more than dragging_threshould
                diff = globalPos - self.__mouseMovePos
                self.move(diff)
                self.__mouseMovePos = globalPos - self.pos()
        super(base_widget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__mousePressPos is not None:
            if event.button() == Qt.LeftButton:
                moved = event.globalPos() - self.__mousePressPos
                if moved.manhattanLength() > self.dragging_threshould:
                    # do not call click event or so on
                    event.ignore()
                self.__mousePressPos = None
        super(base_widget, self).mouseReleaseEvent(event)

if __name__ == '__main__':
    main()
