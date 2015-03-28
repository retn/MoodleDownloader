import string
import sys
import shutil
import json
import time


import requests
import lxml.html

class MoodleDownloader:

    def __init__(self, user, passwd):
        self.__cred = [('username', user), ('password', passwd)]
        self.__ids = {}
        self.__readOldID()
        self.__readJSON()
        self.__url = "https://moodle.adress-of-your-university-or-whatever.edu"

    def start(self):
        print 'Logging in...'
        self.__login()
        print 'Logged in...'

        self.__check()

    def __check(self):

        for course in self.__config:
            self.__getCourse(self.__config[course]['ID'])
            root = lxml.html.fromstring(self.__r.text)

            for typ in self.__config[course]['type']:
                links = root.xpath("//h3[text() = $type]/../ul/li//a", type=typ)
                fileNames = root.xpath("//h3[text() = $type]/../ul/li//a/span/text()", type=typ)

                if len(links) > 0:
                    # Reverese the elements in links to get the newest elment in the categorie
                    # TODO download also all undownloaded files..
                    links.reverse()
                    fileNames.reverse()
                    courseID = course + "." + typ
                    print 'Checking', self.__config[course]['type'][typ], 'in course', course

                    # get the ID of the file -> done this way to be sure that the right element is used..
                    for elemList in links[0].items():
                        if elemList[0] == 'href':
                            elemID = elemList[1].split('?id=')[1]
                            break

                    if elemID == '':
                        print 'Error getting the id from', links[0].items()
                    elif (courseID not in self.__ids) or (self.__ids[courseID] != elemID):
                        # download & write new config
                        self.__downloadPDF(elemID, fileNames[0], self.__config[course]['type'][typ])
                        self.__newID(courseID, elemID)
                    else:
                        print 'No new file for ', course, ' in ', typ,'...'
                else:
                    print 'No links found for ', course , '!'

    def __login(self):
        ''' Login into the moodle server  '''
        # do redirect manually or otherwise the cookies will be lost
        self.__r = requests.post(self.__url + "login/index.php", data=self.__cred, allow_redirects=False)
        self.__cookies = self.__r.cookies
        self.__r = requests.get(self.__r.headers['location'], cookies=self.__cookies)

    def __getCourse(self, courseID):
        ''' get the site of an course for further parsing '''
        payload = {'id' : courseID}
        self.__r = requests.get(self.__url + "course/view.php", params=payload, cookies=self.__cookies)

    def __downloadPDF(self, idOfFile, fileName, path):
        print 'Download new file', fileName, 'with id', idOfFile, '...'
        payload = {'id' : idOfFile}
        self.__r = requests.get(self.__url + 'mod/resource/view.php', params=payload, cookies=self.__cookies)

        # Check if the PDF is opend in a viewer or directly served
        if not self.__checkIfPDF():
            self.__getPDFOfViewer()

        try:
            if 'content-disposition' in self.__r.headers:
                pdfName = self.__r.headers['content-disposition'].split('filename=')[1].strip('"')
            else:
                pdfName = fileName + ".pdf"
        except AttributeError:
            pdfName = str(time.time()) + ".pdf"

        with open(pdfName, 'wb') as pdfFile:
            pdfFile.write(self.__r.content)

        shutil.move(pdfName, path)
        print 'Downloaded', pdfName

    def __checkIfPDF(self):
        ''' Sometimes a viewer get opened, instead of returning the pdf file '''
        if self.__r.text.startswith('<!DOCTYPE'):
            #print 'PDF in viewer'
            return False
        else:
            #print 'PDF-File directly'
            return True

    def __getPDFOfViewer(self):
        self.__r = requests.get(self.__r.url, cookies=self.__cookies)

    # Read the old id's to not download the same pdf again
    def __readOldID(self):
        try:
            oldIDs = open('oldid', 'r+')
            self.__ids = json.load(oldIDs)
            oldIDs.close()
        except IOError:
            print "Couldn't read oldid file!"
            sys.exit(0)
        except:
            print "An error occured while reading the oldid file!"
            print sys.exc_info()
            sys.exit(0)

    # There is a newer file which has been downloaded
    # so set a new old id for next start
    def __newID(self, keyNew, valueNew):
        try:
            fileID = open('oldid', 'w+')
            self.__ids[keyNew] = valueNew
            json.dump(self.__ids, fileID)
            fileID.close()
        except IOError:
            print "Couldn't open oldid file for writing!"
            sys.exit(0)
        except:
            print "An error occured while writing the old id file!"
            print sys.exc_info()
            sys.exit(0)

    # Read the JSON config file
    def __readJSON(self):
        try:
            fileJSON = open('config', 'r')
            self.__config = json.load(fileJSON)
            fileJSON.close()
        except IOError:
            print "Couldn't open config file for reading!"
            sys.exit(0)
        except:
            print "An error occured while reading the config file!"
            print sys.exc_info()
            sys.exit(0)
