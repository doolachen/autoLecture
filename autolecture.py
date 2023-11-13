import requests
from encrpty import genEncrpty
from bs4 import BeautifulSoup
import json
import argparse
from prettytable import PrettyTable
import time
import copy
import ddddocr
import base64
from datetime import datetime
from login import *

ocr = ddddocr.DdddOcr()


def get_code(session):
    c_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/vcode.do"
    c = session.get(c_url)
    c_r = c.json()
    c_img = base64.b64decode(c_r['result'].split(',')[1])
    c = ocr.classification(c_img)
    return c, c_img


# def genLoginSession(username, password):
#     # get session
#     session = requests.session()
#     auth_server = 'https://auth.seu.edu.cn/auth/casapi/login?service=http%3A%2F%2Fehall.seu.edu.cn%2Flogin%3Fservice%3Dhttp%3A%2F%2Fehall.seu.edu.cn%2Fnew%2Findex.html'
#     headers = {
#         'Content-Type': 'application/x-www-form-urlencoded',
#         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
#                       'Chrome/104.0.0.0 Safari/537.36 '
#     }
#     session.headers = headers
#     res = session.get(auth_server, headers=headers)
#     casLoginForm = {
#         "username": username
#     }
#     # other hidden input info
#     soup = BeautifulSoup(res.text, 'html.parser')
#     hidden_inputs = soup.find_all("input", type="hidden")
#     for item in hidden_inputs:
#         if item.has_attr('name'):
#             casLoginForm[item["name"]] = item["value"]
#         else:
#             casLoginForm[item["id"]] = item["value"]
#
#     # password encrypt
#     casLoginForm['password'] = genEncrpty(password, casLoginForm['pwdDefaultEncryptSalt'])
#
#     # post
#     res = session.post(auth_server, data=casLoginForm)
#     # check if success:
#     if "密码有误" in res.text:
#         print("您提供的用户名或者密码有误")
#         return False
#
#     # get user info
#     # for some unknown reasons the first request return 404.... so do some more times(10) until get 200
#     getinfo_ok = False
#     user_info = ''
#     for _ in range(10):
#         user_info = session.post('http://ehall.seu.edu.cn//restful/wecloud/user/userInfo')
#         if user_info.status_code == 200:
#             getinfo_ok = True
#             break
#     if getinfo_ok is False:
#         print("Error occurs while connecting to http://ehall.seu.edu.cn//restful/wecloud/user/userInfo.")
#         return False
#
#     try:
#         user_info = json.loads(user_info.content)
#         user_info['datas']['cname'] = user_info['datas']['cname'][0] + '****'
#         print('登陆成功，你的信息如下：')
#         print(user_info['datas'])
#     except Exception:
#         print("something went wrong...")
#         return False
#
#     return session

def genLoginSession(username, password,url):
    return seu_login(username,password,url)


def doLecture(session, args):
    global wid
    lid = args.lecture_id
    print('开始查询讲座...')
    # url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do#/hdyy"
    # session.get(url)
    lecinfo_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxs.do"
    form = {"pageIndex":1,"pageSize": 100}
    res = session.post(lecinfo_url, data=form)
    res_json = json.loads(res.content)
    lec_list = res_json['datas']['hdxxxs']['rows']
    lec_list_show = copy.deepcopy(lec_list)
    print("已查询到如下讲座信息：")
    lec_table = PrettyTable(['序号', '讲座名', '地点(方式)', '预约开始时间', '讲座时间'])
    index = 0
    for lec in lec_list_show:
        if len(lec['JZMC']) >= 28:
            lec['JZMC'] = lec['JZMC'][:22] + '...' + lec['JZMC'][-6:]
        if len(lec['JZDD']) >= 12:
            lec['JZDD'] = lec['JZDD'][:8] + '..' + lec['JZDD'][-4:]
        lec['YYKSSJ'] = lec['YYKSSJ'][5:-3]
        lec['JZSJ'] = lec['JZSJ'][5:-3]
        lec_table.add_row([index, lec['JZMC'], lec['JZDD'], lec['YYKSSJ'], lec['JZSJ']])
        index += 1
    print(lec_table)
    print("输入抢课的序号:")
    while True:
        if lid is None:
            lec_index = int(input())
        else:
            lec_index = int(lid)

        if lec_index >= len(lec_list):
            print("序号输入错误，没有对应的讲座，请重新输入或运行脚本")
            continue

        wid = lec_list[lec_index]['WID']
        re_login_flag = False

        try:
            print('讲座信息如下:',lec_list[lec_index])
            st_time = time.mktime(time.strptime(lec_list[lec_index]['YYKSSJ'], "%Y-%m-%d %H:%M:%S"))
            ed_time = time.mktime(time.strptime(lec_list[lec_index]['YYJSSJ'], "%Y-%m-%d %H:%M:%S"))
            print('--------------------------------------------')
            print('讲座名：%s' % lec_list[lec_index]['JZMC'])
            print('讲座地点：%s' % lec_list[lec_index]['JZDD'])
            print('--------------------------------------------')
            if time.time() > ed_time:
                print("该讲座已经过了预约时间了！")
                return
            else:
                print('当前时间在该讲座预约期内，准备提交预约...')
                if time.time() < st_time:
                    d2 = datetime.fromtimestamp(st_time)
                    while True:
                        d1 = datetime.now()
                        if d2 >= d1:
                            d = d2 - d1
                        else:
                            print('用户倒计时结束')
                            break
                        time_s = d.days * 86400 + d.seconds
                        if time_s > 120 and not re_login_flag:
                            re_login_flag = True
                            print('倒计时较长，为保持session，1分钟的时候会重新进行登陆验证...')
                        if re_login_flag and 58 <= time_s <= 59:
                            print('\n重新进行登陆验证...')
                            session, redirect_url = genLoginSession(args.username, args.password,'http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do')
                            if session is not None and redirect_url is not None:
                                session.get(redirect_url)
                            else:
                                raise Exception('登陆出错，请检查账号密码是否输入正确或者查看日志！')
                            re_login_flag = False
                        if time_s >= 1:
                            print("\r用户倒计时%d秒" % time_s, end='')
                            time.sleep(1)
                        else:
                            print("\r用户倒计时%d秒" % time_s, end='')
                            break
            break
        except Exception:
            print("课程信息获取失败，请重新输入讲座序号")
            continue

    print("\n开始提交预约...")
    submit_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/yySave.do"
    num = 1
    while True:
        vcode, _ = get_code(session)
        data_json = {'HD_WID': wid, 'vcode': vcode}
        form = {"paramJson": json.dumps(data_json)}
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        session.headers.update(headers) # 更新headers
        res = session.post(submit_url, data=form)
        res = json.loads(res.content)
        print("尝试第%d次,%s" % (num, res))
        if res['code'] == 200 and res['success'] is True:
            print('恭喜预约成功！抢课结束')
            return
        elif 'msg' in res:
            if '人数已满' in res['msg']:
                print('当前预约人数已满，抢课over')
                return
            else:
                print(res['code'], res['msg'], res['success'])
        num += 1
        if num >= 100:
            print('100次执行完毕..请查看最终结果')
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--username', '-u', help='seu一卡通号', required=True)
    parser.add_argument('--password', '-p', help='seu服务中心密码', required=True)
    parser.add_argument('--lecture_id', '-id', help='自动选课的序号', required=False)
    args = parser.parse_args()

    loginSession, redirect_url = genLoginSession(args.username, args.password,'http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do')
    if loginSession is not None and redirect_url is not None:
        loginSession.get(redirect_url)
        doLecture(loginSession, args)
    else:
        raise Exception('登陆出错，请检查账号密码是否输入正确或者查看日志！')
