/**
 * 王者荣耀BP系统前端逻辑 - 全局BP版本
 */

// 状态管理
const state = {
    sessionId: null,
    heroes: [],
    bpState: null,
    // 队伍信息
    teamAName: '蓝队',
    teamBName: '红队',
    teamAIsBlue: true,
    teamAWins: 0,
    teamBWins: 0,
    // 各队已用英雄
    teamAUsed: [],
    teamBUsed: [],
    gameNumber: 1,
    gamesHistory: [],
    currentFilter: 'all',
    selectedHero: null,
    waitingSideSelection: false,
    lastLoser: null,
    seriesFinished: false
};

// API基础路径
const API_BASE = '';

// 腾讯CDN图片URL
function getHeroImageUrl(hero) {
    // 优先使用腾讯CDN（用户可能已缓存）
    if (hero.ename) {
        return `https://game.gtimg.cn/images/yxzj/img201606/heroimg/${hero.ename}/${hero.ename}.jpg`;
    }
    return `/static/img/${hero.avatar}`;
}

// 生成头像HTML（带懒加载和错误回退）
function getAvatarHtml(hero, size = 50) {
    const cdnUrl = hero.ename ? `https://game.gtimg.cn/images/yxzj/img201606/heroimg/${hero.ename}/${hero.ename}.jpg` : '';
    const localUrl = `/static/img/${hero.avatar}`;
    const fallbackSvg = `data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 ${size} ${size}%22><rect fill=%22%23333%22 width=%22${size}%22 height=%22${size}%22/><text x=%22${size/2}%22 y=%22${size*0.6}%22 text-anchor=%22middle%22 fill=%22%23666%22 font-size=%22${size*0.24}%22>${hero.name[0]}</text></svg>`;

    // 使用CDN作为主URL，本地作为回退
    const src = cdnUrl || localUrl;
    const onerror = cdnUrl
        ? `this.onerror=null;this.src='${localUrl}';if(this.onerror)this.onerror=null;this.src='${fallbackSvg}';`
        : `this.src='${fallbackSvg}'`;

    return `<img src="${src}" alt="${hero.name}" loading="lazy" onerror="${onerror}">`;
}

// DOM元素
const elements = {
    startBtn: document.getElementById('startBtn'),
    newGameBtn: document.getElementById('newGameBtn'),
    undoBtn: document.getElementById('undoBtn'),
    gameInfo: document.getElementById('gameInfo'),
    bpStatus: document.getElementById('bpStatus'),
    currentPhase: document.getElementById('currentPhase'),
    currentSide: document.getElementById('currentSide'),
    heroesGrid: document.getElementById('heroesGrid'),
    recommendPanel: document.getElementById('recommendPanel'),
    recommendList: document.getElementById('recommendList'),
    blueBans: document.getElementById('blueBans'),
    bluePicks: document.getElementById('bluePicks'),
    redBans: document.getElementById('redBans'),
    redPicks: document.getElementById('redPicks'),
    blueAnalysis: document.getElementById('blueAnalysis'),
    redAnalysis: document.getElementById('redAnalysis'),
    analysisPanel: document.getElementById('analysisPanel'),
    globalBanInfo: document.getElementById('globalBanInfo'),
    blueUsedHeroes: document.getElementById('blueUsedHeroes'),
    redUsedHeroes: document.getElementById('redUsedHeroes'),
    gamesHistory: document.getElementById('gamesHistory'),
    historyList: document.getElementById('historyList'),
    // 新增元素
    teamSetupPanel: document.getElementById('teamSetupPanel'),
    teamAInput: document.getElementById('teamAInput'),
    teamBInput: document.getElementById('teamBInput'),
    confirmSetupBtn: document.getElementById('confirmSetupBtn'),
    scoreBoard: document.getElementById('scoreBoard'),
    teamAScore: document.getElementById('teamAScore'),
    teamBScore: document.getElementById('teamBScore'),
    blueTeamTitle: document.getElementById('blueTeamTitle'),
    redTeamTitle: document.getElementById('redTeamTitle'),
    blueUsedTitle: document.getElementById('blueUsedTitle'),
    redUsedTitle: document.getElementById('redUsedTitle'),
    winnerPanel: document.getElementById('winnerPanel'),
    blueWinBtn: document.getElementById('blueWinBtn'),
    redWinBtn: document.getElementById('redWinBtn'),
    sideSelectionPanel: document.getElementById('sideSelectionPanel'),
    loserSelectText: document.getElementById('loserSelectText'),
    selectBlueBtn: document.getElementById('selectBlueBtn'),
    selectRedBtn: document.getElementById('selectRedBtn'),
    seriesEndPanel: document.getElementById('seriesEndPanel'),
    winnerText: document.getElementById('winnerText'),
    finalScoreText: document.getElementById('finalScoreText'),
    newSeriesBtn: document.getElementById('newSeriesBtn')
};

// 初始化
async function init() {
    await loadHeroes();
    setupEventListeners();
}

// 加载英雄数据
async function loadHeroes() {
    try {
        const response = await fetch(`${API_BASE}/api/heroes`);
        state.heroes = await response.json();
        renderHeroes();
    } catch (error) {
        console.error('加载英雄数据失败:', error);
    }
}

// 渲染英雄列表
function renderHeroes() {
    const filteredHeroes = state.currentFilter === 'all'
        ? state.heroes
        : state.heroes.filter(h => h.lanes && h.lanes.includes(state.currentFilter));

    const unavailableIds = getUnavailableHeroIds();

    elements.heroesGrid.innerHTML = filteredHeroes.map(hero => {
        const isBanned = unavailableIds.banned.includes(hero.id);
        const isPicked = unavailableIds.picked.includes(hero.id);
        const statusClass = isBanned ? 'banned' : (isPicked ? 'picked' : '');

        return `
            <div class="hero-card ${statusClass}" data-hero-id="${hero.id}">
                <div class="hero-avatar">
                    ${getAvatarHtml(hero, 50)}
                </div>
                <div class="hero-name">${hero.name}</div>
                <div class="hero-position">${hero.lanes ? hero.lanes.join('/') : ''}</div>
            </div>
        `;
    }).join('');

    // 绑定点击事件
    document.querySelectorAll('.hero-card:not(.banned):not(.picked)').forEach(card => {
        card.addEventListener('click', () => selectHero(parseInt(card.dataset.heroId)));
    });
}

// 获取不可用英雄ID
function getUnavailableHeroIds() {
    if (!state.bpState) {
        return { banned: [], picked: [] };
    }

    const banned = [...state.bpState.blue_bans, ...state.bpState.red_bans];
    const picked = [...state.bpState.blue_picks, ...state.bpState.red_picks];

    const currentAction = state.bpState.current_action;
    if (currentAction) {
        // 获取当前蓝方和红方对应的队伍已用英雄
        const blueUsedHeroes = state.teamAIsBlue ? state.teamAUsed : state.teamBUsed;
        const redUsedHeroes = state.teamAIsBlue ? state.teamBUsed : state.teamAUsed;

        if (currentAction.action === 'ban') {
            // Ban阶段：对方已用英雄不能被ban
            if (currentAction.side === 'blue') {
                banned.push(...redUsedHeroes);
            } else {
                banned.push(...blueUsedHeroes);
            }
        } else {
            // Pick阶段：本队已用英雄不能再选
            if (currentAction.side === 'blue') {
                picked.push(...blueUsedHeroes);
            } else {
                picked.push(...redUsedHeroes);
            }
        }
    }

    return { banned, picked };
}

// 设置事件监听
function setupEventListeners() {
    // 开始BP按钮
    elements.startBtn.addEventListener('click', showTeamSetup);

    // 确认设置
    elements.confirmSetupBtn.addEventListener('click', confirmSetup);

    // 新一局按钮
    elements.newGameBtn.addEventListener('click', startNewGame);

    // 撤销按钮
    elements.undoBtn.addEventListener('click', undoAction);

    // 胜者选择
    elements.blueWinBtn.addEventListener('click', () => setWinner('blue'));
    elements.redWinBtn.addEventListener('click', () => setWinner('red'));

    // 选边
    elements.selectBlueBtn.addEventListener('click', () => selectSide('blue'));
    elements.selectRedBtn.addEventListener('click', () => selectSide('red'));

    // 新系列赛
    elements.newSeriesBtn.addEventListener('click', startNewSeries);

    // 分路筛选
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentFilter = btn.dataset.lane;
            renderHeroes();
        });
    });
}

// 显示队伍设置面板
function showTeamSetup() {
    elements.teamSetupPanel.classList.remove('hidden');
    elements.teamAInput.focus();
}

// 确认设置并开始
async function confirmSetup() {
    const teamA = elements.teamAInput.value.trim() || '蓝队';
    const teamB = elements.teamBInput.value.trim() || '红队';

    try {
        // 创建会话
        const startResponse = await fetch(`${API_BASE}/api/bp/start`, { method: 'POST' });
        const startData = await startResponse.json();

        state.sessionId = startData.session_id;

        // 设置队伍名称
        await fetch(`${API_BASE}/api/bp/${state.sessionId}/set-teams`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team_a: teamA, team_b: teamB })
        });

        // 更新状态
        state.teamAName = teamA;
        state.teamBName = teamB;

        // 更新UI
        updateTeamNames();
        elements.teamSetupPanel.classList.add('hidden');
        elements.startBtn.textContent = '重新开始';
        elements.bpStatus.classList.remove('hidden');
        elements.scoreBoard.classList.remove('hidden');
        elements.gameInfo.classList.remove('hidden');
        elements.undoBtn.disabled = false;

        // 获取最新状态
        const stateResponse = await fetch(`${API_BASE}/api/bp/${state.sessionId}/state`);
        const stateData = await stateResponse.json();
        updateFullState(stateData);

    } catch (error) {
        console.error('开始BP失败:', error);
    }
}

// 更新队伍名称显示
function updateTeamNames() {
    const blueTeam = state.teamAIsBlue ? state.teamAName : state.teamBName;
    const redTeam = state.teamAIsBlue ? state.teamBName : state.teamAName;

    elements.blueTeamTitle.textContent = `💙 ${blueTeam}`;
    elements.redTeamTitle.textContent = `❤️ ${redTeam}`;
    elements.blueUsedTitle.textContent = `💙 ${blueTeam}已用`;
    elements.redUsedTitle.textContent = `❤️ ${redTeam}已用`;
    elements.blueWinBtn.textContent = `${blueTeam} 获胜`;
    elements.redWinBtn.textContent = `${redTeam} 获胜`;
    elements.selectBlueBtn.textContent = `选择蓝方 (将成为蓝方)`;
    elements.selectRedBtn.textContent = `选择红方 (将成为红方)`;
}

// 选择英雄
async function selectHero(heroId) {
    if (!state.bpState || state.bpState.is_finished) {
        return;
    }

    const currentAction = state.bpState.current_action;
    if (!currentAction) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/bp/${state.sessionId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hero_id: heroId,
                side: currentAction.side,
                action: currentAction.action
            })
        });

        const result = await response.json();

        if (result.success) {
            updateFullState(result.state);
        } else {
            alert(result.error || '操作失败');
        }

    } catch (error) {
        console.error('执行操作失败:', error);
    }
}

// 撤销操作
async function undoAction() {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/bp/${state.sessionId}/undo`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            updateFullState(result.state);
        }

    } catch (error) {
        console.error('撤销失败:', error);
    }
}

// 设置胜者
async function setWinner(winner) {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/bp/${state.sessionId}/set-winner`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ winner })
        });

        const result = await response.json();

        if (result.success) {
            updateFullState(result.state);

            // 检查系列赛是否结束
            if (state.seriesFinished) {
                showSeriesEnd();
            } else {
                // 显示选边面板
                showSideSelection();
            }
        }

    } catch (error) {
        console.error('设置胜者失败:', error);
    }
}

// 显示选边面板
function showSideSelection() {
    elements.winnerPanel.classList.add('hidden');
    elements.sideSelectionPanel.classList.remove('hidden');

    const loserName = state.lastLoser === 'A' ? state.teamAName : state.teamBName;
    elements.loserSelectText.textContent = `${loserName} 请选择下一局阵营`;
}

// 选择阵营
async function selectSide(side) {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/bp/${state.sessionId}/select-side`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ side })
        });

        const result = await response.json();

        if (result.success) {
            updateFullState(result.state);
            elements.sideSelectionPanel.classList.add('hidden');
            updateTeamNames();
        }

    } catch (error) {
        console.error('选边失败:', error);
    }
}

// 开始新一局
async function startNewGame() {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/bp/${state.sessionId}/new-game`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            updateFullState(result.state);
        } else {
            alert(result.error || '无法开始新一局');
        }

    } catch (error) {
        console.error('开始新一局失败:', error);
    }
}

// 显示系列赛结束
function showSeriesEnd() {
    elements.winnerPanel.classList.add('hidden');
    elements.sideSelectionPanel.classList.add('hidden');
    elements.seriesEndPanel.classList.remove('hidden');

    const winnerName = state.teamAWins >= 4 ? state.teamAName : state.teamBName;
    elements.winnerText.textContent = `🏆 ${winnerName} 获得系列赛胜利！`;
    elements.finalScoreText.textContent = `最终比分: ${state.teamAName} ${state.teamAWins} : ${state.teamBWins} ${state.teamBName}`;
}

// 开始新系列赛
function startNewSeries() {
    // 重置状态
    state.sessionId = null;
    state.teamAUsed = [];
    state.teamBUsed = [];
    state.teamAWins = 0;
    state.teamBWins = 0;
    state.gameNumber = 1;
    state.gamesHistory = [];
    state.seriesFinished = false;
    state.bpState = null;

    // 重置UI
    elements.seriesEndPanel.classList.add('hidden');
    elements.scoreBoard.classList.add('hidden');
    elements.bpStatus.classList.add('hidden');
    elements.gameInfo.classList.add('hidden');
    elements.globalBanInfo.classList.add('hidden');
    elements.gamesHistory.classList.add('hidden');
    elements.startBtn.textContent = '开始BP';
    elements.undoBtn.disabled = true;

    // 显示设置面板
    elements.teamAInput.value = '';
    elements.teamBInput.value = '';
    showTeamSetup();
}

// 更新完整状态
function updateFullState(serverState) {
    state.gameNumber = serverState.game_number || 1;
    state.teamAName = serverState.team_a_name || '蓝队';
    state.teamBName = serverState.team_b_name || '红队';
    state.teamAIsBlue = serverState.team_a_is_blue !== undefined ? serverState.team_a_is_blue : true;
    state.teamAWins = serverState.team_a_wins || 0;
    state.teamBWins = serverState.team_b_wins || 0;
    state.teamAUsed = serverState.team_a_used || [];
    state.teamBUsed = serverState.team_b_used || [];
    state.gamesHistory = serverState.games_history || [];
    state.bpState = serverState.current_bp;
    state.waitingSideSelection = serverState.waiting_side_selection || false;
    state.lastLoser = serverState.last_loser || null;
    state.seriesFinished = serverState.series_finished || false;

    updateUI();
}

// 更新UI
function updateUI() {
    if (!state.bpState) return;

    const bpState = state.bpState;

    // 更新比分
    elements.teamAScore.textContent = state.teamAWins;
    elements.teamBScore.textContent = state.teamBWins;

    // 更新局数信息
    elements.gameInfo.textContent = `第 ${state.gameNumber} 局`;

    // 更新队伍名称
    updateTeamNames();

    // 更新状态提示
    if (bpState.current_action) {
        const action = bpState.current_action;
        const actionText = action.action === 'ban' ? '禁用' : '选择';
        const sideName = action.side === 'blue' ?
            (state.teamAIsBlue ? state.teamAName : state.teamBName) :
            (state.teamAIsBlue ? state.teamBName : state.teamAName);
        elements.currentPhase.textContent = `${sideName}${actionText}`;
        elements.currentSide.textContent = action.side === 'blue' ? '蓝方' : '红方';
        elements.currentSide.className = `side-badge ${action.side}`;
    } else if (bpState.is_finished) {
        elements.currentPhase.textContent = 'BP结束';
        elements.currentSide.textContent = '';

        // 显示胜者选择面板
        if (!state.seriesFinished) {
            elements.winnerPanel.classList.remove('hidden');
            elements.newGameBtn.classList.add('hidden');
        }
    }

    // 更新禁用槽位
    updateSlots(elements.blueBans, bpState.blue_bans, 'ban');
    updateSlots(elements.redBans, bpState.red_bans, 'ban');

    // 更新选择槽位
    updateSlots(elements.bluePicks, bpState.blue_picks, 'pick');
    updateSlots(elements.redPicks, bpState.red_picks, 'pick');

    // 更新英雄列表
    renderHeroes();

    // 更新全局已用显示
    updateGlobalUsed();

    // 更新历史记录
    updateGamesHistory();

    // 获取推荐
    if (bpState.current_action && bpState.current_action.action === 'pick') {
        fetchRecommendations();
    } else {
        elements.recommendPanel.classList.add('hidden');
    }

    // 更新分析
    updateAnalysis();

    // 更新撤销按钮状态
    elements.undoBtn.disabled = bpState.history.length === 0;
}

// 更新槽位显示
function updateSlots(container, heroIds, type) {
    const slots = container.querySelectorAll('.slot');
    slots.forEach((slot, index) => {
        if (index < heroIds.length) {
            const hero = state.heroes.find(h => h.id === heroIds[index]);
            if (hero) {
                slot.classList.add('filled');
                slot.innerHTML = getAvatarHtml(hero, 48);
            }
        } else {
            slot.classList.remove('filled');
            slot.innerHTML = '';
        }
    });
}

// 更新全局已用英雄显示
function updateGlobalUsed() {
    const hasUsed = state.teamAUsed.length > 0 || state.teamBUsed.length > 0;

    if (hasUsed) {
        elements.globalBanInfo.classList.remove('hidden');

        // 获取当前蓝方和红方对应的队伍已用英雄
        const blueUsedHeroes = state.teamAIsBlue ? state.teamAUsed : state.teamBUsed;
        const redUsedHeroes = state.teamAIsBlue ? state.teamBUsed : state.teamAUsed;

        elements.blueUsedHeroes.innerHTML = blueUsedHeroes.map(heroId => {
            const hero = state.heroes.find(h => h.id === heroId);
            if (!hero) return '';
            return `
                <div class="global-hero-item blue">
                    ${getAvatarHtml(hero, 24)}
                    <span>${hero.name}</span>
                </div>
            `;
        }).join('');

        elements.redUsedHeroes.innerHTML = redUsedHeroes.map(heroId => {
            const hero = state.heroes.find(h => h.id === heroId);
            if (!hero) return '';
            return `
                <div class="global-hero-item red">
                    ${getAvatarHtml(hero, 24)}
                    <span>${hero.name}</span>
                </div>
            `;
        }).join('');
    } else {
        elements.globalBanInfo.classList.add('hidden');
    }
}

// 更新历史比赛记录
function updateGamesHistory() {
    if (state.gamesHistory.length > 0) {
        elements.gamesHistory.classList.remove('hidden');
        elements.historyList.innerHTML = state.gamesHistory.map(game => {
            const blueHeroes = game.blue_picks.map(id => state.heroes.find(h => h.id === id)).filter(Boolean);
            const redHeroes = game.red_picks.map(id => state.heroes.find(h => h.id === id)).filter(Boolean);

            return `
                <div class="history-item">
                    <h4>第 ${game.game} 局 - ${game.blue_team || '蓝方'} VS ${game.red_team || '红方'}</h4>
                    <div class="history-teams">
                        <div class="history-team blue">
                            ${blueHeroes.map(h => `<img src="${getHeroImageUrl(h)}" alt="${h.name}" title="${h.name}" loading="lazy" onerror="this.src='/static/img/${h.avatar}'">`).join('')}
                        </div>
                        <div class="history-vs">VS</div>
                        <div class="history-team red">
                            ${redHeroes.map(h => `<img src="${getHeroImageUrl(h)}" alt="${h.name}" title="${h.name}" loading="lazy" onerror="this.src='/static/img/${h.avatar}'">`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        elements.gamesHistory.classList.add('hidden');
    }
}

// 获取推荐
async function fetchRecommendations() {
    if (!state.sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/api/bp/${state.sessionId}/recommend`);
        const data = await response.json();

        if (data.recommendations && data.recommendations.length > 0) {
            renderRecommendations(data.recommendations);
            elements.recommendPanel.classList.remove('hidden');
        } else {
            elements.recommendPanel.classList.add('hidden');
        }

    } catch (error) {
        console.error('获取推荐失败:', error);
    }
}

// 渲染推荐列表
function renderRecommendations(recommendations) {
    elements.recommendList.innerHTML = recommendations.slice(0, 5).map(rec => {
        const hero = state.heroes.find(h => h.id === rec.hero_id);
        if (!hero) return '';

        return `
            <div class="recommend-item" data-hero-id="${rec.hero_id}">
                <div class="hero-icon">
                    ${getAvatarHtml(hero, 40)}
                </div>
                <div class="hero-info">
                    <div class="hero-name">${rec.name}</div>
                    <div class="hero-score">评分: ${rec.score}</div>
                    <div class="hero-reasons">${rec.reasons.join(', ')}</div>
                </div>
            </div>
        `;
    }).join('');

    // 绑定点击事件
    document.querySelectorAll('.recommend-item').forEach(item => {
        item.addEventListener('click', () => {
            selectHero(parseInt(item.dataset.heroId));
        });
    });
}

// 更新分析
async function updateAnalysis() {
    if (!state.bpState) return;

    const bluePicks = state.bpState.blue_picks;
    const redPicks = state.bpState.red_picks;

    if (bluePicks.length > 0 || redPicks.length > 0) {
        elements.analysisPanel.classList.remove('hidden');

        if (bluePicks.length > 0) {
            const blueAnalysis = await analyzeTeam(bluePicks);
            renderTeamAnalysis(elements.blueAnalysis, blueAnalysis);
        }

        if (redPicks.length > 0) {
            const redAnalysis = await analyzeTeam(redPicks);
            renderTeamAnalysis(elements.redAnalysis, redAnalysis);
        }
    } else {
        elements.analysisPanel.classList.add('hidden');
    }
}

// 分析队伍
async function analyzeTeam(heroIds) {
    try {
        const response = await fetch(`${API_BASE}/api/analyze/team`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ heroes: heroIds })
        });
        return await response.json();
    } catch (error) {
        console.error('分析队伍失败:', error);
        return null;
    }
}

// 渲染队伍分析
function renderTeamAnalysis(container, analysis) {
    if (!analysis) {
        container.innerHTML = '';
        return;
    }

    const attrs = analysis.attributes || {};
    const attrNames = {
        damage: '输出',
        tankiness: '坦度',
        control: '控制',
        mobility: '机动',
        early_game: '前期',
        late_game: '后期'
    };

    container.innerHTML = Object.entries(attrs).map(([key, value]) => {
        const color = value >= 70 ? '#2ecc71' : (value >= 50 ? '#f1c40f' : '#e74c3c');
        return `
            <div class="attribute">
                <span>${attrNames[key] || key}</span>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${value}%; background: ${color}"></div>
                </div>
            </div>
        `;
    }).join('');
}

// 初始化应用
init();
