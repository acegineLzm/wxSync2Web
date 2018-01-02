# -*- coding:utf-8 -*-

from selenium import webdriver
from datetime import datetime
import bs4
import os, time, sys
import requests
import json
import re
import urllib
import hashlib

reload(sys)
sys.setdefaultencoding( "utf-8" )

# 公众号列表
accountList = ['baobeijihuaaihuahua']

# 账号 & 员工号 & 密码
cacct = ""
sacct = ""
password = ""

# 图片临时下载文件夹
LOCALPATH = "."

# phantomjs二进制文件绝对路径
phantomjs = "/Users/xx/Downloads/tools/phantomjs-2.1.1-macosx/bin/phantomjs"

base = 'https://mp.weixin.qq.com'
query = 'http://weixin.sogou.com/weixin?type=1&s_from=input&query='

# 为了绕过微信图片防盗链只能先下载后上传服务器改图片域名
class imgUtil():

    def CalcMD5(self, filepath):
        with open(filepath,'rb') as f:
            md5obj = hashlib.md5()
            md5obj.update(f.read())
            hash = md5obj.hexdigest()
            return hash

    def CalcSize(self, filepath):
        return os.path.getsize(filepath)

    def downloadsIMG(self, index, imgUrl):
        savePath = '{}/wx_{}.jpg'.format(LOCALPATH, index)
        urllib.urlretrieve(imgUrl, savePath)
        return savePath

    def uploadsIMG(self, filePath, fileMD5, fileName, fileSize, token, session):
        url = 'http://babyproject.faisco.cn/ajax/advanceUpload.jsp?cmd=_upload&watermarkUse=false&_TOKEN=' + token
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': '_FSESSIONID={};'.format(session)
        }
        files = {
            'filedata': (fileName, open(filePath, 'rb'), 'image/jpeg'),
            'fileMd5': (None, fileMD5),
            'totalSize': (None, str(fileSize)),
            'complete': (None, 'true'),
            'initSize': (None, '0'),
        }
        # proxies = {
        #     'https': 'http://127.0.0.1:8080',
        #     'http': 'http://127.0.0.1:8080'
        # }
        try:
            r =requests.post(url=url, headers=headers, files=files)
            jr = json.loads(r.text)
            return jr['path'] if jr['success'] else ''
        except Exception as e:
            print e
            return ''

    def rmLocalImg(self, imgPath):
        os.remove(imgPath)

# 爬取公众号文章
class articleSpider():
    # 爬取公众号
    def getAccountURL(self, searchURL):
        res = requests.get(searchURL)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "lxml")
        time.sleep(1)
        account = soup.select('a[uigs="account_name_0"]')
        return account[0]['href']

    # 爬取公众号头条文章
    def getArticleURL(self, accountURL):
        # 异步加载获取内容
        browser = webdriver.PhantomJS(phantomjs)
        browser.get(accountURL)
        html = browser.page_source
        accountSoup = bs4.BeautifulSoup(html, "lxml")
        contents = accountSoup.find_all(hrefs=True)
        try:
            partitialLink = contents[0]['hrefs']
            firstLink = base + partitialLink
        except IndexError:
            print '[!] 脚本遇到验证码机制，稍等几分钟后再试，或请手动输入验证码后再运行脚本'
            sys.exit()
        return firstLink

    # 临时保存头条内容
    def saveContent(self, articleURL, token, session):
        res = requests.get(articleURL)
        res.raise_for_status()
        detailPage = bs4.BeautifulSoup(res.text, "lxml")
        art = {}
        parentTag = detailPage.find('div', {'id':'js_content', 'class':'rich_media_content'})
        firstGifTag = parentTag.find('img')
        content = ''
        iu = imgUtil()
        index = 0
        for child in parentTag.children:
            if isinstance(child, bs4.element.Tag):
                # 去除 头gif 和 尾‘阅读原文’
                if '阅读原文' in child.text or str(firstGifTag) in str(child):
                    pass
                # 替换图片链接
                elif child.find('img'):
                    imgURL = child.find('img')['data-src']
                    imgLocalPath = iu.downloadsIMG(index+1, imgURL)
                    imgSize = iu.CalcSize(imgLocalPath)
                    imgMD5 = iu.CalcMD5(imgLocalPath)
                    imgName = 'wx_{}.jpg'.format(index+1)
                    # 上传服务器后获取到的图片新地址
                    imgNewURL = iu.uploadsIMG(imgLocalPath, imgMD5, imgName, imgSize, token, session)
                    time.sleep(10)
                    if imgNewURL:
                        print '[*] 后台上传第{}个图片成功, 并替换微信图片地址为服务器图片地址'.format(index+1)
                        child.find('img')['data-src'] = imgNewURL
                        iu.rmLocalImg(imgLocalPath)
                        print '[*] 本地删除第{}个图片成功'.format(index+1)
                    else:
                        print '[!] 后台上传第{}个图片失败, 该图片已保留, 请后台手动替换'.format(index+1)
                        # sys.exit()
                    content += str(child)
                    index += 1
                else:
                    content += str(child)
            else:
                content += str(child)
        # 将img标签属性data-src改为src才能正常显示
        art['content'] = content.replace('data-src', 'src')
        art['title'] = detailPage.title.text
        return art

# 同步文章至web
class articleSync():

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest'
    }
    # 登录后台获取cookie & token
    def getCookies(self, cacct, sacct, password):
        url = 'http://www.faisco.cn/ajax/login_h.jsp?cmd=loginCorpNew&dogSrc=3'
        data = {
            "validateCode": "",
            "autoLogin": "false",
            "staffLogin": "true",
            "dogId": "0"
        }
        data['cacct'] = cacct
        data['sacct'] = sacct
        data['pwd'] = hashlib.md5(password).hexdigest()
        try:
            r = requests.post(url=url, data=data, headers=self.headers)
            jr = json.loads(r.text)
            session = jr['sessionId']
            token = bs4.BeautifulSoup(jr['_TOKEN'], 'lxml').find('meta')['value']
        except Exception as e:
            print e
            session = token = ''
        return session, token

    # 上传文章
    def addArticle(self, token, session, article, groupId):
        url = 'http://babyproject.faisco.cn/ajax/news_h.jsp?cmd=add&_nmid=null&src=0&_TOKEN='
        data = {
            "title": "",
            "date": "",
            "keyword": "",
            "desc": "",
            "content": "",
            "author": "",
            "source": "",
            "browserTitle": "",
            "flag": "0",
            "link": "",
            "pictureId": "",
            "summary": "",
            "authMemberLevelId": "-1",
            "authCus": "false",
            "nlPictureId": "",
            "groupIds": "[{}]".format(groupId),
            "attachIds": "[]"
        }
        self.headers['Cookie'] = '_FSESSIONID={};'.format(session)
        data['title'] = article['title']
        data['date'] = datetime.now().strftime("%Y-%m-%d %H:%S")
        # data['content'] = urllib.quote(article['content'])
        data['content'] = '<p>' + article['content'] + '<br /></p>'
        # print data['content']
        try:
            r = requests.post(url=url+token, data=data, headers=self.headers)
            jr = json.loads(r.text)
        except Exception as e:
            print e
            jr = {'msg': '上传失败'}
        return jr

desc = '''
    1. 自动同步各公众号头条文章
    2. 输入文章链接自动同步
'''

item = '''
    a. 关于宝贝计画
    b. 产品课程
    c. 微画展
    d. 儿童美术教育
    e. 画展活动
    f. vip绘画课程
    g. 商学院师资培训
    h. 原创绘本推荐
    i. 精品直播
'''

def main():
    print desc
    select1 = raw_input('请选择功能: ')
    print item
    select2 = raw_input('请选择分类: ')
    a = [chr(x) for x in range(ord('a'), ord('j'))]
    b = [x for x in range(18,27)]
    groups = {x:str(y) for x,y in zip(a,b)}
    groupId = groups[select2]
    if not select1.isdigit():
        print '[!] 输入有误'
        sys.exit()
    elif int(select1) < 1 or int(select1) > 2:
        print '[!] 输入有误'
        sys.exit()
    elif 2 == int(select1):
        articleURL = raw_input('请输入文章链接: ')
    if not select2.isalpha():
        print '[!] 输入有误'
        sys.exit()
    elif select2 < 'a' or select2 > 'i':
        print '[!] 输入有误'
        sys.exit()

    artSpinder = articleSpider()
    artSync = articleSync()

    session, token = artSync.getCookies(cacct, sacct, password)
    if session and token:
        print '[*] 登录后台, 成功获取 session: {}  token: {}'.format(session, token)
        if int(select1) == 1:
            for index, account in enumerate(accountList):
                searchURL = query + account
                accountUrl = artSpinder.getAccountURL(searchURL)
                print '[*] {} 公众号链接: {}'.format(account, accountUrl)
                time.sleep(5)
                articleURL = artSpinder.getArticleURL(accountUrl)
                print '[*] {} 对应的头条链接: {}'.format(account, str(articleURL))
                print '[*] 开始第{}个公众号头条文章格式化...'.format(index+1)
                art = artSpinder.saveContent(articleURL, token, session)
                print '[*] 格式化完成'
                jr = artSync.addArticle(token, session, art, groupId)
                print '[*] 头条 "{}" {}'.format(art['title'], jr['msg'])
        else:

            print '[*] 开始文章格式化...'
            art = artSpinder.saveContent(articleURL, token, session)
            print '[*] 格式化完成'
            jr = artSync.addArticle(token, session, art, groupId)
            print '[*] 头条 "{}" {}'.format(art['title'], jr['msg'])
    else:
        print '[*] 后台登录失败'

if __name__ == '__main__':
    main()
