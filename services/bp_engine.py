"""
BP流程引擎
实现KPL全局BP赛制
"""
from enum import Enum
from typing import List, Dict, Optional, Set
import copy

class Side(Enum):
    BLUE = "blue"
    RED = "red"

class ActionType(Enum):
    BAN = "ban"
    PICK = "pick"

class BPState:
    """BP状态管理 - KPL全局BP赛制"""

    # KPL全局BP流程（每队选5英雄，禁5英雄）
    BP_SEQUENCE = [
        # 第一轮Ban（交替，各2个）
        (Side.BLUE, ActionType.BAN, 1),  # 1. 蓝 ban 1
        (Side.RED, ActionType.BAN, 1),   # 2. 红 ban 1
        (Side.BLUE, ActionType.BAN, 1),  # 3. 蓝 ban 2
        (Side.RED, ActionType.BAN, 1),   # 4. 红 ban 2
        # 第一轮Pick: 蓝1→红1/2→蓝2/3→红3
        (Side.BLUE, ActionType.PICK, 1), # 5. 蓝 pick 1
        (Side.RED, ActionType.PICK, 1),  # 6. 红 pick 1
        (Side.RED, ActionType.PICK, 1),  # 7. 红 pick 2
        (Side.BLUE, ActionType.PICK, 1), # 8. 蓝 pick 2
        (Side.BLUE, ActionType.PICK, 1), # 9. 蓝 pick 3
        (Side.RED, ActionType.PICK, 1),  # 10. 红 pick 3
        # 第二轮Ban（交替，各3个）
        (Side.RED, ActionType.BAN, 1),   # 11. 红 ban 3
        (Side.BLUE, ActionType.BAN, 1),  # 12. 蓝 ban 3
        (Side.RED, ActionType.BAN, 1),   # 13. 红 ban 4
        (Side.BLUE, ActionType.BAN, 1),  # 14. 蓝 ban 4
        (Side.RED, ActionType.BAN, 1),   # 15. 红 ban 5
        (Side.BLUE, ActionType.BAN, 1),  # 16. 蓝 ban 5
        # 第二轮Pick: 红4→蓝4/5→红5
        (Side.RED, ActionType.PICK, 1),  # 17. 红 pick 4
        (Side.BLUE, ActionType.PICK, 1), # 18. 蓝 pick 4
        (Side.BLUE, ActionType.PICK, 1), # 19. 蓝 pick 5
        (Side.RED, ActionType.PICK, 1),  # 20. 红 pick 5
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        """重置当前局BP状态（保留全局禁用）"""
        self.step = 0
        self.blue_bans: List[int] = []  # 本局蓝方禁用
        self.red_bans: List[int] = []   # 本局红方禁用
        self.blue_picks: List[int] = [] # 本局蓝方选择
        self.red_picks: List[int] = []  # 本局红方选择
        self.is_finished = False
        self.history: List[Dict] = []

    def get_current_action(self) -> Optional[Dict]:
        """获取当前需要执行的操作"""
        if self.is_finished:
            return None

        if self.step < len(self.BP_SEQUENCE):
            side, action_type, _ = self.BP_SEQUENCE[self.step]
            return {
                "side": side.value,
                "action": action_type.value,
                "step": self.step
            }

        return None

    def execute_action(self, hero_id: int, side: str, action: str) -> Dict:
        """执行Ban/Pick操作"""
        current = self.get_current_action()
        if not current:
            return {"success": False, "error": "BP已结束"}

        if current["side"] != side:
            return {"success": False, "error": f"当前是{current['side']}方操作"}

        if current["action"] != action:
            return {"success": False, "error": f"当前操作类型应为{current['action']}"}

        # 检查英雄是否已被Ban/Pick
        all_bans = self.blue_bans + self.red_bans
        all_picks = self.blue_picks + self.red_picks

        if hero_id in all_bans:
            return {"success": False, "error": "该英雄已被禁用"}
        if hero_id in all_picks:
            return {"success": False, "error": "该英雄已被选择"}

        # 执行操作
        if action == "ban":
            if side == "blue":
                self.blue_bans.append(hero_id)
            else:
                self.red_bans.append(hero_id)
        else:
            if side == "blue":
                self.blue_picks.append(hero_id)
            else:
                self.red_picks.append(hero_id)

        self.history.append({
            "step": self.step,
            "side": side,
            "action": action,
            "hero_id": hero_id
        })

        self.step += 1

        if self.step >= len(self.BP_SEQUENCE):
            self.is_finished = True

        return {
            "success": True,
            "current_action": self.get_current_action(),
            "is_finished": self.is_finished
        }

    def get_state(self) -> Dict:
        """获取当前BP状态"""
        return {
            "step": self.step,
            "blue_bans": self.blue_bans,
            "red_bans": self.red_bans,
            "blue_picks": self.blue_picks,
            "red_picks": self.red_picks,
            "current_action": self.get_current_action(),
            "is_finished": self.is_finished,
            "history": self.history
        }

    def undo_last_action(self) -> bool:
        """撤销上一步操作"""
        if not self.history:
            return False

        last = self.history.pop()

        if last["action"] == "ban":
            if last["side"] == "blue":
                self.blue_bans.remove(last["hero_id"])
            else:
                self.red_bans.remove(last["hero_id"])
        else:
            if last["side"] == "blue":
                self.blue_picks.remove(last["hero_id"])
            else:
                self.red_picks.remove(last["hero_id"])

        self.step -= 1
        self.is_finished = False
        return True


class GlobalBPManager:
    """全局BP管理器 - 管理多场比赛"""

    def __init__(self):
        self.game_number = 1
        self.current_bp: BPState = BPState()

        # 队伍信息
        self.team_a_name = "蓝队"  # 队伍A名称
        self.team_b_name = "红队"  # 队伍B名称
        self.team_a_is_blue = True  # 队伍A当前是否为蓝方

        # 比分
        self.team_a_wins = 0
        self.team_b_wins = 0
        self.first_to = 4  # BO7，先到4胜

        # 各队已用英雄（本队不可再用，对方可以选）
        self.team_a_used: Set[int] = set()
        self.team_b_used: Set[int] = set()

        # 每场比赛记录
        self.games_history: List[Dict] = []

        # 等待选边
        self.waiting_side_selection = False
        self.last_loser = None  # 上一局败者 ('A' 或 'B')

    @property
    def blue_team_name(self) -> str:
        """当前蓝方队伍名称"""
        return self.team_a_name if self.team_a_is_blue else self.team_b_name

    @property
    def red_team_name(self) -> str:
        """当前红方队伍名称"""
        return self.team_b_name if self.team_a_is_blue else self.team_a_name

    @property
    def blue_used(self) -> Set[int]:
        """当前蓝方已用英雄"""
        return self.team_a_used if self.team_a_is_blue else self.team_b_used

    @property
    def red_used(self) -> Set[int]:
        """当前红方已用英雄"""
        return self.team_b_used if self.team_a_is_blue else self.team_a_used

    def set_team_names(self, team_a: str, team_b: str):
        """设置队伍名称"""
        self.team_a_name = team_a or "蓝队"
        self.team_b_name = team_b or "红队"

    def set_winner(self, winner: str):
        """设置本局胜者 ('blue' 或 'red')"""
        if winner == 'blue':
            winner_team = 'A' if self.team_a_is_blue else 'B'
        else:
            winner_team = 'B' if self.team_a_is_blue else 'A'

        if winner_team == 'A':
            self.team_a_wins += 1
            self.last_loser = 'B'
        else:
            self.team_b_wins += 1
            self.last_loser = 'A'

        # 记录本局使用的英雄到对应队伍
        if self.team_a_is_blue:
            self.team_a_used.update(self.current_bp.blue_picks)
            self.team_b_used.update(self.current_bp.red_picks)
        else:
            self.team_b_used.update(self.current_bp.blue_picks)
            self.team_a_used.update(self.current_bp.red_picks)

        # 记录历史
        self.games_history.append({
            "game": self.game_number,
            "blue_team": self.blue_team_name,
            "red_team": self.red_team_name,
            "blue_picks": self.current_bp.blue_picks.copy(),
            "red_picks": self.current_bp.red_picks.copy(),
            "blue_bans": self.current_bp.blue_bans.copy(),
            "red_bans": self.current_bp.red_bans.copy(),
            "winner": winner
        })
        self.game_number += 1

        # 设置等待选边（除非系列赛已结束）
        if not self.is_series_finished():
            self.waiting_side_selection = True

    def select_side(self, side: str):
        """败者选择下一局阵营"""
        if self.last_loser == 'A':
            # 队伍A选择，A想当蓝方就选blue
            self.team_a_is_blue = (side == 'blue')
        else:
            # 队伍B选择，B想当蓝方就选blue
            self.team_a_is_blue = (side != 'blue')

        self.waiting_side_selection = False

    def start_new_game(self):
        """开始新一局"""
        self.current_bp.reset()

    def is_series_finished(self) -> bool:
        """系列赛是否结束"""
        return self.team_a_wins >= self.first_to or self.team_b_wins >= self.first_to

    def get_state(self) -> Dict:
        """获取完整状态"""
        return {
            "game_number": self.game_number,
            "team_a_name": self.team_a_name,
            "team_b_name": self.team_b_name,
            "team_a_is_blue": self.team_a_is_blue,
            "blue_team_name": self.blue_team_name,
            "red_team_name": self.red_team_name,
            "team_a_wins": self.team_a_wins,
            "team_b_wins": self.team_b_wins,
            "first_to": self.first_to,
            "blue_used": list(self.blue_used),
            "red_used": list(self.red_used),
            "team_a_used": list(self.team_a_used),
            "team_b_used": list(self.team_b_used),
            "games_history": self.games_history,
            "current_bp": self.current_bp.get_state(),
            "waiting_side_selection": self.waiting_side_selection,
            "last_loser": self.last_loser,
            "series_finished": self.is_series_finished()
        }


# 会话存储
bp_sessions: Dict[str, GlobalBPManager] = {}

def create_bp_session(session_id: str) -> GlobalBPManager:
    """创建新的全局BP会话"""
    bp_sessions[session_id] = GlobalBPManager()
    return bp_sessions[session_id]

def get_bp_session(session_id: str) -> Optional[GlobalBPManager]:
    """获取BP会话"""
    return bp_sessions.get(session_id)

def delete_bp_session(session_id: str):
    """删除BP会话"""
    if session_id in bp_sessions:
        del bp_sessions[session_id]
