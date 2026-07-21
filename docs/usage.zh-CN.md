# 使用手册 —— 参数详解

[English](usage.md) · [简体中文](usage.zh-CN.md) · [← README](../README.zh-CN.md)

本手册讲每个参数怎么改、改了会发生什么、出错了怎么办。安装步骤见 [安装教程](installation.zh-CN.md)。

## 1. YAML 配置详解

命令行模式改 `box_generator/config.yaml`；网页界面的隔板文本框也能写同样的 YAML。完整字段：

```yaml
box:
  size: [120, 80, 40]          # [长, 宽, 高] mm，长宽必须 ≤ 250（超了直接报错，不会帮你裁剪）
  wall: 2                      # 外墙壁厚 mm
  corner_radius: 8             # 竖直四角圆角半径 mm，0 = 直角
  edge_fillet:
    top: 1                     # 顶口圆角 mm（同时倒外沿+内沿两条棱），上限约 wall/2
    bottom: 1                  # 底面圆角 mm，0 = 直角

partitions:                    # 递归二分隔板树，整段可以是 null（不要隔板）
  split:
    axis: x                    # 沿哪个方向切：x 或 y
    at: 0.5                    # 切割位置：0~1 的比例，或 "30mm" 这种带单位的绝对尺寸
    thickness: 1.5             # 这块隔板的厚度 mm
    height: null               # null = 到顶；填数字 = 隔板矮一截，比如 20 表示只有 20mm 高
  children:
    - split: {axis: y, at: "30mm", thickness: 1.5, height: null}
      children: [null, null]   # 左边那块再横切一刀，切完两块都不再分
    - null                     # 右边那块不再分

hollow:
  hole_size: 8                 # 药丸孔宽度 mm，唯一需要调的镂空参数
  angle: 45                    # 固定 45，改了也会被强制拉回 45（打印免支撑的关键角度）
  border: auto                 # 自动留边框；也可以填数字如 3 指定边框宽度 mm
  faces:
    bottom: true               # 底面要不要镂空
    partitions: true           # 隔板要不要镂空（整体开关，所有隔板一起开/关）

export:
  format: stl
  tolerance: 0.1               # STL 网格精度，越小越精细、文件越大、导出越慢
  filename: box_output.stl
```

### 1.1 取值范围与自动纠错行为

| 字段 | 硬限制（超了报错退出） | 软限制（超了自动钳制+打印警告） |
|---|---|---|
| `box.size[0]` 长 | `> 250mm` 报错 | — |
| `box.size[1]` 宽 | `> 250mm` 报错 | — |
| `box.size[2]` 高 | `> z_max`（默认 250mm）报错 | — |
| `box.wall` | `<= 0` 报错；太厚（`wall*2 >= min(长,宽)`）报错 | — |
| `box.corner_radius` | `< 0` 报错 | 超过 `min(长,宽)/2 * 0.9` 会被钳到这个安全值 |
| `edge_fillet.top` | `< 0` 报错 | 超过 `wall/2 * 0.9` 会被钳住（**注意是壁厚的一半**，原因见 §4.1） |
| `edge_fillet.bottom` | `< 0` 报错 | 超过 `min(高, min(长,宽)/2) * 0.8` 会被钳住 |
| `hollow.hole_size` | `<= 0` 报错 | — |
| `hollow.angle` | — | 强制改回 45，打印警告 |
| `hollow.border` | `< 0` 报错 | `auto` 时取 `max(wall, hole_size*0.5)` |
| `export.tolerance` | `<= 0` 报错 | — |

命令行下硬限制会打印 `[error] ...` 并以非零退出码结束；软限制只在 stderr 打印 `[warn] ...` 后继续。网页界面下硬限制会在页面顶部显示红色错误框。

## 2. 隔板递归树语法

`partitions` 要么是 `null`（整个盒子不要隔板），要么是一个 `{split, children}` 节点：

- `split.axis`：`x`（沿长度方向切，切完左右两半）或 `y`（沿宽度方向切，切完前后两半）
- `split.at`：`0`~`1` 的小数 → 按**比例**切（`0.5` = 正中间）；`"30mm"` 这种带 `mm` 的字符串 → 按**绝对尺寸**切，从该区域自己的起始边算起
- `split.thickness`：这一刀隔板的厚度 mm
- `split.height`：`null` = 顶到盒口；填数字 = 隔板矮一截（从内腔底部往上量）
- `children`：长度固定为 2 的数组，`[第一块的后续, 第二块的后续]`，每项要么 `null`（不再切），要么另一个 `{split, children}` 节点

**关键理解**：切完一刀产生两个子区域后，两块互不干扰，可分别继续细分，也可其中一块不再分——这就是"田字格"和"只切一半"都能做的原因。

**示例 1：十字分四格**

```yaml
partitions:
  split: {axis: x, at: 0.5, thickness: 1.5, height: null}
  children:
    - split: {axis: y, at: 0.5, thickness: 1.5, height: null}
      children: [null, null]
    - split: {axis: y, at: 0.5, thickness: 1.5, height: null}
      children: [null, null]
```

**示例 2：只在左半边加一块矮隔板，右半边不动**

```yaml
partitions:
  split: {axis: x, at: 0.5, thickness: 1.5, height: null}
  children:
    - split: {axis: y, at: 0.4, thickness: 1.5, height: 15}   # 只有15mm高，不到顶
      children: [null, null]
    - null
```

**已知取舍**：递归二分产生的十字格，中间交点不保证完美对齐（左右两侧独立横切，位置可能有细微差异）。这是换取"任意区域独立细分"灵活性的代价；一定要交点对齐的规整网格，需手动算好两侧 `at` 一致。

## 3. 镂空 `hollow` 细节

- **只暴露 `hole_size`**：孔间距、长宽比（药丸长度 = 宽度 × 2.5）都是自动算好的。
- **`angle` 别改**：写死 45° 是为了打印时孔顶能自然收口成拱形、不塌陷、免支撑。改了会被强制拉回 45。
- **外墙永远不镂空**：`hollow.faces` 只能控制 `bottom`（底面）和 `partitions`（隔板），没有外墙选项——这是设计上刻意去掉的。
- **`border` 留边框**：孔阵列贴近边缘会自动裁掉，留一圈实心边框；`auto` 模式边框宽度取 `max(壁厚, 孔径的一半)`。

## 4. 常见问题

### 4.1 顶沿圆角设大一点就建模失败

顶口圆角要同时倒**外沿**和**内沿**两条棱。两个圆角从里外往中间"吃"壁厚，半径接近 `壁厚/2` 时弧面会在薄壁中间相遇，OCCT 内核建不出这种自相交几何，报 `BRep_API: command not done`。程序已把安全上限设到 `wall/2 * 0.9`；手写 YAML 时注意 `edge_fillet.top` 别超过壁厚一半。

### 4.2 改了 `hollow.angle` 没生效

45° 是锁死的值（免支撑打印关键），非 45 会被强制改回并警告，不是 bug。

### 4.3 隔板报错 `does not fit within span`

某个 `split.at` + `thickness/2` 超出了它所在区域范围。检查该节点所在区域的实际可用宽度（上一层切完剩多少），把 `at` 往区域中心调。

### 4.4 网页 3D 预览空白

预览用浏览器端 Three.js（CDN 加载），无法访问 `cdn.jsdelivr.net` 时预览失败，但模型仍正确生成（"外部尺寸/体积/是否合法几何"照常显示），直接下载 STL 即可。

## 5. 网页界面控件对照

| UI 分组 | 控件 | 对应字段 | 备注 |
|---|---|---|---|
| 盒体尺寸 | 长/宽/高/壁厚 | `box.size`, `box.wall` | 长宽滑块上限 250mm，滑不过界 |
| 圆角 | 竖直四角圆角 | `box.corner_radius` | 上限跟随长宽联动 |
| 圆角 | 顶沿圆角 | `edge_fillet.top` | 上限跟随壁厚联动（`wall/2`） |
| 圆角 | 底沿圆角 | `edge_fillet.bottom` | 上限跟随高度/长宽 |
| 隔板 | 快速开始 / 加隔板按钮 / YAML | `partitions` | 点击式加隔板，或直接写 YAML |
| 镂空 | 孔大小 / 边框 / 底面 / 隔板 | `hollow.*` | 边框选"自定义"才出现滑块 |
| 导出 | STL 精度 / 文件名 | `export.*` | — |

右侧主区域：**3D 预览**（左键拖动旋转、滚轮缩放，改参数自动重建）、**统计信息**（外部尺寸/体积/是否合法几何，`OK` 表示可放心导出，`FAIL` 表示当前参数产生了非法几何需调整）、**下载 STL 按钮**。

## 6. 打印建议

- 收纳盒是**顶面开口无盖**设计，打印时开口朝上摆放，无需支撑。
- 底面/隔板的 45° 镂空孔本身免支撑，正常摆放不用单独加支撑。
- 若切片软件仍提示需要支撑，先检查是不是把 `corner_radius`/`edge_fillet` 设得太极端导致意外悬空，而不是默认关掉自动支撑硬打。
