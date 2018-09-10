# encoding=UTF-8
import logging
import thread
import time
import requests
import json

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

def run():
    lens = 0
    #支援辨識pcm-16,16kHz語音
    file = open('今天天氣很好.raw', 'rb')
    DataBuffer = file.read()
    lens = len(DataBuffer)
    
    gStartTime = time.time()
    #步驟一:設定參數
    header = {
    'Action':'connect',
    'ClientId':'Test' #區別每個使用者的unique id, 請自行定義
    }
    
    #步驟二:開始連線，因為要用http 1.1 keep-alive python必須用session
    session = requests.Session()
    res = session.post('http://iot.cht.com.tw/api/chtlasr/MyServlet/tlasr', params=header, data="")

    #步驟三:取得ASR Reference Id, 用來告訴server這些語音buffer是同一次辨識
    res_json = json.loads(res.text)
    ResulsStatus = res_json["ResultStatus"]
    if(ResulsStatus != "Success"):
        print("ErrorMsg:"+res_json["ErrorMessage"])
    
    handle=res_json["AsrReferenceId"]


    print('post Action:connect:(',res.text,')')
    print('handle:(',handle,')')

    if str(res.text).find('fail') == -1: 
        j = 0
        while j < lens:
            bytessend = 4800
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

            if(time.time()-gSyncTime) > 0.15:
                print ' '
            else:#模擬streaming,等時間到再送
                time.sleep(0.15-(time.time()-gSyncTime))
            print (" get text from server %s, %f\n" % (res.text, time.time() - gStartTime))
            #Server通知client, 切到語音，有辨識結果，可以停止送語音過來，並取得辨識結果
            #client通知Server停送語音。另一種情形，如果Server還沒切到音，client要主動停止，也請送SpeechEnd通知Server，取回目前辨識結果。
            res_json = json.loads(res.text)
            ResulsStatus = res_json["ResultStatus"]
            if(ResulsStatus != "Success"):
                print("ErrorMsg:"+res_json["ErrorMessage"])
            else:
                SpeechGot = res_json["SpeechGot"]
                RecognitionDone = res_json["RecognitionDone"]
                if SpeechGot == 1 or RecognitionDone == 1  or (j == lens):
                    header = {
                        'Action':'syncData',
                        'AsrReferenceId':handle,
                        'ByteNum':0,
                        'SpeechEnd':'y'
                    }
                    res = session.post('http://iot.cht.com.tw/api/chtlasr/MyServlet/tlasr', params=header, data="")
                    if str(res.text.encode('utf-8')).find('fail') != -1:
                        print (" No result...")
                    else:
                        print (" final %s, %f\n" % (res.text, time.time() - gStartTime))
                    j = lens+100
                    break
run()
