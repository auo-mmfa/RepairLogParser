# RepairLogParser

Function: Parser Repair Log to MMFA Storage

Depoly: 
1. 進入comcfg資料夾，根據廠別將MMFA資料夾放到對應中繼電腦的 C:/，
   comcfg.ini存放該廠所需的共通設定
2. storage建立webserver，目前storage為NAS，
   建立的webserver為http://10.96.154.148:8080/
3. 進入storage資料夾，將upload_file.php放到建立的webserver下，
   放完後目前路徑為http://10.96.154.148:8080/upload_file.php
4. 中繼電腦啟動RepairLogParser.py，此檔案對應的cfg為Path.cfg

RepairLogParser Flow:
1. 根據Path.cfg & C:\MMFA\comcfg.ini 取得各式設定
2. 由設定建立與機台的連線，這些機台存有Repair Log
3. 將機台超過2天的Log刪除，避免容量不足
4. 讀取機台1天內的Log，並存放到Storage
 

