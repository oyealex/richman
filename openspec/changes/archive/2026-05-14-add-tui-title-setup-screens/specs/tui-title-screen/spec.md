## ADDED Requirements

### Requirement: TitleScreen displays welcome and navigates to SetupScreen

系统 SHALL 提供 `TitleScreen`（Textual `Screen` 子类），展示欢迎画面，用户按键后导航到 `SetupScreen`。

#### Scenario: TitleScreen displays welcome text

- **WHEN** TitleScreen 被 mount
- **THEN** MUST 渲染包含"大富翁"或"Richman"字样的欢迎文字

#### Scenario: TitleScreen displays start hint

- **WHEN** TitleScreen 被 mount
- **THEN** MUST 渲染"按 Enter 开始"或类似的按键提示

#### Scenario: Enter navigates to SetupScreen

- **WHEN** 用户在 TitleScreen 按下 Enter
- **THEN** MUST 推送 `SetupScreen`

#### Scenario: TitleScreen has quit binding

- **WHEN** 用户在 TitleScreen 按下 q
- **THEN** MUST 退出应用

### Requirement: TitleScreen code is isolated in screens package

系统 SHALL 确保 TitleScreen 源码位于 `richman.adapters.textual_tui.screens.title` 模块。

#### Scenario: TitleScreen import path

- **WHEN** 导入 TitleScreen
- **THEN** 导入路径 MUST 为 `richman.adapters.textual_tui.screens.title.TitleScreen`
