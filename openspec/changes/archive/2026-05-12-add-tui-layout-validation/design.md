## Context

`tui_layout` 数据模型（`TuiCellLayout`、`TuiRect`、`TuiLayout`）已在 domain 层稳定。`GameConfig.tui_layout` 为可选字段，默认配置提供合法布局。自定义 JSON/YAML 配置文件也可以携带 `tui_layout`。

当前没有任何代码在消费 `tui_layout` 之前验证其合法性。BoardWidget 将在下一步接入，它需要可靠的 position→slot 映射。校验层是 BoardWidget 和自定义配置之间的安全边界。

## Goals / Non-Goals

**Goals:**
- 提供纯函数 `validate_tui_layout(config: GameConfig) -> TuiLayoutValidationResult`
- 校验所有必须拒绝的错误条件（缺失布局、非法尺寸、重复/缺失 position、越界、中心区重叠）
- 对视觉不相邻路径给出 warning（不阻塞）
- 校验逻辑不依赖 engine、不修改 game state
- 完整的单元测试覆盖

**Non-Goals:**
- 不实现 BoardWidget 或任何 Textual widget
- 不计算终端尺寸或做尺寸不足检测（属于布局计算层）
- 不修改 `GameConfig` 或 `GameSnapshot`
- 不依赖 Textual、Rich 或终端 I/O

## Decisions

### 决策 1：返回类型使用 errors + warnings 双列表

```python
@dataclass(frozen=True, slots=True)
class TuiLayoutValidationResult:
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
```

- `errors` 非空表示布局不可用，TUI 应拒绝进入游戏并显示错误
- `warnings` 非空不阻塞运行，仅用于提示（如视觉不相邻）
- 不抛异常：校验的目的是收集所有问题，而非在第一个错误处终止

**替代方案**：抛 `ValueError` 并在消息中列出所有错误。被否决，因为结构化返回更便于 TUI 设置页或日志展示。

### 决策 2：校验函数签名

```python
def validate_tui_layout(config: GameConfig) -> TuiLayoutValidationResult:
```

接收整个 `GameConfig` 而非单独的 `TuiLayout`，因为：
- 需要 `config.board_cells` 来验证 position 覆盖
- 可以直接检查 `config.tui_layout is None`

**替代方案**：接收 `(tui_layout, board_cells)`。被否决，因为调用方需要手动拆解 config，增加出错可能。

### 决策 3：文件位置

校验逻辑放在 `src/richman/adapters/textual_tui/layout.py`。

**理由**：校验是 TUI adapter 的边界逻辑。它使用 domain 类型但不属于 domain（domain 不应包含校验逻辑）。也不属于 `board`（`board` 负责游戏路径，不负责视觉坐标）。

## Risks / Trade-offs

- **[风险] 校验规则与后续布局计算层重复**：布局计算也需要一些基本合法性保证（如坐标在范围内） → **缓解**：布局计算层可以在入口处再次调用校验，或假定输入已通过校验
- **[权衡] 视觉相邻性检测阈值硬编码为 2**：不同地图形状可能需要调整 → **缓解**：warning 不阻塞运行，阈值可以在未来配置化
