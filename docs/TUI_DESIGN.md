# 终端大富翁 — TUI 交互设计文档

> 面向实现者的完整 TUI 设计参考。涵盖布局、交互、状态流转和视觉规范。

---

## 一、设计概览

| 维度 | 决策 |
|---|---|
| 框架 | Textual (≥6.0)，全屏接管终端 |
| 棋盘 | 配置化坐标布局，格子围绕固定中心展示区 |
| 玩家 | 单人游玩（1 人类 + N 个 AI） |
| 风格 | 明亮清新，浅色背景 + 柔和色彩 |
| 交互 | 键盘 + 鼠标双通路 |
| 引擎 | 统一可步进 `GameEngine`，由 Console/TUI/测试驱动 |

---

## 二、屏幕布局

以下是一个可能的布局示例。实际棋盘格位置由配置文件中的 `tui_layout` 决定；中心展示区始终固定保留，不可被棋盘格占用。

```
┌──────────────────────────────────────────────────────────┐
│  ▌ 第 8 回合  ▌  ⬤ 你的回合  ▌  掷骰移动                   │ ① Header (1行)
├──────────────────────────────────────────────────────────┤
│                                                          │
│              ┌────┬────┬────┬────┬────┬────┐              │
│              │ 21 │ 22 │ 23 │ 24 │ 25 │ 26 │              │
│         ┌────┼────┘                        └────┼────┐    │
│         │ 20 │  ╔══════════════════════════╗  │ 27 │    │
│         ├────┤  ║                          ║  ├────┤    │
│         │ 19 │  ║       🎲 等待掷骰        ║  │ 28 │    │ ② 棋盘主体
│         ├────┤  ║                          ║  ├────┤    │    (1fr 自适应)
│         │ 18 │  ║     [ 按 Enter 掷骰 ]    ║  │ 29 │    │
│         ├────┤  ║                          ║  ├────┤    │
│         │ 17 │  ╚══════════════════════════╝  │ 30 │    │
│         ├────┼────┐                        ┌────┼────┤    │
│         │ 16 │ 15 │ 14 │ 13 │ 12 │ 11 │ 10 │ 9  │ 8  │    │
│         └────┴────┴────┴────┴────┴────┴────┴────┴────┘    │
│               1     2     3     4     5     6     7       │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ ⬤ 你  💰$1,850  🎴×1  🏚×1  🏠×3  │  ○AI-1  △AI-2  ▢AI-3 │ ③ 玩家条 (1行)
├──────────────────────────────────────────────────────────┤
│ > 你掷出了 4！从 5 → 9，踩中「海滨别墅」(AI-1的2级地)      │ ④ 事件提示 (1行)
├──────────────────────────────────────────────────────────┤
│ 你可以:  [ 购买 $120 ]  [ 升级 $50 ]  [ 拆除 ]  [ 跳过 ]   │ ⑤ 动作栏 (1行, 仅阶段④)
└──────────────────────────────────────────────────────────┘
```

### 区域说明

| 区域 | CSS height | 组件类型 | 说明 |
|---|---|---|---|
| ① Header | 1 | Static | 回合数、当前玩家名、当前阶段 |
| ② 棋盘 | 1fr | BoardWidget（自定义） | 配置化地图 + 固定中心动态区，占满剩余空间 |
| ③ 玩家条 | 1 | Static + 可点击区域 | 左侧常驻人类玩家私密信息；右侧 AI 头像 |
| ④ 事件提示 | 1 | Static | 最新一条事件，点击或按 `E` 展开覆盖层 |
| ⑤ 动作栏 | 1 (条件显示) | Horizontal + Button | 仅在阶段④渲染，Textual 原生 Button |

---

## 三、棋盘 Widget 设计

### 3.1 配置化坐标布局

TUI 不假设棋盘必须四边均分，也不固定 START 在某个角落。游戏移动顺序仍由 `board_cells` 的 position 顺序决定；视觉位置由 `tui_layout.cells` 显式配置。

示例配置：

```yaml
tui_layout:
  rows: 9
  columns: 13
  center:
    row: 2
    column: 3
    rows: 5
    columns: 7
  cells:
    - position: 0
      row: 8
      column: 0
    - position: 1
      row: 8
      column: 1
    - position: 2
      row: 8
      column: 2
```

字段含义：

| 字段 | 说明 |
|---|---|
| `rows` / `columns` | 地图 slot 网格尺寸，slot 不是终端字符，而是一个格子布局单位 |
| `center` | 中心展示区占用的 slot 矩形 |
| `cells[].position` | 对应 `board_cells[position]` |
| `cells[].row` / `column` | 该格子左上角所在 slot 坐标，0 基 |

布局校验：

- `cells` 必须覆盖所有 `board_cells` position。
- `position` 不允许重复。
- `row` / `column` 必须在 `rows` / `columns` 范围内。
- 棋盘格不可与 `center` 矩形重叠。
- 棋盘格之间允许不连续，但相邻 position 若在视觉上不相邻，TUI 应在配置校验中给出警告，避免玩家难以理解移动路径。
- 默认内置地图也应提供 `tui_layout`；若自定义配置缺少布局，TUI 拒绝进入游戏并显示配置错误。

中心展示区固定存在。它不参与移动路径，不占用 `board_cells` position，只用于展示骰子、阶段说明、AI 行动、回合摘要等动态内容。

### 3.2 单个格子渲染

每个棋盘格是独立 `CellWidget`，内部可用 Rich `Panel` 或 Textual 样式渲染 3 行内容：

```
┌──────────┐
│ [03] 🏠  │  行1: 编号 + 类型 emoji
│ 海滨别墅  │  行2: 名称（过长截断为前5字+"…"）
│ ●●  AI-1 │  行3: 等级圆点 + 地主名
└──────────┘
```

- 默认格子尺寸固定为约 10~12 字符宽、5 行高（面板边框 2 + 内容 3）。
- 当前不做自动缩放。配置化布局必须在固定格子尺寸下计算所需终端尺寸。
- 如果当前终端尺寸不足，TUI 显示尺寸不足错误页，提示当前尺寸和需要尺寸。
- 未来可以增加地图滚动，但滚动不是当前设计的主路径。

### 3.3 颜色语义

色彩方向：**明亮清新**，浅色 / 柔和色调。

| 格子类型 | 底色 | 边框色 |
|---|---|---|
| 🏁 起点 | 浅绿 | 绿色 |
| 🏠 地块（空地） | 浅棕 / 米色 | 棕色 |
| 🎴 机会卡 | 浅金 / 奶油黄 | 金色 |
| 🚔 入狱格 | 浅红 / 粉色 | 红色 |
| 🔒 监狱格 | 浅灰 | 灰色 |
| ⬜ 空白 | 接近背景色 | 浅灰 |

| 地块归属 | 边框色 |
|---|---|
| 无主 | 中性灰 |
| 人类玩家 | 蓝色 |
| AI-1 | 橙色 |
| AI-2 | 紫色 |
| AI-3 | 青色 |

- 等级圆点：实心 ● (已达到) + 空心 ○ (未达到)，最多 3 个
- 有玩家棋子在的格子边框加粗 / 高亮

### 3.4 玩家棋子显示

- 每个格子上方 / 内部标注当前在此格的所有玩家棋子
- 符号：人类 ⬤，AI-1 ○，AI-2 △，AI-3 ▢
- 多人在同一格时并排显示，如 `⬤△`
- 回合切换时棋子位置瞬时更新（无移动动画）

### 3.5 中心区域

按阶段动态切换内容：

| 阶段 | 中心显示 | 交互 |
|---|---|---|
| ① 效果更新 | "效果更新中..." / 监狱倒计时信息 | 无 |
| ② 掷骰移动 | 大号骰子数字 + "按 Enter 掷骰" | 按 Enter/Space 触发掷骰 |
| ③ 落点效果 | 落点类型 + 效果描述 | 无（效果自动结算） |
| ④ 玩家动作 | 当前局面的文字摘要 | 动作选择在底部动作栏 |
| ⑤ 回合结束 | 回合摘要 | 无 |

AI 回合时，中心区域显示 AI 的行动描述（"AI-1 掷出 4 → 移动到 #8 → 踩中空地 → 选择购买"）。

### 3.6 BoardWidget 组件结构

BoardWidget 当前采用子 Widget 网格布局：

- `BoardWidget` 负责读取 `tui_layout`、校验布局、计算所需终端尺寸。
- 每个棋盘格是独立 `CellWidget(position)`，根据配置中的 `row` / `column` 放入 slot 网格。
- 中心展示区是独立 `CenterPanel`，占用 `tui_layout.center` 指定的矩形。
- `CellWidget` 处理鼠标点击并发出 `CellClicked(position)` 消息。
- 高亮、禁用、拆除目标候选等状态通过 widget class 或 reactive state 更新。
- 连续边框、复杂路径连线、单 renderable 精细绘制不作为当前目标；如未来需要，可在不改变 `tui_layout` schema 的前提下替换 BoardWidget 渲染层。

---

## 四、交互设计

### 4.1 交互总览

| 交互 | 触发方式 | 效果 |
|---|---|---|
| 掷骰 | `Enter` / `Space` | 中心骰子动画→定格结果 |
| 格子详情 | 点击棋盘格子 | 弹出层，显示该格完整信息 |
| 事件日志 | 点击事件栏 / `E` | 覆盖层展开，可滚动，`Esc` 关闭 |
| AI 信息 | 点击 AI 头像 | 临时浮层（公开信息），2秒自动消失 |
| 动作选择 | 点击 Button / `1`~`4` | 执行对应动作 |
| 目标选择 | 点击候选格子 | 拆除卡等二步操作 |
| 退出 | `q` | 退出游戏 |

### 4.2 键盘快捷键

| 按键 | 场景 | 效果 |
|---|---|---|
| `Enter` / `Space` | 阶段② | 触发掷骰 |
| `E` | 任意 | 展开/收起事件日志 |
| `1`~`4` | 阶段④ | 选择第 N 个动作 |
| `Tab` | 阶段④ | 在动作按钮间切换焦点 |
| `↑` `↓` / 滚轮 | 事件日志展开时 | 滚动事件列表 |
| `PgUp` `PgDn` | 事件日志展开时 | 翻页 |
| `Home` `End` | 事件日志展开时 | 跳到最早/最新事件 |
| `Esc` | 弹出层展开时 | 关闭弹出层 |
| `q` | 任意 | 退出游戏 |

### 4.3 鼠标交互

| 操作 | 效果 |
|---|---|
| 点击棋盘格子 | 弹出该格详情覆盖层 |
| 点击事件栏 | 展开事件日志覆盖层 |
| 点击 AI 头像 | 弹出该 AI 公开信息浮层 |
| 点击动作按钮 | 触发对应动作 |
| 点击弹出层外部 | 关闭 toast；modal 是否支持外部关闭由具体实现决定 |
| 滚轮 | 滚动事件日志 |

### 4.4 弹出层 / 覆盖层规范

终端不要求真实半透明。弹层通过 Textual 的 dim 背景、高对比边框、固定宽高和焦点管理与棋盘区分。

弹层分两类：

| 类型 | 用途 | 行为 |
|---|---|---|
| `ModalScreen` | 事件日志、格子详情、入狱选择等需要明确焦点的交互 | `Esc` 关闭；同一时间最多一个；新 modal 打开前关闭旧 modal |
| toast / popover | AI 公开信息等临时提示 | 2 秒自动消失；点击外部消失；新提示替换旧提示 |

Modal 的外部点击关闭不是硬性要求；若实现复杂，优先保证 `Esc`、按钮和焦点行为稳定。

---

## 五、各模块详细设计

### 5.1 启动画面

**流程**：标题画面 → 选择人数 → 输入名字 → 进入游戏

**标题画面**（TitleScreen）：
```
╔══════════════════════════════════════════╗
║                                          ║
║           🎲  终端大富翁  🎲              ║
║                                          ║
║         [ 开始游戏 ]                      ║
║                                          ║
║         按 Enter 或点击按钮开始           ║
║                                          ║
╚══════════════════════════════════════════╝
```

**玩家设置画面**（SetupScreen）：
```
╔══════════════════════════════════════════╗
║  游戏设置                                 ║
║                                          ║
║  总玩家数:  [2] [3] [4]   ← 按钮选择     ║
║  你的名字:  [___________]  ← 输入框       ║
║                                          ║
║         [ 开始游戏 ]                      ║
║                                          ║
╚══════════════════════════════════════════╝
```

- 使用 Textual Screen 栈：`TitleScreen → SetupScreen → GameScreen`
- CLI 保留现有 `richman play` 行为；TUI 通过新增 `richman tui` 进入
- `richman tui` 的人数和人类玩家名称由 SetupScreen 设置，不复用 `richman play --players`
- GameScreen 实现详见第六节

### 5.2 事件日志

**收起态**（始终可见，1 行）：
```
│ > 你掷出了 4！从 5 → 9，踩中「海滨别墅」(AI-1的2级地)  │
```

**展开态**（覆盖层，浮在棋盘上方）：
```
┌─ 事件日志 ─────────────────────────────── [Esc 关闭] ─┐
│────────────────────────────────────────────────────────│
│ 0.  第 3 回合开始 — AI-1 的回合                          │
│ 1.  AI-1 掷出 2                                         │
│ 2.  AI-1 从 5 移动到 7                                  │
│ 3.  AI-1 踩中「农场」，选择升级                          │
│ 4.  AI-1 升级了「农场」到 2级                            │
│ 5.  你掷出 4                                            │
│ 6.  你从 5 移动到 9                                     │
│ 7.  你踩中「海滨别墅」(AI-1的2级地)                      │
│ 8.  你支付租金 $90 给 AI-1                              │
│                                         ↑↓ 滚动  PgUp/PgDn │
└────────────────────────────────────────────────────────┘
```

**交互规范**：
- 事件按时间正序展示（最新在底部）
- 展开后自动滚底；手动滚动后停止跟随
- 隐私遮蔽：AI 玩家的现金、手牌在事件中显示为 `已隐藏`
- 关闭后收起态显示最新一条

### 5.3 玩家条

**布局**：
```
┌──────────────────────────────────────────────────────────────────┐
│ ⬤ 你  💰$1,850  🎴×1  🏚×1  🏠×3  │  ○AI-1  △AI-2  ▢AI-3       │
└──────────────────────────────────────────────────────────────────┘
  左侧：人类玩家私密信息（常驻）         右侧：AI 头像（可点击）
```

**点击 AI 头像**：
```
            ┌─ AI-1 · 机器人小明 ──────┐
            │ 位置: #14 (🏠农场)         │
            │ 地块: 3块                  │
            │ 状态: 🔒 坐牢中 (剩2轮)    │
            └───────────────────────────┘
```
- 浮层显示公开信息：名字、位置、持有地块数、监狱状态、破产状态
- 不显示现金、手牌（私密信息）
- 2 秒后自动消失，或点击外部消失

### 5.4 骰子动画

**阶段② 掷骰流程**：
1. 棋盘中心显示大字骰子数字
2. 数字 1~6 快速循环切换（~0.3 秒，类似老虎机）
3. 定格在最终结果
4. 显示 "你掷出了 N！"
5. 自动进入阶段③

**触发**：`Enter` 或 `Space`

### 5.5 动作栏

**仅在阶段④显示**，使用 Textual 原生 `Button`：

```
│ 你可以:  [ 购买 $120 ]  [ 升级 $50 ]  [ 拆除 ]  [ 跳过 ]         │
```

- 按钮间水平排列，`Horizontal` 容器
- 可用动作从 `StepResult.required_input.options` 或 snapshot 中的动作字段计算而来
- 无效时（现金不足等）对应按钮不可点击 / 灰显
- `Tab` 切换焦点，`Enter`/`Space`/鼠标点击 触发
- 快捷键 `1`~`4` 映射到第 1~4 个按钮

### 5.6 格子详情弹出层

点击棋盘格子 → 弹出覆盖层：

**地块格**：
```
┌─ #05 · 🏠 海滨别墅 ────────────┐
│                                │
│  地主: AI-1 (小明)              │
│  等级: ●●○ (2级)               │
│  地价: $120  升级费: $50       │
│  当前租金: $90                 │
│                                │
│  租金表:                       │
│    空地  $8                    │
│    1级   $30                   │
│    2级   $90  ← 当前           │
│    3级   $250                  │
└────────────────────────────────┘
```

**非地块格**：
```
┌─ #00 · 🏁 起点 ───────────────┐
│                                │
│  经过或停留时获得 +$200        │
│                                │
└────────────────────────────────┘
```

各类型展示内容：

| 格子类型 | 展示内容 |
|---|---|
| START | "经过或停留时获得 +$200" |
| PROPERTY | 地主、等级、地价、升级费、当前租金、四级租金表 |
| CHANCE | "踩中时随机抽取一张机会卡" |
| GO_TO_JAIL | "踩中时直接入狱（可用免狱卡避免）" |
| JAIL_SPACE | "监狱格，被关押玩家所在位置" |
| BLANK | "空白格，无事发生" |

### 5.7 拆除卡的二步交互

1. 阶段④动作栏点击 `[ 拆除 ]`
2. 棋盘上所有在范围内的**有等级地块**高亮（特殊边框或闪烁）
3. 玩家点击高亮的格子 → 确认执行
4. 若点不相关的格子 / 按 `Esc` → 取消，回到动作选择
5. 执行后，动作栏恢复（跳过回合已消耗一次动作）

### 5.8 入狱判决交互

当踩中入狱格或抽到入狱卡时：

- 如果玩家有免狱卡：弹出选择 `[ 使用免狱卡 ] [ 接受入狱 ]`
  - 点"使用免狱卡" → 消耗一张，不入狱，继续阶段④
  - 点"接受入狱" → 入狱，当前回合立即结束
- 如果玩家无免狱卡：自动入狱，中心显示 "你被捕了！入狱 3 轮"，当前回合结束

---

## 六、游戏状态流转

### 6.1 统一可步进 Engine

Engine 不直接调用 Renderer，也不阻塞等待输入。Console、TUI、测试都通过同一套 step API 驱动 Engine：

```python
frame = engine.advance(input=None)

if frame.required_input is not None:
    user_input = adapter.collect_input(frame.required_input)
    frame = engine.advance(user_input)

adapter.render(frame)
```

建议模型：

```python
@dataclass(frozen=True)
class StepResult:
    snapshot: GameSnapshot
    events: tuple[GameEvent, ...]
    phase: Phase
    required_input: RequiredInput | None
    game_over: bool

@dataclass(frozen=True)
class RequiredInput:
    kind: InputKind
    player_index: int
    options: tuple[Action, ...] = ()
    candidates: tuple[int, ...] = ()
```

`advance()` 采用中等粒度：

- 所有用户输入点必须停下：等待掷骰、动作选择、拆除目标选择、入狱判决。
- 关键展示点也应停下并返回 frame：骰子结果、玩家移动、落点事件、抽卡、租金支付、破产、回合结束。
- 普通内部计算不必拆成独立 step，避免状态机过碎。

Console 和 TUI 的差异只在 adapter 层：

- Console adapter 渲染 frame 后在终端收集文本输入。
- TUI adapter 渲染 frame 后通过按钮、快捷键、鼠标事件提交输入。
- 测试 adapter 直接传入预设输入并断言 StepResult。

`GameEngine.start()` 可以作为兼容 helper 保留，但内部也应基于 step API 循环实现，不能另写一套规则流程。

### 6.2 Screen 栈

```
App
├── TitleScreen        "终端大富翁" + 开始按钮
├── SetupScreen        选择人数 + 输入名字
└── GameScreen         ← 主游戏画面（本文档描述的布局）
```

### 6.3 回合流程与 UI 同步

每个玩家回合仍然走五阶段，但阶段推进由 `advance()` 返回的 StepResult 驱动：

```
阶段① EFFECT_UPDATE
  ├─ StepResult: TURN_START / JAIL_TICKED 等事件
  ├─ UI: Header 阶段文字更新；中心显示状态说明
  └─ 如果仍在监狱，返回 END 展示点

阶段② DICE_ROLL
  ├─ StepResult.required_input = ROLL_DICE
  ├─ UI: 中心显示 "🎲 按 Enter 掷骰"
  ├─ 玩家按 Enter/Space 或点击 → adapter 提交 RollDiceInput
  ├─ Engine 返回骰子结果展示点
  └─ TUI 可在展示点播放 ~0.3s 骰子动画后继续 advance

阶段③ LANDING
  ├─ Engine 在关键展示点返回 frame：移动、落点、抽卡、租金、破产
  ├─ UI: 中心显示当前展示点描述
  ├─ 移动卡连锁可连续产生多个 LANDING 展示点
  └─ 若触发入狱且有免狱卡，返回 JailChoice RequiredInput

阶段④ ACTION
  ├─ StepResult.required_input = ACTION_CHOICE
  ├─ UI: 底部动作栏出现
  ├─ 玩家选择动作 → adapter 提交 ActionInput
  ├─ 若选择拆除，Engine 返回 DEMOLISH_TARGET RequiredInput
  └─ 执行后返回动作结果展示点，再进入 END

阶段⑤ END
  ├─ StepResult: TURN_END / GAME_OVER 等事件
  ├─ UI: 中心显示回合摘要
  ├─ 检查胜利条件
  └─ adapter 在短暂停留后继续 advance 到下一位玩家
```

### 6.4 AI 回合特殊处理

AI 回合仍通过同一套 step API 推进。区别是 adapter 不等待人类输入，而是由 AI 策略生成输入或由 Engine 内部非阻塞策略生成自动决策。

```
AI 回合开始
  ├─ 横幅 "▶ AI-1 的回合" (0.5s)
  ├─ 每个 StepResult 展示点间隔约 0.3s
  ├─ ACTION_CHOICE / DEMOLISH_TARGET 由 AI 策略立即提交
  ├─ 中心区域描述 AI 当前操作
  ├─ 棋盘、事件日志实时更新
  └─ 回合结束 → 下一个玩家
```

---

## 七、GameScreen 组件树

```
GameScreen
├── Header (Static)
│   └── Text: "第 N 回合 | 轮到 XXX | 阶段: XXX"
│
├── BoardWidget (自定义容器)
│   ├── CellWidget(position) × N  ← 按 tui_layout row/column 放置
│   ├── CenterPanel               ← 固定中心动态区
│   └── CellWidget 点击 → CellClicked(position) 消息
│
├── PlayerStrip (Static)
│   ├── 左侧: 人类玩家私密信息
│   └── 右侧: AI 头像 (可点击 → PlayerInfoToast)
│
├── EventLine (Static + 可点击)
│   ├── 收起: 最新一条事件
│   └── 点击/E → EventLogModal (可滚动)
│
├── ActionBar (Horizontal, 条件渲染)
│   └── Button × N (BUY / UPGRADE / USE_DEMOLISH / SKIP)
│
└── Footer (Static)
    └── Text: "Enter:掷骰 | 1-4:选择动作 | E:事件日志 | Esc:关闭 | Q:退出"
```

### 弹出层 / 临时提示

| 组件 | 类型 | 触发 | 内容 |
|---|---|---|---|
| CellDetailModal | ModalScreen | 点击棋盘格子 | 格子完整信息 |
| EventLogModal | ModalScreen | 点击事件栏 / `E` | 完整事件日志，可滚动 |
| JailChoiceModal | ModalScreen | 入狱判决 | "使用免狱卡" / "接受入狱" 按钮 |
| PlayerInfoToast | toast / popover | 点击 AI 头像 | AI 玩家公开信息 |

---

## 八、与现有模块的关系

```
domain
  ├─ 领域类型、事件、快照、输入/输出数据结构
  └─ 可新增 RequiredInput / EngineInput / StepResult 等纯数据类型

board / rules / player
  ├─ board: 仍只负责空间查询和移动
  ├─ rules: 仍只负责纯规则计算
  └─ player: AI 策略和非 UI 决策逻辑；Human 不再通过阻塞 InputContext 驱动 TUI

engine
  ├─ 唯一持有并修改完整游戏状态
  ├─ 提供统一可步进 advance(input) API
  ├─ 不直接调用 Renderer
  └─ 不阻塞等待终端输入

adapters
  ├─ console: 渲染 StepResult 并收集文本输入
  ├─ textual_tui: 渲染 StepResult 并通过 Textual 事件提交输入
  └─ tests/headless: 直接提交预设输入并断言 StepResult

app / cli
  ├─ richman play: 保留现有 console 入口语义，内部改用 step driver
  └─ richman tui: 新增 Textual 入口，使用 TitleScreen / SetupScreen / GameScreen
```

关键原则：

- 各种渲染方式架构一致：adapter 驱动 Engine，Engine 返回 StepResult。
- Renderer/adapter 不直接修改 `InternalGameState`。
- Engine 不依赖 Textual，也不依赖 console I/O。
- TUI 可以定义自己的 widget view model，但必须从 `GameSnapshot` / `StepResult` 派生。
- 规则不在 TUI 层重复实现；所有购买、升级、租金、破产、入狱等状态变更仍由 Engine 完成。

---

## 九、实现注意事项

1. **Engine step API 是交互地基**。TUI、console、测试都应使用同一套 `advance(input)`，避免 TUI 单独绕私有方法或后台线程驱动旧同步循环。

2. **TUI 布局由配置驱动**。`tui_layout` 负责视觉坐标；`board_cells` 负责游戏路径。两者通过 `position` 对齐。

3. **当前不做缩放**。BoardWidget 按固定格子尺寸计算需要终端尺寸；不足时显示错误页。滚动可作为未来增强。

4. **弹出层互斥**。ModalScreen 同一时间最多一个，新 modal 出现前关闭旧 modal；AI toast 可替换旧 toast。

5. **隐私保护**。事件日志、弹窗、toast 展示时，AI 玩家的私密字段（现金、手牌、投入成本）全部显示为 `已隐藏` 或不展示。

6. **键盘与鼠标双通路**。所有主要交互同时支持键盘和鼠标，不强制用户切换输入方式。

7. **不要在 TUI 重写规则**。动作可用性、拆除候选、入狱选择、破产处理等由 Engine 计算并通过 StepResult 暴露。

---

## 十、实施依赖与验收标准

### 10.1 实施依赖

1. Engine 必须先提供统一 step API，渲染适配器才能一致驱动游戏。
2. Console driver 应先迁移到 step API，验证旧入口行为不变。
3. `tui_layout` schema 和校验完成后，BoardWidget 才能可靠渲染配置化地图。
4. BoardWidget 必须先支持 `position → CellWidget` 映射和点击回传，格子详情、拆除目标选择才能实现。
5. Modal/toast 基础能力完成后，再接事件日志、格子详情、AI 信息和入狱选择。
6. `richman tui` 入口完成后，再接启动画面、设置画面和完整 GameScreen。

### 10.2 验收标准

- Step API 能完整推进一局游戏；现有规则、board、player、app 测试保持通过。
- `richman play` 保留现有语义，内部可改为 step driver。
- 新增 `richman tui` 入口，进入 TitleScreen → SetupScreen → GameScreen。
- `tui_layout` 校验能发现缺失 position、重复 position、越界坐标、格子与中心区重叠。
- 终端尺寸不足时显示明确错误页，包含当前尺寸和需要尺寸。
- BoardWidget 按配置坐标显示所有格子，中心区固定显示动态内容。
- 点击任意 CellWidget 返回正确 position。
- 事件日志展开态按时间正序显示，最新事件在底部，并自动滚底。
- Cell detail、event log、jail choice 使用 ModalScreen，`Esc` 可关闭且 modal 互斥。
- AI 信息使用 toast / popover，不显示现金、手牌、投入成本，并可自动消失或被新 toast 替换。
- 动作栏根据 StepResult.required_input 显示按钮，`1`~`4` 快捷键与按钮顺序一致。
- 拆除卡二步交互只高亮 Engine 返回的候选格；取消后回到动作选择。
- AI 回合通过同一套 step API 自动推进，展示点之间有短暂停留，UI 不阻塞。
