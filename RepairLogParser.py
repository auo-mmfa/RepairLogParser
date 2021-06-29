import os
from os import remove
from os.path import join, getmtime
import datetime
import configparser
import requests
import base64
import win32wnet

class HttpRequestSrv():
    '''
    Http Request增加Retry與設定Proxy服務
    '''
    def __init__(self, proxies):
        self.proxies = proxies
        self.RetryTimes = 3
    
    def Post(self, url, obj):
        result = False
        for cnt in range(self.RetryTimes):
            try:
                response = requests.post(url, data = obj ,proxies = self.proxies)
                if response.status_code == 200:
                    result = True
                    break
                else:
                    pass
            except:
                    pass
        if cnt == self.RetryTimes-1:
            result = False
        return result

def GetConfig():
    '''
    取得設定檔
    '''
    pathCfg = configparser.ConfigParser()
    pathCfg.read('Path.cfg')
    comcfgPath = pathCfg.get('System','comcfgPath')
    sysCfg = configparser.ConfigParser()
    sysCfg.read(comcfgPath)
    FAB = sysCfg.get('Env','FAB')
    proxyUrl = sysCfg.get('Env','Proxy')
    proxies = {'http': proxyUrl}
    username = sysCfg.get('Account','username')
    password = sysCfg.get('Account','password')
    storageInterface = pathCfg.get('Storage','MainPath') + pathCfg.get('Storage','Interface')
    folderPath = pathCfg.get('Storage','FolderPath').replace('$[FAB]', FAB)
    toolsPath = []
    for k in pathCfg[FAB+'_Tool']:
        pair = [k, pathCfg[FAB+'_Tool'][k]]
        toolsPath.append(pair)
    return proxies, storageInterface, folderPath, toolsPath, username, password

def ConnectTool(toolsPath, username, password):
    '''
    對機台進行 unc 連接
    '''
    for i in range(len(toolsPath)):
        toolID = toolsPath[i][0]
        toolPath = toolsPath[i][1]
        toolPath = toolPath[0:-1]
        net_resource = win32wnet.NETRESOURCE()
        net_resource.lpRemoteName = toolPath
        flags = 0
        #flags |= CONNECT_INTERACTIVE
        print("Trying to create connection to: {:s}".format(toolPath))
        try:
            win32wnet.WNetAddConnection2(net_resource, password, username, flags)
        except Exception as e:
            print(e)
        else:
            print("Success!")

def HouseKeeper(toolsPath, days):
    '''
    機台Log只保留 days 天數, 超過刪除
    '''
    for i in range(len(toolsPath)):
        toolID = toolsPath[i][0]
        toolPath = toolsPath[i][1]
        print('*****Start*****')
        print("Search the Path: "+ toolPath)
        for root, dirs, files in os.walk(toolPath):
            for file in files:
                fileTime = datetime.datetime.fromtimestamp(getmtime(join(root,file)))
                nowTime = datetime.datetime.now()
                insterval = nowTime - fileTime
                if(insterval.days > days): 
                    remove(join(root,file))
                    print("Delete: "+ join(root,file))
        print('*****End*****')

def SaveRepairLog(HttpRequest, storageInterface, folderPath, toolsPath, minutes):
    '''
    將RepairLog存檔到Storage
    '''
    url = storageInterface
    for i in range(len(toolsPath)):
        toolID = toolsPath[i][0]
        toolPath = toolsPath[i][1]
        print('*****Start*****')
        print("Search the Path: "+ toolPath)
        for root, dirs, files in os.walk(toolPath):
            for file in files:
                fileTime = datetime.datetime.fromtimestamp(getmtime(join(root,file)))
                nowTime = datetime.datetime.now()
                insterval = nowTime - fileTime
                if(insterval.seconds <= minutes * 60): 
                    filePath = join(root,file)    
                    savePath = folderPath + filePath.replace(toolPath, '').replace('\\','/')
                    with open(filePath, "rb") as f:
                        encodedData = base64.b64encode(f.read()).decode('utf-8')
                        obj = {'encodedData': encodedData, 'savePath': savePath}             
                        result = HttpRequest.Post(url, obj)
                        if result == True:
                            print("Success Save: "+ filePath)
                        elif result == False:
                            print("Fail Save: "+ filePath)
        print('*****End*****')

def main():
    proxies, storageInterface, folderPath, toolsPath, username, password = GetConfig()
    HttpRequest = HttpRequestSrv(proxies)
    ConnectTool(toolsPath, username, password)
    HouseKeeper(toolsPath, days = 2)
    SaveRepairLog(HttpRequest, storageInterface, folderPath, toolsPath, minutes = 180)   # 抓最新3小時內的資料

if __name__ == '__main__':    
    
    lockFilePath = 'RepairLogParser_lock'
    if os.path.isfile(lockFilePath):
        fileTime = datetime.datetime.fromtimestamp(getmtime(lockFilePath))
        nowTime = datetime.datetime.now()
        insterval = nowTime - fileTime
        minutes = 20
        if insterval.seconds >= minutes * 60:   # 超過 20min視為上一Run執行到一半有問題，而不是重複run
            remove(lockFilePath)
        else:
            print('RepairLogParser is still Running')    
            exit()    
    with open(lockFilePath, 'a') as lockFile:
        lockFile.write('Running')
    main()
    remove(lockFilePath)
       