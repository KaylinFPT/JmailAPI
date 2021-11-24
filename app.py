from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.param_functions import Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import DbContext
import uopy
import datetime

app = FastAPI()

origins = ['https://www.google.com']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Jmail(BaseModel):
    Sender: str
    Recipient: str
    Subject: str
    Date: str
    Time:str
    Message: str
    Stype: str
    Attachment:str

jmail =[]

@app.get("/")
def root():
    return ""

@app.get("/Jmail/")
def Get_all():
    ses = uopy.connect(host='172.16.88.23', user='KAYLIN', password='Welcome01', account='DUR')
    records = DbContext.get_all_jmail()
    ses.close()
    return records


@app.get("/Jmail/{id}")
def Get(id: int):
    ses = uopy.connect(host='172.16.88.23', user='KAYLIN', password='Welcome01', account='DUR')
    records = DbContext.get_jmail(id)
    ses.close()
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Jmail {id} not found")
    return records


@app.post("/Jmail")
def Create_Jmail(jmail: Jmail):
    ses = uopy.connect(host='172.16.88.23', user='KAYLIN', password='Welcome01', account='DUR')
    x = datetime.datetime.now()
    try:
        DbContext.create_jmail(jmail.Sender,jmail.Recipient,jmail.Subject,x.strftime("%x"),x.strftime("%X"),jmail.Message,jmail.Stype,jmail.Attachment)
    except NameError:
        print:(NameError)
        #raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="jmail not created")

@app.put("/Jmail/{id}/",status_code=status.HTTP_201_CREATED)
def Update_Jmail(id: int,jmail: Jmail):
    ses = uopy.connect(host='172.16.88.23', user='KAYLIN', password='Welcome01', account='DUR')
   
    try:
        DbContext.update_jmail(id,jmail.Sender,jmail.Recipient,jmail.Subject,jmail.Date,jmail.Time,jmail.Message,jmail.Stype,jmail.Attachment)
    except:
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="jmail not updated")

@app.delete("/Jmail/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stuff(id: int):
    ses = uopy.connect(host='172.16.88.23', user='KAYLIN', password='Welcome01', account='DUR')
    if not DbContext.delete_jmail(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post {id} not found")
    return {"message": f"{id} deleted successfully"}