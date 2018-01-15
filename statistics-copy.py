from pymongo import MongoClient
import datetime
import time
import regex
import json
import pdb
from collections import Counter


# 查询参数
info_days = 6  # 收集多少天的信息

# 算法参数
limit_mktime = 18000    # 只读取赛前 n/3600 小时内的数据
limit_support = 1
limit_probability = -0.03   # 小于该数字的概率可以排除

search_date = []
for i in range(info_days):
    add_day = (datetime.datetime.now() + datetime.timedelta(days=-(i + 3))).strftime("%Y-%m-%d")
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
        }
        for coll_match_name in coll_match_list:
            # 找到是整场比赛的集合
            if len(regex.findall(r'match_', coll_match_name)) == 0:
                continue
            coll = db[coll_match_name]  # 获得collection的句柄
            match_id = coll_match_name.split('_')[-1]
            single_date_rate_dict = {}
            for single_match_dict in coll.find():
                # 遍历当天所有比赛
                start_time = single_match_dict['start_time']    # 如：2018-01-12 18:00
                start_timestamp = time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M"))  # 开赛时间戳
                match_result = single_match_dict['match_result']
                match_company_id_list = single_match_dict['match_company_id_list']
                # 单场比赛信息字典
                single_match_info_dict = {
                    'start_time': start_time,
                    'match_result': match_result,
                }
                # 单场比赛的支持数
                single_match_support_dict = {
                    'home': 0,
                    'draw': 0,
                    'away': 0,
                }
                last_home_prob_list = []   # 平均限制时间终主赔列表
                last_draw_prob_list = []   # 平均限制时间终平赔列表
                last_away_prob_list = []   # 平均限制时间终客赔列表
                if len(match_company_id_list) < 10:
                    continue    # 该场比赛开盘公司数目小于10就跳过
                for single_company_id in match_company_id_list:
                # 遍历单场比赛所有赔率公司列表, 为了求限制时间前的平均概率
                    company_coll = db[single_company_id]
                    company_coll_cursor = company_coll.find().sort('update_time', 1)    # 时间从早到晚排序
                    prev_home_probability = 0
                    prev_draw_probability = 0
                    prev_away_probability = 0
                    prev_update_mktime = 0
                    current_company_odd_num = company_coll_cursor.count()   # 当前比赛当前公司赔率数目
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
                last_home_prob_average = round(sum(last_home_prob_list)/len(last_home_prob_list), 3)
                last_draw_prob_average = round(sum(last_draw_prob_list)/len(last_draw_prob_list), 3)
                last_away_prob_average = round(sum(last_away_prob_list)/len(last_away_prob_list), 3)

                for single_company_id in match_company_id_list:
                # 遍历单场比赛所有赔率公司列表，为了找出小于一定概率阈值而排除的方向
                    if single_company_id.split('_')[-1] != '37':
                        continue
                    company_coll_2 = db[single_company_id]
                    company_coll_cursor_2 = company_coll_2.find().sort('update_time', 1)    # 时间从早到晚排序
                    # 单家公司的支持数
                    single_company_support_dict = {
                        'home': 0,
                        'draw': 0,
                        'away': 0,
                    }
                    pdb.set_trace()
                    for single_match_company_dict in company_coll_cursor_2:
                        update_time = single_match_company_dict['update_time']
                        update_mktime = time.mktime(time.strptime(update_time, "%Y-%m-%d %H:%M"))  # 当前更新时间戳
                        if (start_timestamp - update_mktime) > limit_mktime:
                            continue
                        # # 遍历单场比赛单家公司所有赔率
                        # home_odd = single_match_company_dict['home_odd']
                        # draw_odd = single_match_company_dict['draw_odd']
                        # away_odd = single_match_company_dict['away_odd']
                        # home_probability = round(
                        #     (draw_odd * away_odd) / (home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                        # draw_probability = round(
                        #     (home_odd * away_odd) / (home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                        # away_probability = round(
                        #     (home_odd * draw_odd) / (home_odd * draw_odd + home_odd * away_odd + draw_odd * away_odd), 3)
                        # kaili_home_betfair = round((home_probability / last_home_prob_average), 3)
                        # kaili_draw_betfair = round((draw_probability / last_draw_prob_average), 3)
                        # kaili_away_betfair = round((away_probability / last_away_prob_average), 3)
                        pdb.set_trace()



                # current_support_num = 0     # 当前比赛支持数量
                # current_support_right = 0     # 当前比赛支持是否正确  1：正确    0：错误
                # current_support_netRate = 0     # 当前比赛支持净评分
                # if not (single_match_info_dict['support']['home'] >= limit_support and single_match_info_dict['support']['draw'] >= limit_support and single_match_info_dict['support']['away'] >= limit_support):
                #     if single_match_info_dict['support']['home'] >= limit_support:
                #         if single_match_info_dict['match_result'] == 3:
                #             current_support_netRate = (single_match_info_dict['last_home_odd'] - 1)
                #             current_support_right = 1
                #         if single_match_info_dict['last_away_odd'] < 1.5 and single_match_info_dict['match_result'] == 1 and single_match_info_dict['support']['draw'] < limit_support:
                #             current_support_netRate = round(0.5 * single_match_info_dict['last_home_odd'] - 1, 2)
                #             current_support_right = 1
                #         current_support_num += 1
                #     if single_match_info_dict['support']['draw'] >= limit_support:
                #         if single_match_info_dict['match_result'] == 1:
                #             current_support_netRate = (single_match_info_dict['last_draw_odd'] - 1)
                #             current_support_right = 1
                #         if single_match_info_dict['last_away_odd'] < 1.5 and single_match_info_dict['match_result'] == 3 and single_match_info_dict['support']['home'] < limit_support:
                #             current_support_netRate = round(0.5 * single_match_info_dict['last_home_odd'] - 1, 2)
                #             current_support_right = 1
                #         if single_match_info_dict['last_home_odd'] < 1.5 and single_match_info_dict['match_result'] == 0 and single_match_info_dict['support']['away'] < limit_support:
                #             current_support_netRate = round(0.5 * single_match_info_dict['last_away_odd'] - 1, 2)
                #             current_support_right = 1
                #         current_support_num += 1
                #     if single_match_info_dict['support']['away'] >= limit_support:
                #         if single_match_info_dict['match_result'] == 0:
                #             current_support_netRate = (single_match_info_dict['last_away_odd'] - 1)
                #             current_support_right = 1
                #         if single_match_info_dict['last_home_odd'] < 1.5 and single_match_info_dict['match_result'] == 1 and single_match_info_dict['support']['draw'] < limit_support:
                #             current_support_netRate = round(0.5 * single_match_info_dict['last_draw_odd'] - 1, 2)
                #             current_support_right = 1
                #         current_support_num += 1
                # if current_support_num != 0:
                #     print('主odd:', single_match_info_dict['last_home_odd'])
                #     print('平odd:', single_match_info_dict['last_draw_odd'])
                #     print('客odd:', single_match_info_dict['last_draw_odd'])
                #     match_info_dict['support_total_right'] += current_support_right
                #     match_info_dict['support_total_netRate'] += round(current_support_netRate / current_support_num, 2)
                #     print('加上：', round(current_support_netRate / current_support_num, 2))
                #     print('--------------------')
                #     match_info_dict['support_total_num'] += 1
        # date_info_list.append(match_info_dict)
    # all_support_total_right = 0
    # all_support_total_netRate = 0
    # all_support_total_num = 0
    # for date_info in date_info_list:
    #     all_support_total_right += date_info['support_total_right']
    #     all_support_total_netRate += date_info['support_total_netRate']
    #     all_support_total_num += date_info['support_total_num']
    #
    # print('limit_mktime: %s, limit_support: %s, limit_differential_coefficient: %s' % (limit_mktime, limit_support, limit_differential_coefficient))
    # print('all_support_total_right: %s, all_support_total_netRate: %s, all_support_total_num: %s, margin_rate: %s' % (all_support_total_right, all_support_total_netRate, all_support_total_num, round((all_support_total_netRate - all_support_total_num + all_support_total_right)/all_support_total_num, 2)))

finally:
    client.close()