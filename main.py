from io import BufferedRandom
from time import sleep

from pyquery import PyQuery as pq
import requests
import os
import hashlib
import threading

startUrl = "http://t.cn/A65CNYeA"
session = requests.Session()

lock = threading.RLock()
imglock = threading.RLock()


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
            # print("302 found %s" % location)

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


imgCaches: list = []


def download(src: str, filePath: str):
    # img = send(src)
    fileName = hashlib.md5(src.encode("utf-8")).hexdigest()
    filetype = "png"
    real = "%s/%s.%s" % (filePath, fileName, filetype)

    data = {
        "local": real,
        "url": src,
        "title": filePath
    }
    imgCaches.append(data)
    log("缓存队列投入数据 %s" % data)


batch = 64

cacheing: list = []


def saveImgAndFolder(url: str):
    # 获取三条实际地址链接
    # print(url)
    global startUrl

    a1 = send(url)

    lock.acquire()
    process = True
    for id in cacheing:
        if id == url:
            log("发现已在队列中处理该页面,跳过 %s " % url)
            process = False
    if process:
        cacheing.append(url)
    lock.release()

    # 同步锁不缓存多个对象
    if not process:
        return False

    a2 = pq(a1.text)
    pwd = a2("input[name='pwd']")
    pwd = pwd.attr('value')
    # print(pwd)

    if pwd is None:
        pwd = a2("meta[name='description']")
        pwd = pq(pwd).attr('content')
        a3 = pwd.split("访问密码：")
        if len(a3) == 2:
            pwd = a3[1]
            url = a1.url
        else:
            return False

    if pwd is None:
        return False
    a1 = send(url, {
        "Cookie": 'pwd=' + pwd
    })
    a2 = pq(a1.text)
    pagetitle = a2("title").text()
    if pagetitle == '':
        pagetitle = "无标题帖子统一目录"
    filePath = "./imgs/%s" % pagetitle

    if not os.path.exists(filePath):
        os.mkdir(filePath)

    a2 = a2('.note-body > .note-content > .note-body > .note-content')
    home = a2
    boards = a2
    a4 = a2(".note-content > div:first-child")
    if a4.length == 0:
        a4 = a2(".note-content > p:first-child")
    a2 = a4
    content = home.text()

    a5 = a2('img')

    if len(a5) <= 0:
        a5 = home("img")

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

    for a3 in elements:
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
        log("[%s] cache progress : %s" % (pagetitle, a2.length))
    log("[%s] cache success." % pagetitle)
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

    threads: list = []
    localUrl = startUrl

    while True:
        mainpage = send(localUrl)
        random = pq(mainpage.text)('.tab-pane.active > .media')
        for a1 in random.items():
            a1_click = a1.attr("onclick")
            a1_click = getClickJumpUrl(a1_click)
            if cacheContent.find(a1_click) == -1:
                t = threading.Thread(target=parseUrl, args=(a1_click,))
                threads.append(t)
                t.start()
                # t.join()
            else:
                global frezz
                frezz += 1
                # log("url %s 已缓存,跳过." % a1_click)
                localUrl = a1_click

            while len(threads) > 0:
                t = threads.pop()
                t.join()


frezz = 0
cacheFile: BufferedRandom = None
cacheContent = ""


def init():
    global cacheFile
    global cacheContent
    # load config
    CACHE = './cached.txt'
    STORE = "./imgs"
    if not os.path.isfile(CACHE):
        fd = open(CACHE, mode="w", encoding="utf-8")
        fd.close()
    cacheFile = open(CACHE, 'rt+')
    cacheContent = cacheFile.read()
    print("读入配置项完成。")

    if not os.path.exists(STORE):
        os.mkdir(STORE)


def downcore(img):
    bin = send(img['url'])
    ll = open(img['local'], "wb+")
    ll.write(bin.content)
    ll.flush()


def log(s):
    print(s, end="\r")


downSize = 32


def imgServer():
    threads: list = []
    log("开始启动下载服务。")
    count = 0
    while True:
        strs = "-"
        if count > 4:
            count = 1
        if count == 1:
            strs = "\\"
        if count == 2:
            strs = "|"
        if count == 3:
            strs = "/"
        if count == 4:
            strs = "-"
        log("[%s] 下载图片队列数量: %s，跳过重复或已缓存的Url: %s" % (strs, len(imgCaches), frezz))
        count += 1
        if len(imgCaches) == 0:
            sleep(.5)
            continue
        img = imgCaches.pop()
        t = threading.Thread(target=downcore, args=(img,))
        t.start()
        threads.append(t)
        log("剩余: %s | %s" % (len(imgCaches), img['local'],))
        if len(threads) >= downSize:
            t = threads[0]
            t.join()
            threads.remove(t)


if __name__ == '__main__':
    init()
    down = threading.Thread(target=imgServer)
    down.start()
    threads: list = []
    for i in range(1, 32):
        t = threading.Thread(target=mainHandle)
        t.start()
        threads.append(t)

    while True:
        t = threads[0]
        t.join()
        print(t.name + " Final.")
        threads.remove(t)
        if len(threads) == 0:
            break

    down.join()
    print("task finally.")
