# -*- coding: utf-8 -*-

# 数据库结构说明:
# 每天建一个数据库，如：7m_matchs_2018_01_01
# 当天数据库每场比赛建一个集合（表）, 如：match_2373123
# 文档结构：
# {
#     '_id': '',
#     'league_name': '',
#     'home_name': '',
#     'away_name': '',
#     'start_time': '',
#     'half_match_result': '',
#     'match_result': '',
#     'company_list': ['', ''],   # 其中为match_id + '_' + company_id
# }
# 每场比赛每个公司再建一个赔率表，如：match_id_company_id
# 文档结构：
# {
#     '_id': '',
#     'company_name': '',
#     'home_odd': '',
#     'draw_odd': '',
#     'away_odd': '',
#     'update_time': '',
#     'count_index': '',
# }



from pymongo import MongoClient
import datetime
import json
import pdb

class AutoOddsComparePipeline(object):
    def __init__(self):
        # 链接数据库
        self.client = MongoClient(host='localhost', port=27017)
        # self.client.admin.authenticate(settings['MINGO_USER'], settings['MONGO_PSW'])     #如果有账户密码

    def process_item(self, item, spider):
        if spider.name == 'auto_odds_compare':
        # 这里写爬虫 auto_odds_compare 的逻辑
            db_name = '7m_matchs_' + item['current_search_date']
            self.db = self.client[db_name]  # 获得数据库的句柄
            match_name = 'match_' + item['match_id']
            # 如果match_name（集合名称） 在 该数据中，则使用update更新，否则insert
            if match_name in self.db.collection_names():
                col_exist = True
            else:
                col_exist = False
            self.coll = self.db[match_name]  # 获得collection的句柄

            try:
                match_company_id = item['match_id'] + '_' + item['company_id']  # 比赛id_公司id
                try:
                    league_name = item['league_name']
                    home_name = item['home_name']
                    away_name = item['away_name']
                    start_time = item['start_time']
                    half_match_result = item['half_match_result']
                    match_result = item['match_result']

                    # 如果col_exist，则update，否则insert
                    if col_exist:
                        updateItem = dict(match_company_id_list=match_company_id)
                        self.coll.update({}, {'$addToSet': updateItem})
                    else:
                        insertItem = dict(league_name=league_name, home_name=home_name, away_name=away_name,
                                        start_time=start_time, half_match_result=half_match_result,
                                        match_result=match_result, match_company_id_list=[match_company_id])
                        self.coll.insert(insertItem)
                except Exception as err:
                    print(err)
                    pass

                # match_name_2 = match_company_id
                # if match_name_2 in self.db.getCollectionNames():
                #     col_2_exist = True
                # else:
                #     col_2_exist = False
                self.coll_2 = self.db[match_company_id]  # 获得比赛ID_公司ID collection的句柄
                try:
                    company_name = item['company_name']
                    home_odd = item['home_odd']
                    draw_odd = item['draw_odd']
                    away_odd = item['away_odd']
                    update_time = item['update_time']
                    count_index = item['count_index']

                    # 不管col_2_exist，都insert
                    insertItem = dict(company_name=company_name, home_odd=home_odd, draw_odd=draw_odd,
                                      away_odd=away_odd, update_time=update_time, count_index=count_index)
                    self.coll_2.insert(insertItem)
                except Exception as err:
                    print(err)
                    pass
            finally:
                self.client.close()

        return item
