# -*- coding: utf-8 -*-

from gevent import monkey
import time
monkey.patch_all()

import datetime

from dock.common import init_dockenv
init_dockenv()
import traceback
from gevent.pool import Pool
from datetime import timedelta
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.ad import Ad
from dock_console.business_manager.libs import BusinessManagerToken
from dock_console.utils.helpers import generate_list_chunks
from dock_console.sdk.facebook_marketing import FacebookAPI

#from dock_ads.topasset.libs.creative import Creative
from dock_ads.asset.libs.creative import Creative
from dock_console import logger
from dock.pubsub import PubSub
from dock_ads.asset.crawlers import FacebookAdBatchMetricsCrawler
from dock_console import connect_mongodb
from dock_console.configs import cherrypie_config
from dock_console.utils.helpers import generate_date_chunks
from dock_console.common.agency import AgencyType

connect_mongodb()


def get_ads(agency_type, ad_account_id, start_date, end_date, status='ACTIVE'):
    time_st = time.time()
    ad_creative_lst = list()
    ad_dict = {}
    account = AdAccount(ad_account_id)
    ads = account.get_ads(params={'fields': ['creative']})
    for ad in ads:
        ad_creative_lst.append((ad['id'], ad['creative']['id']))
    time_end = time.time()
    logger.info(
        'account {} get ads use time {}, num {}'.format(ad_account_id, time_end - time_st, len(ad_creative_lst)))
    return ad_creative_lst


def crawl_insight(agency_type, start_date, end_date, insight_pool_size, account_ids):
    business_info = dict()
    for _ in range(3):
        try:
            for token in BusinessManagerToken.get_tokens_by_tag(cherrypie_config.business_manager_tags['facebook_asset']):
                business = token.get_media_manager_token_info()
                if business['agency_type'] == agency_type:
                    business_info = business
                    break
        except:
            logger.error('get token by tag error, retry')
            logger.error('TRACEBACK', traceback.format_exc())
    if not business_info:
        return False
    Creative.init_products()
    api_wrapper = FacebookAPI(business_info)
    ad_creative_lst = list()
    end_date_for_get_ads = start_date + timedelta(days=1)
    for account_id in account_ids:
        ad_creative_lst.extend(get_ads(agency_type, account_id, start_date, end_date_for_get_ads))
    logger.info('download ad insights start, ads is {}'.format(len(ad_creative_lst)))
    crawler = FacebookAdBatchMetricsCrawler(agency_type, start_date, end_date)
    pool = Pool(insight_pool_size)
    ad_creative_lst = generate_list_chunks(ad_creative_lst, 2000)
    for ad_creatives in ad_creative_lst:
        pool.spawn(crawler.crawl_ads_insights, api_wrapper, ad_creatives)
    pool.join()
    return True


def run_creative_insight(account_ids):
    try:
        logger.info("Task repair creative insight crawl start.")
        start_date = datetime.datetime.strptime('2019-01-08', '%Y-%m-%d')
        end_date = datetime.datetime.strptime('2019-01-18', '%Y-%m-%d')

        for s, e in sorted(generate_date_chunks(start_date, end_date, chunk_size=1), reverse=True):
            logger.info(
                "Task repair creative insight crawl {} {} start.".format(s, e))
            for agency_type in [AgencyType.Opua]:
                success = crawl_insight(agency_type, s, e, 2, account_ids)
                if not success:
                    logger.info("Task creative insight crawl {} {} {} no token.".format(s, e, agency_type))
            p = PubSub.create([])
            msg = {"message_info": {"expiration_time": 1547944200.0, "start_date": s.strftime('%Y-%m-%d'), "end_date": e.strftime('%Y-%m-%d')}}
            p.publish(msg, cherrypie_config.pubsub_topics.get('creative_insight_topics', {}).get('sync'))
            logger.info(
                "Task repair creative insight crawl {} {} finish.".format(s, e))

        logger.info("Task repair creative insight crawl finish. {}")

    except:
        logger.info('Task creative insight crawl failed!')
        logger.captureException()
        logger.traceback()
        logger.error('Task creative insight crawl error', exc_info=True)
    logger.info('Task creative insight crawl end')


if __name__ == '__main__':
    account_ids = ['act_727284444322928', 'act_282812992424880', 'act_2155718148013235', 'act_331966674075757']
    run_creative_insight(account_ids)

