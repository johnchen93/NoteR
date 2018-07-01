
'''
noter_io_lite.py provides the in/out functionalities of the NoteR widget, such as writing records to file.

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
import json
import errno
import os

import re
import sys
from bs4 import BeautifulSoup
import requests
import datetime
import shutil
import subprocess
import webbrowser

import argparse

from csv_io import *
from collections import OrderedDict

'''
This version of noter_io is written with python 3 as the main python version
and is remade to use a simpler data reading method, compared to importing pandas.

'''
# work from the directory above the one where the source code or exe is stored to reduce clutter
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

start_path = application_path
os.chdir(application_path)
print(os.getcwd())
os.chdir('..')

# Initialize Noter, load settings and check for default records
def make_sure_path_exists(path):
    # recursively creates a series of directories if it does not already exist
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


# beginning of helper methods
def save_settings(custom_path=None):
    if custom_path:
        path = custom_path
    else:
        path = settings_path
    with open(path, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(settings, ensure_ascii=False))

def merge_records():
    print('merging records')
    new_data_all = []
    for rec in settings['records']:
        print(rec)
        if os.path.isfile( os.path.join(settings['txt_path'], rec+'_noter.tab') ):
            data = read_db(rec)
            if len(data) == 0 :
                return

            revise=False
            if not 'Notes' in data[0].keys():
                revise = True

            new_data=[]
            for row in data:
                new_item = OrderedDict()
                for key, value in row.items():
                    if not revise or (revise and key not in ['Main Findings','Tags','Method Notes']):
                        new_item[key] = value
                    elif key == 'Main Findings':
                        new_item['Notes'] = row['Main Findings'] + '\n' + row['Method Notes']
                    elif key == 'Tags':
                        new_item[key] = rec
                new_data.append(new_item)

            new_data_all.extend(new_data)
    #print(new_data_all)
    if len(new_data_all) > 0:
        csv_out( new_data_all, os.path.join( settings['txt_path'], 'noter_records.tab' ))
    else:
        # just make a blank file
        with open(os.path.join( settings['txt_path'], 'noter_records.tab' ), 'w'):
            print('making an empty file')

def conservative_load(path):
    if os.path.isfile( path ):
        data = csv_in(path, delimiter='\t')
        if len(data) == 0 :
            return

        mapping = { 'Title':[], 'Short Name':['short name', 'shortname','short_name'], 'PMID':['pubmed id','pubmed_id'], 'DOI':[], 'Notes':[], 'Main Findings':['main_findings','main_finding','main finding'], 'Method Notes':['method_notes','methods','method note', 'method_note'], 'Tags':[] }
        data = equiv_headers(data, mapping)
        revise=False
        if not 'Notes' in data[0].keys():
            revise = True

        new_data=[]
        for row in data:
            new_item = OrderedDict()
            for key, value in row.items():
                if not revise or (revise and key not in ['Main Findings','Method Notes']):
                    new_item[key] = value
                elif key == 'Main Findings':
                    new_item['Notes'] = row['Main Findings'] + '\n' + row['Method Notes']
                #elif key == 'Tags':
                #    new_item[key] = rec
            new_data.append(new_item)
        return new_data

def equiv_headers(data, mapping):
    headers = data[0].keys()
    new_dict = {}
    for x in headers:
        for name, equiv in mapping.items():
            equiv.append(name.lower())
            if x in equiv or x == name:
                new_dict[x] = name
                break
    out = []
    for row in data:
        renamed = {}
        for k, v in row.items():
            renamed[ new_dict[k] ] = v
        out.append(renamed)

    return out

def read_db(path):
    if os.path.isfile(path):
        data = csv_in( path, delimiter='\t')
        return data
    else:
        return None

def read_aggregate_db():
    if not settings.get('aggregated'):
        return None
    return csv_in( os.path.join(settings['txt_path'], 'noter_records.tab' ), delimiter='\t')

def save_aggregate(data):
    csv_out( data, os.path.join( settings['txt_path'], 'noter_records.tab' ))

def extract_db_lite(path, fetch=False, progress_signal=None):

    data = conservative_load(path)
    if len(data) == 0:
        return

    total=len(data)
    curr=0
    if fetch:
        for row in data:
            curr+=1
            row['PMID'] = str(row['PMID']).split('.')[0]
            if not row['PMID'] in ['']:
                fetch_pmid(row, log=None)
            if progress_signal is not None:
                progress_signal.emit(curr/total*100)

    return data

def get_backup_directory():
    return settings['dump_path']

def backup_dump( data):
    dump_time = datetime.datetime.now().strftime("%Y%m%d")
    csv_out(data,os.path.join(settings['dump_path'], 'noter_records_{}.tab'.format(dump_time)), delimiter='\t')
    save_settings( custom_path = os.path.join( settings['dump_path'], 'noter_settings_{}.txt'.format(dump_time)) )
    return

def load_last_backup():
    filenames = []
    for root, directory, files in os.walk( settings['dump_path'] ):
        filenames.extend(files)
    to_find = settings['records'] + ['noter_settings']
    to_find = [ 'noter_records', 'noter_settings' ]
    found = {}
    for f in filenames:
        front = os.path.splitext(f)[0]
        name = '_'.join(front.split('_')[:-1])
        date = front.split('_')[-1:][0]
        if name in to_find:
            try:
                found[name].append(int(date))
            except:
                found[name] = [int(date)]
    for name, dates in found.items():
        last_date = str(max(dates))
        if name == 'noter_settings':
            with open( name+'.txt', 'w' ) as f_out:
                with open( os.path.join( settings['dump_path'], name+'_'+last_date+'.txt'), 'r' ) as f_in:
                    for line in f_in:
                        f_out.write(line)
        elif name == 'noter_records':
            data = read_db( os.path.join( settings['dump_path'], name+'_'+last_date+'.txt') )
        #else:
        #    extract_db( os.path.join( settings['dump_path'], name+'_'+last_date+'.tab') , name, form='tab' )
    return data

def fetch_pmid(row, log=None, pmid=None):
    if pmid is not None:
        pmid = pmid
        row = {}
    else:
        pmid = row['PMID']
    if not pmid in ['nan']:
        try:
            pmo = PubMedObject(pmid = pmid)
            if pmo.soup:
                print('Page found, extracting info')
                row['Title'] = pmo.title
                first_author = pmo.first_author
                cit = pmo.citation
                row['Short Name'] = pmo.short_name
                row['DOI'] = pmo.ext_url
            else:
                print('Something went wrong, the page was not found. Please check the PMID is correct')
        except:
            print('Query for pmid failed, please check there is internet connection')
    return row

def make_short_name(author, cit):
    author = ''.join(author.split('.'))
    fa_split = author.split(',')
    fa_last = fa_split[0].strip()
    fa_init = fa_split[1].strip()

    cit_split = ''.join(cit.split(';')[0].split('.'))
    short_name = '{}_{}( {} )'.format( fa_last, fa_init, cit_split )
    return short_name

def short_name_to_file_name(short_name, log=None):
    sn_list = list(short_name)
    for char in avoid_in_filename:
        if char in sn_list:
            print('The character \'{}\' is not suitable for a filename, please change the short name to remove this character.'.format(char))
            if log is not None:
                log.append('The character \'{}\' is not suitable for a filename, please change the short name to remove this character.'.format(char))
            return
    rem_full_stop = ''.join( short_name.split('.') )
    rem_comma = '_'.join( rem_full_stop.split(',') )
    return rem_comma

def add_pdf(file_path, out_name, record=None, log=None):
    if record:
        pdf_dir = os.path.join( settings['pdf_path'], record )
    else:
        pdf_dir = settings['pdf_path']

    make_sure_path_exists( pdf_dir )
    name = short_name_to_file_name(out_name, log=log)
    if name:
    # some form of valid filename was made
        try:
            shutil.copyfile(file_path, os.path.join(pdf_dir, name+'.pdf') )
            print('The file for {} was copied to {}'.format(name, pdf_dir) )
            if log is not None:
                log.append('The file for {} was copied to {}'.format(name, pdf_dir) )
            return True
        except:
            print('The file was not copied')
    elif name == '':
        if log is not None:
            log.append('The short name field is empty. The entry must have a short name to track pdfs.')

def find_pdf(out_name, record=None):
    name = short_name_to_file_name(out_name)
    if record is not None:
        path = os.path.join(settings['pdf_path'], record, name+'.pdf')
    else:
        path = os.path.join(settings['pdf_path'], name+'.pdf')
    #if name and record:
        #try:
        #    with open( os.path.join(settings['pdf_path'], record, name+'.pdf'), 'r'):
        #        return True
        #except:
        #    print('The PDF file for \'{}\' was not found'.format(name))
        #    return False
    return os.path.isfile(path)

def noter_open_pdf(out_name, record=None):
    name = short_name_to_file_name(out_name)

    if record is not None:
        path = os.path.join(settings['pdf_path'], record, name+'.pdf')
    else:
        path = os.path.join(settings['pdf_path'], name+'.pdf')

    if curr_os in ['darwin','linux','linux2']:
        command = ['open']
    elif curr_os in ['win32','cygwin']:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        command = ['cmd','/C','start', '' ]
    #if name and record:
    try:
        if curr_os in ['darwin','linux','linux2']:
            command = ['open']
            subprocess.call( command + [ path ] )
        elif curr_os in ['win32','cygwin']:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            command = ['cmd','/C','start', '' ]
            subprocess.call( command + [ path ], startupinfo=si )
    except:
        print('Failed to open pdf')

def noter_open_doi(doi):
    try:
        print(doi)
        webbrowser.open(doi, new=0, autoraise=True)
    except:
        print('Failed to open external url')


class PubMedObject(object):
    soup = None
    url = None

    # pmid is a PubMed ID
    # url is the url of the PubMed web page
    # search_term is the string used in the search box on the PubMed website
    def __init__(self, pmid=None, url='', search_term=''):
        if pmid:
            pmid = str(pmid).strip()
            url = "http://www.ncbi.nlm.nih.gov/pubmed/%s" % pmid
            self.pmid = pmid
        if search_term:
            url = "http://www.ncbi.nlm.nih.gov/pubmed/?term=%s" % search_term
        try:
            page = requests.get(url).text
            self.soup = BeautifulSoup(page, "html.parser")
        except:
            print('The connection could not be made.')
            return

        # set the url to be the fixed one with the PubMedID instead of the search_term
        if search_term:
            try:
                url = "http://www.ncbi.nlm.nih.gov/pubmed/%s" % self.soup.find("dl",class_="rprtid").find("dd").text
            except AttributeError as e:  # NoneType has no find method
                print("Error on search_term=%s" % search_term)
        self.url = url
        self.pre_fetch()

    def pre_fetch(self):
        self.title = self.get_title()
        self.authors, self.first_author = self.get_authors()
        self.citation = self.get_citation()
        self.ext_url = self.get_external_url()

        self.short_name = make_short_name(self.first_author, self.citation)

    def get_title(self):
        return self.soup.find(class_="abstract").find("h1").text

    #auths is the string that has the list of authors to return
    def get_authors(self):
        result = []
        author_list = [a.text for a in self.soup.find(class_="auths").findAll("a")]
        for author in author_list:
            lname, remainder = author.rsplit(' ', 1)
            #add periods after each letter in the first name
            fname = ".".join(remainder) + "."
            result.append(lname + ', ' + fname)

        return ', '.join(result), result[0]

    def get_citation(self):
        return self.soup.find(class_="cit").text

    def get_external_url(self):
        url = None
        doi_string = self.soup.find(text=re.compile("doi:"))
        if doi_string:
            doi = doi_string.split("doi:")[-1].strip().split(" ")[0][:-1]
            if doi:
                url = "http://dx.doi.org/%s" % doi
        else:
            doi_string = self.soup.find(class_="portlet")
            if doi_string:
                doi_string = doi_string.find("a")['href']
                if doi_string:
                    return doi_string

        return url or self.url

def set_default_style(style):
    settings['def_style'] = style
    save_settings()

def get_default_style():
    return settings.get('def_style')

def set_autosave(boolean):
    settings['autosave'] = boolean
    save_settings()

def get_autosave():
    return settings.get('autosave')

# things to do on import
curr_os = sys.platform

avoid_in_filename = ['\\','/',':','*','?','\"','\'','<','>','|']

# minimum required fields to be compatible with this program
#req_fields = ['PMID','Title','Short Name']
#basic_fields = ['Main Findings','Tags','Method Notes','PMID','Title','Short Name','DOI']

#field_order = ['Main Findings','Method Notes','Tags','Short Name','PMID','Title','DOI']
#reader_order = ['Title','Short Name','PMID','DOI','Tags','Main Findings','Method Notes']

settings_path = os.path.join( start_path, 'noter_settings.txt' )
settings_list = ['txt_path','dump_path','pdf_path']

if os.path.isfile(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
else:
    # make a fresh settings file
    settings = {'txt_path':'txt_records','dump_path':'backup','pdf_path':'pdf','records':[]}
    with open(settings_path, 'w', encoding='utf-8') as outfile:
        outfile.write(json.dumps(settings, ensure_ascii=False))

for setting in settings_list:
    try:
        settings[setting]
        print("{} found.".format(setting))
    except:
        raise Exception('{} was not found in settings.'.format(setting))
    make_sure_path_exists(settings[setting])

if not 'records' in settings.keys():
    settings['records'] = []

for rec in settings['records']:
    rec_path = os.path.join( settings['txt_path'] , rec+'_noter.tab' )
    if not os.path.isfile(rec_path):
        settings['records'].remove(rec)

if not settings.get('aggregated') or not os.path.isfile( os.path.join( settings['txt_path'], 'noter_records.tab' ) ):
    merge_records()
    settings['aggregated'] = True
    save_settings()
# run if used as main program
#if __name__ == '__main__':
#    parser = argparse.ArgumentParser(description='Helper program for NOTER. Can be run to import database from an excel file.')
#    parser.add_argument("-imp", type = str, help = 'File path for importing a records file, the file must have \'Main Findings\', \'Method Notes\',\'Tags\' and \'PMID\' as headers.')
#    parser.add_argument("-imp_as", type = str, help = 'Name for the imported database.')
#    parser.add_argument('-e', action='store_true', help = 'Sets the flag to find the file specified by -imp inside the excel folder set in settings')
#    parser.add_argument('-r', action='store_true', help = 'Refresh the data base, retrieving info. Recommended to back up before this.')
#    parser.add_argument('-b', action='store_true', help = 'Backup all records on file')
#    parser.add_argument('-l', action='store_true', help = 'Load backup from latest date')
#    args = parser.parse_args()

#    if args.b:
#        backup_all()
#    elif args.l:
#        load_last_backup()
#    elif args.r:
#        refresh_db()
#    elif args.imp:
#        if args.imp_as:
#            name = args.imp_as
#        else:
#            name = os.path.splitext(args.imp)[0]
#        if args.e:
#            path = os.path.join(settings['excel_path'], args.imp)
#        else:
#            path = args.imp

        #extract_db( path, name)

