
'''
noter_styles.py creates pyqt palettes so they can be applied to the main NoteR application.

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

from PyQt5.QtGui import QFont, QPalette, QColor, QPainter, QLinearGradient
from PyQt5.QtCore import Qt

class palette_selection():

    def_pal = 'Matcha'

    def __init__(self):
        self.palettes = {   'Java':self.pal_java(),
                            'Vanilla':self.pal_vanilla(),
                            'Liquorice':self.pal_liquorice(),
                            'Matcha':self.pal_matcha()}

    def default_palette(self):
        return self.palettes.get(self.def_pal)

    def palette_keys(self):
        return self.palettes.keys()

    def get_palette(self, key):
        return self.palettes.get(key)

    def pal_vanilla(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(220,215,210))
        palette.setColor(QPalette.WindowText,QColor(50,50,50))# Qt.white)
        palette.setColor(QPalette.Base, QColor(170,165,160))
        palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
        #palette.setColor(QPalette.ToolTipBase, Qt.white)
        #palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, QColor(60,60,60))# Qt.white)
        palette.setColor(QPalette.Button, QColor(200,195,190))
        palette.setColor(QPalette.ButtonText, QColor(50,50,50))# Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(40,40,30))

        palette.setColor(QPalette.Highlight, QColor(130,136,120) )#.lighter())
        palette.setColor(QPalette.HighlightedText, Qt.black)

        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(220,215,210))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100,100,100))
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(220,215,210))
        return palette

    def pal_java(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53,41,34))
        palette.setColor(QPalette.WindowText,QColor(170,170,170))# Qt.white)
        palette.setColor(QPalette.Base, QColor(30,24,18))
        palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
        #palette.setColor(QPalette.ToolTipBase, Qt.white)
        #palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, QColor(200,200,200))# Qt.white)
        palette.setColor(QPalette.Button, QColor(60,48,36))
        palette.setColor(QPalette.ButtonText, QColor(170,170,170))# Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(200,180,150))

        palette.setColor(QPalette.Highlight, QColor(138,116,45) )#.lighter())
        palette.setColor(QPalette.HighlightedText, Qt.black)

        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(53,41,34))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100,100,100))
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(53,41,34))
        return palette

    def pal_matcha(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(70,130,70))
        palette.setColor(QPalette.WindowText,QColor(200,200,200))# Qt.white)
        palette.setColor(QPalette.Base, QColor(55,70,55))
        palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
        #palette.setColor(QPalette.ToolTipBase, Qt.white)
        #palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, QColor(200,200,200))# Qt.white)
        palette.setColor(QPalette.Button, QColor(40,68,40))
        palette.setColor(QPalette.ButtonText, QColor(200,200,200))# Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(150,180,150))

        palette.setColor(QPalette.Highlight, QColor(120,146,120) )#.lighter())
        palette.setColor(QPalette.HighlightedText, Qt.black)

        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(70,130,70))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100,100,100))
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(70,130,70))
        return palette

    def pal_liquorice(self):
        # style by QuantimCD, ported to pyqt by Ischmierer
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(170, 170,170) )
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        #palette.setColor(QPalette.ToolTipBase, Qt.white)
        #palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, QColor(170,170,170) )
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))

        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)

        palette.setColor(QPalette.Disabled, QPalette.Button, QColor(53,53,53))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100,100,100))
        palette.setColor(QPalette.Disabled, QPalette.Base, QColor(53,53,53))
        return palette


