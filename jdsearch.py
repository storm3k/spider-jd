import os
import pickle

import requests
from lxml import etree
import re
from random import choice

from xpinyin import Pinyin

# 下载图片
from tasks import save_image


class JDSearch(object):

    def __init__(self, kw):
        self.base_url = 'http://search.jd.com/Search'
        self.headers = {
            'User-Agent': 'Mozilla / 5.0(Windows NT 10.0; WOW64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 70.0.3538.110 Safari / 537.36'
        }
        self.params = '&keyword={}&wq={}&enc=utf-8&stock=0'.format(
            kw, self.get_pinyin(kw)
        )
        self.url = self.base_url + "?" + self.params

    @staticmethod
    def get_pinyin(word):
        p = Pinyin()
        return p.get_pinyin(word, '')

    def get_response(self, url):
        try:
            data = requests.get(url, headers=self.headers).text
            return data
        except Exception as e:
            print("获取响应失败：", url)
            print(e)
            return None

    def get_all_search_page(self):
        """获取所有的搜索页面"""
        response = self.get_response(self.url)
        # 最大页面数量
        try:
            max_page = re.search('page_count:"(\d+)"', response).group(1)
            max_page = int(max_page)
            print("最大页面数： ", max_page)
        except Exception as e:
            print("解析最大页面过程出错：", e)
            max_page = 0

        if max_page >= 12:
            max_page = 12

        """
        &page=5&s=121&click=0
        """
        goods_list = []
        for i in range(max_page):
            # 将拼接的页面加到商品列表
            goods_list.append(self.url + '&page={}&s={}&click=0'.format(2*i+1, i*60 + 1))

        return goods_list

    def parse_search_page(self, url):
        """解析商品页面，得到每个商品的详情页"""
        response = self.get_response(url)
        selector = etree.HTML(response)
        # 商品列表
        detail_urls = selector.xpath('//ul/li/div/div/a/@href')

        ret = []
        for temp in detail_urls:
            if re.findall('item', temp):
                ret.append(temp)

        return ret

    @staticmethod
    def rm_duplication(lst):
        """去重"""
        l = []
        for temp in lst:
            if temp not in l:
                l.append(temp)

        return l

    def parse_detail_page(self, url):

        # print("正在解析 {}".format(url))

        try:
            data = self.get_response('https:' + url)
        except Exception as e:
            print(e)
            data = None
        if not data:
            return None, None
        # http://img13.360buyimg.com/n1/jfs/t1/3911/39/8399/261530/5ba99d9dEb735e3e1/4de4b3af03bfa264.jpg
        # 默认的前边部分
        # img后边的可以是10-14
        # n0是大图，有水印
        # n1是小图，无水印，n2更小
        # 随机选择一个，可能会降低被反爬的几率
        random_num = ['10', '11', '12', '13']
        img_base_url_small = "http://img{}.360buyimg.com/n1/".format(choice(random_num))
        img_base_url_big = "http://img{}.360buyimg.com/n0/".format(choice(random_num))
        """
        mageList: ["jfs/t1/5857/3/8457/387947/5ba99dc2E8de55b5a/6c391dfcc9b65874.jpg","jfs/t1/3911/39/8399/261530/5ba99d9dEb735e3e1/4de4b3af03bfa264.jpg","jfs/t1/2484/36/8186/185631/5ba99dd0E40d6307f/8a440e8db28fa2a2.jpg","jfs/t1/1297/27/8424/183784/5ba99dd4Efa807fc5/bcd4bd62927cd815.jpg"],
        """
        # 获取小图片的url
        try:
            # 如果是 海囤全球 则不适用
            image_urls = re.findall('imageList: \[(.*?)\]', data)[0].split(',')
        except Exception as e:
            print('解析详情页面失败： ', url, e)
            return None, None

        # 拼接图片url
        image_urls_small = [img_base_url_small + i[1:-1] for i in image_urls]
        image_urls_big = [img_base_url_big + i[1:-1] for i in image_urls]

        return image_urls_small, image_urls_big

    def run(self):

        # 某一商品的搜索页面
        goods_list = self.get_all_search_page()

        # 详情商品列表
        detail_urls = []
        for url in goods_list:
            detail_urls.extend(self.parse_search_page(url))

        detail_urls = self.rm_duplication(detail_urls)

        print(detail_urls)

        print("已获取商品详情列表: %d 个" % len(detail_urls))

        # 解析详情列表
        # 小图片
        small_urls = []
        # 大图片
        big_urls = []
        for detail_url in detail_urls:
            small_url, big_url = self.parse_detail_page(detail_url)
            if small_url is not None:
                small_urls.extend(small_url)
                big_urls.extend(big_url)

        print("已解析完成图片地址 共 %d 个" % len(small_urls))

        return small_urls, big_urls


class ToFile(object):
    """
    使用方法：
    实例化：传入文件的路径
    1. 将字典序列化成文件，.from_dict(字典类型)
    2. 将文件反序列化成字典， .from_file()
    """
    def __init__(self, file_name):
        """给定一个要创建的文件名"""
        self.file_name = file_name

    def from_dict(self, data):
        """字典序列化"""
        assert isinstance(data, dict)
        with open(self.file_name, 'wb') as f:
            pickle.dump(data, f)

    def from_file(self):
        """字典反序列化"""
        with open(self.file_name, 'rb') as f:
            data = pickle.load(f)
        return data


def get_dict_from_local(path):
    """从本地文件反序列化字典"""
    tf = ToFile(path)
    obj_dict = tf.from_file()

    return obj_dict


def get_keywork():
    all_keyword = {
        "蔬菜": [
            '菠菜', '白菜', '芹菜', '油菜', '芦笋', '菜花',
            '土豆', '竹笋', '山药', '豆角', '茄子', '西红柿',
            '青椒', '南瓜', '胡萝卜', '西葫芦', '黄瓜', '蘑菇',
            '平菇', '金针菇', '银耳', '木耳', '洋葱', '西蓝花',
            '藕', '苦瓜',
        ],
        "肉类": [
            '猪肉', '牛肉', '羊肉', '鸡胸肉', '鸭肉', '火腿',
            '腊肉', '排骨', '猪蹄', '肥牛', '鸡翅', '香肠',
            '鸡腿', '鸡爪', '牛排', '百叶'
        ],
        "水产": [
            '虾', '虾仁', '龙虾', '北极虾', '基围虾', '皮皮虾',
            '大闸蟹', '梭子蟹', '鲍鱼', '蛤蜊', '海带', '海参',
        ],
        "水果": [
            '苹果', '葡萄','柚子','西瓜','橙子','梨',
            '香蕉',
            '菠萝', '草莓',
            '木瓜',  '桃',
        ],
        "鱼类": [
            '鲫鱼', '带鱼', '鲈鱼', '鳕鱼', '鲤鱼', '草鱼',
            '鱿鱼',
        ],
        "豆类": [
            '豆腐', '腐竹', '黄豆芽', '黄豆', '红豆', '绿豆',
            '豆皮'
        ],
        "蛋类": [
            '鸡蛋', '鸭蛋', '鹌鹑蛋', '皮蛋'
        ],
        "干果": [
            '花生', '核桃仁', '腰果', '杏仁'
        ],
        "药食": [
            '燕窝', '红枣', '枸杞子'
        ],

    }
    download_list = [
        "蔬菜", "肉类", "水产", "水果", "鱼类",
        "豆类", "蛋类", "干果", "药食"
    ]

    for kind in download_list:
        for name in all_keyword[kind]:
            yield kind, name



def dl_search_name():
    small_images_path = '/media/gaoshuai/数据集/images/蔬菜识别/'

    t = get_dict_from_local('./jdfresh_all')

    change_name = {
        '油菜': '上海青/油菜',
        '土豆': '土豆/洋芋',
        '豆角': '四季豆',
        '银耳': '木耳/银耳',
        '西蓝花': '西兰花',
        '藕': '莲藕',
        '排骨': '肋排',
        '百叶': '肚',
        '龙虾': '小龙虾',
        '北极虾': '北极甜虾',
        '皮蛋': '松花蛋/皮蛋',
        '菠萝': '菠萝/凤梨',

    }

    for kind, name in get_keywork():
        first_path = small_images_path + kind
        if not os.path.exists(first_path):
            os.mkdir(first_path)
        second_path = os.path.join(first_path, name)
        if not os.path.exists(second_path):
            os.mkdir(second_path)

        if change_name.get(name):
            continue
        elif t.get(name):
            continue

        jd = JDSearch(name)
        print("开始解析 {} 页面".format(name))

        small_urls, big_urls = jd.run()

        s_path = second_path + os.sep

        print("开始保存图片")

        for num, small_url in enumerate(small_urls):
            # 保存的文件名
            file_name = str(num) + '.jpg'
            save_image.delay(small_url, s_path, file_name, jd.headers)


def wrong_name():
    wrong = [
        '燕窝',
        '杏仁',
        '腰果',
        '核桃仁',
        '花生',
        '豆皮',
        '绿豆',
        '红豆',
        '黄豆',
        '黄豆芽',
        '腐竹',
        '豆腐',
        '草鱼',
        '鲤鱼',
        '鲫鱼',
        '蛤蜊',
        '香肠',
        '鸭肉',
        '木耳',
        '金针菇',
        '蘑菇',
        '竹笋',
    ]

    second_path = '/media/gaoshuai/数据集/images/蔬菜识别/wrong'

    for name in wrong:
        jd = JDSearch(name)
        print("开始解析 {} 页面".format(name))

        small_urls, big_urls = jd.run()

        os.mkdir(os.path.join(second_path, name))

        s_path = os.path.join(second_path, name) + os.sep

        print("开始保存图片")

        for num, small_url in enumerate(small_urls):
            # 保存的文件名
            file_name = str(num) + '.jpg'
            save_image.delay(small_url, s_path, file_name, jd.headers)

        # break

if __name__ == '__main__':
    # jd = JDSearch("菠菜")
    # jd.run()

    # 搜索方法下载
    # dl_search_name()

    # 错误的
    wrong_name()

