import requests
import pdb
import random

class MyTools():
    def __init__(self):
        pass

    def list_average(mylist):
        num = len(mylist)
        sum_score = sum(mylist)
        ave_num = round(sum_score / num, 2)
        return ave_num

    def over_threshold_num(mylist, ave_num, threshold_value, direction):
        # direction=1,表示升高方向;   direction=-1,表示降低方向
        if direction == -1:
            over_num = len([i for i in mylist if (i - ave_num) < -threshold_value])
        elif direction == 1:
            over_num = len([i for i in mylist if (i - ave_num) > threshold_value])
        return over_num

    # def get_proxy():
    #     return requests.get("http://127.0.0.1:5010/get/").content
    #
    # def delete_proxy(proxy):
    #     requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

    def get_proxy():
        proxy_index = random.randint(1, 50)
        with open('auto_odds_compare/proxy_list.txt', 'r', encoding='utf-8') as proxy_list_file:
            line_count = 1
            for line in proxy_list_file.readlines():
                if proxy_index == line_count:
                    get_proxy = line.strip()
                    break
                line_count += 1
        return get_proxy

    def delete_proxy(proxy):
        print('代理出错：', proxy)