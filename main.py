import re
from bs4 import BeautifulSoup
import json

from login import *

#engine = 'VOCALOID'
#title = '殿堂'
class Videoids:
    def __init__(self, nnd: (str|None), ytb: (str|None), bb: (str|None)):
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

def req_bcount(bbid) -> int :
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }
    vid = get_bv(bbid)
    print(vid)
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
    response = json.loads(requests.get(url=url, headers=headers).text)
    print(response)
    views = response['data']['stat']['view']
    return int(views)

def req_ncount(nnid) -> int :
    response = requests.get(f'https://www.nicovideo.jp/watch/{nnid}')
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        rawjson = soup.find('script', attrs={'class', 'LdJson'})
        raw = json.loads(rawjson.get_text())
        return int(raw['interactionStatistic'][0]['userInteractionCount'])
    else:
        print('无法获取n站播放')

def req_ycount(ytid) -> int:
    response = requests.get(f'https://www.youtube.com/watch?v={ytid}')
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        rawmeta = soup.select_one('meta[itemprop="interactionCount"][content]')
        return int(rawmeta['content'])
    else:
        print('无法获取YouTube播放')

def get_vid (text) -> Videoids:
    if not re.match(r'\{\{tabs', text.text):
        nnd = re.findall(r'\|nnd_id\s*=\s*(sm\d+)', text.text, re.IGNORECASE)
        ytb = re.findall(r'\|yt_id\s*=\s*(\w{11})', text.text)
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

def gen_heading(vid: Videoids) -> str:
    header = "{{虚拟歌手歌曲荣誉题头|" + engine
    ids = [vid.nnd, vid.ytb, vid.bb]
    ncount = req_ncount(ids[0])
    ycount = req_ycount(ids[1])
    bcount = req_bcount(ids[2])
    if ncount is not None:
        print('niconico上的播放数为' + str(ncount))
        if 100000 <= ncount < 1000000:
            header = header + '|nrank = 1'
        elif 1000000 <= ncount < 10000000:
            header = header + '|nrank = 2'
        elif ncount >= 10000000:
            header = header + '|nrank = 3'
    else:
        print('无niconico投稿数据')
    if bcount is not None:
        print('bilibili上的播放数为' + str(bcount))
        if 100000 <= bcount < 1000000:
            header = header + '|brank = 1'
        elif 1000000 <= bcount < 10000000:
            header = header + '|brank = 2'
        elif bcount >= 10000000:
            header = header + '|brank = 3'
    else:
        print('无bilibili投稿数据')
    if ycount is not None:
        print('YouTube上的播放数为'+str(ycount))
        if 100000 <= ycount < 1000000:
            header = header + '|yrank = 1'
        elif 1000000 <= ycount < 10000000:
            header = header + '|yrank = 2'
        elif 10000000 <= ycount < 100000000:
            header = header + '|yrank = 3'
        elif ycount >= 100000000:
            header = header + '|yrank = 4'
    else:
        print('无YouTube投稿数据')
    header = header + '}}'
    print('应悬挂的题头为：' + header)
    return header

def main():
    LogIn()
    with open(workspace['f_path']) as f:
        for line in f:
            page = line.rstrip()
            text = requests.get(
                f"https://moegirl.uk/api.php?action=parse&format=json&page={page}&prop=parsewarnings%7Cwikitext&section=0&disabletoc=1&useskin=vector&utf8=1")
            vid = get_vid(text)
            header = gen_heading(vid)
            replace = r'\{\{VOCALOID(?:殿堂|传说)曲题头\S*\}\}'
            wikitext = json.loads(text.text)['parse']['wikitext']['*']
            new_text = re.sub(pattern = replace, repl = header, string = wikitext, flags = re.IGNORECASE)
            param = {
                'action': 'edit',
                'format': 'json',
                'title': 'page',
                'section': 0,
                'text': new_text,
                'summary': '批量替换题头',
                'tags': 'Bot',
                'minor': 1,
                'bot': 1,
                'nocreate': 1,
                'redirect': 1,
                'token': FetchToken('csrf'),
                'utf8':1
            }
            result = json.loads(PostAPI(param))
            if result["edit"]["result"] == "Success":
                if 'newrevid' in result["edit"]:
                    oidid = '{}'.format(result["edit"]["newrevid"])
                    print(f"页面{page}编辑成功，新的修订id为{oidid}")
                else:
                    print(f"页面{page}内容一致")
            else:
                print(f"页面{page}编辑失败，请检查后重试")

if __name__ == '__main__':
    main()