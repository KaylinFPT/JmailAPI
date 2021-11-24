from logging import Formatter
from os import times
import uopy
from uopy import Session, File, List, DynArray
from uopy import EXEC_MORE_OUTPUT, Command
from uopy import UOError
import gc


ses = uopy.connect(host='172.16.88.23', user='KAYLIN', password='Welcome01', account='DUR')

def getSelectList( thelistcommand ):
    """getSelectList( thelistcommand ) - returns selected items as pythonlist"""
    
    cmd = Command(session=ses)
    cmd.command_text = "CLEARSELECT"
    cmd.run()
    cmd.command_text = thelistcommand
    cmd.run()
	
    theRtnList = []
    try:
        theList = List(0, session=ses)
        theidList = theList.read_list()
        #print(theDynList.count(0))
        
        for each in theidList:
            if len(each) > 0:
                theRtnList.extend( [each] )

        return theRtnList
    except UOError as e:
        return theRtnList

def get_all_jmail():
    ListOfIds = getSelectList('SELECT JMAIL.Q')
    AllRecords = list()
    test_file = File("JMAIL.Q")

    for i,id in enumerate(ListOfIds):
        record =test_file.read(id)
        recordlist = record.list
        SENDER = recordlist[0]
        RECIPIENT = recordlist[1]
        SUBJECT = recordlist[2]
        DATE =recordlist[3]
        TIME = recordlist[4]
        MESSAGE = recordlist[5]
        STYPE = recordlist[6]
        ATTACHMENT = recordlist[7]

        record = {
            "id": id,
            "sender": str(SENDER),
            "recipient": str(RECIPIENT),
            "subject": str(SUBJECT),
            "date":str(DATE),
            "time":str(TIME),
            "message": str(MESSAGE),
            "stype": str(STYPE),
            "attachment":str(ATTACHMENT)    
            }            
        AllRecords.append(record)
    return AllRecords

def get_jmail(id):
    test_file = File("JMAIL.Q")
    try:
        record =test_file.read(id)
        recordlist = record.list
        SENDER = recordlist[0]
        RECIPIENT = recordlist[1]
        SUBJECT = recordlist[2]
        DATE =recordlist[3]
        TIME = recordlist[4]
        MESSAGE = recordlist[5]
        STYPE = recordlist[6]
        ATTACHMENT = recordlist[7]
        record = {
            "id": id,
            "sender": str(SENDER),
            "recipient": str(RECIPIENT),
            "subject": str(SUBJECT),
            "date":str(DATE),
            "time":str(TIME),
            "message": str(MESSAGE),
            "stype": str(STYPE),
            "attachment":str(ATTACHMENT)    
            }                    
        return record
    except:
        return None

def create_jmail(sender,recipient,subject,date,time,message,stype,attachment):
    ListOfIds = getSelectList('SELECT JMAIL.Q')
    lastId = ListOfIds[len(ListOfIds) -1]
    newId = int(lastId) + 1
    with File("JMAIL.Q") as test_file:
        test_file.write(newId,[sender,recipient,subject,date,time,message,stype,attachment])
        
def update_jmail(id,sender,recipient,subject,date,time,message,stype,attachment):
    with File("JMAIL.Q") as test_file:
        test_file.write(id,[sender,recipient,subject,date,time,message,stype,attachment])

def delete_jmail(id):
    test_file = File("JMAIL.Q")
    try:
        test_file.delete(id)
        return True
    except:
        return False
