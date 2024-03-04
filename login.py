import requests

workspace = {  # 创建字典用以储存用户和令牌信息
    'URL': "https://mzh.moegirl.org.cn/api.php",
    'SESSION': requests.Session(),
    'lgname': '',# 用户名
    'lgpassword': "",# 密码
    'f_path' : 'pages.txt',
    'csrftoken': '',
}
def LogIn():
    # 输入：无
    # 功能：用户登录，返回登录结果
    # 输出：无

    token = FetchToken("login")
    params = {
        "action": "login",
        "lgname": workspace['lgname'],
        "lgpassword": workspace['lgpassword'],
        "lgtoken": token,
        "format": "json"
    }
    data = PostAPI(params)
    if (data["login"]["result"] == "Success"):
        print("登录成功，登录用户名：" + data["login"]["lgusername"] + "\n可以开始执行操作")
    else:
        print("登录失败，请退出重试")


def FetchToken(tokentype):
    # 输入：字符串类型，需要请求的令牌类型。（可选参数：csrf-编辑令牌, login-登录令牌, rollback-回退令牌, patrol-巡查令牌）
    # 功能：请求各类令牌
    # 输出：字符串类型，令牌参数

    params = {
        "action": "query",
        "meta": "tokens",
        "type": tokentype,
        "format": "json"
    }
    data = PostAPI(params)
    return data['query']['tokens'][tokentype + 'token']


def PostAPI(params, timeout=20):
    # 输入：字典类型，访问API的模块名、方法名和参数等
    # 功能：将一个请求通过API提交并解析返回值（JSON格式）
    # 输出：字典类型，经过解析的原始返回值
    # 另注：鉴于内容很多，取消了timeout参数，不然时间不足以完全提交上去
    status = False
    request_times = 1
    while not status:
        if request_times <= 15:
            try:
                resource = workspace['SESSION'].post(url=workspace['URL'], data=params)
                data = resource.json()
                if resource.status_code == 200:
                    status = True
                    return data
                else:
                    print(f'第{request_times}次请求错误，HTTP状态码为{resource.status_code}，正在重试')
                    request_times = request_times + 1
            except:
                print(f'第{request_times}次请求错误，正在重试')
                request_times = request_times + 1


