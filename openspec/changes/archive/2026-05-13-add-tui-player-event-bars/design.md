## 组件架构

```
GameScreen (layout: vertical)
├── Header                    (height: 1)
├── BoardWidget               (height: rows - 1 - 1 - 1 - 5)
├── PlayerStrip               (height: 1)
├── EventLine                 (height: 1)
└── ActionBar                 (height: 5)
```

### PlayerStrip

**职责**：一行横向展示所有玩家的紧凑状态。人类玩家展示现金、位置、手牌（出狱卡/拆除卡）、入狱/破产状态；AI 玩家仅展示名称、位置、入狱/破产状态。

**数据来源**：
- `GameSnapshot.public_players` — 所有玩家公开信息（名称、位置、入狱回合、破产）
- `GameSnapshot.viewer_private` — 当前视角玩家的私有信息（现金、手牌）
- `player_controllers: Sequence[Player]` — 区分人类/AI（`isinstance(p, HumanPlayer)`）

**显示规则**：
- **当前视角人类玩家**（`player_index == viewer_index` 且 controller 为 HumanPlayer）：展示现金 + 手牌 + 位置 + 状态
- **其他人类玩家**（非 viewer 的 HumanPlayer）：展示名称 + 位置 + 状态（快照不含其现金，暂缺）
- **AI 玩家**：仅展示名称 + 位置 + 入狱/破产状态，不展示现金和手牌

**渲染方案**：使用 Textual `Widget` + `render()` 方法返回 Rich `Text` 对象，各玩家用竖线 `|` 分隔，当前玩家用高亮色标记。单行高度由 `height: 1` 固定。

**更新方式**：通过 `update_snapshot(snapshot)` 方法设置新快照并 `refresh()`。

### EventLine

**职责**：一行展示最新事件摘要，点击发出 `OpenRequested` 消息。

**数据来源**：`GameSnapshot.event_log[-1]`

**交互**：
- 鼠标点击 → `self.post_message(EventLine.OpenRequested())`
- 键盘 E → 由 GameScreen 级 `on_key` 绑定处理，直接发出 `EventLine.OpenRequested`（无需 EventLine 获得焦点；ActionBar mount 后主动 focus 会抢走焦点）
- `OpenRequested` 是冒泡 `Message`，由父级 Screen 处理（当前仅发出消息，后续由 EventLogModal 消费）

**渲染方案**：使用 Textual `Widget` + `render()`，Rich `Text` 左对齐，超出截断。`height: 1`。

**更新方式**：通过 `update_snapshot(snapshot)` 方法设置新快照并 `refresh()`。

### GameScreen 布局调整

当前布局：
```
board_rows = height - _HEADER_HEIGHT(1) - _ACTION_BAR_HEIGHT(5)
```

新布局：
```
board_rows = height - _HEADER_HEIGHT(1) - _PLAYER_STRIP_HEIGHT(1) - _EVENT_LINE_HEIGHT(1) - _ACTION_BAR_HEIGHT(5)
```

`_apply_step_result` 方法扩展为同时更新 `PlayerStrip` 和 `EventLine`：
```python
for player_strip in self.query(PlayerStrip):
    player_strip.update_snapshot(result.snapshot)
for event_line in self.query(EventLine):
    event_line.update_snapshot(result.snapshot)
```

### 消息流

```
EventLine.click
  → EventLine.OpenRequested() bubble up
  → GameScreen.on_event_line_open_requested() (当前仅 stop，后续挂 EventLogModal)

GameScreen key E (screen-level binding, 不依赖 EventLine 焦点)
  → GameScreen.post_message(EventLine.OpenRequested())
  → GameScreen.on_event_line_open_requested()
```

## 文件变更

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `widgets/player_strip.py` | 新增 | PlayerStrip widget |
| `widgets/event_line.py` | 新增 | EventLine widget |
| `widgets/__init__.py` | 修改 | 导出 PlayerStrip、EventLine |
| `screens/game.py` | 修改 | 布局重排、高度扣减、_apply_step_result 扩展 |

## 不变部分

- BoardWidget、CellWidget、CenterPanel、ActionBar 自身不变
- domain 模型不变（GameSnapshot 已包含所需数据）
- engine 不变
- layout.py 不变
- 控制台路径不受影响
