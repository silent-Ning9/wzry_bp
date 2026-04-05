"""
王者荣耀英雄数据爬虫
从王者荣耀官网Wiki抓取英雄数据
"""
import requests
import json
import os

# 数据保存路径
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
HEROES_FILE = os.path.join(DATA_DIR, 'heroes.json')
IMG_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'img')

# 王者荣耀官网英雄列表页
HERO_LIST_URL = "https://pvp.qq.com/web201605/js/herolist.json"

# 英雄类型映射（官网类型）
HERO_TYPE_MAP = {
    1: "战士",
    2: "法师",
    3: "坦克",
    4: "刺客",
    5: "射手",
    6: "辅助"
}

# 特殊英雄分路映射（手动定义多位置英雄）
SPECIAL_LANES = {
    # 打野为主的英雄
    "李白": ["打野"],
    "韩信": ["打野"],
    "阿轲": ["打野"],
    "兰陵王": ["打野"],
    "娜可露露": ["打野"],
    "橘右京": ["打野"],
    "百里玄策": ["打野"],
    "裴擒虎": ["打野"],
    "云中君": ["打野"],
    "镜": ["打野"],
    "澜": ["打野"],
    "暃": ["打野"],
    "孙悟空": ["打野"],
    "典韦": ["打野"],
    "刘备": ["打野"],
    "露娜": ["打野", "中路"],
    "司马懿": ["打野", "中路"],
    "雅典娜": ["打野"],
    "赵云": ["打野", "对抗路"],
    "宫本武藏": ["打野"],
    "曜": ["打野", "对抗路"],
    "云缨": ["打野"],
    "大司命": ["打野"],
    "阿古朵": ["打野"],

    # 上单为主的英雄
    "吕布": ["对抗路"],
    "关羽": ["对抗路"],
    "花木兰": ["对抗路"],
    "老夫子": ["对抗路"],
    "杨戬": ["对抗路"],
    "曹操": ["对抗路"],
    "达摩": ["上单", "打野"],
    "程咬金": ["对抗路"],
    "夏侯惇": ["上单", "游走"],
    "项羽": ["上单", "游走"],
    "廉颇": ["上单", "游走"],
    "白起": ["上单", "游走"],
    "猪八戒": ["对抗路"],
    "蒙恬": ["对抗路"],
    "李信": ["对抗路", "发育路"],
    "狂铁": ["对抗路"],
    "孙策": ["上单", "游走"],
    "马超": ["上单", "打野"],
    "夏洛特": ["对抗路"],
    "司空震": ["对抗路", "发育路"],
    "亚连": ["对抗路"],
    "姬小满": ["对抗路"],
    "赵怀真": ["游走"],
    "亚瑟": ["上单", "打野"],
    "钟无艳": ["上单", "游走"],
    "哪吒": ["对抗路"],
    "盘古": ["上单", "打野"],
    "影": ["对抗路"],
    "蚩奼": ["对抗路", "发育路", "打野"],

    # 中路为主的英雄
    "小乔": ["中路"],
    "妲己": ["中路"],
    "安琪拉": ["中路"],
    "王昭君": ["中路"],
    "甄姬": ["中路"],
    "武则天": ["中路"],
    "貂蝉": ["中路"],
    "嬴政": ["中路"],
    "干将莫邪": ["中路"],
    "不知火舞": ["中路"],
    "诸葛亮": ["中路", "打野"],
    "上官婉儿": ["中路"],
    "嫦娥": ["中路", "对抗路"],
    "米莱狄": ["中路"],
    "西施": ["中路"],
    "杨玉环": ["中路", "游走"],
    "弈星": ["中路"],
    "沈梦溪": ["中路"],
    "女娲": ["中路"],
    "姜子牙": ["中路", "游走"],
    "周瑜": ["中路"],
    "高渐离": ["中路"],
    "扁鹊": ["中路"],
    "芈月": ["对抗路"],
    "张良": ["中路", "游走"],
    "金蝉": ["中路"],
    "海月": ["中路"],
    "海诺": ["中路", "对抗路"],
    "元流之子(法师)": ["中路"],
    "元流之子(坦克)": ["对抗路"],
    "元流之子(射手)": ["发育路"],
    "元流之子(辅助)": ["游走"],
    "元流之子(刺客)": ["打野"],
    "空空儿": ["游走"],

    # 射手
    "后羿": ["发育路"],
    "鲁班七号": ["发育路"],
    "孙尚香": ["发育路"],
    "马可波罗": ["发育路"],
    "狄仁杰": ["发育路"],
    "虞姬": ["发育路"],
    "黄忠": ["发育路"],
    "李元芳": ["射手", "打野"],
    "百里守约": ["发育路"],
    "公孙离": ["发育路"],
    "伽罗": ["发育路"],
    "蒙犽": ["发育路"],
    "艾琳": ["发育路"],
    "戈娅": ["发育路"],
    "莱西奥": ["发育路"],
    "敖隐": ["发育路"],
    "苍": ["发育路"],
    "孙权": ["发育路"],

    # 辅助
    "蔡文姬": ["游走"],
    "瑶": ["游走"],
    "大乔": ["游走"],
    "明世隐": ["游走"],
    "庄周": ["辅助", "对抗路"],
    "刘禅": ["游走"],
    "孙膑": ["游走"],
    "牛魔": ["游走"],
    "张飞": ["游走"],
    "钟馗": ["游走"],
    "太乙真人": ["游走"],
    "东皇太一": ["游走"],
    "鬼谷子": ["游走"],
    "盾山": ["游走"],
    "苏烈": ["辅助", "对抗路"],
    "鲁班大师": ["游走"],
    "桑启": ["游走"],
    "朵莉亚": ["游走"],
    "少司缘": ["游走"],
    "大禹": ["游走"],

    # 特殊
    "墨子": ["辅助", "中路"],
    "刘邦": ["上单", "游走"],
    "梦奇": ["上单", "打野"],
    "铠": ["打野", "对抗路"],
    "芈月": ["对抗路"],
}


def fetch_hero_list():
    """从官网获取英雄列表JSON数据"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://pvp.qq.com/web201605/herolist.shtml'
        }
        response = requests.get(HERO_LIST_URL, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        return response.json()
    except Exception as e:
        print(f"获取英雄列表失败: {e}")
        return None


def download_avatar(hero_id, hero_name):
    """下载英雄头像"""
    avatar_url = f"https://game.gtimg.cn/images/yxzj/img201606/heroimg/{hero_id}/{hero_id}.jpg"
    avatar_path = os.path.join(IMG_DIR, f"{hero_id}.jpg")

    if os.path.exists(avatar_path):
        return f"{hero_id}.jpg"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://pvp.qq.com/'
        }
        response = requests.get(avatar_url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(avatar_path, 'wb') as f:
                f.write(response.content)
            return f"{hero_id}.jpg"
    except Exception as e:
        print(f"下载头像失败 {hero_name}: {e}")

    return None


def infer_lanes(hero_name, hero_type, hero_type2):
    """推断英雄分路"""
    # 优先使用手动定义
    if hero_name in SPECIAL_LANES:
        return SPECIAL_LANES[hero_name]

    lanes = []

    # 根据类型推断
    type1 = HERO_TYPE_MAP.get(hero_type, "")
    type2 = HERO_TYPE_MAP.get(hero_type2, "") if hero_type2 else ""

    all_types = [type1, type2] if type2 else [type1]

    for t in all_types:
        if t == "射手":
            if "射手" not in lanes:
                lanes.append("射手")
        elif t == "辅助":
            if "辅助" not in lanes:
                lanes.append("辅助")
        elif t == "法师":
            if "中路" not in lanes:
                lanes.append("中路")
        elif t == "刺客":
            if "打野" not in lanes:
                lanes.append("打野")
        elif t == "坦克":
            if "上单" not in lanes:
                lanes.append("上单")
        elif t == "战士":
            if "上单" not in lanes:
                lanes.append("上单")

    return lanes if lanes else ["对抗路"]


def parse_hero_data(raw_data):
    """解析英雄数据"""
    heroes = []
    hero_id_counter = 1

    for hero in raw_data:
        ename = hero.get('ename', '')
        cname = hero.get('cname', '')
        hero_type = hero.get('hero_type', 0)
        hero_type2 = hero.get('hero_type2', 0)

        # 推断分路
        lanes = infer_lanes(cname, hero_type, hero_type2)

        # 获取原始类型作为标签
        tags = []
        if hero_type in HERO_TYPE_MAP:
            tags.append(HERO_TYPE_MAP[hero_type])
        if hero_type2 and hero_type2 in HERO_TYPE_MAP and HERO_TYPE_MAP[hero_type2] not in tags:
            tags.append(HERO_TYPE_MAP[hero_type2])

        # 下载头像
        avatar = download_avatar(ename, cname)

        hero_data = {
            "id": hero_id_counter,
            "ename": ename,
            "name": cname,
            "lanes": lanes,  # 分路
            "tags": tags if tags else ["战士"],  # 原始类型标签
            "difficulty": 2,
            "avatar": avatar or f"{ename}.jpg"
        }

        heroes.append(hero_data)
        hero_id_counter += 1
        print(f"处理英雄: {cname} - {lanes}")

    return heroes


def save_heroes(heroes):
    """保存英雄数据到JSON文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HEROES_FILE, 'w', encoding='utf-8') as f:
        json.dump(heroes, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(heroes)} 个英雄数据到 {HEROES_FILE}")


def crawl():
    """主爬虫函数"""
    print("开始爬取王者荣耀英雄数据...")

    # 确保目录存在
    os.makedirs(IMG_DIR, exist_ok=True)

    # 获取数据
    raw_data = fetch_hero_list()
    if not raw_data:
        print("获取数据失败")
        return False

    # 解析数据
    heroes = parse_hero_data(raw_data)

    # 保存数据
    save_heroes(heroes)

    print("爬取完成!")
    return True


if __name__ == '__main__':
    crawl()
