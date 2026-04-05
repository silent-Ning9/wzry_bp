from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import os
import uuid
from pypinyin import lazy_pinyin

from services.bp_engine import create_bp_session, get_bp_session, delete_bp_session
from services.recommend import RecommendService
from services.analysis import AnalysisService

app = Flask(__name__)
CORS(app)

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 全局数据缓存
_heroes_cache = None
_counters_cache = None


def load_heroes():
    """加载英雄数据"""
    global _heroes_cache
    if _heroes_cache is None:
        heroes_path = os.path.join(DATA_DIR, 'heroes.json')
        if os.path.exists(heroes_path):
            with open(heroes_path, 'r', encoding='utf-8') as f:
                _heroes_cache = json.load(f)
    return _heroes_cache or []


def load_counters():
    """加载克制关系数据"""
    global _counters_cache
    if _counters_cache is None:
        counters_path = os.path.join(DATA_DIR, 'counters.json')
        if os.path.exists(counters_path):
            with open(counters_path, 'r', encoding='utf-8') as f:
                _counters_cache = json.load(f)
    return _counters_cache or []


def get_recommend_service():
    """获取推荐服务实例"""
    return RecommendService(load_heroes(), load_counters())


def get_analysis_service():
    """获取分析服务实例"""
    return AnalysisService(load_heroes())


# ========== 页面路由 ==========

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


# ========== 英雄数据API ==========

@app.route('/api/heroes')
def get_heroes():
    """获取所有英雄"""
    heroes = load_heroes()
    # 按名称拼音排序
    heroes = sorted(heroes, key=lambda h: lazy_pinyin(h.get('name', '')))
    return jsonify(heroes)


@app.route('/api/heroes/<int:hero_id>')
def get_hero(hero_id):
    """获取单个英雄详情"""
    heroes = load_heroes()
    for hero in heroes:
        if hero['id'] == hero_id:
            return jsonify(hero)
    return jsonify({"error": "英雄不存在"}), 404


@app.route('/api/counters')
def get_counters():
    """获取克制关系"""
    counters = load_counters()
    return jsonify(counters)


# ========== 全局BP流程API ==========

@app.route('/api/bp/start', methods=['POST'])
def start_bp():
    """开始新的全局BP会话"""
    session_id = str(uuid.uuid4())[:8]
    manager = create_bp_session(session_id)

    return jsonify({
        "session_id": session_id,
        "state": manager.get_state()
    })


@app.route('/api/bp/<session_id>/action', methods=['POST'])
def execute_bp_action(session_id):
    """执行BP操作"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    data = request.get_json()
    hero_id = data.get('hero_id')
    side = data.get('side')
    action = data.get('action')

    if not all([hero_id is not None, side, action]):
        return jsonify({"error": "参数不完整"}), 400

    bp_state = manager.current_bp
    current_action = bp_state.get_current_action()

    if not current_action:
        return jsonify({"success": False, "error": "BP已结束"})

    if current_action["side"] != side:
        return jsonify({"success": False, "error": f"当前是{current_action['side']}方操作"})

    if current_action["action"] != action:
        return jsonify({"success": False, "error": f"当前操作类型应为{current_action['action']}"})

    # Ban阶段：对方已用英雄不能被ban
    if action == 'ban':
        if side == 'blue' and hero_id in manager.red_used:
            return jsonify({"success": False, "error": "红方已用过的英雄不能被禁用"})
        if side == 'red' and hero_id in manager.blue_used:
            return jsonify({"success": False, "error": "蓝方已用过的英雄不能被禁用"})

    # Pick阶段：本队已用英雄不能再选
    if action == 'pick':
        if side == 'blue' and hero_id in manager.blue_used:
            return jsonify({"success": False, "error": "蓝方在之前比赛中已选择该英雄"})
        if side == 'red' and hero_id in manager.red_used:
            return jsonify({"success": False, "error": "红方在之前比赛中已选择该英雄"})

    result = bp_state.execute_action(hero_id, side, action)

    if result['success']:
        result['state'] = manager.get_state()

    return jsonify(result)


@app.route('/api/bp/<session_id>/undo', methods=['POST'])
def undo_bp_action(session_id):
    """撤销上一步操作"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    success = manager.current_bp.undo_last_action()
    return jsonify({
        "success": success,
        "state": manager.get_state()
    })


@app.route('/api/bp/<session_id>/new-game', methods=['POST'])
def start_new_game(session_id):
    """开始新一局（全局BP）"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    if not manager.current_bp.is_finished:
        return jsonify({"success": False, "error": "当前比赛尚未结束"})

    manager.start_new_game()
    return jsonify({
        "success": True,
        "state": manager.get_state()
    })


@app.route('/api/bp/<session_id>/set-teams', methods=['POST'])
def set_team_names(session_id):
    """设置队伍名称"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    data = request.get_json()
    team_a = data.get('team_a', '蓝队')
    team_b = data.get('team_b', '红队')

    manager.set_team_names(team_a, team_b)
    return jsonify({
        "success": True,
        "state": manager.get_state()
    })


@app.route('/api/bp/<session_id>/set-winner', methods=['POST'])
def set_winner(session_id):
    """设置本局胜者"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    if not manager.current_bp.is_finished:
        return jsonify({"success": False, "error": "当前比赛尚未结束"})

    data = request.get_json()
    winner = data.get('winner')  # 'blue' 或 'red'

    if winner not in ['blue', 'red']:
        return jsonify({"success": False, "error": "无效的胜者"})

    manager.set_winner(winner)
    return jsonify({
        "success": True,
        "state": manager.get_state()
    })


@app.route('/api/bp/<session_id>/select-side', methods=['POST'])
def select_side(session_id):
    """败者选择下一局阵营"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    if not manager.waiting_side_selection:
        return jsonify({"success": False, "error": "当前不需要选边"})

    data = request.get_json()
    side = data.get('side')  # 'blue' 或 'red'

    if side not in ['blue', 'red']:
        return jsonify({"success": False, "error": "无效的阵营"})

    manager.select_side(side)
    manager.start_new_game()

    return jsonify({
        "success": True,
        "state": manager.get_state()
    })


@app.route('/api/bp/<session_id>/state')
def get_bp_state(session_id):
    """获取BP状态"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    return jsonify(manager.get_state())


@app.route('/api/bp/<session_id>', methods=['DELETE'])
def delete_bp(session_id):
    """删除BP会话"""
    delete_bp_session(session_id)
    return jsonify({"success": True})


# ========== 推荐API ==========

@app.route('/api/bp/<session_id>/recommend')
def get_recommendations(session_id):
    """获取英雄推荐"""
    manager = get_bp_session(session_id)
    if not manager:
        return jsonify({"error": "会话不存在"}), 404

    state = manager.current_bp.get_state()
    current_action = state.get('current_action')

    if not current_action or current_action['action'] != 'pick':
        return jsonify({"recommendations": [], "message": "当前不是Pick阶段"})

    # 获取当前阵营不可用的英雄
    if current_action['side'] == 'blue':
        global_used = list(manager.blue_used)
    else:
        global_used = list(manager.red_used)

    recommend_service = get_recommend_service()
    recommendations = recommend_service.recommend(
        banned=state['blue_bans'] + state['red_bans'],
        blue_picks=state['blue_picks'],
        red_picks=state['red_picks'],
        current_side=current_action['side'],
        top_n=10
    )

    return jsonify({
        "recommendations": recommendations,
        "current_side": current_action['side']
    })


# ========== 阵容分析API ==========

@app.route('/api/analyze', methods=['POST'])
def analyze_matchup():
    """分析双方阵容"""
    data = request.get_json()
    blue_picks = data.get('blue_picks', [])
    red_picks = data.get('red_picks', [])

    analysis_service = get_analysis_service()
    result = analysis_service.analyze_matchup(blue_picks, red_picks)

    return jsonify(result)


@app.route('/api/analyze/team', methods=['POST'])
def analyze_team():
    """分析单个队伍阵容"""
    data = request.get_json()
    hero_ids = data.get('heroes', [])

    analysis_service = get_analysis_service()
    result = analysis_service.get_team_summary(hero_ids)

    return jsonify(result)


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
