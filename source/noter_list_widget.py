
'''
noter_list_widget.py contains the main widgets for displaying information in NoteR.

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
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from noter_io_lite import *

def HLine():
    toto = QFrame()
    toto.setFrameShape(QFrame.HLine)
    toto.setFrameShadow(QFrame.Plain)
    toto.setContentsMargins(0,0,0,0)
    return toto

class noter_list(QScrollArea):

    scroll_anim_signal = pyqtSignal(int)
    focus_signal = pyqtSignal(object)

    def __init__(self, parent=None, fontsize=12, tags_func=None):
        super(noter_list, self).__init__(parent=parent)
        self.tags_func = tags_func

        self.font = QFont()
        self.font.setPointSize(fontsize)

        self.area_widget = QWidget(self)
        self.setWidget(self.area_widget)
        self.setWidgetResizable(True)
        #self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.scroll_anim = QPropertyAnimation(self.verticalScrollBar(), b'value')
        self.scroll_anim.setDuration(400)
        self.scroll_anim_signal.connect(self.play_scroll_anim)
        self.scroll_anim.setEasingCurve(QEasingCurve.OutQuad)

        self.focus_signal.connect( self.new_focus )
        self.curr_focus = None

        self.area_widget.setContentsMargins(10, 10, 10, 10)

        # for tracking an checking up on newly created entries to see if they are still empty
        self.new_header = None

        self.data =[]

    def new_focus(self, focus):
        if focus is not self.curr_focus and self.curr_focus is not None:
            start_pos = self.curr_focus.geometry().top()
            height_diff = self.curr_focus.body.geometry().height()
            self.curr_focus.toggle_expanded(False)
            end_pos = focus.geometry().top()
            self.curr_focus = focus
            if end_pos > start_pos:
                self.play_scroll_anim(end_pos, height_diff)
            else:
                self.play_scroll_anim(end_pos)
        elif self.curr_focus is None:
            end_pos = focus.geometry().top()
            self.curr_focus = focus
            self.play_scroll_anim(end_pos)

    def make_new_header(self):
        header = header_widget(self.area_widget, resize_func=self.size_change, font=self.font, scroll_signal=self.scroll_anim_signal, focus_signal = self.focus_signal, tags_func = self.tags_func, delete_func=self.delete_entry)
        return header

    # loading function, knows nothing of what to load, and so has to be called externally
    def load_entries(self, data, append=False):
        # data is expected to be an ordered dict, or dict
        # assumes that only one copy of data will be held at a time
        #print(len(self.data))
        if append:
            self.data.extend(data)
        else:
            self.data=data
        #print(len(self.data))

        if append:
            layout = self.area_widget.layout()
        else:
            # in the case of fully replacing the data
            if self.area_widget.layout() is None:
                layout = QVBoxLayout()
                layout.setContentsMargins(0,0,0,0)
            elif self.area_widget.layout() is not None:
                layout = self.area_widget.layout()
                clearLayout(layout)
                self.new_header = None
            new_label = QLabel('Top')
            new_label.setAlignment( Qt.AlignCenter )
            layout.addWidget(new_label)
            self.entry_list = []

        for i in range(len(data)):
            header= self.make_new_header()
            body = header.body
            header.index = i
            if append:
                layout.insertWidget(self.area_widget.layout().count()-1, header)
            else:
                layout.addWidget(header)
            header.text_in( data[i]['Title'].strip(), data[i]['Short Name'].strip(), data[i]['Tags'] )
            header.activate_buttons(pdf=data[i]['Short Name'], doi=data[i]['DOI'])
            body.text_in( data[i]['PMID'], data[i]['Notes'].strip() )
            body.set_loaded_pmid( data[i]['PMID'] ) # let the body know the pmid is loaded so it can warn the user of changes
            self.entry_list.append( (header, body) )

        if not append:
            padding_widget = QWidget()
            avail_desktop = QApplication.desktop()
            if avail_desktop is not None:
                avail_height = avail_desktop.availableGeometry().height()
            else:
                avail_height = 1000 # take a guess
            padding_widget.setFixedHeight( avail_height/2 )
            sub_layout = QVBoxLayout()
            sub_layout.addWidget(HLine())
            new_label = QLabel('End')
            new_label.setAlignment( Qt.AlignCenter )
            sub_layout.addWidget(new_label)
            sub_layout.addStretch()
            padding_widget.setLayout(sub_layout)
            layout.addWidget(padding_widget)

        if self.area_widget.layout() is None:
            self.area_widget.setLayout(layout)
        #print(self.area_widget.layout().count())

    def play_scroll_anim(self, value, y_offset = 0):
        self.scroll_anim.stop()
        self.scroll_anim.setStartValue(self.verticalScrollBar().value()-y_offset)
        self.scroll_anim.setEndValue(value)
        self.scroll_anim.start()

    def size_change(self):
        self.area_widget.adjustSize()

    def search_entries(self, text):
        self.show_all()
        show_list = []
        for x in self.entry_list:
            #print(x[0].index)
            inheader = x[0].search_text(text)
            inbody = x[1].search_text(text)
            if inheader or inbody:
                show_list.append(x[0].index)
        #print(show_list)
        self.show_only(show_list)
        self.parent().status_bar.showMessage('{} entries found'.format(len(show_list)))
        #self.area_widget.adjustSize()
        self.play_scroll_anim(0)

    def show_only(self, entries):
        for x in self.entry_list:
            index = x[0].index
            if index not in entries:
                x[0].setHidden(True)

    def show_all(self):
        for x in self.entry_list:
            x[0].setHidden(False)

    def save(self):
        if self.new_header is not None and self.entry_has_id(self.new_header):
            self.data.append( self.entry_list[self.new_header.index][0].text_out())
            self.new_header = None
        #print(len(self.data))
        change_list = []
        for x in self.entry_list:
            if x[0].interacted or x[1].interacted:
                change_list.append(x[0].index)
        #print(change_list)

        new_data = []
        for i in range(len(self.data)):
            if i in change_list:
                #print( self.entry_list[i] )
                #print( self.entry_list[i][0].text_out() )
                new_data.append( self.entry_list[i][0].text_out() )
            else:
                new_data.append( self.data[i] )
        #print(len(new_data))
        self.data = new_data
        if len(new_data) > 0:
            save_aggregate(new_data)

    def new_entry(self):
        if self.new_header is None or self.entry_has_id(self.new_header):
            if self.entry_has_id(self.new_header):
                self.data.append( self.entry_list[self.new_header.index][0].text_out())
            header= self.make_new_header()
            self.area_widget.layout().insertWidget( self.area_widget.layout().count()-1, header)
            header.index = len(self.entry_list)
            self.new_header = header
            self.entry_list.append( (header, header.body) )
            self.new_header.setVisible(True)
            #self.new_header.adjustSize()
            self.new_header.toggle_expanded(True)

        #self.area_widget.adjustSize()
        #print(self.new_header.geometry())
        self.play_scroll_anim( self.new_header.geometry().top() )

    def entry_has_content(self, entry):
        if entry is None:
            return False
        text = entry.text_out()
        for k, v in text.items():
            if v != '':
                return True
        return False

    def entry_has_id(self, entry):
        if entry is None:
            return False
        text = entry.text_out()
        for key in ['Short Name','Title','PMID']:
            if text[key] != '':
                return True
        return False

    def delete_entry(self, entry):

        resp = QMessageBox.warning(self, 'Delete This Entry?', 'Caution: You are trying to delete this entry from the records. All notes you have taken on this paper will be lost. This can not be undone. Do you still wish to proceed?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if resp == QMessageBox.Yes:
            self.save() # force the new entry into the dataset, so it is part of self.data, regardless if it is being deleted
            rem_index = entry.index
            new_data = []
            for i in range(len(self.data)):
                if i == rem_index:
                    continue
                new_data.append(self.data[i])
            self.load_entries(new_data)
            self.curr_focus = None
            self.parent().status_bar.showMessage('Entry has been deleted', 5000)

def clearLayout(layout):
  while layout.count():
    child = layout.takeAt(0)
    if child.widget():
      child.widget().deleteLater()

class header_widget(QWidget):

    def __init__(self, parent=None, resize_func=None, font=None, scroll_signal=None, focus_signal=None, tags_func=None, delete_func=None):
        super(header_widget, self).__init__(parent=parent)

        self.setMouseTracking = True
        self.scroll_signal = scroll_signal
        self.focus_signal = focus_signal
        self.tags_func = tags_func
        self.setAcceptDrops(True)
        self.delete_func = delete_func

        self.resize_func = resize_func
        self.font=font
        self.font_metric=None
        self.def_height = None
        self.font_size=12
        if font is not None:
            self.setFont(font)
            self.font_metric = QFontMetrics(font)
            self.def_height = self.font_metric.height()
            self.font_size=font.pointSize()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5,5,5,5)

        self.layout.addWidget(HLine())

        self.tags_layout = QHBoxLayout()
        self.tags_layout.setContentsMargins(0, 10, 0, 0)
        self.tags_entry = QLineEdit('',self)
        #self.tags_entry.setStyleSheet( ':disabled {background-color: palette(window)}')
        self.tags_entry.setContentsMargins(0,0,0,0)
        #self.tags_entry.setDisabled(True)
        self.tags_entry.setReadOnly(True)
        self.tags_entry.setFont(self.font)
        self.tags_entry.setPlaceholderText('Tags')
        self.tags_entry.addAction(QIcon(start_path+'/tag_icon2.png'), QLineEdit.LeadingPosition)
        #self.tags_entry.clicked.connect( self.mousePressEvent )
        self.tags_entry.mousePressEvent = lambda x : self.mousePressEvent(x)
        self.tags_entry.setAcceptDrops(False)
        self.tags_layout.addWidget(self.tags_entry)
        self.tags_button = QPushButton('Edit Tags', self)
        self.tags_button.setHidden(True)
        self.tags_button.clicked.connect(self.edit_tags)
        self.tags_layout.addWidget(self.tags_button)
        self.layout.addLayout(self.tags_layout)

        self.title_layout = QHBoxLayout()
        #self.title_label = QLabel('Title:',self)
        #self.title_entry = GrowingTextEdit('Title', self, text_size_func=self.text_entered, start_size=None, start_height=self.def_height*1.5)
        self.title_font=QFont()
        self.title_font.setPointSize(self.font_size*1.8)
        self.title_font.setBold(True)
        #self.title_entry.setFont(self.title_font)
        self.title_entry = edit_stack(self, text_size_func=self.text_entered, start_height=self.def_height*1.5, font=self.title_font, placeholder_text = 'Title')
        #self.title_entry.setStyleSheet( 'QTextEdit {background-color: palette(window)}');
        #self.title_entry.setStyleSheet( ':disabled {background-color: palette(window)}')
        self.title_entry.setDisabled(True)
        self.title_entry.setAcceptDrops(False)
        #self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.title_entry)
        self.layout.addLayout(self.title_layout)

        self.shortname_layout = QHBoxLayout()
        #self.shortname_label = QLabel('Short Name:',self)
        self.shortname_entry = QLineEdit('', self)
        self.shortname_entry.setPlaceholderText('Short name: e.g. Author, journal, year')
        #self.shortname_entry.setStyleSheet( 'QLineEdit {background-color: palette(window)}');
        #self.shortname_entry.setStyleSheet( ':disabled {background-color: palette(window)}')
        self.shortname_entry.setContentsMargins(0,0,0,0)
        self.shortname_entry.setDisabled(True)
        self.shortname_entry.setFont(self.font)
        self.shortname_entry.setAcceptDrops(False)
        #self.shortname_layout.addWidget(self.shortname_label)
        self.shortname_layout.addWidget(self.shortname_entry)
        self.layout.addLayout(self.shortname_layout)


        self.util_layout = QHBoxLayout()
        self.expand_label = QPushButton('+ Edit')
        self.expand_label.clicked.connect(self.toggle_expanded)
        self.pdf_button = QPushButton('PDF', self)
        self.pdf_button.setHidden(True)
        self.pdf_button.clicked.connect(self.open_pdf)
        self.link_button = QPushButton('Link', self)
        self.link_button.setHidden(True)
        self.link_button.clicked.connect(self.open_url)
        self.link_button.link = ''
        self.util_layout.addWidget(self.expand_label)
        self.util_layout.addWidget(self.pdf_button)
        self.util_layout.addWidget(self.link_button)
        self.layout.addLayout(self.util_layout)

        self.interacted = False

        #self.layout.addWidget(HLine())

        self.body = body_widget(self, resize_func = self.text_entered, start_height= self.def_height, font=self.font, delete_func = self.delete_entry)
        self.layout.addWidget(self.body)

        self.buttons = [self.pdf_button, self.link_button]
        for x in self.buttons:
            x.setFixedWidth(self.font_metric.boundingRect(self.link_button.text()).width()*1.5)
            #x.setStyleSheet( ':disabled { color: rgb(0,0,0)}')
        self.edits = [self.title_entry, self.shortname_entry]
        self.setLayout(self.layout)

    def delete_entry(self):
        if self.delete_func is not None:
            self.delete_func(self)

    def activate_edits(self, activate=True):
        for x in self.edits:
            x.setDisabled(not activate)
            if type(x) == edit_stack:
                x.cue_edit(activate)
        self.tags_button.setHidden(not activate)
        self.interacted = True

    def activate_buttons(self, pdf='', doi=''):
        if find_pdf(pdf):
            #self.pdf_button.setDisabled(False)
            self.pdf_button.setHidden(False)
        if doi != '':
            #self.link_button.setDisabled(False)
            self.link_button.setHidden(False)
            self.link_button.link = doi

    def edit_tags(self):
        if self.tags_func is not None:
            tags = self.tags_entry.text()
            self.tags_func(self.set_tags, tags)

    def set_tags(self, tags):
        self.tags_entry.setText(', '.join(tags) )

    def text_entered(self):
        self.adjustSize()
        if self.resize_func is not None:
            self.resize_func()

    def toggle_expanded(self, ev=None, show=None):
        #print('mouse press')
        expand = False
        if show is not None:
            expand = show
        elif self.body.isHidden():
            expand = True
        elif self.body.isVisible():
            expand = False

        if expand:
            self.activate_edits()
            self.body.show_widget(True)
            self.expand_label.setText('- Hide')
            if self.focus_signal is not None:
                self.focus_signal.emit(self)
            if self.resize_func is not None:
                self.resize_func()
            #if self.scroll_signal is not None:
            #    self.scroll_signal.emit(self.geometry().top())
        else:
            self.body.show_widget(False)
            self.activate_edits(False)
            self.expand_label.setText('+ Edit')

    def mousePressEvent(self, ev):
        if self.body.isHidden():
            self.toggle_expanded(None, True)

    def change_focus(self, other):
        if other is not self:
            self.toggle_expanded(None, False)

    def text_in(self, title, shortname, tags=''):
        self.title_entry.setText(title)
        #title_metric = QFontMetrics(self.title_font)
        #height = title_metric.boundingRect(self.title_entry.toPlainText()).height()
        #print(height)
        #self.title_entry.setMinimumHeight(height)
        #self.title_entry.setMaximumHeight(height)
        self.shortname_entry.setText(shortname)
        self.tags_entry.setText(tags)

    def text_out(self):
        title = self.title_entry.edit.toPlainText()
        shortname = self.shortname_entry.text()
        tags = self.tags_entry.text()
        link = self.link_button.link
        header_fields = {'Title':title, 'Short Name':shortname, 'Tags':tags, 'DOI':link}

        body_fields = self.body.text_out()
        header_fields.update(body_fields)

        return header_fields

    def open_pdf(self):
        print('pdf button pressed')
        noter_open_pdf( self.shortname_entry.text())

    def open_url(self):
        print('link button pressed')
        noter_open_doi( self.link_button.link)

    def search_text(self, text):
        found = False
        for x in [self.tags_entry, self.shortname_entry]:
            x.deselect()
            index = x.text().lower().find(text)
            if index != -1:
                x.setSelection(index, len(text))
                found = True
        for x in [self.title_entry]:
            x.edit.setTextCursor(QTextCursor(x.edit.document()))
            #x.label.deselect()
            result = x.edit.find(text)
            #print(result)
            if result:
                index = x.label.text().lower().find(text)
                x.label.setSelection( index, len(text ) )
                found = True
            else:
                x.edit.textCursor().movePosition(QTextCursor.End)
                x.label.setSelection(0,0)
        return found

    # drag and drop pdf
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        #if len(event.mimeData().urls())>1:
            #self.log.append('Please drop 1 file at a time.')
            #self.update_log()
        #    return
        #if self.loaded_row is None:
            #self.log.append('Cannot add file to blank entry, add an identifier and save the entry first.')
            #self.update_log()
        #    return

        file_added = False
        for url in event.mimeData().urls():
            if file_added:
                # only add the first in the list in case of multiple
                break
            path = url.toLocalFile()
            print(path)
            if os.path.isfile(path):
                if path.lower().endswith('.pdf'):{}
                else:
                    #self.log.append('Wrong file format, only pdf files are archived')
                    return
            else:
                #self.log.append( 'Could not find a valid file path' )
                return

            added = add_pdf( path, self.shortname_entry.text() )
            if added:
                print('pdf added')
                #self.log.append('PDF file added to records')
                #self.pdf_button.setEnabled(True)
                self.pdf_button.setVisible(True)
            else:
                #self.log.append('The file was not added')
                print('pdf not added')
            #self.update_log()

class body_widget(QWidget):

    def __init__(self, parent=None, resize_func=None, start_height=20, font=None, delete_func=None):
        super(body_widget, self).__init__(parent=parent)
        self.resize_func = resize_func
        self.def_height = start_height
        self.delete_func = delete_func
        self.font = font
        if font is not None:
            self.setFont(font)
            self.font_metric = QFontMetrics(font)
            self.def_height = self.font_metric.height()
            self.font_size=font.pointSize()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20,0,5,0)

        self.layout.addWidget(HLine())

        self.pmid_layout = QHBoxLayout()
        self.pmid_label = QLabel('PMID:',self)
        self.pmid_entry = QLineEdit('',self)
        self.pmid_entry.setFixedHeight(self.def_height*1.5)
        self.pmid_entry.setAcceptDrops(False)
        self.fetch_button = QPushButton('Fetch', self)
        self.fetch_button.clicked.connect( self.get_pmid_info )
        self.pmid_entry.returnPressed.connect(self.fetch_button.click)
        #self.pdf_button = QPushButton('PDF', self)
        #self.link_button = QPushButton('Link', self)
        self.pmid_layout.addWidget(self.pmid_label)
        self.pmid_layout.addWidget(self.pmid_entry)
        self.pmid_layout.addWidget(self.fetch_button)
        #self.pmid_layout.addWidget(self.pdf_button)
        #self.pmid_layout.addWidget(self.link_button)
        self.layout.addLayout(self.pmid_layout)

        self.layout.addWidget(HLine())
        self.layout.addWidget(QLabel('Notes:'))
        self.edit_layout = QVBoxLayout()
        self.layout.addLayout(self.edit_layout)
        self.layout.addWidget(HLine())
        self.remove_layout = QHBoxLayout()
        self.remove_button = QPushButton('Delete')
        self.remove_button.clicked.connect(self.delete_entry)
        self.remove_layout.addStretch()
        self.remove_layout.addWidget(self.remove_button)
        self.layout.addLayout(self.remove_layout)


        self.buttons = [self.fetch_button] #, self.pdf_button, self.link_button]
        for x in self.buttons:
            x.setFixedWidth(self.font_metric.boundingRect(self.fetch_button.text()).width()*1.8)

        self.setLayout(self.layout)
        self.append_box()
        self.setHidden(True)

        self.interacted = False
        self.loaded_pmid = None

    def delete_entry(self):
        if self.delete_func is not None:
            self.delete_func()

    def set_loaded_pmid(self, pmid):
        self.loaded_pmid = pmid

    def get_pmid_info(self):
        try:
            pmid = int(self.pmid_entry.text().strip())
        except:
            print('Invalid PMID')
            return

        if self.loaded_pmid is not None:
            resp = QMessageBox.warning(self, 'Replace Info for Current Entry?', 'Caution: You are trying to fetch PubMed information on an entry with EXISTING labels. If you proceed, the labels of the entry may not match the paper you are taking notes on! If you would like to replace the current entry with something else, please delete this entry and add a new entry instead.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            #print(resp)
            if resp == QMessageBox.No:
                return

        result = fetch_pmid(None, None, pmid=pmid)
        for x in ['DOI', 'Title', 'Short Name']:
            if not x in result.keys():
                print('Incomplete results')
                return
            header = self.parent()
            header.text_in( result['Title'], result['Short Name'], header.tags_entry.text() )
            header.activate_buttons( result['Short Name'], result['DOI'] )

    def show_widget(self, show=True):
        if show:
            self.interacted = True
        self.setHidden(not show)

        # really bad coding, but it works, somehow resizing of the scroll area widget is needed to get things working
        self.parent().parent().adjustSize()
        for i in range(self.edit_layout.count()):
            self.edit_layout.itemAt(i).widget().cue_edit(True, False)

    def append_on_enter(self, widget):
        if self.edit_layout.count()>0:
            index = self.edit_layout.indexOf(widget)
            #print(index, widget)
            # shouldn't happen, but just as a back up
            if index == -1:
                return
            cursor = widget.edit.textCursor()
            text=''
            if not cursor.atEnd():
                cursor.setPosition( cursor.position(), QTextCursor.MoveAnchor )
                cursor.movePosition( QTextCursor.End , QTextCursor.KeepAnchor )
                text = cursor.selectedText()
                cursor.removeSelectedText()
            #new = self.append_box()
            new = self.append_box(index=index+1, text=text)
            new.setVisible(True)
            self.parent().parent().adjustSize()
            #print(text)
            new.cue_edit(True, False)

    def append_box(self, index=None, text=None):
        new_edit = edit_stack(self, text_size_func=self.resize_func, start_size=None, start_height=40, enter_func=self.append_on_enter, remove_func=self.remove_box, font = self.font)
        if index is None:
            self.edit_layout.addWidget(new_edit)
        else:
            self.edit_layout.insertWidget(index, new_edit)
        if text is not None:
            new_edit.setText(text)
        new_edit.setFocus()
        new_edit.setAcceptDrops(False)
        return new_edit

    def remove_box(self, widget):
        if self.edit_layout.count()>1:
            index = self.edit_layout.indexOf(widget)
            #print(index, widget)
            if index == -1:
                return

            widget.setHidden(True)
            self.edit_layout.removeWidget(widget)

            cursor = widget.edit.textCursor()
            cursor.setPosition( cursor.position(), QTextCursor.MoveAnchor )
            cursor.movePosition( QTextCursor.End , QTextCursor.KeepAnchor )
            text = cursor.selectedText().strip()
            cursor.removeSelectedText()

            if index < self.edit_layout.count() and index > 0:
                #print('index within')
                #self.edit_layout.itemAt(index-1).widget().setFocus()
                edit = self.edit_layout.itemAt(index-1).widget()
            elif self.edit_layout.count() > 1  and index == 0:
                #self.edit_layout.itemAt(1).widget().setFocus()
                edit= self.edit_layout.itemAt(1).widget()
            else:
                #print('index over')
                #self.edit_layout.itemAt(self.edit_layout.count()-1).widget().setFocus()
                edit = self.edit_layout.itemAt(self.edit_layout.count()-1).widget()
            edit.cue_edit(True, True)
            edit.edit.textCursor().movePosition( QTextCursor.End, QTextCursor.MoveAnchor )
            endpos = edit.edit.textCursor().position()

            edit.edit.textCursor().insertText(text)

            cursor = QTextCursor(edit.edit.document())
            cursor.setPosition( endpos )
            edit.edit.setTextCursor(cursor)
            #edit.edit.sizeChange()

    def text_entered(self):
        #self.adjustSize()
        if self.resize_func is not None:
            self.resize_func()

    def text_in(self, pmid, body):
        self.pmid_entry.setText(pmid)
        body = body.split('\n')
        for i in range(len(body)):
            text = body[i].strip()
            if text== '':
                continue
            if i < self.edit_layout.count():
                entry = self.edit_layout.itemAt(i).widget()
            else:
                self.append_box()
                entry = self.edit_layout.itemAt(self.edit_layout.count()-1).widget()
            entry.setText(text)

    def text_out(self):
        pmid = self.pmid_entry.text()
        body = []
        for i in range(self.edit_layout.count()):
            body.append(self.edit_layout.itemAt(i).widget().edit.toPlainText())
        body = '\n'.join(body)
        return {'PMID':pmid,'Notes':body}

    def search_text(self, text):
        found = False
        for x in [self.pmid_entry]:
            x.deselect()
            index = x.text().lower().find(text)
            if index != -1:
                x.setSelection(index, len(text))
                found = True
        for i in range(self.edit_layout.count()) :
            x = self.edit_layout.itemAt(i).widget()
            x.edit.setTextCursor(QTextCursor(x.edit.document()))
            result = x.edit.find(text)
            if result:
                index = x.label.text().lower().find(text)
                x.label.setSelection( index, len(text) )
                found = True
            else:
                x.edit.textCursor().movePosition(QTextCursor.End)
                x.label.setSelection(0,0)
        return found

class edit_stack(QWidget):

    def __init__(self, *args, text_size_func=None, start_size=None, start_height=None, enter_func=None, remove_func=None, font=None, placeholder_text=None, **kwargs):
        super(edit_stack, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()

        #self.setStyleSheet( 'QLabel {background-color: palette(base); border-radius: 3px}' )
        self.stack = QStackedWidget(self)
        #self.dse = QGraphicsDropShadowEffect()
        #self.dse.setBlurRadius(5)
        #self.dse.setOffset( 2, 2)
        #self.dse.setColor( QColor( 30, 30, 30, 180) )
        #self.dse.setColor( QApplication.palette().base().color() )
        self.label = clickLabel(self, self.cue_edit)
        self.label.setWordWrap(True)
        self.label.setContentsMargins(5,5,5,5)
        self.label.setMouseTracking(True)
        #self.label.setGraphicsEffect(self.dse)
        #self.label.setStyleSheet('QLabel {background-color: palette(base); border-radius: 3px}')
        self.edit = GrowingTextEdit(self, text_size_func=self.text_change, start_size=start_size, start_height=start_height, enter_func=enter_func, remove_func=remove_func, to_remove=self, **kwargs)
        self.edit.setAcceptDrops(False)
        self.edit.setContentsMargins(5,0,0,0)

        if placeholder_text is not None:
            self.label.setText(placeholder_text)
            self.edit.setPlaceholderText(placeholder_text)
        else:
            self.label.setText('New Entry')

        self.stack.addWidget(self.label)
        self.stack.addWidget(self.edit)
        self.setMinimumHeight(self.label.rect().height())
        self.font = font
        if font is not None:
            self.label.setFont(font)
            self.edit.setFont(font)

        #self.label.setStyleSheet('QLabel {background-color: palette(base); border-radius: 3px} :disabled {background-color: palette(window)}')

        self.layout.addWidget(self.stack)
        self.layout.setAlignment(Qt.AlignRight)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)

    def set_size(self):
        #self.adjustSize()
        if self.stack.currentIndex() == 0:
            self.resize(self.label.rect().size())
        elif self.stack.currentIndex() == 1:
            #print('setting size')
            #print(self.geometry())
            #self.resize(self.edit.rect().size())
            self.setFixedHeight(self.edit.document().size().height())
            #print(self.geometry())

    def cue_edit(self, activate = True, cursor_end = True):
        if activate:
            self.stack.setCurrentIndex(1)
            self.stack.currentWidget().setFocus()
            self.stack.currentWidget().setFixedHeight(self.label.geometry().height())
            if cursor_end:
                new_cursor = QTextCursor(self.edit.document())
                new_cursor.movePosition(QTextCursor.End)
                self.edit.setTextCursor(new_cursor)
            #self.edit.textCursor().movePosition(QTextCursor.End)
            self.setFixedHeight(self.label.geometry().height())

            if self.stack.currentWidget().text_size_func is not None:
                self.stack.currentWidget().text_size_func()
        else:
            self.stack.setCurrentIndex(0)

    def setText(self, text):
        self.label.setText(text)
        #self.set_size()
        self.edit.setText(text)

    # method passed to the q text edit, use this to change size and the text in the label
    def text_change(self):
        #print('growing text edit')
        self.label.setText(self.edit.toPlainText())
        self.set_size()

#simple label that can be clicked
class clickLabel(QLabel):

    def __init__(self, parent=None, click_func = None,**kwargs):
        super(clickLabel, self).__init__(parent=parent, **kwargs)
        self.click_func = click_func
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def mousePressEvent(self, ev):
        #print('click')
        if self.click_func is not None:
            self.click_func()

# taken from jdi on stackexchange
# with additional modifications
# kept as a reference for now
class GrowingTextEdit(QTextEdit):

    def __init__(self, *args, text_size_func=None, start_size=None, start_height=None, enter_func=None, remove_func=None, to_remove=None, **kwargs):
        super(GrowingTextEdit, self).__init__(*args, **kwargs)
        self.document().contentsChanged.connect(self.sizeChange)
        self.enter_func = enter_func
        self.remove_func = remove_func
        self.to_remove=to_remove

        self.heightMin = 0
        self.heightMax = 65000
        self.text_size_func=text_size_func
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setLineWrapMode(True)
        if start_size is not None:
            self.resize(start_size)
            self.setMaximumHeight(self.rect().height())
            self.heightMin = start_size.height()
        elif start_height is not None:
            self.setMinimumHeight(start_height)
            self.setMaximumHeight(start_height)
            self.heightMin = start_height
        #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def keyPressEvent(self, ev):
        #print('key press')
        if ev.key() == Qt.Key_Return:
            #print('return pressed')
            if self.enter_func is not None and self.toPlainText().strip() != '':
                self.enter_func(self.to_remove)
        elif ev.key() == Qt.Key_Backspace:
            #print('backspace')
            if self.remove_func is not None and self.textCursor().selectedText() == '' and self.textCursor().atStart():
                #print('remove blank')
                #self.setHidden(True)
                self.remove_func(self.to_remove)
            else:
                super(GrowingTextEdit, self).keyPressEvent(ev)
        else:
            super(GrowingTextEdit, self).keyPressEvent(ev)

    def sizeChange(self):
        docHeight = self.document().size().height()
        #print(docHeight, self.geometry().height())
        if self.heightMin <= docHeight <= self.heightMax:
            self.setMinimumHeight(docHeight)
            self.setMaximumHeight(docHeight)
        if self.text_size_func is not None:
            self.text_size_func()

    def resizeEvent(self, ev):
        self.sizeChange()
        super(GrowingTextEdit, self).resizeEvent(ev)

    def focusOutEvent(self, ev):
        #print(self.toPlainText())
        #print('lost focus')
        if self.remove_func is not None and self.toPlainText().strip() == '':
            #print('remove blank')
            #self.setHidden(True)
            self.remove_func(self.to_remove)
        super(GrowingTextEdit, self).focusOutEvent(ev)
