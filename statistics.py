from pymongo import MongoClient
import datetime
import time
import regex
import json
import pdb
import numpy
from collections import Counter


# 查询参数
open_assign_search_date = False     # 是否制定确切日期
open_save_single_match = True      # 是否保存单场比赛信息

need_company_id = '17'  # 必须含有的公司ID
need_company_number = 35    # 开赔率公司必须达到的数量

if open_assign_search_date:
    assign_search_date = '2018-01-05'
    coll_name = assign_search_date.replace('-', '')
else:
    info_days = 8  # 收集多少天的信息
    start_date = (datetime.datetime.now() + datetime.timedelta(days=-((info_days-1) + 4))).strftime("%Y-%m-%d")
    end_date = (datetime.datetime.now() + datetime.timedelta(days=-(0 + 4))).strftime("%Y-%m-%d")
    coll_name = start_date.replace('-', '') + '_' + end_date.replace('-', '')

# 算法参数
# limit_mktime = 14200    # 只读取赛前 n/3600 小时内的数据
# limit_change_prob = 0.05    # 变化限制赔率

for limit_mktime in range(14100, 14400, 300):
    for limit_change_prob in numpy.arange(0.05, 0.055, 0.005):
        limit_change_prob = round(limit_change_prob, 3)
        search_date = []
        if open_assign_search_date:
            search_date.append(assign_search_date)
        else:
            for i in range(info_days):
                add_day = (datetime.datetime.now() + datetime.timedelta(days=-(i + 4))).strftime("%Y-%m-%d")
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
                        original_home_prob_list = []  # 初主赔列表
                        original_draw_prob_list = []  # 初平赔列表
                        original_away_prob_list = []  # 初客赔列表

                        last_home_prob_list = []   # 平均限制时间终主赔列表
                        last_draw_prob_list = []   # 平均限制时间终平赔列表
                        last_away_prob_list = []   # 平均限制时间终客赔列表
                        if len(match_company_id_list) < need_company_number:
                            continue    # 该场比赛开盘公司数目小于10就跳过

                        # 如果某公司ID不在该场比赛中就跳过
                        if need_company_id != '' and not need_company_id in [item.split('_')[-1] for item in match_company_id_list]:
                            continue
                        for single_company_id in match_company_id_list:
                        # 遍历单场比赛所有赔率公司列表, 为了求限制时间前的平均概率
                            company_coll = db[single_company_id]
                            company_coll_cursor = company_coll.find().sort('update_time', 1)    # 时间从早到晚排序
                            prev_home_probability = 0
                            prev_draw_probability = 0
                            prev_away_probability = 0
                            prev_update_mktime = 0
                            current_company_odd_num = company_coll_cursor.count()   # 当前比赛当前公司赔率数目
                            # if single_company_id.split('_')[-1] == '37':
                            #     single_match_company_list = []
                            #     for single_match_company_dict in company_coll_cursor:
                            #         home_odd = single_match_company_dict['home_odd']
                            #         draw_odd = single_match_company_dict['draw_odd']
                            #         away_odd = single_match_company_dict['away_odd']
                            #         update_time = single_match_company_dict['update_time']
                            #         update_mktime = time.mktime(time.strptime(update_time, "%Y-%m-%d %H:%M"))  # 当前更新时间戳
                            #         # if (start_timestamp - update_mktime) > limit_mktime:
                            #         #     continue
                            #         # 保存限定时间内该公司的赔率
                            #         current_dict = {
                            #             'home': home_odd,
                            #             'draw': draw_odd,
                            #             'away': away_odd,
                            #             'update_mktime': update_mktime,
                            #         }
                            #         single_match_company_list.append(current_dict)
                            #     specific_company_dict['37'] = single_match_company_list
                            # else:
                            count = 0
                            for single_match_company_dict in company_coll_cursor:
                            # 遍历单场比赛单家公司所有赔率
                                home_odd = single_match_company_dict['home_odd']
                                draw_odd = single_match_company_dict['draw_odd']
                                away_odd = single_match_company_dict['away_odd']
                                home_probability = round((draw_odd * away_odd)/(home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                                draw_probability = round((home_odd * away_odd)/(home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                                away_probability = round((home_odd * draw_odd)/(home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                                update_time = single_match_company_dict['update_time']
                                update_mktime = time.mktime(time.strptime(update_time, "%Y-%m-%d %H:%M"))    # 当前更新时间戳
                                if count == 0:
                                    original_home_prob_list.append(home_probability)
                                    original_draw_prob_list.append(draw_probability)
                                    original_away_prob_list.append(away_probability)
                                if (start_timestamp - update_mktime) <= limit_mktime:
                                    # 如果小于最近几小时的限定时间，就开始计算概率比较平均概率
                                    # 取prev赔率为最后赔率
                                    if prev_update_mktime != 0:
                                        last_home_prob_list.append(prev_home_probability)
                                        last_draw_prob_list.append(prev_draw_probability)
                                        last_away_prob_list.append(prev_away_probability)
                                    break
                                    # 将当前信息保存到到prev中
                                prev_home_probability = home_probability
                                prev_draw_probability = draw_probability
                                prev_away_probability = away_probability
                                prev_update_mktime = update_mktime
                                count += 1
                        if len(last_home_prob_list) == 0:
                            continue
                        last_home_prob_average = round(sum(last_home_prob_list)/len(last_home_prob_list), 3)
                        last_draw_prob_average = round(sum(last_draw_prob_list)/len(last_draw_prob_list), 3)
                        last_away_prob_average = round(sum(last_away_prob_list)/len(last_away_prob_list), 3)

                        original_home_prob_average = round(sum(original_home_prob_list) / len(original_home_prob_list), 3)
                        original_draw_prob_average = round(sum(original_draw_prob_list) / len(original_draw_prob_list), 3)
                        original_away_prob_average = round(sum(original_away_prob_list) / len(original_away_prob_list), 3)

                        # pdb.set_trace()
                        home_pro_diff = (last_home_prob_average - original_home_prob_average) - limit_change_prob
                        draw_pro_diff = (last_draw_prob_average - original_draw_prob_average) > limit_change_prob
                        away_pro_diff = (last_away_prob_average - original_away_prob_average) > limit_change_prob
                        if home_pro_diff > 0 or draw_pro_diff > 0 or away_pro_diff > 0:
                            if home_pro_diff > 0:
                                # 跳过选择方向赔率小于1.5的比赛
                                if (0.95/last_home_prob_average) < 1.5:
                                    continue
                                if single_match_info_dict['match_result'] == 3:
                                    match_info_dict['support_total_right'] += 1
                                    match_info_dict['support_total_netRate'] += (0.95/last_home_prob_average-1)
                                else:
                                    match_info_dict['support_total_netRate'] += -1
                                match_info_dict['support_total_num'] += 1
                                single_match_info_dict['support_direction'] = 3
                            if draw_pro_diff > 0:
                                # 跳过选择方向赔率小于1.5的比赛
                                if (0.95 / last_draw_prob_average) < 1.5:
                                    continue
                                if single_match_info_dict['match_result'] == 1:
                                    match_info_dict['support_total_right'] += 1
                                    match_info_dict['support_total_netRate'] += (0.95/last_draw_prob_average-1)
                                else:
                                    match_info_dict['support_total_netRate'] += -1
                                match_info_dict['support_total_num'] += 1
                                single_match_info_dict['support_direction'] = 1
                            if away_pro_diff > 0:
                                # 跳过选择方向赔率小于1.5的比赛
                                if (0.95 / last_away_prob_average) < 1.5:
                                    continue
                                if single_match_info_dict['match_result'] == 0:
                                    match_info_dict['support_total_right'] += 1
                                    match_info_dict['support_total_netRate'] += (0.95/last_away_prob_average-1)
                                else:
                                    match_info_dict['support_total_netRate'] += -1
                                match_info_dict['support_total_num'] += 1
                                single_match_info_dict['support_direction'] = 0
                            single_match_info_dict['search_date'] = single_date
                            single_match_info_dict['league_name'] = league_name
                            single_match_info_dict['home_name'] = home_name
                            single_match_info_dict['away_name'] = away_name
                            single_match_info_dict['home_odd'] = 0.95 / last_home_prob_average
                            single_match_info_dict['draw_odd'] = 0.95 / last_draw_prob_average
                            single_match_info_dict['away_odd'] = 0.95 / last_away_prob_average
                            match_info_dict['match_info_list'].append(single_match_info_dict)
                date_info_list.append(match_info_dict)
            all_support_total_right = 0
            all_support_total_netRate = 0
            all_support_total_num = 0
            success_rate_list = []
            for date_info in date_info_list:
                if open_save_single_match:
                # 保存单场比赛信息
                    db_name = 'odds_compare_statistics'
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
                current_success_rate = round(all_support_total_right/all_support_total_num, 2)
                success_rate_list.append(current_success_rate)

            success_rate_variance = numpy.var(numpy.array(success_rate_list))
            success_rate_mean = numpy.mean(numpy.array(success_rate_list))
            print('临场N小时: %s, 限制概率变化: %s, 支持正确数: %s,'
                  ' 支持净利润: %s, 总支持数: %s, 命中率平均值: %s, 命中率方差: %s,'
                  ' 利润率: %s' % (limit_mktime, limit_change_prob, all_support_total_right, round(all_support_total_netRate, 3), all_support_total_num, round(success_rate_mean, 3), round(success_rate_variance, 3), round(all_support_total_netRate/all_support_total_num, 3)))
            db_name = 'odds_compare_statistics'
            db = client[db_name]  # 获得数据库的句柄db = self.client[db_name]  # 获得数据库的句柄
            coll = db[coll_name]  # 获得collection的句柄
            insertItem = dict(临场N小时=limit_mktime, 限制概率变化=limit_change_prob, 支持正确数=all_support_total_right,
                              支持净利润=round(all_support_total_netRate, 3), 总支持数=all_support_total_num,
                              命中率平均值=round(success_rate_mean, 3), 命中率方差=round(success_rate_variance, 3), 利润率=round(all_support_total_netRate/all_support_total_num, 3))
            coll.insert(insertItem)

        finally:
            client.close()