# encoding=UTF-8
import logging
import _thread
import time
import requests
import json

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

def run():
    lens = 0
    file = open('TestInput0.raw', 'rb')
    DataBuffer = file.read()
    lens = len(DataBuffer)
    
    gStartTime = time.time()
    #步驟一:設定參數
    header = {
      'Action': 'connect',
      'IP': '127.0.0.1',
      'AsrType': 'AsrAgent',
      'ClientName': 'AssistantTest',
      'MaxCandidateNum': '3',
      'AsrEngName': 'TLAsrSrv_SttDnnKd',
      'SpeechFormat': '0',
      'AsrGrmNum': '0',
      'AsrGrmName0': ''
    }
    
    #步驟二:開始連線，因為要用http 1.1 keep-alive python必須用session
    session = requests.Session()
    res = session.post('http://iot.cht.com.tw/api/chtlasr/MyServlet/tlasr', params=header,data="")

    #步驟三:取得ASR Reference Id, 用來告訴server這些語音buffer是同一次辨識
    handle = str(res.text).split(';')[0]
    print (handle)
    if str(res.text).find('fail') == -1: 
        j = 0
        while j < lens:
            bytessend = 9600
            if(j + bytessend > lens):
                bytessend = lens - j
                
            #步驟四:開始傳送音檔buffer
            gSyncTime=time.time()
            header = {
            'Action':'syncData',
            'AsrReferenceId':handle,
            'ByteNum':bytessend,
            'SpeechEnd':'n'
            }
            res = session.post('http://iot.cht.com.tw/api/chtlasr/MyServlet/tlasr', params=header, data=DataBuffer[j:j+bytessend])
            j = j + bytessend

            print (" get text from server %s, %f\n" % (res.text, time.time() - gStartTime))
            #Server通知client, 切到語音，有辨識結果，可以停止送語音過來
            if str(res.text).find('Speech Got') != -1:
                #client通知Server停送語音。另一種情形，如果Server還沒切到音，client要主動停止，也請送SpeechEnd通知Server，取回目前辨識結果。
                header = {
                    'Action':'syncData',
                    'AsrReferenceId':handle,
                    'ByteNum':0,
                    'SpeechEnd':'y'
                }
                res = session.post('http://iot.cht.com.tw/api/chtlasr/MyServlet/tlasr', params=header, data="")
                print (" final %s, %f\n" % (res.text, time.time() - gStartTime))
                j = lens+100
                break

        #步驟五:跟server要辨識結果
        header = {'AsrReferenceId':handle}
        res = session.get('http://iot.cht.com.tw/api/chtlasr/MyServlet/tlasr', params=header)
        print ("%s = %f\n" % (res.text,time.time() - gStartTime))
    
run()


