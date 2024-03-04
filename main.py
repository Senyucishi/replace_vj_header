import re
from bs4 import BeautifulSoup
import json
import urllib.parse

from login import *

class Videoids:
    def __init__(self, nnd: (str | None), ytb: (str | None), bb: (str | None)):
        self.nnd = nnd
        self.ytb = ytb
        self.bb = bb


#感谢lih老师的av/bv号转换
table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
tr = {}
for index in range(58):
    tr[table[index]] = index
s = [11, 10, 3, 8, 4, 6]
xor = 177451812
add = 8728348608

def send_request_get(url: str, reqname: str, headers: dict=None, max_retries: int=3, timeout: int=15) -> (requests.Response | None):
    if headers is None:
        headers = {}
    retries = 0
    while retries < max_retries:
        try:
            response = workspace['SESSION'].get(url, headers=headers ,timeout=timeout)
            if response.status_code == 200 or response.status_code == 400 or response.status_code == 404:
                # 请求成功，返回响应
                return response
            else:
                print(f"对{reqname}的请求发生异常，HTTP状态码为{response.status_code}")
        except requests.exceptions.Timeout:
            print(f"对{reqname}的GET请求超时，正在进行第 {retries + 1} 次重试...")
        except requests.exceptions.RequestException as e:
            print(f"对{reqname}的请求发生异常：{e}")
        retries += 1

    print(f"对{reqname}的请求失败，达到最大重试次数。{retries}")
    return None

def av_to_bv(av: str) -> str:
    x = int(av[2:])
    x = (x ^ xor) + add
    r = list('BV1  4 1 7  ')
    for i in range(6):
        r[s[i]] = table[x // 58 ** i % 58]
    print(''.join(r))
    return ''.join(r)

def get_bv(vid: str) -> str:
    search_bv = re.search("BV[0-9a-zA-Z]+", vid, re.IGNORECASE)
    if search_bv is not None:
        return search_bv.group(0)
    search_av = re.search("av[0-9]+", vid, re.IGNORECASE)
    if search_av is not None:
        return av_to_bv(search_av.group(0))
    return vid

def req_bcount(bbid: str) -> int :
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }
    vid = get_bv(bbid)
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(send_request_get(url=url, headers=headers, reqname='bilibili').text)
    if response['code'] == 0 :
        views = response['data']['stat']['view']
        return int(views)
    else:
        print('bilibili已删稿')
        raise TabError


def req_ncount(nnid: str) -> int :
    response = send_request_get(url=f'https://www.nicovideo.jp/watch/{nnid}', reqname='niconico')
    if response.status_code == 404 or response.status_code == 400 :
        print('niconico已删稿')
        soup = BeautifulSoup(response.text, 'lxml')
        data = soup.find('p', attrs={'class', 'TXT10'})
        if data is not None:
            return int(re.search('再生：(.*)', string=str(data.get_text())).group(1))
        else:
            print('无法获取niconico再生')
            raise TabError
    else:
        soup = BeautifulSoup(response.text, 'lxml')
        rawjson = soup.find('script', attrs={'class', 'LdJson'})
        if rawjson is not None:
            raw = json.loads(rawjson.get_text())
            return int(raw['interactionStatistic'][0]['userInteractionCount'])

def req_ycount(ytid: str) -> int:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }
    response = send_request_get(f'https://www.youtube.com/watch?v={ytid}',headers=headers, reqname='YouTube')
    soup = BeautifulSoup(response.text, 'lxml')
    rawmeta = soup.select_one('meta[itemprop="interactionCount"][content]')
    if rawmeta is not None:
        return int(rawmeta['content'])
    else:
        print('Youtube已删稿')
        raise TabError

def get_vid(text) -> Videoids:
    nnd = re.findall(r'\|nnd_id\s*=\s*((?:sm|nm|so|)\d+)', text.text, re.IGNORECASE)
    ytb = re.findall(r'\|yt_id\s*=\s*([a-zA-Z0-9_-]{11})', text.text, re.IGNORECASE)
    bb = re.findall(r'\|bb_id\s*=\s*((?:av|bv)\w+)', text.text, re.IGNORECASE)
    if len(nnd) == 1:
        fnnd = nnd[0]
    else:
        fnnd = None
    if len(ytb) == 1:
        fytb = ytb[0]
    else:
        fytb = None
    if len(bb) == 1:
        fbb = bb[0]
    else:
        fbb = None

    return Videoids(nnd=fnnd, ytb=fytb, bb=fbb)

def gen_heading(vid: Videoids, engines: str) -> str:
    header = "{{虚拟歌手歌曲荣誉题头|" + engines
    ids = [vid.nnd, vid.ytb, vid.bb]
    ncount = None
    bcount = None
    ycount = None
    num = 0
    if ids[0] is not None:
        ncount = req_ncount(ids[0])
    if ids[1] is not None:
        ycount = req_ycount(ids[1])
    if ids[2] is not None:
        bcount = req_bcount(ids[2])
    if ncount is not None:
        print('niconico上的播放数为' + str(ncount))
        if 100000 <= ncount < 1000000:
            header = header + '|nrank=1'
            num = num + 1
        elif 1000000 <= ncount < 10000000:
            header = header + '|nrank=2'
            num = num + 1
        elif ncount >= 10000000:
            header = header + '|nrank=3'
            num = num + 1
    else:
        print('无niconico投稿数据')
    if ycount is not None:
        print('YouTube上的播放数为'+str(ycount))
        if 100000 <= ycount < 1000000:
            header = header + '|yrank=1'
            num = num + 1
        elif 1000000 <= ycount < 10000000:
            header = header + '|yrank=2'
            num = num + 1
        elif 10000000 <= ycount < 100000000:
            header = header + '|yrank=3'
            num = num + 1
        elif ycount >= 100000000:
            header = header + '|yrank=4'
            num = num + 1
    else:
        print('无YouTube投稿数据')
    if bcount is not None:
        print('bilibili上的播放数为' + str(bcount))
        if 100000 <= bcount < 1000000:
            header = header + '|brank=1'
            num = num + 1
        elif 1000000 <= bcount < 10000000:
            header = header + '|brank=2'
            num = num + 1
        elif bcount >= 10000000:
            header = header + '|brank=3'
            num = num + 1
    else:
        print('无bilibili投稿数据')
    #if num == 1:
        #print('识别到单平台成就')
        #raise TabError
    if num == 0:
        print('未识别到成就')
        raise TabError
    header = header + '}}'
    print('应悬挂的题头为：' + header)
    return header

def post_edit (page, new_text):
    param = {
        'action': 'edit',
        'format': 'json',
        'title': page,
        'section': 0,
        'text': new_text,
        'summary': '批量替换题头',
        'tags': 'Bot',
        'minor': 1,
        'bot': 1,
        'nocreate': 1,
        'token': FetchToken('csrf'),
        'utf8': 1
    }
    result = PostAPI(param)
    print(result)
    if result["edit"]["result"] == "Success":
        if 'newrevid' in result["edit"]:
            oidid = '{}'.format(result["edit"]["newrevid"])
            print(f"页面{page}编辑成功，新的修订id为{oidid}")
        else:
            print(f"页面{page}内容一致")
    else:
        print(f"页面{page}编辑失败，请检查后重试")

def main():
    LogIn()
    with open(workspace['f_path']) as f:
        for line in f:
            enginelist = []
            engine = ''
            page = line.rstrip()
            encodedpage = urllib.parse.quote(page)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
            }
            text = send_request_get(
                f"https://zh.moegirl.org.cn/api.php?action=parse&format=json&page={encodedpage}&prop=parsewarnings%7Cwikitext%7Ccategories&section=0&utf8=1",headers=headers, reqname='请求wikitext')
            print(f'\n对于条目{page}:')
            while re.search('WafCaptcha',text.text) is not None:
                input('请检查主站验证码，按回车键继续')
                text = send_request_get(
                    f"https://zh.moegirl.org.cn/api.php?action=parse&format=json&page={encodedpage}&prop=parsewarnings%7Cwikitext%7Ccategories&section=0&utf8=1",
                    headers=headers, reqname='请求wikitext')
            if 'error' in json.loads(text.text):
                print('无法请求条目wikitext，请检查页面名')
                continue
            else:
                wikitext = json.loads(text.text)['parse']['wikitext']['*']
            if re.search('\{\{tabs', text.text, re.IGNORECASE) is not None:
                print('监测到tabs')
                print(f'已跳过{page}')
                continue

            if len(re.findall(r'\{\{([a-zA-Z/]+)(?:殿堂|传说|傳說|神话)曲(?:题头|題頭)\S*}}', wikitext)) != 0:
                try:
                    vid = get_vid(text)
                except TabError:
                    print(f'已跳过{page}')
                    continue
                a=re.findall(r'\{\{([a-zA-Z/]+)(?:殿堂|传说|傳說|神话)曲(?:题头|題頭)\S*}}', wikitext)
                replace = re.compile(r'\{\{'+str(a[0])+r'(?:殿堂|传说|傳說)曲(?:题头|題頭)\S*}}', flags = re.IGNORECASE)
                try:
                    header = gen_heading(vid, str(a[0]))
                except TabError:
                    print(f'已跳过{page}')
                    continue
                new_text = replace.sub(repl = header, string = wikitext)

            elif len(re.findall(pattern='\{\{虚拟歌手歌曲荣誉题头\|[\w|=\s]+}}',string= wikitext)) != 0:

                try:
                    vid = get_vid(text)
                except TabError:
                    print(f'已跳过{page}')
                    continue
                old_header = re.findall(pattern='\{\{虚拟歌手歌曲荣誉题头\|([\w|=\s]+)}}',string= wikitext)[0]
                paramlist = old_header.split("|")
                print(paramlist)
                for i in list(set(paramlist)):
                    if re.search(pattern=r'=\d+', string=i) is None:
                        enginelist.append(i)
                engine = '|'.join(list(set(enginelist)))
                try:
                    header = gen_heading(vid, engine)
                except TabError:
                    print(f'已跳过{page}')
                    continue
                if old_header == header:
                    continue
                else:
                    new_text = re.sub(pattern=r'\{\{虚拟歌手歌曲荣誉题头\|[\w|=\s]+}}', repl=header, string=wikitext)

            else:
                if get_vid(text).nnd == get_vid(text).ytb == get_vid(text).bb is None:
                    print(f'未在序言部分找到有效模板，已跳过{page}')
                    continue
                try:
                    vid = get_vid(text)

                    cat = send_request_get(
                        f"https://zh.moegirl.org.cn/api.php?action=parse&format=json&page={encodedpage}&prop=categories&utf8=1",
                        headers=headers, reqname='请求分类')
                    while re.search('WafCaptcha', cat.text) is not None:
                        input('请检查主站验证码，按回车键继续')
                        cat = send_request_get(
                            f"https://zh.moegirl.org.cn/api.php?action=parse&format=json&page={encodedpage}&prop=categories&utf8=1",
                            headers=headers, reqname='请求分类')
                    if 'error' in json.loads(text.text):
                        print('无法请求条目分类，请检查页面名')
                        continue
                    for i in json.loads(cat.text)['parse']['categories']:
                        if len(re.findall(pattern=r'使用([A-Za-z_\s]+)的歌曲', string=i["*"])) != 0:
                            enginelist.append(re.findall(pattern=r'使用([A-Za-z_\s]+)的歌曲', string=i["*"])[0])
                    engine = '|'.join(list(set(enginelist)))
                except KeyError:

                    print(f'未找到分类，已跳过{page}')
                    continue
                try:
                    header = gen_heading(vid, engine)
                except TabError:
                    print(f'已跳过{page}')
                    continue
                new_text = re.sub(pattern='\{\{VOCALOID_Songbox', repl=header+'\n'+'{{VOCALOID_Songbox', string=wikitext)

            if new_text != wikitext:
                post_edit(page, new_text)
            else:
                print(f"页面{page}内容一致")


if __name__ == '__main__':
    main()