// BoxForge 基础版 (MakerWorld Customizer 版) —— 无隔板圆角镂空收纳盒
// ---------------------------------------------------------------------------
// 建模逻辑对齐 Python/CadQuery 版 (box_builder/body.py + hollow.py):
//   实心盒 -> 竖直四角圆角 + 底沿圆角 -> 抽壳(顶面开口) -> 顶口内外沿圆角
//   底面 45° 免支撑药丸镂空阵列 (交错排布, 固定长度独立胶囊)
// 坐标约定: X/Y 居中, 盒体坐落在打印板 Z=0, 顶面开口无盖。
//
// 依赖: BOSL2 (https://github.com/BelfrySCAD/BOSL2)
//   本地渲染前需先安装 BOSL2 到 OpenSCAD 库目录。
//   MakerWorld 平台已内置 BOSL2, 直接上传即可出 Customize 面板。
// ---------------------------------------------------------------------------

include <BOSL2/std.scad>

/* [尺寸 Size] */
length = 120;   // [40:1:250]   长 mm
width  = 80;    // [40:1:250]   宽 mm
height = 40;    // [20:1:250]   高 mm
wall   = 2;     // [1:0.5:5]    壁厚 mm

/* [圆角 Fillet] */
corner_radius = 8;  // [0:1:30]    竖直四角圆角半径 mm (0=直角)
top_fillet    = 1;  // [0:0.5:5]   顶沿圆角半径 mm
bottom_fillet = 1;  // [0:0.5:5]   底沿圆角半径 mm

/* [镂空 Hollow] */
hollow_bottom = true;   // 底面镂空开关
hole_size     = 8;      // [4:1:20]  药丸孔宽度 mm

/* [Hidden] */
$fa = 2;
$fs = 0.4;
EPS = 0.01;

// --- 安全钳制 (对齐 validate.py 的硬校验 / 几何上限) ------------------------
_min_lw = min(length, width);

assert(length <= 250 && width <= 250, "长/宽必须 <= 250mm (适配 256x256 打印板)");
assert(wall * 2 < _min_lw,            "壁厚过大: wall*2 必须 < min(长,宽)");
assert(wall < height,                 "壁厚不得超过盒高");

// 圆角半径几何钳制 (与 validate.py 一致)
cr = min(corner_radius, _min_lw / 2 * 0.9);              // 竖直角上限
tf = min(top_fillet,    wall / 2 * 0.9);                 // 顶沿: 内外两侧对咬, 上限 wall/2
bf = min(bottom_fillet, min(height, _min_lw / 2) * 0.8); // 底沿

// --- 药丸镂空参数 (对齐 hollow.py) ------------------------------------------
PILL_RATIO = 2.5;                       // 药丸长 = hole_size * 2.5
HOLLOW_ANGLE = 45;                      // 固定 45° 免支撑
pill_len      = hole_size * PILL_RATIO;
_gap          = max(hole_size * 0.4, 0.8);   // 相邻药丸最小桥壁
spacing_axial = pill_len + _gap;             // 沿长轴: 全长 + 桥, 保持独立胶囊
spacing_perp  = hole_size + _gap;            // 沿短轴: 宽 + 桥
border        = max(wall, hole_size * 0.5);  // auto 边框

// ===========================================================================
// 盒体本体
// ===========================================================================
// 用 rounded_prism 一次成型: 2D 圆角矩形截面 -> 竖直角圆角(cr);
// joint_bot/joint_top -> 底沿/顶沿圆角。抽壳 = 外壳减内腔。
module body() {
    difference() {
        // 外壳
        rounded_prism(
            rect([length, width], rounding = cr),
            height = height,
            joint_bot = bf, joint_top = tf,
            anchor = BOTTOM
        );
        // 内腔: 向内缩壁厚, 底抬升壁厚留出底板, 顶端正好在 height 处并做顶沿圆角
        // -> 相减后即得开口 + 顶口内沿圆角 + 内底沿圆角。
        up(wall)
        rounded_prism(
            rect([length - 2 * wall, width - 2 * wall],
                 rounding = max(cr - wall, 0)),
            height = height - wall,
            joint_bot = max(bf - wall, 0), joint_top = tf,
            anchor = BOTTOM
        );
    }
}

// ===========================================================================
// 底面 45° 药丸镂空
// ===========================================================================
// 单个药丸 (2D): 两端半圆 + 中间矩形, 即 slot。
module pill2d(len, w) {
    hull() {
        translate([-(len - w) / 2, 0]) circle(d = w);
        translate([ (len - w) / 2, 0]) circle(d = w);
    }
}

// 底板可镂空区: 内腔矩形再内缩 border, 交错网格铺满后与该矩形求交(裁边)。
module bottom_holes_2d() {
    ix0 = -(length / 2 - wall) + border;
    ix1 =  (length / 2 - wall) - border;
    iy0 = -(width  / 2 - wall) + border;
    iy1 =  (width  / 2 - wall) - border;

    if (ix1 > ix0 && iy1 > iy0) {
        cu = (ix0 + ix1) / 2;
        cv = (iy0 + iy1) / 2;
        dx = ix1 - ix0;
        dy = iy1 - iy0;
        diag = sqrt(dx * dx + dy * dy);
        na = floor(diag / (2 * spacing_axial)) + 2;
        np = floor(diag / (2 * spacing_perp)) + 2;
        C = cos(HOLLOW_ANGLE);
        S = sin(HOLLOW_ANGLE);

        intersection() {
            union() {
                for (j = [-np : np]) {
                    q  = j * spacing_perp;
                    ro = (j % 2 != 0) ? spacing_axial / 2 : 0;   // 交错: 隔行错半格
                    for (i = [-na : na]) {
                        p = i * spacing_axial + ro;
                        u = cu + p * C - q * S;
                        v = cv + p * S + q * C;
                        translate([u, v])
                            rotate(HOLLOW_ANGLE)
                                pill2d(pill_len, hole_size);
                    }
                }
            }
            // 裁到 border 内框, 越界药丸被切成局部胶囊(与参考设计一致)
            translate([cu, cv]) square([dx, dy], center = true);
        }
    }
}

// ===========================================================================
// 组装
// ===========================================================================
difference() {
    body();
    if (hollow_bottom)
        translate([0, 0, -EPS])
            linear_extrude(height = wall + 2 * EPS)
                bottom_holes_2d();
}
