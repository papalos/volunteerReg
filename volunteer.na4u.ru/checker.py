import json


def pswAdm(adm_lgn, adm_psw):
    fp = open('conn.fig')
    s = fp.read()
    dic = json.loads(s)
    check = (adm_lgn == dic.get('adm_lgn')) and (adm_psw == dic.get('adm_psw')) if True else False
    fp.close()
    return check

