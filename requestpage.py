import json
from login import *


LogIn()

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
            }

def getpages(category):
    rawpagelist = []
    pagelist = set()
    cont = ""
    while True:
        # 将uccontinue参数加入请求。注意：一开始cont为空字符串。
        result = workspace["SESSION"].get(f"https://mzh.moegirl.org.cn/api.php?action=query&format=json&list=categorymembers&utf8=1&cmtitle=Category:{category}&cmprop=title%7Cids&cmnamespace=0&cmlimit=max" +cont, headers=headers)
        # 将返回的结果转化为json数据
        data = json.loads(result.text)
        # 提取贡献，并把贡献存入contributions
        rawpagelist.extend(data['query']['categorymembers'])

        # 如果api返回的数据中包含continue，表明还有更多贡献未获取
        if 'continue' in data:
            # 将uccontinue参数放入cont变量，用于下一次循环的get请求
            cont = "&cmcontinue=" + data['continue']['cmcontinue']
        else:  # 如果不包含continue，说明所有贡献已被读取完毕，可以退出循环
            break
    for i in rawpagelist:
        pagelist.add(i['title'] + '\n')
    return pagelist

list1 = getpages('使用VOCALOID的歌曲')
list2 = getpages('使用CeVIO的歌曲')
list3 = getpages('日本音乐作品')

hlist = (list1 & list3) | (list2 & list3)
file = open('pages.txt', mode='w', encoding='utf-8')
file.writelines(hlist)
file.close()
