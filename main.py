from io import BufferedRandom
from time import sleep

from pyquery import PyQuery as pq
import requests
import os
import hashlib
import threading

startUrl = "http://v4yi6bbu.itxiaoka.cn:666/qq.php?t=161362787936029&gs=tar18&_wv=vmsl&alert%28%29id=1807139605#alert%28%29"
session = requests.Session()


def getClickJumpUrl(text: str):
    # jump('http://t.cn/A65j5bUS')
    list = text.split('\'')
    if len(list) == 3:
        return list[1]
    else:
        return None


def send(u: str, head: map = None):
    try:
        ret = session.get(url=u, headers=head, allow_redirects=False)
        if ret.status_code == 302:
            location = ret.headers['Location']
            print("302 found %s" % location)

            if location.find('?backUrl=') != -1:
                location = location.split("?backUrl=")[1]

                if location.find("http://marlzkeniqy.westarcloud.net/news/") != -1:
                    location = location.split("?t=")[1]
                    location = "http://api.toweknow.cn:666/api.php?act=geturl&t=" + location
                    ret = send(location)
                    ret = ret.json()
                    if ret['code'] == 1:
                        location = ret['url']
                    else:
                        pass
            ret = send(location, head)
        return ret
    except Exception as err:
        sleep(1)
        return send(u, head)


def getSrc(element):
    return pq(element).attr("src")


def download(src: str, filePath: str):
    img = send(src)
    fileName = hashlib.md5(img.content).hexdigest()
    filetype = "png"
    if not os.path.exists("%s/%s.%s" % (filePath, fileName, filetype)):
        with open("%s/%s.%s" % (filePath, fileName, filetype), "wb+") as imgs:
            imgs.write(img.content)
    # print(src)


batch = 64


def saveImgAndFolder(url: str):
    # 获取三条实际地址链接
    # print(url)

    a1 = send(url)

    a2 = pq(a1.text)
    pwd = a2("input[name='pwd']")
    pwd = pwd.attr('value')
    # print(pwd)

    if pwd:
        pwd = a2("meta[name='description']")
        pwd = pq(pwd).attr('content')
        a3 = pwd.split("访问密码：")
        if len(a3) == 2:
            pwd = a3[1]
            url = a1.url
        else:
            return False

    if pwd == None:
        return False
    a1 = send(url, {
        "Cookie": 'pwd=' + pwd
    })
    a2 = pq(a1.text)
    pagetitle = a2("title").text()

    filePath = "./imgs/%s" % pagetitle

    if not os.path.exists(filePath):
        os.mkdir(filePath)

    a2 = a2('.note-body > .note-content > .note-body > .note-content')
    boards = a2
    a4 = a2(".note-content > div:first-child")
    if a4.length == 0:
        a4 = a2(".note-content > p:first-child")
    a2 = a4
    content = a2.text()

    a5 = a2('img')

    videos = boards("video source")

    a2 = a5

    elements: list = []

    for im in a2:
        elements.append(im)

    mp4 = ''
    for vp in videos:
        # elements.append(vp)
        src = getSrc(vp)
        mp4 += src + "\n"

    with open("%s/link.txt" % filePath, "wt") as info:
        info.write(url + "\npwd:" + pwd + "\n" + content + "\n" + mp4)

    threads: list = []

    lens = 0
    for a3 in elements:
        lens += 1
        src = getSrc(a3)
        thread = threading.Thread(target=download, args=(
            src, filePath
        ))
        threads.append(thread)
        thread.start()
        while len(threads) >= batch:
            thread = threads[0]
            thread.join()
            threads.remove(thread)
            # print("结束一个了")
        print("[%s] cache progress : %s/%s" % (pagetitle, lens, a2.length))
    print("[%s] cache success." % pagetitle)
    return a2.length > 0


def parseUrl(url):
    global cacheContent
    global cacheFile

    save = saveImgAndFolder(url)
    if save:
        data = url + "\n"
        cacheContent += data
        cacheFile.write(data)
        cacheFile.flush()


def mainHandle():
    global cacheContent
    global cacheFile
    mainpage = send(startUrl)
    random = pq(mainpage.text)('.tab-pane.active > .media')
    threads: list = []
    for a1 in random.items():
        a1_click = a1.attr("onclick")
        a1_click = getClickJumpUrl(a1_click)
        if cacheContent.find(a1_click) == -1:
            t = threading.Thread(target=parseUrl, args=(a1_click,))
            threads.append(t)
            t.start()

    while len(threads) > 0:
        t = threads[0]
        t.join()
        threads.remove(t)


cacheFile: BufferedRandom = None
cacheContent = ""


def init():
    global cacheFile
    global cacheContent
    # load config
    cacheFile = open('cached.txt', 'rt+')
    cacheContent = cacheFile.read()
    print("读入配置项完成。")


if __name__ == '__main__':
    init()
    threads: list = []
    for i in range(1, 1000):
        t = threading.Thread(target=mainHandle)
        threads.append(t)
        t.start()
        while len(threads) >= 32:
            t = threads[0]
            t.join()
            threads.remove(t)
    print("task finally.")
