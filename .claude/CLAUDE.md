# 项目说明

**BoxForge — 参数化 3D 收纳盒生成器**

用户填几个参数（尺寸、圆角、递归隔板布局、镂空开关）→ 程序生成一个带圆角、可加递归隔板、可选 45° 免支撑药丸镂空的收纳盒 → 导出 STL 供 3D 打印。打印板 256×256，故长宽硬性上限 250mm。收纳盒顶面开口无盖。

分两种用法，共用同一套建模逻辑：
- **命令行**：改 `config.yaml` → `python main.py` → 导出 STL
- **网页 UI**：`streamlit run app.py` → 浏览器内拖滑块 + 实时 3D 预览 + 下载 STL

## 技术栈
- **Python 3.10~3.13**（本项目在 3.13 验证通过；3.14 装不上 CadQuery 的 OCP 轮子）
- **CadQuery**（基于 OpenCASCADE 真实 B-rep CAD 内核，非 mesh 库）—— 圆角/抽壳/布尔运算/STL 导出
- **PyYAML** —— 读嵌套 YAML 配置
- **Streamlit** —— 网页 UI；3D 预览用 CDN 加载的 Three.js（`STLLoader` + `OrbitControls`），无额外 Python 依赖
- 虚拟环境在项目根 `.venv/`

## 目录结构
```
box_generator/
├── config.yaml            # 命令行模式的默认配置样例（对外接口，见 docs 执行计划 §4）
├── main.py                # 命令行入口：读config → 建模 → 导出；build_from_config() 供 UI 复用
├── box_builder/
│   ├── validate.py         # YAML 校验 + 安全钳制（长宽≤250硬校验、圆角半径几何上限钳制）
│   ├── body.py             # 盒体本体：实心盒 → 竖直角/底沿圆角 → 抽壳 → 顶口内外沿圆角（抽壳后）
│   ├── partitions.py       # 递归二分(BSP)隔板树，产出隔板实体 + 各隔板可镂空面的规格
│   ├── hollow.py           # 45° 药丸孔阵列（自动间距/边框），只作用于底面和隔板，外墙永不镂空
│   └── export.py           # STL 导出
└── app.py                  # 网页 UI 入口：streamlit run app.py
docs/                       # 执行计划（技术方案定稿）+ 使用手册
```

**建模顺序关键约束**（改 body.py 时务必遵守）：竖直角圆角在抽壳前做；顶口内外两条沿棱的圆角必须在抽壳**之后**做（抽壳后内沿棱才存在）。棱边一律按方向/位置筛选，禁止按索引硬编码。


## Git 提交规范
每完成一次需求相关的改动，必须执行一次 git commit。
提交信息格式：feat: <中文介绍更新点>
（如果是修复bug用 fix:，重构用 refactor:等）
禁止把多个不相关需求的改动堆在一次提交里。