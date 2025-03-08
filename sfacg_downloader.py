import time
import requests
import re
import hashlib
import json
import uuid
from requests.exceptions import ConnectTimeout, ConnectionError, Timeout

with open('dict.json', 'r', encoding='utf-8') as file:
    dictionary = json.load(file)
nonce = "C7DC5CAD-31CF-4431-8635-B415B75BF4F3"
device_token = str(uuid.uuid4()).upper()
SALT = "FN_Q29XHVmfV3mYX"
headers = {
    'Host': 'api.sfacg.com',
    'accept-charset': 'UTF-8',
    'authorization': 'Basic YW5kcm9pZHVzZXI6MWEjJDUxLXl0Njk7KkFjdkBxeHE=',
    'accept': 'application/vnd.sfacg.api+json;version=1',
    'user-agent': f'boluobao/5.0.36(android;32)/H5/{device_token.lower()}/H5',
    'accept-encoding': 'gzip',
    'Content-Type': 'application/json; charset=UTF-8'
}


def md5_hex(input, case):
    m = hashlib.md5()
    m.update(input.encode())

    if case == 'Upper':
        return m.hexdigest().upper()
    else:
        return m.hexdigest()


def get_catalog(novel):
    chapter = []
    title = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

    url = f"https://book.sfacg.com/Novel/{novel}/MainIndex/"

    with requests.get(url, headers=headers) as resp:
        links = re.findall(r'<a href="(.*?)" title=', resp.text)
        title = re.findall(r'<h1 class="story-title">(.*?)</h1>', resp.text)[0]
        for link in links:
            chapter_id = link.split('/')[-2]
            chapter.append(chapter_id)
    return title, chapter


def download_chapter(chapters):
    content = ""
    for chapter in chapters:
        retry = 3  # 最大重试次数
        while retry > 0:
            try:
                timestamp = int(time.time() * 1000)
                sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
                headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
                url = f"https://api.sfacg.com/Chaps/{chapter}?expand=content%2CneedFireMoney%2CoriginNeedFireMoney%2Ctsukkomi%2Cchatlines%2Cisbranch%2CisContentEncrypted%2CauthorTalk&autoOrder=false"
                # 设置超时时间为10秒
                resp = requests.get(url, headers=headers, timeout=10).json()
                if resp['status']['httpCode'] == 200:
                    content += resp['data']['title'] + '\n'
                    tmp = ""
                    warn = ""
                    if 'content' in resp['data']:
                        tmp += resp['data']['content']
                        if 'expand' in resp['data'] and 'content' in resp['data']['expand']:
                            tmp += resp['data']['expand']['content']
                    else:
                        tmp += resp['data']['expand']['content']
                    for char in tmp:
                        if char in dictionary:
                            content += dictionary[char]
                        else:
                            # if ('\u4e00' <= char <= '\u9fff'):
                            #     warn = '该章节有错字未替换，请检查\n'
                            content += char
                    content += '\n' + warn
                    print(f"{resp['data']['title']} 已下载")
                    break  # 成功则跳出重试循环
                else:
                    print(f"{chapter} 下载失败，HTTP状态码：{resp['status']['httpCode']}")
                    break
            except (ConnectTimeout, ConnectionError, Timeout) as e:
                print(f"请求超时，剩余重试次数：{retry-1}")
                retry -= 1
                time.sleep(5)  # 重试前等待5秒
            except Exception as e:
                print(f"未知错误：{str(e)}")
                break
        if retry == 0:
            print(f"{chapter} 下载失败，已达最大重试次数")
            content += f"\n{chapter} 下载失败\n"
    return content


def get_cookie(username, password):
    timestamp = int(time.time() * 1000)
    sign = md5_hex(f"{nonce}{timestamp}{device_token}{SALT}", 'Upper')
    headers['sfsecurity'] = f'nonce={nonce}&timestamp={timestamp}&devicetoken={device_token}&sign={sign}'
    data = json.dumps(
        {"password": password, "shuMeiId": "", "username": username})
    url = "https://api.sfacg.com/sessions"
    resp = requests.post(url, headers=headers, data=data)
    if (resp.json()["status"]["httpCode"] == 200):
        cookie = requests.utils.dict_from_cookiejar(resp.cookies)
        return f'.SFCommunity={cookie[".SFCommunity"]}; session_APP={cookie["session_APP"]}'
    else:
        return "请检查账号或密码是否错误"


if __name__ == "__main__":

    novel = input("输入小说ID:")
    username = input("输入手机号:")
    password = input("输入密码:")
    headers['cookie'] = get_cookie(username, password)
    print(headers['cookie'])
    if (headers['cookie'] == "请检查账号或密码是否错误"):
        print("请检查账号或密码是否错误")
    else:
        title, chapter = get_catalog(novel)
        content = title + '\n\n' + download_chapter(chapter)
        title = title.replace('\\', ' ').replace('\/', ' ').replace(':', ' ').replace('*', ' ').replace(
            '?', ' ').replace('\"', ' ').replace('<', ' ').replace('>', ' ').replace('|', ' ')
        with open(f'{title}.txt', 'w', encoding="utf-8") as f:
            f.write(content)
