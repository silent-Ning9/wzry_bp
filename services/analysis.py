"""
阵容分析服务
分析阵容的优劣势
"""
from typing import List, Dict

class AnalysisService:
    """阵容分析服务"""

    # 英雄属性评分（基础数据）
    HERO_ATTRIBUTES = {
        # 输出能力评分 (1-10)
        "damage": {
            "射手": 9, "刺客": 8, "法师": 7, "战士": 6, "坦克": 4, "辅助": 3
        },
        # 坦度评分 (1-10)
        "tankiness": {
            "坦克": 9, "战士": 7, "辅助": 6, "刺客": 4, "法师": 3, "射手": 2
        },
        # 控制能力评分 (1-10)
        "control": {
            "辅助": 8, "坦克": 7, "法师": 6, "战士": 5, "刺客": 3, "射手": 2
        },
        # 机动性评分 (1-10)
        "mobility": {
            "刺客": 9, "战士": 7, "射手": 5, "法师": 4, "坦克": 3, "辅助": 4
        },
        # 前期能力评分 (1-10)
        "early_game": {
            "刺客": 8, "战士": 7, "辅助": 6, "坦克": 6, "法师": 4, "射手": 3
        },
        # 后期能力评分 (1-10)
        "late_game": {
            "射手": 10, "法师": 8, "战士": 7, "坦克": 6, "刺客": 5, "辅助": 5
        }
    }

    def __init__(self, heroes: List[Dict]):
        self.heroes = {h['id']: h for h in heroes}

    def get_hero_tags(self, hero_id: int) -> List[str]:
        """获取英雄标签"""
        hero = self.heroes.get(hero_id)
        return hero.get('tags', []) if hero else []

    def calculate_team_attribute(self, hero_ids: List[int], attribute: str) -> float:
        """计算队伍某项属性的总分"""
        if attribute not in self.HERO_ATTRIBUTES:
            return 0

        attr_values = self.HERO_ATTRIBUTES[attribute]
        total = 0

        for hero_id in hero_ids:
            tags = self.get_hero_tags(hero_id)
            hero_score = max([attr_values.get(tag, 5) for tag in tags], default=5)
            total += hero_score

        # 归一化到0-100
        return round(total / 5 * 10, 1)

    def analyze_team_composition(self, hero_ids: List[int]) -> Dict:
        """分析队伍构成"""
        composition = {
            "战士": 0, "法师": 0, "坦克": 0,
            "刺客": 0, "射手": 0, "辅助": 0
        }

        for hero_id in hero_ids:
            tags = self.get_hero_tags(hero_id)
            for tag in tags:
                if tag in composition:
                    composition[tag] += 1

        return composition

    def check_team_balance(self, hero_ids: List[int]) -> Dict:
        """检查阵容平衡性"""
        composition = self.analyze_team_composition(hero_ids)
        issues = []

        # 检查是否有坦克
        if composition["坦克"] == 0 and composition["战士"] == 0:
            issues.append("阵容缺少前排，建议补充坦克或战士")

        # 检查是否有输出
        if composition["射手"] == 0 and composition["法师"] == 0:
            issues.append("阵容缺少核心输出，建议补充射手或法师")

        # 检查是否有辅助
        if composition["辅助"] == 0:
            issues.append("阵容缺少辅助，团队保护能力可能不足")

        # 检查是否输出过多
        if composition["射手"] + composition["法师"] > 3:
            issues.append("阵容输出过多，可能缺乏前排或控制")

        # 检查是否刺客过多
        if composition["刺客"] > 2:
            issues.append("刺客过多，阵容容错率较低")

        return {
            "composition": composition,
            "issues": issues,
            "is_balanced": len(issues) == 0
        }

    def analyze_matchup(self, blue_picks: List[int], red_picks: List[int]) -> Dict:
        """分析双方对阵情况"""
        # 计算双方各项属性
        blue_attrs = {
            "damage": self.calculate_team_attribute(blue_picks, "damage"),
            "tankiness": self.calculate_team_attribute(blue_picks, "tankiness"),
            "control": self.calculate_team_attribute(blue_picks, "control"),
            "mobility": self.calculate_team_attribute(blue_picks, "mobility"),
            "early_game": self.calculate_team_attribute(blue_picks, "early_game"),
            "late_game": self.calculate_team_attribute(blue_picks, "late_game")
        }

        red_attrs = {
            "damage": self.calculate_team_attribute(red_picks, "damage"),
            "tankiness": self.calculate_team_attribute(red_picks, "tankiness"),
            "control": self.calculate_team_attribute(red_picks, "control"),
            "mobility": self.calculate_team_attribute(red_picks, "mobility"),
            "early_game": self.calculate_team_attribute(red_picks, "early_game"),
            "late_game": self.calculate_team_attribute(red_picks, "late_game")
        }

        # 分析双方优劣势
        comparison = {}
        for attr in blue_attrs:
            diff = blue_attrs[attr] - red_attrs[attr]
            if diff > 10:
                comparison[attr] = {"winner": "blue", "advantage": "明显优势"}
            elif diff > 5:
                comparison[attr] = {"winner": "blue", "advantage": "小幅优势"}
            elif diff < -10:
                comparison[attr] = {"winner": "red", "advantage": "明显优势"}
            elif diff < -5:
                comparison[attr] = {"winner": "red", "advantage": "小幅优势"}
            else:
                comparison[attr] = {"winner": "even", "advantage": "势均力敌"}

        # 阵容平衡性检查
        blue_balance = self.check_team_balance(blue_picks)
        red_balance = self.check_team_balance(red_picks)

        return {
            "blue": {
                "attributes": blue_attrs,
                "balance": blue_balance
            },
            "red": {
                "attributes": red_attrs,
                "balance": red_balance
            },
            "comparison": comparison
        }

    def get_team_summary(self, hero_ids: List[int]) -> Dict:
        """获取队伍摘要"""
        if not hero_ids:
            return {"summary": "暂无选择", "strengths": [], "weaknesses": []}

        attrs = {
            "damage": self.calculate_team_attribute(hero_ids, "damage"),
            "tankiness": self.calculate_team_attribute(hero_ids, "tankiness"),
            "control": self.calculate_team_attribute(hero_ids, "control"),
            "mobility": self.calculate_team_attribute(hero_ids, "mobility"),
            "early_game": self.calculate_team_attribute(hero_ids, "early_game"),
            "late_game": self.calculate_team_attribute(hero_ids, "late_game")
        }

        # 找出优势和劣势
        strengths = []
        weaknesses = []

        for attr, value in attrs.items():
            attr_names = {
                "damage": "输出能力",
                "tankiness": "坦度",
                "control": "控制能力",
                "mobility": "机动性",
                "early_game": "前期能力",
                "late_game": "后期能力"
            }

            if value >= 75:
                strengths.append(f"{attr_names[attr]}强")
            elif value <= 50:
                weaknesses.append(f"{attr_names[attr]}弱")

        balance = self.check_team_balance(hero_ids)
        weaknesses.extend(balance["issues"])

        # 生成摘要
        hero_names = [self.heroes.get(h_id, {}).get('name', '未知') for h_id in hero_ids]
        summary = f"阵容: {', '.join(hero_names)}"

        return {
            "summary": summary,
            "attributes": attrs,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "composition": balance["composition"]
        }
