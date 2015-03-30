import string
import sys
import shutil
import json
import time
import logging
import os

import requests
import lxml.html

class MoodleDownloader:

    loginURL = "login/index.php"
    courseURL = "course/view.php"
    resourceURL = "mod/resource/view.php"

    def __init__(self, user, passwd, url):
        self._cred = [('username', user), ('password', passwd)]
        self._ids = {}
        self._readOldID()
        self._readJSON()
        self._url = url

    def start(self):
        print('Logging in...')
        self._login()
        print('Logged in...')

        self._check()

    def _check(self):

        for course in self._config:
            self._getCourse(self._config[course]['ID'])
            root = lxml.html.fromstring(self._r.text)

            for typ in self._config[course]['type']:
                links = root.xpath("//h3[text() = $type]/../ul/li//a", type=typ)
                fileNames = root.xpath("//h3[text() = $type]/../ul/li//a/span/text()", type=typ)

                if len(links) > 0:
                    # Reverese the elements in links to get the newest elment in the categorie
                    # TODO download also all undownloaded files..
                    links.reverse()
                    fileNames.reverse()
                    courseID = course + "." + typ
                    print('Checking %s in course %s' % (typ, course))

                    # get the ID of the file -> done this way to be sure that the right element is used..
                    for elemList in links[0].items():
                        if elemList[0] == 'href':
                            elemID = elemList[1].split('?id=')[1]

                    if elemID == '':
                        print('Error getting the id from %s' % links[0].items())
                    elif (courseID not in self._ids) or (self._ids[courseID] != elemID):
                        # download & write new config
                        self._downloadPDF(elemID, fileNames[0], self._config[course]['type'][typ])
                        self._newID(courseID, elemID)
                    else:
                        print('No new file for %s in %s...' % (course, typ))
                else:
                    print('No links found for %s!' % course)

    def _login(self):
        ''' Login into the moodle server  '''
        # do redirect manually or otherwise the cookies will be lost
        self._r = requests.post(self._url + self.loginURL, data=self._cred, allow_redirects=False)
        self._cookies = self._r.cookies
        self._r = requests.get(self._r.headers['location'], cookies=self._cookies)

    def _getCourse(self, courseID):
        ''' get the site of an course for further parsing '''
        payload = {'id' : courseID, 'redirect' : 1}
        self._r = requests.get(self._url + self.courseURL, params=payload, cookies=self._cookies, allow_redirects=True)

    def _downloadPDF(self, idOfFile, fileName, path):
        print('Download new file %s with id %s...' % (fileName, idOfFile))
        payload = {'id' : idOfFile}
        self._r = requests.get(self._url + self.resourceURL, params=payload, cookies=self._cookies)

        # Check if the PDF is opend in a viewer, subsite or directly served
        if not self._checkIfPDF():
            self._getPDFOfViewerOrOther(fileName)

        try:
            if 'content-disposition' in self._r.headers:
                pdfName = self._r.headers['content-disposition'].split('filename=')[1].strip('"')
            else:
                pdfName = fileName + ".pdf"
        except AttributeError:
            pdfName = str(time.time()) + ".pdf"

        with open(pdfName, 'wb') as pdfFile:
            pdfFile.write(self._r.content)

        try:
            shutil.move(pdfName, path)
            print('Downloaded %s' % pdfName)
        except shutil.Error:
            os.remove(pdfName)
            print('File %s already exists, deleting downloaded..' % pdfName)


    def _checkIfPDF(self):
        ''' Sometimes a viewer get opened, instead of returning the pdf file '''
        if self._r.text.startswith('<!DOCTYPE'):
            return False
        else:
            return True

    def _getPDFOfViewerOrOther(self, name):
        root = lxml.html.fromstring(self._r.text)
        links = root.xpath("//h2[text() = $name]/..//a", name=name)

        for elemList in links[0].items():
            if elemList[0] == 'href':
                url = elemList[1]

        self._r = requests.get(url, cookies=self._cookies)

    # Read the old id's to not download the same pdf again
    def _readOldID(self):
        try:
            if (os.path.isfile('oldid')) and (os.stat('oldid').st_size > 0):
                oldIDs = open('oldid', 'r')
                self._ids = json.load(oldIDs)
                oldIDs.close()
        except IOError:
            print("Couldn't read oldid file!")
        except:
            print("An error occured while reading the oldid file!")
            print(sys.exc_info())
            sys.exit(0)

    # There is a newer file which has been downloaded
    # so set a new old id for next start
    def _newID(self, keyNew, valueNew):
        try:
            fileID = open('oldid', 'w+')
            self._ids[keyNew] = valueNew
            json.dump(self._ids, fileID)
            fileID.close()
        except IOError:
            print("Couldn't open oldid file for writing!")
            sys.exit(0)
        except:
            print("An error occured while writing the old id file!")
            print(sys.exc_info())
            sys.exit(0)

    # Read the JSON config file
    def _readJSON(self):
        try:
            fileJSON = open('config', 'r')
            self._config = json.load(fileJSON)
            fileJSON.close()
        except IOError:
            print("Couldn't open config file for reading!")
            sys.exit(0)
        except:
            print("An error occured while reading the config file!")
            print(sys.exc_info())
            sys.exit(0)
