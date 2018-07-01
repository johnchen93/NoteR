'''
noter_2.py is the main code body that executes the NoteR widget.

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
import queue
import time
from threading import Thread
import widget_styles
from base_widget import base_widget
from noter_list_widget import noter_list
from noter_io_lite import *
from csv_io import find_row

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
#import ctypes
#myappid = u'noter.app' # arbitrary string
#ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def main():

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(start_path+'/noter_icon.ico'))

    w = noter_widget()
    #noter_w = noter_widget()
    #w.append_widget(noter_w)
    #w.setWindowIcon(QIcon('icon.png'))
    w.show()
    #w.setWindowIcon(QIcon('icon.png'))
    sys.exit(app.exec_())

class noter_widget(base_widget):

    progress_signal = pyqtSignal(int)
    completion_signal = pyqtSignal(object, list)
    timer_signal = pyqtSignal()
    save_signal = pyqtSignal()

    def __init__(self):
        # create some testing widget
        super(noter_widget, self).__init__(title='NoteR')
        def_style = get_default_style()
        if def_style is None or def_style not in self.palettes.palette_keys():
            def_style = self.palettes.def_pal

        self.widgets = []
        self.thread_queue = TaskQueue(num_workers=3)
        self.timer_signal.connect(self.periodic_save)

        layout = QVBoxLayout()

        # create a menu bar
        self.menubar = QMenuBar(self)
        self.menubar.setNativeMenuBar(False)
        filemenu = self.menubar.addMenu('File')
        filemenu.addAction('New entry', self.new_entry, QKeySequence.New)
        filemenu.addAction('Save',  self.save, QKeySequence.Save)
        filemenu.addAction('Import Records', self.import_record)
        filemenu.addSeparator()
        filemenu.addAction('Backup Records', self.backup_record)
        filemenu.addAction('Load Backup', self.load_backup)
        configmenu = self.menubar.addMenu('Config')
        stylemenu = configmenu.addMenu('Style')
        self.styleoptions = []
        for x in sorted(self.palettes.palette_keys()):
            temp_act = check_action(x, stylemenu, self.change_style)
            stylemenu.addAction(temp_act)
            temp_act.setCheckable(True)
            self.styleoptions.append(temp_act)
            if x == def_style:
                temp_act.setChecked(True)
        self.autosave_on = get_autosave()
        if self.autosave_on is None:
            self.autosave_on = True
            set_autosave(self.autosave_on)
        autosave = check_action('Auto-save',configmenu, self.toggle_autosave)
        autosave.setCheckable(True)
        autosave.setChecked(self.autosave_on)
        configmenu.addAction(autosave)

        self.widgets.append(self.menubar)
        layout.addWidget(self.menubar)

        # setting the style
        self.curr_style = None
        self.change_style(def_style)

        # add the search bar
        self.search_layout = QHBoxLayout()
        self.search_layout.setContentsMargins(5,10 ,5, 10)
        self.search_entry = QLineEdit('')
        self.search_entry.setPlaceholderText('Search... or click the magnifying glass for a list of all tags.')
        self.search_entry.setClearButtonEnabled(True)
        tags_action = self.search_entry.addAction(QIcon(start_path+'/search_icon2.png'), QLineEdit.LeadingPosition)
        self.search_entry.returnPressed.connect(self.search_entries)
        self.search_button = QPushButton('Go')
        self.search_button.clicked.connect(self.search_entries)
        self.search_layout.addWidget(self.search_entry)
        self.search_layout.addWidget(self.search_button)
        layout.addLayout(self.search_layout)

        # add a status bar
        self.status_layout = QHBoxLayout()
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_layout.addWidget(self.status_bar)
        self.status_layout.addWidget(self.progress_bar)
        layout.addLayout(self.status_layout)

        # add the main text widget
        self.data = read_aggregate_db()
        self.nl = noter_list(parent=None, fontsize=12, tags_func = self.start_tags_dialog)
        self.nl.load_entries(self.data)
        self.list_tags(self.data)
        self.widgets.append(self.nl)
        layout.addWidget(self.nl)

        # set up autocomplete for tags in the search
        #self.set_completer()
        tags_action.triggered.connect(self.completer.complete)

        # add the layout to the base frame
        self.append_layout(layout)

        self.resize(600, 800)

        # connect signals
        self.filename_hold = None
        self.progress_signal.connect(self.set_progress_bar)
        self.completion_signal.connect(self.merge_new_records)
        self.timer_signal.connect(self.periodic_save)
        self.save_signal.connect(self.show_save_message)

        self.periodic_save()

    def set_completer(self):

        self.completer = QCompleter(self.all_tags, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        #completer.setCompletionMode(QCompleter.InlineCompletion)
        self.search_entry.setCompleter(self.completer)

    def change_style(self, style, state=True):
        #print(style, state)
        if self.curr_style is None or style != self.curr_style:
            self.curr_style = style
            self.app.setPalette(self.palettes.get_palette(style))
            #for x in self.widgets:
            #    x.setPalette(self.palettes.get_palette(style))
            for x in self.styleoptions:
                if x.text() != style:
                    x.setChecked(False)
            set_default_style(self.curr_style)

    def periodic_save(self):
        if self.autosave_on:
            self.save()
        print('calling periodic func')
        self.thread_queue.add_task(periodic_func, 60, self.periodic_save)

    def backup_record(self):
        self.save()
        #print(len(self.data))
        backup_dump(self.data)

    def list_tags(self, data):
        tags_list = []
        for row in data:
            tags = row['Tags'].split(',')
            tags_list.extend(tags)
        unique = [ x.strip() for x in list(set(tags_list)) ]
        unique = [ x for x in unique if x != '' ]
        self.all_tags = sorted(unique)
        self.set_completer()

    def search_entries(self):
        text = self.search_entry.text().strip().lower()
        if text != '':
            self.nl.search_entries(text)
        else:
            self.nl.show_all()

    def save(self):
        print('saving')
        self.save_signal.emit()
        self.nl.save()

    def show_save_message(self):
        self.status_bar.showMessage('Saving...', 2000)

    def toggle_autosave(self, text, state):
        print('auto-save option: {}'.format(state))
        self.autosave_on = state

    def import_record(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self,"Select a file to load.", "","All Files (*);;Excel Files (*.xls, *.xlsx);;Tab separated files (*.tab)", options=options)
        if filename:
            self.filename_hold = filename
            print(filename)
            self.start_tags_dialog(self.new_record_dialog, [])

    def new_record_dialog(self, tags=[]):
        resp = QMessageBox.question(self, 'Get Info from PubMed?', 'Do you wish to fetch info based on PubMed IDs?\nThis will fail if you do not have internet or you do not have PubMed IDs in the imported record.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #print(resp)
        if resp == QMessageBox.Yes:
            fetch = True
        else:
            fetch = False
        #resp = QMessageBox.information(self, 'Importing Record', 'NoteR will load your entries in the background, you can continue to use the main window. NOTE: Entries that already exist are ignored and only the current entry will be kept.', QMessageBox.Ok)
        self.thread_queue.add_task(load_record, self.filename_hold, fetch, self.progress_signal, self.completion_signal, tags = tags)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage('Loading records')
        self.filename_hold = None

    def set_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def merge_new_records(self, data, tags=[]):
        new_count = 0
        old_count = 0
        append_list = []
        data = self.dedup(data)
        for row in data:
            title = row.get('Title')
            #shortname = row.get('Short Name')
            pmid = row.get('PMID')
            id_list = [title, pmid]
            is_old = False
            for curr_data in self.data:
                curr_title = curr_data.get('Title')
                #curr_shortname = curr_data.get('Short Name')
                curr_pmid = curr_data.get('PMID')
                for x in [curr_title, curr_pmid]:
                    if x in id_list:
                        old_count +=1
                        is_old = True
                        break
                if is_old:
                    break
            if is_old:
                continue
            else:
                new_count += 1
                append_list.append(row)
        # set the tags given by the user
        # if none are chosen use the existing tags
        if len(tags) > 0:
            for row in append_list:
                row['Tags'] = ', '.join(tags)

        self.nl.load_entries(append_list, append=True)

        QMessageBox.information(self, 'Records Loaded', 'Your imported records have been loaded. {} new entries were added and {} existing records were found.'.format(new_count, old_count), QMessageBox.Ok)

        self.progress_bar.setVisible(False)
        self.status_bar.showMessage('Loading complete', 3000)

        #self.data.extend(append_list)
        self.list_tags(self.data)

    def dedup(self, data):

        unique_sets = []
        dups_seen = []
        for i in range(len(data)):
            x = data[i]
            if x in dups_seen:
                continue
            title = x.get('Title')
            #shortname = x.get('Short Name')
            pmid = x.get('PMID')
            id_list_x = [title, pmid]
            dups_list = [x]
            for k in range(len(data)):
                y = data[k]
                if i == k:
                    continue
                title = y.get('Title')
                #shortname = y.get('Short Name')
                pmid = y.get('PMID')
                id_list_y = [title, pmid]
                for term in id_list_y:
                    if term in id_list_x:
                        dups_list.append(y)
                        break
            unique_sets.append(dups_list)
            if len(dups_list) > 1:
                dups_seen.extend(dups_list)
        out = []
        for x in unique_sets:
            out.extend(x)
        #print(out)
        return out

    def new_entry(self):
        print('making new entry')
        self.nl.new_entry()

    def start_tags_dialog(self, return_func, checked):
        #print(return_func)
        dialog = tags_dialog(self.all_tags, return_func, checked, self.refresh_tags)
        dialog.exec()

    def refresh_tags(self, tags):
        self.all_tags = tags
        self.set_completer()

    def load_backup(self):

        QMessageBox.information(self, 'Load Records from Backup', 'You have selected to load a backup file. This differs from a regular import in that ALL ENTRIES WILL BE REPLACED with those in the backup file. If you are unsure the file being loaded is the right one, backup your current work using File>Backup Records.', QMessageBox.Ok)

        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self,"Select a file to load.", get_backup_directory() ,"All Files (*);;Excel Files (*.xls, *.xlsx);;Tab separated files (*.tab)", options=options)

        data = conservative_load(filename)
        self.nl.load_entries(data)
        self.list_tags(self.data)

    def closeEvent(self, event):
        if self.autosave_on:
            self.save()

        autosave_text = 'Auto-save is on.'
        if not self.autosave_on:
            autosave_text = 'Auto-save is off.'
        quit_msg = "Are you sure you want to exit the program? {}".format(autosave_text)
        reply = QMessageBox.question(self, 'Quit Noter',
                         quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def load_record(path, fetch=False, progress_signal=None, completion_signal=None, tags=[]):
    if path is None:
        return
    #feed = feedparser.parse(url)
    #if finish_signal:
    #    finish_signal.emit(feed, url)
    data=extract_db_lite(path, fetch, progress_signal)
    #print('processed {}'.format(url))
    if completion_signal is not None:
        completion_signal.emit(data, tags)

def periodic_func(delay, func=None, periodic_signal=None):
    time.sleep(delay)
    if func:
        func()
    #if periodic_signal:
    #    periodic_signal.emit()

class check_action(QAction):

    emit_text = pyqtSignal(str)

    def __init__(self, string, parent=None, func=None):
        super(check_action, self).__init__(string, parent)
        self.triggered.connect(self.give_text)
        self.func = func

    def give_text( self, state):
        #print(state)
        if self.func is not None:
            self.func( self.text(), state )

class tags_dialog(QDialog):

    return_tags_signal = pyqtSignal(list)

    def __init__(self, tags=[], caller_func=None, checked=[], add_tag_func=None):
        super(tags_dialog, self).__init__()
        if caller_func is not None:
            self.return_tags_signal.connect( caller_func )
        #flags = Qt.WindowFlags(Qt.FramelessWindowHint) # | Qt.WindowStaysOnTopHint)
        #self.setWindowFlags(flags)
        self.setWindowTitle('Manage Tags')

        self.tags_list = tags
        self.checked = checked
        self.add_tag_func = add_tag_func

        layout=QVBoxLayout()

        self.label = QLabel('Please choose the tags associated with this entry. \n\nIf making new tags, try to make them unique and different than what might be easily found in regular text; e.g. \'evolution_papers\' vs \'evolution\'. This will make searches more effective.')
        self.label.setWordWrap(True)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        layout.addWidget(self.label)

        self.entry_bar = QHBoxLayout()
        self.tags_entry = QLineEdit()
        self.tags_entry.setPlaceholderText('Add a new tag')
        self.add_button = QPushButton('New')
        self.add_button.clicked.connect(self.add_tag)
        self.entry_bar.addWidget(self.tags_entry)
        self.entry_bar.addWidget(self.add_button)
        layout.addLayout(self.entry_bar)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Available Tags'])
        #print(self.tree.topLevelItemCount())
        self.tree_widget.itemClicked.connect(self.toggle_tag)
        layout.addWidget(self.tree_widget)

        buttons = QHBoxLayout()
        ok_button = QPushButton('Ok')
        ok_button.clicked.connect(self.return_tags)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        self.setLayout(layout)

        self.load_tree(self.tags_list)

    def load_tree(self, tags):
        self.tree_widget.clear()
        for x in tags:
            item = QTreeWidgetItem( [x])
            item.setFlags( item.flags() | Qt.ItemIsUserCheckable )
            if x in self.checked:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)
            self.tree_widget.addTopLevelItem(item)

    def return_tags(self):
        self.accept()
        tags = []
        #print(self.tree_widget.topLevelItemCount())
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.checkState(0) == Qt.Checked:
                tags.append(item.text(0))
        self.return_tags_signal.emit( tags )

    def toggle_tag(self, item, column):
        if item.checkState(0) == Qt.Unchecked:
            item.setCheckState(0, Qt.Checked)
        else:
            item.setCheckState(0, Qt.Unchecked)

    def add_tag(self):
        tag = self.tags_entry.text()
        if tag not in self.tags_list:
            self.tags_list.append(tag)
            self.load_tree( self.tags_list )
            if self.add_tag_func is not None:
                self.add_tag_func(self.tags_list)

class TaskQueue(queue.Queue):

    def __init__(self, num_workers=1, timeout=None):
        queue.Queue.__init__(self)
        self.num_workers = num_workers
        self.timeout = timeout
        self.start_workers()

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put((task, args, kwargs), True, self.timeout)

    def start_workers(self):
        for i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            item, args, kwargs = self.get()
            print('starting task')
            item(*args, **kwargs)
            self.task_done()

if __name__ == '__main__':
    main()
