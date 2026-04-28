## 1. 模块骨架

- [x] 1.1 创建 `src/richman/engine/model.py`（GameEngine 类 + _EngineInputContext）
- [x] 1.2 更新 `src/richman/engine/__init__.py` 导出 GameEngine

## 2. 初始化和工厂方法

- [x] 2.1 实现 `GameEngine.create(config, board, players, renderer, seed)` 静态工厂，校验 JAIL_SPACE 存在
- [x] 2.2 实现 `_init_state()` 初始化 InternalGameState（玩家、地块、回合计数）
- [x] 2.3 实现 `get_state()` 和 `snapshot_for(viewer_index)` 公共访问器

## 3. 主循环和回合推进

- [x] 3.1 实现 `start()` 主循环（跳过破产玩家、递增 turn、调用 process_turn）
- [x] 3.2 实现 `_advance_to_next_player()`（跳过已破产玩家）
- [x] 3.3 实现 `_check_game_over()` 和 `_is_game_over()`（存活玩家数 == 1）

## 4. 五阶段回合流程

- [x] 4.1 实现 Phase ① EFFECT_UPDATE（TURN_START、监狱倒计时、JAIL_TICKED/JAIL_RELEASED）
- [x] 4.2 实现 Phase ② DICE_ROLL（wait_for_dice、掷骰、board_move、起点奖金）
- [x] 4.3 实现 Phase ③ landing 入口 `_process_landing()`（六种格子类型路由）
- [x] 4.4 实现 Phase ④ action 入口 `_process_action_phase()`（计算动作、调用 decide、执行）
- [x] 4.5 实现 Phase ⑤ END（TURN_END、清理 dice_value/available_actions、检查胜利条件）

## 5. 落点处理

- [x] 5.1 实现 `_process_property_landing()`（空地/己方/他人/地主坐牢 四分支）
- [x] 5.2 实现 `_process_chance_card()`（抽卡、resolve_card_intent、执行效果）
- [x] 5.3 实现 `_execute_card_intent()`（GrantMoney/DeductMoney/Move/GoToJail/ObtainCard）
- [x] 5.4 实现 `_execute_move_intent()`（随机方向/步数、board_move、递归 landing）
- [x] 5.5 实现 `_handle_jail_decision()`（有/无免狱卡两种路径）

## 6. 动作计算和执行

- [x] 6.1 实现 `_compute_actions()`（BUY/UPGRADE/USE_DEMOLISH/SKIP 条件判断）
- [x] 6.2 实现 `_execute_action()`（BUY: 扣钱+add_property；UPGRADE: 扣钱+升级；SKIP: 无）
- [x] 6.3 实现 `_execute_demolish()`（get_range、过滤候选、choose_demolish_target、降级）
- [x] 6.4 实现 `_add_property()`（设置 owner、level、acquired_at、purchase_price、增加 holdings）

## 7. 破产回收

- [x] 7.1 实现 `_pay_debt()`（现金足够→直接付；现金不足→回收→付清或破产）
- [x] 7.2 实现 `_reclaim_property()`（重置 PropertyState、从 holdings 移除）
- [x] 7.3 实现 `_finalize_bankruptcy()`（现金归零、手牌清除、标记 bankrupt）

## 8. 视图生成

- [x] 8.1 实现 `_build_public_board()`（基于 Board + properties_by_position 生成 PublicCellInfo）
- [x] 8.2 实现 `_build_public_players()`（不含现金和手牌）
- [x] 8.3 实现 `_build_player_view()`（PlayerView with viewer private data）
- [x] 8.4 实现 `_build_snapshot()`（GameSnapshot with full event log）
- [x] 8.5 实现 `_EngineInputContext`（仅暴露 prompt_choice）

## 9. 测试

- [x] 9.1 测试初始化和工厂（JAIL_SPACE 校验、PlayerState 创建、PropertyState 初始化、seed 确定性）
- [x] 9.2 测试主循环（turn 递增、破产玩家跳过、游戏结束判定）
- [x] 9.3 测试五阶段流程（Phase 顺序、事件日志序列）
- [x] 9.4 测试监狱机制（倒计时、跳过阶段、出狱）
- [x] 9.5 测试落点处理（空地/己方/他人地/地主坐牢/CHANCE/GO_TO_JAIL/JAIL_SPACE/BLANK）
- [x] 9.6 测试机会卡（加钱/扣钱/移动卡连锁/入狱/获得免狱卡/拆除卡）
- [x] 9.7 测试动作（BUY/UPGRADE/USE_DEMOLISH/SKIP/无动作）
- [x] 9.8 测试破产（租金不足→回收地块→付清；回收不足→破产→地主收不到钱）
- [x] 9.9 测试视图（PlayerView 含私有数据、GameSnapshot 含事件日志、PublicPlayerInfo 不含现金）
- [x] 9.10 测试 InputContext（只暴露 prompt_choice）

## 10. 验证

- [x] 10.1 `uv run pytest` 全部通过
- [x] 10.2 `uv run ruff check` 通过
- [x] 10.3 `uv run ruff format --check` 通过
- [x] 10.4 `uv run mypy src` 通过
