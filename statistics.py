from pymongo import MongoClient
import datetime
import time
import regex
import json
import pdb
import numpy
from collections import Counter

def compute_payBackRate(odd0,odd1,odd2):
    # 计算返还率
    pay_back_rate = round(odd0*odd1*odd2/(odd0*odd1+odd0*odd2+odd1*odd2), 4)
    return pay_back_rate
def compute_lastOdd(odd0,odd1):
    # 计算返还率
    lastOdd = round(odd0*odd1/(odd0*odd1-odd0-odd1), 4)
    return lastOdd
def judge_profit(support_direction, match_result, home_odd, draw_odd, away_odd):
    support_total_netRate = -1
    sum_support_direction = sum(support_direction)
    if match_result == 3 and support_direction[0] == 1:
        if sum_support_direction == 2:
            support_total_netRate = home_odd * 0.5 - 1
        else:
            support_total_netRate = home_odd - 1
    if match_result == 1 and support_direction[1] == 1:
        if sum_support_direction == 2:
            support_total_netRate = draw_odd * 0.5 - 1
        else:
            support_total_netRate = draw_odd - 1
    if match_result == 0 and support_direction[2] == 1:
        if sum_support_direction == 2:
            support_total_netRate = away_odd * 0.5 - 1
        else:
            support_total_netRate = away_odd - 1
    return support_total_netRate

# 查询参数
open_assign_search_date = False     # 是否制定确切日期
open_save_single_match = True      # 是否保存单场比赛信息

need_company_id = '156'  # 必须含有的公司ID
need_company_number = 35    # 开赔率公司必须达到的数量

if open_assign_search_date:
    assign_search_date = '2017-01-06'
    # assign_search_date = '2018-01-06'
    coll_name = assign_search_date.replace('-', '')
else:
    info_days = 20   # 收集多少天的信息
    assign_end_date = datetime.datetime(2017, 1, 20)  # 指定结束日期
    start_date = (assign_end_date + datetime.timedelta(days=-(info_days - 1))).strftime("%Y-%m-%d")
    end_date = (assign_end_date + datetime.timedelta(days=0)).strftime("%Y-%m-%d")
    coll_name = start_date.replace('-', '') + '_' + end_date.replace('-', '')

# 算法参数
# limit_mktime = 14200    # 最后只读取赛前 n/3600 小时内的数据
# limit_change_prob = 0.05    # 变化限制赔率

search_date = []
if open_assign_search_date:
    search_date.append(assign_search_date)
else:
    for i in range(info_days):
        add_day = (assign_end_date + datetime.timedelta(days=-(i))).strftime("%Y-%m-%d")
        search_date.append(add_day)

# 链接数据库
client = MongoClient(host='localhost', port=27018)
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
                    'search_date': single_date,
                    'league_name': league_name,
                    'home_name': home_name,
                    'away_name': away_name,
                }
                limit_home_odd = ''  # 最大限制主赔
                limit_draw_odd = ''  # 最大限制平赔
                limit_away_odd = ''  # 最大限制客赔
                support_direction = [1, 1, 1]

                # 如果某公司ID不在该场比赛中就跳过
                if need_company_id != '' and not need_company_id in [item.split('_')[-1] for item in match_company_id_list]:
                    continue
                for single_company_id in match_company_id_list:
                    if single_company_id.split('_')[-1] != need_company_id:
                        continue
                    # 遍历单场比赛所有赔率公司列表, 为了求限制时间前的平均概率
                    company_coll = db[single_company_id]
                    company_coll_cursor = company_coll.find().sort('count_index', -1)    # 时间从早到晚排序
                    count = 0
                    for single_match_company_dict in company_coll_cursor:
                        # 遍历单场比赛单家公司所有赔率
                        home_odd = single_match_company_dict['home_odd']
                        draw_odd = single_match_company_dict['draw_odd']
                        away_odd = single_match_company_dict['away_odd']
                        if count == 0:
                            limit_home_odd = compute_lastOdd(draw_odd, away_odd)
                            limit_draw_odd = compute_lastOdd(home_odd, away_odd)
                            limit_away_odd = compute_lastOdd(draw_odd, home_odd)
                        else:
                            if home_odd > limit_home_odd:
                                support_direction[0] = 0
                            if draw_odd > limit_draw_odd:
                                support_direction[1] = 0
                            if away_odd > limit_away_odd:
                                support_direction[2] = 0
                        single_match_info_dict['home_odd'] = home_odd
                        single_match_info_dict['draw_odd'] = draw_odd
                        single_match_info_dict['away_odd'] = away_odd
                        count += 1
                support_direction_sum = sum(support_direction)
                support_total_netRate = 0
                # if support_direction_sum != 3 and support_direction_sum != 0:
                if support_direction_sum == 1:
                    support_total_netRate = judge_profit(support_direction, single_match_info_dict['match_result'], single_match_info_dict['home_odd'], single_match_info_dict['draw_odd'], single_match_info_dict['away_odd'])
                    match_info_dict['support_total_num'] += 1  # 一场比赛有支持就加上1
                    # print('match_result: %s' % single_match_info_dict['match_result'])
                    # print('support_direction: %s %s %s' % (
                    # support_direction[0], support_direction[1], support_direction[2]))

                single_match_info_dict['support_direction'] = str(support_direction[0]) + str(support_direction[1]) + str(support_direction[2])
                single_match_info_dict['support_total_netRate'] = round(support_total_netRate, 2)
                if round(support_total_netRate, 2) > 0:
                    # 如果利润大于0，正确数就加1
                    match_info_dict['support_total_right'] += 1
                match_info_dict['support_total_netRate'] += round(support_total_netRate, 2)
                match_info_dict['match_info_list'].append(single_match_info_dict)
        date_info_list.append(match_info_dict)
    all_support_total_right = 0
    all_support_total_netRate = 0
    all_support_total_num = 0
    success_rate_list = []
    for date_info in date_info_list:
        if open_save_single_match:
            # 保存单场比赛信息
            db_name = 'odds_compare_statistics_latest'
            db = client[db_name]  # 获得数据库的句柄db = self.client[db_name]  # 获得数据库的句柄
            for single_match_info_dict in date_info['match_info_list']:
                coll = db[coll_name + '_matchs_' + single_match_info_dict['search_date']]
                insertItem = dict(联赛名称=single_match_info_dict['league_name'], 主队名称=single_match_info_dict['home_name'], 客队名称=single_match_info_dict['away_name'],
                                  比赛结果=single_match_info_dict['match_result'], 主胜=single_match_info_dict['home_odd'],
                                  平局=single_match_info_dict['draw_odd'], 客胜=single_match_info_dict['away_odd'],
                                  支持方向=single_match_info_dict['support_direction'])
                coll.insert(insertItem)
        all_support_total_right += date_info['support_total_right']
        all_support_total_netRate += date_info['support_total_netRate']
        all_support_total_num += date_info['support_total_num']
        if all_support_total_num == 0:
            continue
        current_success_rate = round(all_support_total_right/all_support_total_num, 2)
        success_rate_list.append(current_success_rate)
    if all_support_total_num == 0:
        if open_assign_search_date:
            print('当前无推荐比赛')
        else:
            print('当天无推荐比赛')
    success_rate_variance = numpy.var(numpy.array(success_rate_list))
    success_rate_mean = numpy.mean(numpy.array(success_rate_list))
    print('支持正确数: %s,'
          ' 支持净利润: %s, 总支持数: %s, 命中率平均值: %s, 命中率方差: %s,'
          ' 利润率: %s' % (all_support_total_right, round(all_support_total_netRate, 3), all_support_total_num, round(success_rate_mean, 3), round(success_rate_variance, 3), round(all_support_total_netRate/all_support_total_num, 3)))
    # 将统计数据保存到数据库
    db_name = 'odds_compare_statistics_latest'
    db = client[db_name]  # 获得数据库的句柄db = self.client[db_name]  # 获得数据库的句柄
    coll = db[coll_name]  # 获得collection的句柄
    insertItem = dict(支持正确数=all_support_total_right,
                      支持净利润=round(all_support_total_netRate, 3), 总支持数=all_support_total_num,
                      命中率平均值=round(success_rate_mean, 3), 命中率方差=round(success_rate_variance, 3), 利润率=round(all_support_total_netRate/all_support_total_num, 3))
    coll.insert(insertItem)

finally:
    client.close()