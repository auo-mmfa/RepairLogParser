import os
from os import remove
from os.path import join, getmtime
from datetime import datetime
import configparser
import requests
import base64

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
    return FAB, proxies, storageInterface, folderPath, toolsPath, username, password

def ConnectTool(toolsPath, username, password):
    '''
    對機台進行 Net Use 連接
    '''
    for i in range(len(toolsPath)):
        toolID = toolsPath[i][0]
        toolPath = toolsPath[i][1]
        cmd = "C:/Windows/System32/net.exe use Z: %s /user:%s %s" % (toolPath, username, password)
        os.system(cmd)

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
                fileTime = datetime.fromtimestamp(getmtime(join(root,file)))
                nowTime = datetime.now()
                insterval = nowTime - fileTime
                if(insterval.days > days): 
                    remove(join(root,file))
                    print("Delete: "+ join(root,file))
        print('*****End*****')

def SaveRepairLog(FAB, proxies, storageInterface, folderPath, toolsPath, days):
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
                fileTime = datetime.fromtimestamp(getmtime(join(root,file)))
                nowTime = datetime.now()
                insterval = nowTime - fileTime
                if(insterval.days <= days): 
                    filePath = join(root,file)    
                    savePath = folderPath + filePath.replace(toolPath, '').replace('\\','/')
                    with open(filePath, "rb") as f:
                        encodedData = base64.b64encode(f.read()).decode('utf-8')
                        myobj = {'encodedData': encodedData, 'savePath': savePath}
                        response = requests.post(url, data = myobj ,proxies = proxies)
                        if response.status_code == 200:
                            print("Success Save: "+ filePath)
                        else:
                            print("Fail Save: "+ filePath)
        print('*****End*****')

if __name__ == '__main__':    
    
    FAB, proxies, storageInterface, folderPath, toolsPath, username, password = GetConfig()
    ConnectTool(toolsPath, username, password)
    HouseKeeper(toolsPath, days = 20)
    SaveRepairLog(FAB, proxies, storageInterface, folderPath, toolsPath, days = 1)


       