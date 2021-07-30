import os
from os import remove
from os.path import join, getmtime
import datetime
from configparser import ConfigParser
import requests
import base64
import win32wnet

class HttpRequestSrv:
    '''
    Http Request增加Retry與設定Proxy服務
    '''
    proxies = None
    _retryTimes = 3

    @classmethod
    def post(cls, url, obj):
        result = False
        for _ in range(cls._retryTimes):
            try:
                response = requests.post(url, data = obj, proxies = cls.proxies)
                if response.status_code == 200:
                    result = True
                    break
            except:
                pass
        else:
            result = False
        return result

def get_config():
    '''
    取得設定檔
    '''
    pathCfg = ConfigParser()
    pathCfg.read('Path.cfg')
    comcfgPath = pathCfg.get('System', 'comcfgPath')

    sysCfg = ConfigParser()
    sysCfg.read(comcfgPath)
    fab = sysCfg.get('Env', 'FAB')
    proxyUrl = sysCfg.get('Env', 'Proxy')

    proxies = {'http': proxyUrl}
    username = sysCfg.get('Account', 'username')
    password = sysCfg.get('Account', 'password')
    storageInterface = pathCfg.get('Storage', 'MainPath') + pathCfg.get('Storage', 'Interface')
    folderPath = pathCfg.get('Storage', 'FolderPath').replace('$[FAB]', fab)

    toolsPath = []
    for k in pathCfg[fab+'_Tool']:
        pair = (k, pathCfg[fab+'_Tool'][k])
        toolsPath.append(pair)
    return proxies, storageInterface, folderPath, toolsPath, username, password

def connect_tool(toolsPath, username, password):
    '''
    對機台進行 unc 連接
    '''
    for i in range(len(toolsPath)):
        _, toolPath = toolsPath[i] # toolID, toolPath
        toolPath = toolPath[0:-1] # remove redundant space
        netResource = win32wnet.NETRESOURCE()
        netResource.lpRemoteName = toolPath
        flags = 0
        # flags |= CONNECT_INTERACTIVE
        print("Trying to create connection to: {:s}".format(toolPath))
        try:
            win32wnet.WNetAddConnection2(netResource, password, username, flags)
        except Exception as e:
            print(e)
        else:
            print("Success!")

def house_keep(toolsPath, days):
    '''
    機台Log只保留 days 天數, 超過刪除
    '''
    for i in range(len(toolsPath)):
        _, toolPath = toolsPath[i] # toolID, toolPath
        print('*****Start*****')
        print("Search the Path: " + toolPath)
        for root, _, files in os.walk(toolPath):
            for file in files:
                fileTime = datetime.datetime.fromtimestamp(getmtime(join(root, file)))
                nowTime = datetime.datetime.now()
                insterval = nowTime - fileTime
                if(insterval.days > days): 
                    remove(join(root,file))
                    print("Delete: " + join(root,file))
        print('*****End*****')

def save_repair_log(storageInterface, folderPath, toolsPath, minutes):
    '''
    將RepairLog存檔到Storage
    '''
    url = storageInterface
    for i in range(len(toolsPath)):
        _, toolPath = toolsPath[i] # toolID, toolPath
        print('*****Start*****')
        print("Search the Path: " + toolPath)
        for root, _, files in os.walk(toolPath):
            for file in files:
                fileTime = datetime.datetime.fromtimestamp(getmtime(join(root, file)))
                nowTime = datetime.datetime.now()
                insterval = nowTime - fileTime
                if(insterval.seconds <= minutes * 60): 
                    filePath = join(root, file)
                    savePath = folderPath + filePath.replace(toolPath, '').replace('\\', '/')
                    with open(filePath, "rb") as f:
                        encodedData = base64.b64encode(f.read()).decode('utf-8')
                        obj = {'encodedData': encodedData, 'savePath': savePath}
                        result = HttpRequestSrv.post(url, obj)
                        if result:
                            print("Success Save: " + filePath)
                        else:
                            print("Fail Save: " + filePath)
        print('*****End*****')

def main():
    proxies, storageInterface, folderPath, toolsPath, username, password = get_config()
    HttpRequestSrv.proxies = proxies
    connect_tool(toolsPath, username, password)
    house_keep(toolsPath, days = 2)
    save_repair_log(storageInterface, folderPath, toolsPath, minutes = 180)   # 抓最新3小時內的資料

if __name__ == '__main__':
    lockFilePath = 'RepairLogParser_lock'
    if os.path.isfile(lockFilePath):
        fileTime = datetime.datetime.fromtimestamp(getmtime(lockFilePath))
        nowTime = datetime.datetime.now()
        timeDiff = nowTime - fileTime
        timeout = 20 * 60
        if timeDiff.seconds >= timeout:   # 超過 20min視為上一Run執行到一半有問題，而不是重複run
            remove(lockFilePath)
        else:
            print('RepairLogParser is still Running')    
            exit()    
    with open(lockFilePath, 'a') as lockFile:
        lockFile.write('Running')
    main()
    remove(lockFilePath)
