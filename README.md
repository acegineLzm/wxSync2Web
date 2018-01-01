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

```
accountList = ['baobeijihuaaihuahua']
```

添加后台 账号 & 员工号 & 密码

```
cacct = ""
sacct = ""
password = ''
```

图片临时下载文件夹（可不修改）

```
LOCALPATH = '.'
```

修改phantomjs绝对路径

```
phantomjs = "/Users/xx/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs"
```

下载链接为 [http://phantomjs.org/download.html](http://phantomjs.org/download.html)

---

```shell
python sync.py

    1. 自动同步各公众号头条文章
    2. 输入文章链接自动同步
```

### 备注

1. 微信公众号文章有强校验及很短时效性，因此最简单是从搜狗微信爬取；
2. 公众号文章为异步加载，爬虫要使用 selenium + PhantomJS；
3. 文章图片有防盗链机制，绕过方法：
- 在head中添加<meta name="referrer" content="never">
- 使用第三方cdn或本地代理中转
- 下载后上传服务器，使用新链接，下载图片使用urllib.urlretrieve方法，上传使用requests.post的files属性，格式化方法如下：

```python
files = {
            'filedata': (fileName, open(filePath, 'rb'), 'image/jpeg'),
            'fileMd5': (None, fileMD5),
            'totalSize': (None, str(fileSize)),
            'complete': (None, 'true'),
            'initSize': (None, '0'),
        }
```

4. 公众号文章中的图片标签的引用属性为data-src，需修改为src才能正常显示；
5. 因服务器处理原因，上传图片失败需手动在后台上传并在文章编辑处修改图片。
