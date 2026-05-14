# tui-board-widget (delta)

## Purpose

为 BoardWidget 增加通用的候选格高亮机制（`highlight_positions` reactive），供上层（如 tui-demolish-target-flow）按需驱动。

## ADDED Requirements

### Requirement: BoardWidget accepts highlight positions for candidate cells

系统 SHALL 为 BoardWidget 提供 `highlight_positions: Reactive[frozenset[int]]` reactive 属性，接收需要高亮的 position 集合。watcher 为对应 CellWidget 添加或移除 CSS class `candidate`。

#### Scenario: Setting highlight_positions adds candidate class

- **WHEN** `board.highlight_positions = frozenset({3, 5})`
- **THEN** position 3 和 5 的 CellWidget MUST 添加 CSS class `candidate`
- **AND** 其他 CellWidget MUST NOT 有 `candidate` class

#### Scenario: Updating highlight_positions replaces previous highlights

- **WHEN** `board.highlight_positions` 从 `frozenset({3, 5})` 变为 `frozenset({7})`
- **THEN** position 7 的 CellWidget MUST 有 `candidate` class
- **AND** position 3 和 5 的 CellWidget MUST NOT 有 `candidate` class

#### Scenario: Empty highlight_positions clears all highlights

- **WHEN** `board.highlight_positions = frozenset()`
- **THEN** 所有 CellWidget 的 `candidate` CSS class MUST 被移除

### Requirement: CellWidget renders candidate highlight style

系统 SHALL 为 CellWidget 定义 `candidate` CSS class，以高亮边框样式区分候选格。

#### Scenario: Candidate cell has distinctive border

- **WHEN** CellWidget 拥有 CSS class `candidate`
- **THEN** 该 CellWidget MUST 使用区别于 `current` 的高亮边框样式
- **AND** `candidate` 和 `current` class 可同时存在（玩家站在候选格上时）
