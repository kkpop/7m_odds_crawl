from pymongo import MongoClient
import datetime
import time
import regex
import json
import pdb
import math
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
from pylab import *
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

mpl.rcParams['font.sans-serif'] = ['SimHei']    #支持中文
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号

# 查询参数
open_assign_search_date = False     # 是否制定确切日期
open_save_single_match = False      # 是否保存单场比赛信息

need_company_id = ['37', '156']  # 必须含有的公司ID
need_company_number = 35    # 开赔率公司必须达到的数量
assign_company_id = '156'   # 指定的要比较的公司

if open_assign_search_date:
    assign_search_date = '2017-07-08'
    # assign_search_date = '2018-01-06'
    coll_name = assign_search_date.replace('-', '')
else:
    info_days = 10  # 收集多少天的信息
    assign_end_date = datetime.datetime(2017, 7, 10)    # 指定结束日期
    start_date = (assign_end_date + datetime.timedelta(days=-(info_days-1))).strftime("%Y-%m-%d")
    end_date = (assign_end_date + datetime.timedelta(days=0)).strftime("%Y-%m-%d")
    coll_name = start_date.replace('-', '') + '_' + end_date.replace('-', '')

# 算法参数
limit_mktime_hour = 1440    # 最后只读取赛前 n 分钟内的数据
per_n_min = 5   # 每几分钟读取一次赔率
# limit_change_prob = 0.05    # 变化限制赔率

# 将List中为0的元素用后面的赔率替换
def fill_list_gap(list, pre_odd):
    wait_to_change_index_list = []
    for i, v in enumerate(list):
        if i != len(list) - 1:
            if v == 0:
                wait_to_change_index_list.append(i)
            elif len(wait_to_change_index_list) != 0:
                for index in wait_to_change_index_list:
                    list[index] = v
                wait_to_change_index_list = []
        elif v == 0 and prev_home_odd != 0:
        # 如果最后一个值也是0，且pre值不等于0，那么就用pre值替换掉所有为0的数
            wait_to_change_index_list.append(i)
            for index in wait_to_change_index_list:
                list[index] = pre_odd
            wait_to_change_index_list = []
    if len(wait_to_change_index_list) != 0:
        # 剩下后面全是0的情况
        first_blank_index = wait_to_change_index_list[0]
    else:
        first_blank_index = -1
    list.append(first_blank_index)
    return list

# 对每个list元素求和
def merge_list_element(total_list, single_List):
    temp_list = []
    for i, j in zip(total_list, single_List):
        sum = i + j
        temp_list.append(sum)
        total_list = temp_list  # 主胜赔率列表
    return total_list

# 求每个列表元素的平均值
def compute_average_list(list, divide_list):
    temp_list = []
    for i, j in zip(list, divide_list):
        if j == 0:
            sum = 0
        else:
            sum = round(i / j, 3)
        temp_list.append(sum)
    list = temp_list
    return list

# 求前面概率相对后面概率的变化，并保存进list
def get_odds_change_list(list):
    temp_list = []
    for i, j in enumerate(list):
        if i == len(list)-1:
            sum = 0
        else:
            sum = j - list[i + 1]
        temp_list.append(sum)
    return temp_list

for limit_mktime in range(14100, 14400, 300):
    for limit_change_prob in np.arange(0.05, 0.055, 0.005):
        for limit_pro_change in np.arange(0.03, 0.031, 0.001):
            limit_pro_change = round(limit_pro_change, 4)
            search_date = []
            if open_assign_search_date:
                search_date.append(assign_search_date)
            else:
                for i in range(info_days):
                    add_day = (assign_end_date + datetime.timedelta(days=-(i))).strftime("%Y-%m-%d")
                    search_date.append(add_day)

            # 链接数据库
            client = MongoClient(host='localhost', port=27017)
            # client.admin.authenticate(settings['MINGO_USER'], settings['MONGO_PSW'])     #如果有账户密码
            try:
                date_info_list = []
                for single_date in search_date:
                    db_name = '7m_matchs_' + single_date.replace('-', '_')
                    db = client[db_name]  # 获得数据库的句柄
                    coll_match_list = db.collection_names()
                    match_info_dict = {
                        'support_total_right': 0,
                        'support_total_netRate': 0,
                        'support_total_num': 0,
                        'match_info_list': [],
                    }
                    correct_support = []
                    wrong_support = []
                    for coll_match_name in coll_match_list:
                        # 找到是整场比赛的集合
                        if len(regex.findall(r'match_', coll_match_name)) == 0:
                            continue
                        coll = db[coll_match_name]  # 获得collection的句柄
                        match_id = coll_match_name.split('_')[-1]
                        for single_match_dict in coll.find():
                            # 遍历当天所有比赛
                            league_name = single_match_dict['league_name']
                            home_name = single_match_dict['home_name']
                            away_name = single_match_dict['away_name']
                            start_time = single_match_dict['start_time']    # 如：2018-01-12 18:00
                            start_timestamp = time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M"))  # 开赛时间戳
                            match_result = single_match_dict['match_result']
                            match_company_id_list = single_match_dict['match_company_id_list']
                            # 单场比赛信息字典
                            single_match_info_dict = {
                                'start_time': start_time,
                                'match_result': match_result,
                            }

                            if len(match_company_id_list) < need_company_number:
                                continue    # 该场比赛开盘公司数目小于10就跳过

                            # 如果某公司ID不在该场比赛中就跳过
                            # pdb.set_trace()
                            if need_company_id != '':
                                if_continue = False
                                for company_id in need_company_id:
                                    if not company_id in [item.split('_')[-1] for item in match_company_id_list]:
                                        if_continue = True
                                if if_continue:
                                    continue
                            # 该场比赛所有筛选出公司的赔率和列表
                            all_home_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)  # 主胜赔率
                            all_draw_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)  # 平局赔率
                            all_away_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)  # 客胜赔率
                            # 指定的公司的赔率和列表
                            assign_companys_all_home_odd_per_5_min_list = [0] * int(
                                limit_mktime_hour / per_n_min)  # 主胜赔率
                            assign_companys_all_draw_odd_per_5_min_list = [0] * int(
                                limit_mktime_hour / per_n_min)  # 平局赔率
                            assign_companys_all_away_odd_per_5_min_list = [0] * int(
                                limit_mktime_hour / per_n_min)  # 客胜赔率
                            # betfair的赔率和列表
                            betfair_all_home_odd_per_5_min_list = [0] * int(
                                limit_mktime_hour / per_n_min)  # 主胜赔率
                            betfair_all_draw_odd_per_5_min_list = [0] * int(
                                limit_mktime_hour / per_n_min)  # 平局赔率
                            betfair_all_away_odd_per_5_min_list = [0] * int(
                                limit_mktime_hour / per_n_min)  # 客胜赔率

                            first_blank_index_list = []     # 记录第一个位置为空的index,为了之后求平均值计算除数
                            assign_first_blank_index_list = []     # 记录第一个位置为空的index,为了之后求平均值计算除数
                            betfair_first_blank_index_list = []     # 记录第一个位置为空的index,为了之后求平均值计算除数
                            for single_company_id in match_company_id_list:
                            # 遍历单场比赛所有赔率公司列表, 为了求限制时间前的平均概率
                                company_coll = db[single_company_id]
                                company_coll_cursor = company_coll.find().sort('count_index', -1)    # 时间从早到晚排序
                                # 跳过所有变赔数量小于10的公司
                                # if company_coll_cursor.count() < 5:
                                #     continue
                                # 保存前一次赔率
                                prev_home_odd = 0
                                prev_draw_odd = 0
                                prev_away_odd = 0
                                prev_assign_home_odd = 0
                                prev_assign_draw_odd = 0
                                prev_assign_away_odd = 0

                                count = 0
                                # 每5分钟记录一个赔率的列表
                                single_company_all_home_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)   # 主胜赔率
                                single_company_all_draw_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)   # 平局赔率
                                single_company_all_away_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)   # 客胜赔率
                                # 指定公司的赔率列表
                                assign_company_all_home_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)  # 主胜赔率
                                assign_company_all_draw_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)  # 平局赔率
                                assign_company_all_away_odd_per_5_min_list = [0] * int(limit_mktime_hour / per_n_min)  # 客胜赔率

                                for single_match_company_dict in company_coll_cursor:
                                # 遍历单场比赛单家公司所有赔率
                                    update_time = single_match_company_dict['update_time']
                                    update_mktime = time.mktime(time.strptime(update_time, "%Y-%m-%d %H:%M"))    # 当前更新时间戳
                                    before_start_mktime_min = (start_timestamp - update_mktime)/60   # 赛前多少分钟
                                    home_odd = single_match_company_dict['home_odd']
                                    draw_odd = single_match_company_dict['draw_odd']
                                    away_odd = single_match_company_dict['away_odd']
                                    if before_start_mktime_min >= limit_mktime_hour:
                                        # 跳过大于等于limit_mktime_hour分钟（limit_mktime_hour/60个小时）的更新时间
                                        # 将当前信息保存到到prev中
                                        prev_home_odd = home_odd
                                        prev_draw_odd = draw_odd
                                        prev_away_odd = away_odd
                                        if single_company_id.split('_')[-1] == assign_company_id:
                                            prev_assign_home_odd = home_odd
                                            prev_assign_draw_odd = draw_odd
                                            prev_assign_away_odd = away_odd
                                        continue
                                    home_probability = round((draw_odd * away_odd) / (
                                            home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                                    draw_probability = round((home_odd * away_odd) / (
                                            home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                                    away_probability = round((home_odd * draw_odd) / (
                                            home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)

                                    per_5_min_list_index = int(before_start_mktime_min / per_n_min)  # 计算应该放在列表中的索引值
                                    single_company_all_home_odd_per_5_min_list[per_5_min_list_index] = home_odd  # 存储到赔率列表中，靠近开赛时间的赔率保存在列表低位
                                    single_company_all_draw_odd_per_5_min_list[per_5_min_list_index] = draw_odd  # 存储到赔率列表中
                                    single_company_all_away_odd_per_5_min_list[per_5_min_list_index] = away_odd  # 存储到赔率列表中

                                    # 如果该公司是指定公司
                                    if single_company_id.split('_')[-1] == assign_company_id:
                                        assign_company_all_home_odd_per_5_min_list[per_5_min_list_index] = home_odd
                                        assign_company_all_draw_odd_per_5_min_list[per_5_min_list_index] = draw_odd
                                        assign_company_all_away_odd_per_5_min_list[per_5_min_list_index] = away_odd
                                    elif single_company_id.split('_')[-1] == '37':
                                        betfair_all_home_odd_per_5_min_list[per_5_min_list_index] = home_odd
                                        betfair_all_draw_odd_per_5_min_list[per_5_min_list_index] = draw_odd
                                        betfair_all_away_odd_per_5_min_list[per_5_min_list_index] = away_odd
                                    count += 1

                                # 在遍历单家公司所有赔率后，把是0的用后面的值补上

                                single_company_all_home_odd_per_5_min_list = fill_list_gap(single_company_all_home_odd_per_5_min_list, prev_home_odd)
                                single_company_all_home_odd_per_5_min_list.pop()    # 去掉最后一个标志位
                                single_company_all_draw_odd_per_5_min_list = fill_list_gap(single_company_all_draw_odd_per_5_min_list, prev_draw_odd)
                                single_company_all_draw_odd_per_5_min_list.pop()  # 去掉最后一个标志位
                                single_company_all_away_odd_per_5_min_list = fill_list_gap(single_company_all_away_odd_per_5_min_list, prev_away_odd)
                                first_blank_index_mark = single_company_all_away_odd_per_5_min_list.pop()  # 去掉最后一个标志位,-1 说明全都有赔率，否则是第一个为blank的Index
                                if first_blank_index_mark != -1:
                                    # 剩下后面全是0的情况
                                    first_blank_index = first_blank_index_mark
                                else:
                                    first_blank_index = int(limit_mktime_hour / per_n_min)
                                first_blank_index_list.append(first_blank_index)

                                if single_company_id.split('_')[-1] == assign_company_id:
                                    # 在遍历指定公司所有赔率后，把是0的用后面的值补上
                                    assign_company_all_home_odd_per_5_min_list = fill_list_gap(
                                        assign_company_all_home_odd_per_5_min_list, prev_assign_home_odd)
                                    assign_company_all_home_odd_per_5_min_list.pop()  # 去掉最后一个标志位
                                    assign_company_all_draw_odd_per_5_min_list = fill_list_gap(
                                        assign_company_all_draw_odd_per_5_min_list, prev_assign_draw_odd)
                                    assign_company_all_draw_odd_per_5_min_list.pop()  # 去掉最后一个标志位
                                    assign_company_all_away_odd_per_5_min_list = fill_list_gap(
                                        assign_company_all_away_odd_per_5_min_list, prev_assign_away_odd)
                                    first_blank_index_mark = assign_company_all_away_odd_per_5_min_list.pop()  # 去掉最后一个标志位,-1 说明全都有赔率，否则是第一个为blank的Index
                                    if first_blank_index_mark != -1:
                                        # 剩下后面全是0的情况
                                        assign_first_blank_index = first_blank_index_mark
                                    else:
                                        assign_first_blank_index = int(limit_mktime_hour / per_n_min)
                                    assign_first_blank_index_list.append(assign_first_blank_index)

                                if single_company_id.split('_')[-1] == '37':
                                    # 在遍历到betfair所有赔率后，把是0的用后面的值补上
                                    betfair_all_home_odd_per_5_min_list = fill_list_gap(
                                        betfair_all_home_odd_per_5_min_list, prev_assign_home_odd)
                                    betfair_all_home_odd_per_5_min_list.pop()  # 去掉最后一个标志位
                                    betfair_all_draw_odd_per_5_min_list = fill_list_gap(
                                        betfair_all_draw_odd_per_5_min_list, prev_assign_draw_odd)
                                    betfair_all_draw_odd_per_5_min_list.pop()  # 去掉最后一个标志位
                                    betfair_all_away_odd_per_5_min_list = fill_list_gap(
                                        betfair_all_away_odd_per_5_min_list, prev_assign_away_odd)
                                    betfair_first_blank_index_mark = betfair_all_away_odd_per_5_min_list.pop()  # 去掉最后一个标志位,-1 说明全都有赔率，否则是第一个为blank的Index
                                    if betfair_first_blank_index_mark != -1:
                                        # 剩下后面全是0的情况
                                        betfair_first_blank_index = betfair_first_blank_index_mark
                                    else:
                                        betfair_first_blank_index = int(limit_mktime_hour / per_n_min)
                                    betfair_first_blank_index_list.append(betfair_first_blank_index)

                                # 对列表求和
                                all_home_odd_per_5_min_list = merge_list_element(all_home_odd_per_5_min_list, single_company_all_home_odd_per_5_min_list)
                                all_draw_odd_per_5_min_list = merge_list_element(all_draw_odd_per_5_min_list, single_company_all_draw_odd_per_5_min_list)
                                all_away_odd_per_5_min_list = merge_list_element(all_away_odd_per_5_min_list, single_company_all_away_odd_per_5_min_list)
                                # 对指定公司列表求和
                                assign_companys_all_home_odd_per_5_min_list = merge_list_element(assign_companys_all_home_odd_per_5_min_list, assign_company_all_home_odd_per_5_min_list)
                                assign_companys_all_draw_odd_per_5_min_list = merge_list_element(assign_companys_all_draw_odd_per_5_min_list, assign_company_all_draw_odd_per_5_min_list)
                                assign_companys_all_away_odd_per_5_min_list = merge_list_element(assign_companys_all_away_odd_per_5_min_list, assign_company_all_away_odd_per_5_min_list)
                                # pdb.set_trace()

                            # 给每阶段赔率分配除数的列表
                            total_odd_divide_list = [len(first_blank_index_list)] * int(limit_mktime_hour / per_n_min)
                            for blank_index in first_blank_index_list:
                            # 遍历first_blank_index_List, 改变odd_divide_list
                                max_list_len = int(limit_mktime_hour / per_n_min)
                                if blank_index != max_list_len:
                                # 当空白index不等于最大值时，说明divide需要降低
                                    for i in range(blank_index, max_list_len):
                                    # 每个blank_index及以后都减去1
                                        total_odd_divide_list[i] -= 1

                            total_odd_divide_assign_company_list = [len(assign_first_blank_index_list)] * int(limit_mktime_hour / per_n_min)
                            for blank_index in assign_first_blank_index_list:
                            # 遍历assign_first_blank_index_list, 改变total_odd_divide_assign_company_list
                                max_list_len = int(limit_mktime_hour / per_n_min)
                                if blank_index != max_list_len:
                                # 当空白index不等于最大值时，说明divide需要降低
                                    for i in range(blank_index, max_list_len):
                                    # 每个blank_index及以后都减去1
                                        total_odd_divide_assign_company_list[i] -= 1

                            total_odd_divide_betfair_company_list = [len(betfair_first_blank_index_list)] * int(
                                limit_mktime_hour / per_n_min)
                            for blank_index in betfair_first_blank_index_list:
                            # 遍历betfair_first_blank_index_list, 改变total_odd_divide_betfair_company_list
                                max_list_len = int(limit_mktime_hour / per_n_min)
                                if blank_index != max_list_len:
                                # 当空白index不等于最大值时，说明divide需要降低
                                    for i in range(blank_index, max_list_len):
                                    # 每个blank_index及以后都减去1
                                        total_odd_divide_betfair_company_list[i] -= 1

                            # 遍历赔率列表，求每阶段赔率的平均值
                            max_not_blank_index = len(total_odd_divide_list)-1
                            for i, v in enumerate(total_odd_divide_list):
                                if v == 0:
                                    max_not_blank_index = i-1
                                    break
                            for i, v in enumerate(betfair_all_home_odd_per_5_min_list):
                                if v == 0 and i <= max_not_blank_index:
                                    max_not_blank_index = i - 1
                                    break
                            for i, v in enumerate(assign_companys_all_home_odd_per_5_min_list):
                                if v == 0 and i <= max_not_blank_index:
                                    max_not_blank_index = i - 1
                                    break

                            all_home_odd_per_5_min_list = compute_average_list(all_home_odd_per_5_min_list, total_odd_divide_list)
                            all_draw_odd_per_5_min_list = compute_average_list(all_draw_odd_per_5_min_list, total_odd_divide_list)
                            all_away_odd_per_5_min_list = compute_average_list(all_away_odd_per_5_min_list, total_odd_divide_list)
                            # 遍历指定公司赔率列表，求每阶段赔率的平均值
                            assign_companys_all_home_odd_per_5_min_list = compute_average_list(assign_companys_all_home_odd_per_5_min_list, total_odd_divide_assign_company_list)
                            assign_companys_all_draw_odd_per_5_min_list = compute_average_list(assign_companys_all_draw_odd_per_5_min_list, total_odd_divide_assign_company_list)
                            assign_companys_all_away_odd_per_5_min_list = compute_average_list(assign_companys_all_away_odd_per_5_min_list, total_odd_divide_assign_company_list)
                            # 遍历betfair公司赔率列表，求每阶段赔率的平均值
                            betfair_all_home_odd_per_5_min_list = compute_average_list(betfair_all_home_odd_per_5_min_list, total_odd_divide_betfair_company_list)
                            betfair_all_draw_odd_per_5_min_list = compute_average_list(betfair_all_draw_odd_per_5_min_list, total_odd_divide_betfair_company_list)
                            betfair_all_away_odd_per_5_min_list = compute_average_list(betfair_all_away_odd_per_5_min_list, total_odd_divide_betfair_company_list)
                            # pdb.set_trace()

                            # home_odd_differ_list = []
                            # for i, j in zip(all_home_odd_per_5_min_list, assign_companys_all_home_odd_per_5_min_list):
                            #     home_odd_differ_list.append(round(i-j, 3))
                            # draw_odd_differ_list = []
                            # for i, j in zip(all_draw_odd_per_5_min_list, assign_companys_all_draw_odd_per_5_min_list):
                            #     draw_odd_differ_list.append(round(i - j, 3))
                            # away_odd_differ_list = []
                            # for i, j in zip(all_away_odd_per_5_min_list, assign_companys_all_away_odd_per_5_min_list):
                            #     away_odd_differ_list.append(round(i - j, 3))

                            # 颠倒后最左边为最久远的更新赔率
                            if len(assign_first_blank_index_list) == 0:
                                assign_first_blank_index_value = len(all_home_odd_per_5_min_list)
                            else:
                                assign_first_blank_index_value = assign_first_blank_index_list[0]
                            # home_odd_differ_list = home_odd_differ_list[:assign_first_blank_index_value]
                            # draw_odd_differ_list = draw_odd_differ_list[:assign_first_blank_index_value]
                            # away_odd_differ_list = away_odd_differ_list[:assign_first_blank_index_value]
                            # home_odd_differ_list.reverse()
                            # draw_odd_differ_list.reverse()
                            # away_odd_differ_list.reverse()
                            try:
                                all_home_probility_per_5_min_list = [(0.95/odd) for odd in all_home_odd_per_5_min_list[:max_not_blank_index]]
                                all_draw_probility_per_5_min_list = [(0.95/odd) for odd in all_draw_odd_per_5_min_list[:max_not_blank_index]]
                                all_away_probility_per_5_min_list = [(0.95/odd) for odd in all_away_odd_per_5_min_list[:max_not_blank_index]]
                                all_home_probility_per_5_min_list.reverse()
                                all_draw_probility_per_5_min_list.reverse()
                                all_away_probility_per_5_min_list.reverse()
                                all_home_odd_per_5_min_list = all_home_odd_per_5_min_list[:max_not_blank_index]
                                all_draw_odd_per_5_min_list = all_draw_odd_per_5_min_list[:max_not_blank_index]
                                all_away_odd_per_5_min_list = all_away_odd_per_5_min_list[:max_not_blank_index]
                                all_home_odd_per_5_min_list.reverse()
                                all_draw_odd_per_5_min_list.reverse()
                                all_away_odd_per_5_min_list.reverse()
                                # all_home_probility_per_5_min_change_list = get_odds_change_list(all_home_probility_per_5_min_list)
                                # all_draw_probility_per_5_min_change_list = get_odds_change_list(all_draw_probility_per_5_min_list)
                                # all_away_probility_per_5_min_change_list = get_odds_change_list(all_away_probility_per_5_min_list)
                                # all_home_probility_per_5_min_change_list.reverse()
                                # all_draw_probility_per_5_min_change_list.reverse()
                                # all_away_probility_per_5_min_change_list.reverse()
                                assign_companys_all_home_pro_per_5_min_list = [(0.95/odd) for odd in assign_companys_all_home_odd_per_5_min_list[:max_not_blank_index]]
                                assign_companys_all_draw_pro_per_5_min_list = [(0.95/odd) for odd in assign_companys_all_draw_odd_per_5_min_list[:max_not_blank_index]]
                                assign_companys_all_away_pro_per_5_min_list = [(0.95/odd) for odd in assign_companys_all_away_odd_per_5_min_list[:max_not_blank_index]]
                                assign_companys_all_home_pro_per_5_min_list.reverse()
                                assign_companys_all_draw_pro_per_5_min_list.reverse()
                                assign_companys_all_away_pro_per_5_min_list.reverse()
                                assign_companys_all_home_odd_per_5_min_list = assign_companys_all_home_odd_per_5_min_list[:max_not_blank_index]
                                assign_companys_all_draw_odd_per_5_min_list = assign_companys_all_draw_odd_per_5_min_list[:max_not_blank_index]
                                assign_companys_all_away_odd_per_5_min_list = assign_companys_all_away_odd_per_5_min_list[:max_not_blank_index]
                                assign_companys_all_home_odd_per_5_min_list.reverse()
                                assign_companys_all_draw_odd_per_5_min_list.reverse()
                                assign_companys_all_away_odd_per_5_min_list.reverse()
                                betfair_all_home_pro_per_5_min_list = [(0.95/odd) for odd in betfair_all_home_odd_per_5_min_list[:max_not_blank_index]]
                                betfair_all_draw_pro_per_5_min_list = [(0.95/odd) for odd in betfair_all_draw_odd_per_5_min_list[:max_not_blank_index]]
                                betfair_all_away_pro_per_5_min_list = [(0.95/odd) for odd in betfair_all_away_odd_per_5_min_list[:max_not_blank_index]]
                                betfair_all_home_pro_per_5_min_list.reverse()
                                betfair_all_draw_pro_per_5_min_list.reverse()
                                betfair_all_away_pro_per_5_min_list.reverse()
                                betfair_all_home_odd_per_5_min_list = betfair_all_home_odd_per_5_min_list[:max_not_blank_index]
                                betfair_all_draw_odd_per_5_min_list = betfair_all_draw_odd_per_5_min_list[:max_not_blank_index]
                                betfair_all_away_odd_per_5_min_list = betfair_all_away_odd_per_5_min_list[:max_not_blank_index]
                                betfair_all_home_odd_per_5_min_list.reverse()
                                betfair_all_draw_odd_per_5_min_list.reverse()
                                betfair_all_away_odd_per_5_min_list.reverse()
                            except:
                                print('ERROR!')
                                pdb.set_trace()
                            names = []
                            for i in range(len(all_home_odd_per_5_min_list)):
                                if i % 5 == 0:
                                    name = str((i+1)*per_n_min)
                                else:
                                    name = ''
                                names.append(name)
                            names.reverse()
                            x = arange(len(names))
                            # limit_x = assign_first_blank_index_list[0] * 5
                            # pdb.set_trace()
                            # xlim(0, limit_x)
                            # ax = plt.subplot(111)  # 注意:一般都在ax中设置,不再plot中设置
                            plt.plot(x, assign_companys_all_home_odd_per_5_min_list, marker='o', mec='r', ms=10, label=u'pin主胜赔率')
                            plt.plot(x, betfair_all_home_odd_per_5_min_list, marker='o', mec='g', ms=10, label=u'betfair主胜赔率')
                            plt.plot(x, assign_companys_all_draw_odd_per_5_min_list, marker='*', mec='g', ms=10, label=u'pin平局赔率')
                            plt.plot(x, betfair_all_draw_odd_per_5_min_list, marker='*', mec='g', ms=10, label=u'betfair平局赔率')
                            plt.plot(x, assign_companys_all_away_odd_per_5_min_list, marker='^', mec='g', ms=10, label=u'pin客胜赔率')
                            plt.plot(x, betfair_all_away_odd_per_5_min_list, marker='^', mec='g', ms=10, label=u'betfair客胜赔率')
                            # plt.plot(x, away_odd_differ_list, marker='o', mec='b', ms=10, label=u'客胜赔率differ')
                            plt.xticks(x, names, rotation=45)
                            # xmajorLocator = MultipleLocator(5)
                            # xminorLocator = MultipleLocator(1)
                            # ax.xaxis.set_major_locator(xmajorLocator)
                            # ax.xaxis.set_minor_locator(xminorLocator)
                            # ax.xaxis.grid(True, which='major')  # x坐标轴的网格使用主刻度
                            # plt.minorticks_off()
                            plt.margins(0)
                            plt.subplots_adjust(bottom=0.15)
                            plt.xlabel(u"per_time(min): %s" % per_n_min)  # X轴标签
                            plt.ylabel("odd differ")  # Y轴标签
                            plt.legend()  # 让图例生效
                            plt.grid(True)
                            odds_text = str(all_home_odd_per_5_min_list[3]) + ' ' + str(all_draw_odd_per_5_min_list[3]) + ' ' + str(all_away_odd_per_5_min_list[3])
                            plt.title("平均赔率-pinnacle 赛果:%s 赔率: %s" % (single_match_info_dict['match_result'], odds_text))  # 标题
                            plt.show()

                            first_find_index = ''
                            first_find_direction = ''
                            # for i,v in enumerate(all_home_probility_per_5_min_change_list):
                            #     if v > limit_pro_change and (first_find_index == '' or i < first_find_index):
                            #         first_find_index = i
                            #         first_find_direction = 3
                            #         print('推荐3')
                            #         break
                            # for i,v in enumerate(all_draw_probility_per_5_min_change_list):
                            #     if v > limit_pro_change and (first_find_index == '' or i < first_find_index):
                            #         first_find_index = i
                            #         first_find_direction = 1
                            #         print('推荐1')
                            #         break
                            # for i,v in enumerate(all_away_probility_per_5_min_change_list):
                            #     if v > limit_pro_change and (first_find_index == '' or i < first_find_index):
                            #         first_find_index = i
                            #         first_find_direction = 0
                            #         print('推荐0')
                            #         break
                            # if first_find_direction != '':
                            #     print('赛果: %s' % single_match_info_dict['match_result'])
                            #     print('---------')
                            #     pdb.set_trace()
                            # if single_match_info_dict['match_result'] == first_find_direction:
                            #     if first_find_direction == 3:
                            #         correct_support.append(all_home_odd_per_5_min_list[0] - 1)
                            #     elif first_find_direction == 1:
                            #         correct_support.append(all_draw_odd_per_5_min_list[0] - 1)
                            #     else:
                            #         correct_support.append(all_away_odd_per_5_min_list[0] - 1)
                            # elif first_find_direction != '':
                            #     wrong_support.append(-1)
                            # pdb.set_trace()

                    print('limit_pro_change: %s' % limit_pro_change)
                    print('总收入: %s' % sum(correct_support))
                    print('总支出: %s' % sum(wrong_support))
                    print('---0---')
                    # pdb.set_trace()
                    date_info_list.append(match_info_dict)
                # all_support_total_right = 0
                # all_support_total_netRate = 0
                # all_support_total_num = 0
                # success_rate_list = []
                # for date_info in date_info_list:
                #     if open_save_single_match:
                #     # 保存单场比赛信息
                #         db_name = 'odds_compare_statistics'
                #         db = client[db_name]  # 获得数据库的句柄db = self.client[db_name]  # 获得数据库的句柄
                #         for single_match_info_dict in date_info['match_info_list']:
                #             coll = db[coll_name + '_matchs_' + single_match_info_dict['search_date']]
                #             insertItem = dict(联赛名称=single_match_info_dict['league_name'], 主队名称=single_match_info_dict['home_name'], 客队名称=single_match_info_dict['away_name'],
                #                               比赛结果=single_match_info_dict['match_result'], 主胜=single_match_info_dict['home_odd'],
                #                               平局=single_match_info_dict['draw_odd'], 客胜=single_match_info_dict['away_odd'],
                #                               支持方向=single_match_info_dict['support_direction'])
                #             coll.insert(insertItem)
                #     all_support_total_right += date_info['support_total_right']
                #     all_support_total_netRate += date_info['support_total_netRate']
                #     all_support_total_num += date_info['support_total_num']
                #     if all_support_total_num == 0:
                #         continue
                #     current_success_rate = round(all_support_total_right/all_support_total_num, 2)
                #     success_rate_list.append(current_success_rate)
                #
                # # pdb.set_trace()
                # if len(success_rate_list) == 0:
                #     continue
                # success_rate_variance = np.var(np.array(success_rate_list))
                # success_rate_mean = np.mean(np.array(success_rate_list))
                # if open_assign_search_date and all_support_total_num == 0:
                #     break
                # print('临场N小时: %s, 限制概率变化: %s, 限制平局赔率差: %s, 支持正确数: %s,'
                #       ' 支持净利润: %s, 总支持数: %s, 命中率平均值: %s, 命中率方差: %s,'
                #       ' 利润率: %s' % (limit_mktime, limit_change_prob, limit_draw_odd_differ, all_support_total_right, round(all_support_total_netRate, 3), all_support_total_num, round(success_rate_mean, 3), round(success_rate_variance, 3), round(all_support_total_netRate/all_support_total_num, 3)))
                # db_name = 'odds_compare_statistics'
                # db = client[db_name]  # 获得数据库的句柄db = self.client[db_name]  # 获得数据库的句柄
                # coll = db[coll_name]  # 获得collection的句柄
                # insertItem = dict(临场N小时=limit_mktime, 限制概率变化=limit_change_prob, 限制平局赔率差=limit_draw_odd_differ, 支持正确数=all_support_total_right,
                #                   支持净利润=round(all_support_total_netRate, 3), 总支持数=all_support_total_num,
                #                   命中率平均值=round(success_rate_mean, 3), 命中率方差=round(success_rate_variance, 3), 利润率=round(all_support_total_netRate/all_support_total_num, 3))
                # coll.insert(insertItem)

            finally:
                client.close()