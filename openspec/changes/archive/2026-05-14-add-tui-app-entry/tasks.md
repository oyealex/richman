## 1. 新增 CLI tui 子命令

- [x] 1.1 在 `cli.py` 中新增 `tui` Typer 子命令，参数：`--players` / `-p` (int, 2-4, default=2, help="总玩家数（1 人类 + N-1 AI）")、`--seed` (int or None, default=None)、`--config` / `-c` (Path or None, default=None)
- [x] 1.2 `tui` 命令调用 app 层的 `run_tui_game(players_count, seed, config_path)`

## 2. 新增 app 层 TUI 装配函数

- [x] 2.1 在 `app.py` 中新增 `create_tui_players(players_count: int) -> tuple[Player, ...]` 函数：创建 1 个 `HumanPlayer("玩家")` + (players_count - 1) 个 `AIPlayer("AI 1", ...)`
- [x] 2.2 在 `app.py` 中新增 `run_tui_game(players_count, seed, config_path)` 函数：调用 `create_tui_players(players_count)` 创建玩家，调用 `create_engine(config, players, seed=seed)`，创建并 `run()` RichmanTuiApp

## 3. 改造 RichmanTuiApp

- [x] 3.1 `RichmanTuiApp.__init__` 增加可选参数 `engine: GameEngine | None = None` 和 `player_controllers: Sequence[Player] | None = None`
- [x] 3.2 `on_mount()` 中：当 engine 和 player_controllers 都存在时，`await self.push_screen(GameScreen(self._engine, self._config, self._player_controllers))`
- [x] 3.3 engine/player_controllers 为 None 时维持现有行为（静态展示）

## 4. 测试

- [x] 4.1 CLI smoke test：用 Typer `CliRunner` 验证 `richman tui` 命令参数解析正确（默认值、各参数解析），mock `run_tui_game` 避免启动 TUI
- [x] 4.2 App smoke test：验证 `run_tui_game()` 创建的玩家列表含 1 个 HumanPlayer 和 N-1 个 AIPlayer
- [x] 4.3 App smoke test：验证 `run_tui_game()` 创建的 engine 配置正确
- [x] 4.4 App smoke test：通过 monkeypatch `RichmanTuiApp.run` 验证 `run_tui_game()` 不阻塞，传入的 engine/config/players 正确
