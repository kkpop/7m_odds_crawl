# 小型比赛根据support购买该方向，如果《40能够盈利则及时卖出，否则就等到赛终
# 大型比赛目前同理


=====================================共同准确公司（17-12，18-1）：
"Vcbet", "Macauslot", "Pinnacle", "G England Johns", "Betfair", "Bet 365", "Lottery Official", "PlanetWin365", "Sbobet", "Marathon", "18Bet", "Ladbrokes", "Smarkets", "10BET", "Manbetx",


爬虫部分：
redis_crawl.txt 用来添加需要爬取的页面        通过cmd下 type redis_crawl.txt | redis-cli 执行
pushed_redis_crawl  用来记录已经添加过的页面    如果需要重新爬取页面需要删除相关部分，并且进入redis-cli, flushdb

代理部分：
目前使用ipproxy项目获取代理
MySql ipproxy.free_ipproxy 中储存的即是proxy相关信息
proxy_list.txt 用来写pass的proxy，是临时折衷办法，如果需要使用，需要更改tools.py中获取代理的方法