import requests
from encrpty import genEncrpty
from bs4 import BeautifulSoup
import json
import argparse
from prettytable import PrettyTable
import time
import ddddocr
import base64

ocr = ddddocr.DdddOcr()


def get_code(session):
    c_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/vcode.do"
    c = session.get(c_url)
    c_r = c.json()
    c_img = base64.b64decode(c_r['result'].split(',')[1])
    c = ocr.classification(c_img)
    return c, c_img


def genLoginSession(username, password):
    # get session
    session = requests.session()
    auth_server = 'https://newids.seu.edu.cn/authserver/login?service=https://newids.seu.edu.cn/authserver/login2.jsp'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/104.0.0.0 Safari/537.36 '
    }
    session.headers = headers
    res = session.get(auth_server, headers=headers)
    casLoginForm = {
        "username": username
    }
    # other hidden input info
    soup = BeautifulSoup(res.text, 'html.parser')
    hidden_inputs = soup.find_all("input", type="hidden")
    for item in hidden_inputs:
        if item.has_attr('name'):
            casLoginForm[item["name"]] = item["value"]
        else:
            casLoginForm[item["id"]] = item["value"]

    # password encrypt
    casLoginForm['password'] = genEncrpty(password, casLoginForm['pwdDefaultEncryptSalt'])

    # post
    res = session.post(auth_server, data=casLoginForm)
    # check if success:
    if "密码有误" in res.text:
        print("您提供的用户名或者密码有误")
        return False

    # get user info
    # for some unknown reasons the first request return 404.... so do some more times(10) until get 200
    getinfo_ok = False
    user_info = ''
    for _ in range(10):
        user_info = session.post('http://ehall.seu.edu.cn//restful/wecloud/user/userInfo')
        if user_info.status_code == 200:
            getinfo_ok = True
            break
    if getinfo_ok is False:
        print("Error occurs while connecting to http://ehall.seu.edu.cn//restful/wecloud/user/userInfo.")
        return False

    try:
        user_info = json.loads(user_info.content)
        user_info['datas']['cname'] = user_info['datas']['cname'][0] + '****'
        print('登陆成功，你的信息如下：')
        print(user_info['datas'])
    except Exception:
        print("something went wrong...")
        return False

    return session


def doLecture(session, lid=None):
    global wid
    print('开始查询讲座...')
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/*default/index.do#/hdyy"
    session.get(url)
    lecinfo_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxs.do"
    form = {"pageSize": 12, "pageNumber": 1}
    res = session.post(lecinfo_url, data=form)
    res_json = json.loads(res.content)
    lec_list = res_json['datas']['hdxxxs']['rows']
    print("已查询到如下讲座信息：")
    lec_table = PrettyTable(['序号', '讲座WID', '讲座名', '预约开始时间', '预约结束时间'])
    index = 0
    for lec in lec_list:
        lec_table.add_row([index, lec['WID'], lec['JZMC'], lec['YYKSSJ'], lec['YYJSSJ']])
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
        url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/modules/hdyy/hdxxxq_cx.do"
        data = {'WID': wid}
        res = session.post(url, data=data)
        try:
            result = json.loads(res.content)['datas']['hdxxxq_cx']['rows'][0]
            print('讲座信息如下:')
            print(result)
            st_time = time.mktime(time.strptime(lec_list[lec_index]['YYKSSJ'], "%Y-%m-%d %H:%M:%S"))
            ed_time = time.mktime(time.strptime(lec_list[lec_index]['YYJSSJ'], "%Y-%m-%d %H:%M:%S"))
            if time.time() > ed_time:
                print("该讲座已经过了预约时间了！")
                return
            else:
                print('当前时间在该讲座预约期内，准备提交预约...')
            break
        except Exception:
            print("课程信息获取失败，请重新输入讲座序号")
            continue
    print("开始提交预约..")
    submit_url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/yySave.do"
    num = 1
    while True:
        vcode, _ = get_code(session)
        data_json = {'HD_WID': wid, 'vcode': vcode}
        form = {"paramJson": json.dumps(data_json)}
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
        num += 1
        if num >= 50:
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--username', '-u', help='seu一卡通号', required=True)
    parser.add_argument('--password', '-p', help='seu服务中心密码', required=True)
    parser.add_argument('--lecture_id', '-id', help='自动选课的序号', required=False)
    args = parser.parse_args()

    loginSession = genLoginSession(args.username, args.password)
    if loginSession is not False:
        doLecture(loginSession, args.lecture_id)
    else:
        raise Exception('登陆出错，请检查账号密码是否输入正确或者查看日志！')