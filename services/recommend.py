"""
英雄推荐服务
基于克制关系和阵容分析推荐英雄
"""
from typing import List, Dict, Optional
import json
import os

class RecommendService:
    """推荐服务"""

    def __init__(self, heroes: List[Dict], counters: List[Dict]):
        self.heroes = {h['id']: h for h in heroes}
        self.counters = {c['hero_id']: c for c in counters}

        # 构建英雄ID到名称的映射
        self.id_to_name = {h['id']: h['name'] for h in heroes}

    def get_available_heroes(self, banned: List[int], picked: List[int]) -> List[int]:
        """获取可选英雄列表"""
        unavailable = set(banned + picked)
        return [h_id for h_id in self.heroes.keys() if h_id not in unavailable]

    def calculate_counter_score(self, hero_id: int, enemy_picks: List[int]) -> float:
        """计算英雄对敌方的克制得分"""
        if hero_id not in self.counters:
            return 0

        counter_data = self.counters[hero_id]
        score = 0

        # 计算克制敌方英雄的得分
        for enemy_id in enemy_picks:
            if enemy_id in counter_data.get('counters', []):
                score += 10  # 克制敌方英雄

        # 计算被敌方克制的扣分
        for enemy_id in enemy_picks:
            if enemy_id in counter_data.get('countered_by', []):
                score -= 8  # 被敌方克制

        return score

    def calculate_team_synergy(self, hero_id: int, ally_picks: List[int]) -> float:
        """计算与队友的配合得分"""
        if not ally_picks or hero_id not in self.heroes:
            return 0

        hero = self.heroes[hero_id]
        ally_tags = []
        for ally_id in ally_picks:
            if ally_id in self.heroes:
                ally_tags.extend(self.heroes[ally_id].get('tags', []))

        score = 0

        # 检查阵容平衡性
        hero_tags = hero.get('tags', [])

        # 阵容需要坦克
        if '坦克' not in ally_tags and '坦克' in hero_tags:
            score += 5

        # 阵容需要控制
        if '辅助' in hero_tags:
            score += 3

        # 避免分路重叠
        hero_lanes = hero.get('lanes', [])
        ally_lanes = []
        for ally_id in ally_picks:
            if ally_id in self.heroes:
                ally_lanes.extend(self.heroes[ally_id].get('lanes', []))

        # 如果分路重叠较多，扣分
        overlap = len(set(hero_lanes) & set(ally_lanes))
        if overlap > 0:
            score -= overlap * 2

        return score

    def recommend(self,
                  banned: List[int],
                  blue_picks: List[int],
                  red_picks: List[int],
                  current_side: str,
                  top_n: int = 5) -> List[Dict]:
        """
        推荐英雄

        Args:
            banned: 已禁用的英雄ID列表
            blue_picks: 蓝方已选英雄
            red_picks: 红方已选英雄
            current_side: 当前阵营 'blue' 或 'red'
            top_n: 返回前N个推荐

        Returns:
            推荐英雄列表，包含得分和原因
        """
        available = self.get_available_heroes(banned, blue_picks + red_picks)

        # 当前阵营的队友和敌方
        if current_side == 'blue':
            ally_picks = blue_picks
            enemy_picks = red_picks
        else:
            ally_picks = red_picks
            enemy_picks = blue_picks

        recommendations = []

        for hero_id in available:
            hero = self.heroes.get(hero_id)
            if not hero:
                continue

            # 计算各项得分
            counter_score = self.calculate_counter_score(hero_id, enemy_picks)
            synergy_score = self.calculate_team_synergy(hero_id, ally_picks)

            # 综合得分
            total_score = counter_score + synergy_score

            # 生成推荐原因
            reasons = []
            if counter_score > 0:
                reasons.append(f"克制敌方英雄")
            elif counter_score < 0:
                reasons.append("注意：可能被敌方克制")
            if synergy_score > 0:
                reasons.append("补全阵容")
            if not reasons:
                reasons.append("常规选择")

            recommendations.append({
                "hero_id": hero_id,
                "name": hero.get('name', ''),
                "lanes": hero.get('lanes', []),
                "score": round(total_score, 1),
                "counter_score": round(counter_score, 1),
                "synergy_score": round(synergy_score, 1),
                "reasons": reasons
            })

        # 按得分排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return recommendations[:top_n]
