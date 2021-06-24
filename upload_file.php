<?php
function forceDir($dir){
//自動生成資料夾
    if(!is_dir($dir)){
        $dir_p = explode('/',$dir);
        for($a = 1 ; $a <= count($dir_p) ; $a++){
            @mkdir(implode('/',array_slice($dir_p,0,$a)));  
        }
    }
}
$encodedData =$_POST['encodedData'];
$savePath =$_POST['savePath'];
$folder = substr($savePath, 0, strrpos($savePath,'/') );
forceDir($folder);
$file = base64_decode($encodedData);
file_put_contents($savePath, $file);
?>

