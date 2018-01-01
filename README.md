# wxSync2Web

### 概述

同步公众号文章至网站

### 环境

python 2.x

*依赖模块*

scrapy
openpyxl
selenium
bs4
requests
json
urllib
hashlib
re

### 使用

**修改脚本如下配置**

在公众号列表中添加 **搜狗微信** 能搜到的公众号id
accountList = ['baobeijihuaaihuahua']

添加后台 账号 & 员工号 & 密码
cacct = ""
sacct = ""
password = ''

图片临时下载文件夹（可不修改）
LOCALPATH = '.'

修改phantomjs绝对路径
phantomjs = "/Users/xx/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs"
下载链接为 [](http://phantomjs.org/download.html)

```shell
python sync.py

    1. 自动同步各公众号头条文章
    2. 输入文章链接自动同步
```
