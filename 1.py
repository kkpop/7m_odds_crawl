# -*- coding: utf-8 -*-

import requests
import random
import json
import pdb

proxy_total_num = 200
proxy_index = random.randint(0, proxy_total_num-1)
proxy_list_text = requests.get("http://127.0.0.1:8000/select?name=ipproxy.free_ipproxy&count={}".format(proxy_total_num)).content.decode()
proxy_dict = json.loads(proxy_list_text)[proxy_index]
proxy = proxy_dict['ip'] + ':' + str(proxy_dict['port'])
pdb.set_trace()

