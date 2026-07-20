"""graph_viz.py：急腹症知识图谱稳定版。

不依赖 networkx / pyvis，只依赖浏览器端 vis-network CDN。
保留原项目接口：build_full_graph、build_disease_subgraph、
render_graph_html、render_comparison_graph。
"""
from __future__ import annotations

from dataclasses import dataclass, field
import html
import json
from typing import Any, Dict, List, Optional, Tuple


STYLE = {
    "disease": (
        "疾病",
        "#2563EB",
        "#1D4ED8",
        "#FFFFFF",
        "#2563EB",
        3.0,
        False,
    ),
    "core": (
        "核心证据",
        "#DCFCE7",
        "#16A34A",
        "#14532D",
        "#22C55E",
        3.2,
        False,
    ),
    "supportive": (
        "支持证据",
        "#EFF6FF",
        "#60A5FA",
        "#1E3A8A",
        "#93C5FD",
        1.8,
        False,
    ),
    "opposing": (
        "反向证据",
        "#FEF2F2",
        "#EF4444",
        "#7F1D1D",
        "#F87171",
        2.0,
        [7, 6],
    ),
    "shared": (
        "共享证据",
        "#F3E8FF",
        "#9333EA",
        "#581C87",
        "#A855F7",
        2.6,
        False,
    ),
    "mixed": (
        "多重关系",
        "#FFF7ED",
        "#F59E0B",
        "#7C2D12",
        "#F59E0B",
        2.4,
        False,
    ),
}

ORDER = {
    "core": 0,
    "supportive": 1,
    "opposing": 2,
}

FONT = (
    "Microsoft YaHei, PingFang SC, "
    "Noto Sans CJK SC, Arial"
)


@dataclass
class SimpleDiGraph:
    """轻量有向图对象。"""

    nodes_data: Dict[str, Dict[str, Any]] = field(
        default_factory=dict
    )
    edges_data: Dict[
        Tuple[str, str],
        Dict[str, Any],
    ] = field(default_factory=dict)
    graph: Dict[str, Any] = field(default_factory=dict)

    def add_node(
        self,
        node_id: str,
        **attrs: Any,
    ) -> None:
        self.nodes_data.setdefault(
            node_id,
            {},
        ).update(attrs)

    def add_edge(
        self,
        source: str,
        target: str,
        **attrs: Any,
    ) -> None:
        self.edges_data[(source, target)] = attrs

    def has_node(
        self,
        node_id: str,
    ) -> bool:
        return node_id in self.nodes_data

    def number_of_nodes(self) -> int:
        return len(self.nodes_data)

    def number_of_edges(self) -> int:
        return len(self.edges_data)

    def nodes(
        self,
        data: bool = False,
    ):
        if data:
            return list(self.nodes_data.items())

        return list(self.nodes_data)

    def edges(
        self,
        data: bool = False,
    ):
        if data:
            return [
                (source, target, attrs)
                for (
                    source,
                    target,
                ), attrs in self.edges_data.items()
            ]

        return list(self.edges_data)


def _groups(
    info: Dict,
) -> Dict[str, Dict[str, int]]:
    """提取三种证据类型。"""

    return {
        category: {
            str(name): int(weight)
            for name, weight in dict(
                info.get(category, {}) or {}
            ).items()
        }
        for category in (
            "core",
            "supportive",
            "opposing",
        )
    }


def _emap(
    info: Dict,
) -> Dict[str, Tuple[str, int]]:
    """把疾病证据转换为证据映射。"""

    result: Dict[
        str,
        Tuple[str, int],
    ] = {}

    for category, items in _groups(info).items():
        for name, weight in items.items():
            result[name] = (
                category,
                weight,
            )

    return result


def _wrap(
    text: str,
    length: int,
) -> str:
    """长中文自动换行。"""

    text = str(text).strip()

    return "\n".join(
        text[index:index + length]
        for index in range(
            0,
            len(text),
            length,
        )
    )


def _node(
    node_id: str,
    label: str,
    category: str,
    weight: Optional[int] = None,
    **position: Any,
) -> Dict[str, Any]:
    """创建节点数据。"""

    (
        category_name,
        background,
        border,
        font_color,
        _,
        _,
        _,
    ) = STYLE[category]

    is_disease = category == "disease"

    title = [
        f"<b>{html.escape(label)}</b>",
        f"类型：{category_name}",
    ]

    if weight is not None:
        sign = (
            "−"
            if category == "opposing"
            else "+"
        )

        title.append(
            f"权重：{sign}{abs(weight)}"
        )

    result: Dict[str, Any] = {
        "id": node_id,
        "label": _wrap(
            label,
            10 if is_disease else 13,
        ),
        "shape": (
            "ellipse"
            if is_disease
            else "box"
        ),
        "color": {
            "background": background,
            "border": border,
            "highlight": {
                "background": background,
                "border": "#0F172A",
            },
            "hover": {
                "background": background,
                "border": "#334155",
            },
        },
        "borderWidth": (
            3 if is_disease else 2
        ),
        "font": {
            "size": (
                17 if is_disease else 13
            ),
            "color": font_color,
            "face": FONT,
        },
        "margin": (
            16
            if is_disease
            else {
                "top": 9,
                "right": 12,
                "bottom": 9,
                "left": 12,
            }
        ),
        "shadow": {
            "enabled": True,
            "color": "rgba(15,23,42,.12)",
            "size": 8,
            "x": 0,
            "y": 3,
        },
        "title": "<br>".join(title),
    }

    result.update(position)

    return result


def _edge(
    source: str,
    target: str,
    category: str,
    weight: int,
    color: Optional[str] = None,
) -> Dict[str, Any]:
    """创建连线数据。"""

    (
        category_name,
        _,
        border,
        _,
        default_color,
        width,
        dashes,
    ) = STYLE[category]

    edge_color = color or default_color

    sign = (
        "−"
        if category == "opposing"
        else "+"
    )

    return {
        "from": source,
        "to": target,
        "label": (
            f"{sign}{abs(weight)}"
        ),
        "width": width,
        "dashes": dashes,
        "color": {
            "color": edge_color,
            "highlight": edge_color,
            "hover": edge_color,
        },
        "arrows": {
            "to": {
                "enabled": True,
                "scaleFactor": 0.55,
            }
        },
        "font": {
            "size": 11,
            "color": border,
            "face": "Arial",
            "strokeWidth": 4,
            "strokeColor": "#FFFFFF",
        },
        "title": (
            f"{category_name}，"
            f"权重 {sign}{abs(weight)}"
        ),
    }


def build_full_graph(
    knowledge_base: Dict[str, Dict],
) -> SimpleDiGraph:
    """构建完整知识图谱。"""

    graph = SimpleDiGraph(
        graph={
            "layout": "full",
            "title": "完整知识图谱",
        }
    )

    roles: Dict[str, set] = {}
    max_weight: Dict[str, int] = {}

    for info in knowledge_base.values():
        for (
            category,
            items,
        ) in _groups(info).items():
            for evidence, weight in items.items():
                roles.setdefault(
                    evidence,
                    set(),
                ).add(category)

                max_weight[evidence] = max(
                    max_weight.get(
                        evidence,
                        0,
                    ),
                    abs(weight),
                )

    for (
        disease,
        info,
    ) in knowledge_base.items():
        disease = str(disease)

        disease_id = (
            f"disease:{disease}"
        )

        graph.add_node(
            disease_id,
            **_node(
                disease_id,
                disease,
                "disease",
            ),
        )

        for (
            category,
            items,
        ) in _groups(info).items():
            for evidence, weight in items.items():
                evidence_id = (
                    f"evidence:{evidence}"
                )

                display_category = (
                    category
                    if len(roles[evidence]) == 1
                    else "mixed"
                )

                if not graph.has_node(
                    evidence_id
                ):
                    graph.add_node(
                        evidence_id,
                        **_node(
                            evidence_id,
                            evidence,
                            display_category,
                            max_weight[evidence],
                        ),
                    )

                graph.add_edge(
                    disease_id,
                    evidence_id,
                    **_edge(
                        disease_id,
                        evidence_id,
                        category,
                        weight,
                    ),
                )

    return graph


def build_disease_subgraph(
    knowledge_base: Dict[str, Dict],
    disease_name: str,
) -> Optional[SimpleDiGraph]:
    """构建单个疾病证据网络。"""

    if disease_name not in knowledge_base:
        return None

    graph = SimpleDiGraph(
        graph={
            "layout": "single",
            "title": disease_name,
        }
    )

    disease_id = (
        f"disease:{disease_name}"
    )

    graph.add_node(
        disease_id,
        **_node(
            disease_id,
            disease_name,
            "disease",
            level=0,
        ),
    )

    for category in (
        "core",
        "supportive",
        "opposing",
    ):
        items = sorted(
            dict(
                knowledge_base[
                    disease_name
                ].get(
                    category,
                    {},
                ) or {}
            ).items(),
            key=lambda item: (
                -abs(int(item[1])),
                str(item[0]),
            ),
        )

        for evidence, weight in items:
            evidence = str(evidence)
            weight = int(weight)

            evidence_id = (
                f"evidence:{evidence}"
            )

            graph.add_node(
                evidence_id,
                **_node(
                    evidence_id,
                    evidence,
                    category,
                    weight,
                    level=1,
                ),
            )

            graph.add_edge(
                disease_id,
                evidence_id,
                **_edge(
                    disease_id,
                    evidence_id,
                    category,
                    weight,
                ),
            )

    return graph


def _json(
    value: Any,
) -> str:
    """安全生成 JavaScript JSON。"""

    return json.dumps(
        value,
        ensure_ascii=False,
    ).replace(
        "</",
        "<\\/",
    )


def _legend(
    title: str,
) -> str:
    """生成顶部图例。"""

    items = [
        ("#2563EB", "疾病"),
        ("#16A34A", "核心"),
        ("#60A5FA", "支持"),
        ("#EF4444", "反向"),
        ("#9333EA", "共享"),
        ("#F59E0B", "多重关系"),
    ]

    chips = "".join(
        (
            '<span>'
            f'<i style="background:{color}"></i>'
            f"{label}"
            "</span>"
        )
        for color, label in items
    )

    return (
        '<div class="bar">'
        f"<b>{html.escape(title)}</b>"
        f'<div class="legend">{chips}</div>'
        '<div class="actions">'
        '<button id="fit">适配画布</button>'
        '<button id="reset">重置视图</button>'
        "</div>"
        "</div>"
    )


def _render(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    options: Dict[str, Any],
    title: str,
    height: str,
    width: str,
    freeze: bool,
) -> str:
    """生成完整的知识图谱 HTML。"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<link
    rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css"
>

<script
    src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"
></script>

<style>
* {{
    box-sizing: border-box;
}}

html,
body {{
    width: 100%;
    height: 100%;
    margin: 0;
    overflow: hidden;
    background: #f8fafc;
    font-family: {FONT};
}}

.shell {{
    width: {width};
    height: {height};
    min-height: 380px;
    position: relative;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    background: #ffffff;
    box-shadow:
        0 7px 24px
        rgba(15, 23, 42, 0.06);
}}

.bar {{
    position: absolute;
    z-index: 20;
    top: 10px;
    left: 12px;
    right: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    padding: 8px 10px;
    border: 1px solid #e2e8f0;
    border-radius: 11px;
    background:
        rgba(255, 255, 255, 0.94);
    box-shadow:
        0 5px 18px
        rgba(15, 23, 42, 0.07);
}}

.bar b {{
    font-size: 14px;
    color: #0f172a;
}}

.legend {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}

.legend span {{
    font-size: 11px;
    color: #475569;
}}

.legend i {{
    display: inline-block;
    width: 9px;
    height: 9px;
    margin-right: 4px;
    border-radius: 3px;
}}

.actions {{
    margin-left: auto;
    display: flex;
    gap: 6px;
}}

button {{
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 4px 8px;
    background: #ffffff;
    color: #334155;
    font-size: 11px;
    cursor: pointer;
}}

button:hover {{
    background: #f1f5f9;
}}

#net {{
    width: 100%;
    height: 100%;
    background:
        radial-gradient(
            circle at 50% 48%,
            rgba(219, 234, 254, 0.5),
            transparent 42%
        ),
        linear-gradient(
            180deg,
            #ffffff,
            #f8fafc
        );
}}

#loading {{
    position: absolute;
    z-index: 15;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    font-size: 13px;
    pointer-events: none;
}}

.hint {{
    position: absolute;
    z-index: 10;
    right: 14px;
    bottom: 10px;
    padding: 4px 7px;
    border-radius: 7px;
    background:
        rgba(255, 255, 255, 0.84);
    color: #64748b;
    font-size: 10px;
}}
</style>
</head>

<body>
<div class="shell">
    {_legend(title)}

    <div id="loading">
        正在生成知识图谱…
    </div>

    <div id="net"></div>

    <div class="hint">
        拖拽节点 · 滚轮缩放 · 悬停查看详情
    </div>
</div>

<script>
(function () {{
    const loading =
        document.getElementById("loading");

    if (
        !window.vis ||
        !window.vis.Network
    ) {{
        loading.textContent =
            "图谱脚本加载失败，请检查网络后刷新页面。";

        loading.style.color =
            "#b91c1c";

        return;
    }}

    const data = {{
        nodes: new vis.DataSet(
            {_json(nodes)}
        ),
        edges: new vis.DataSet(
            {_json(edges)}
        )
    }};

    const network =
        new vis.Network(
            document.getElementById("net"),
            data,
            {_json(options)}
        );

    function fit(animated) {{
        network.fit({{
            animation: animated
                ? {{
                    duration: 420,
                    easingFunction:
                        "easeInOutQuad"
                }}
                : false
        }});
    }}

    function finishLoading() {{
        loading.style.display =
            "none";
    }}

    network.once(
        "afterDrawing",
        function () {{
            setTimeout(
                function () {{
                    fit(false);
                    finishLoading();
                }},
                100
            );
        }}
    );

    network.once(
        "stabilizationIterationsDone",
        function () {{
            if ({_json(freeze)}) {{
                network.setOptions({{
                    physics: {{
                        enabled: false
                    }}
                }});
            }}

            fit(true);
            finishLoading();
        }}
    );

    document
        .getElementById("fit")
        .onclick = function () {{
            fit(true);
        }};

    document
        .getElementById("reset")
        .onclick = function () {{
            network.moveTo({{
                position: {{
                    x: 0,
                    y: 0
                }},
                scale: 1,
                animation: {{
                    duration: 350,
                    easingFunction:
                        "easeInOutQuad"
                }}
            }});
        }};
}})();
</script>
</body>
</html>
"""


def render_graph_html(
    graph: SimpleDiGraph,
    height: str = "620px",
    width: str = "100%",
) -> str:
    """渲染完整图或单疾病图。"""

    if graph is None:
        raise ValueError(
            "图对象为 None，请检查疾病名称。"
        )

    if not isinstance(
        graph,
        SimpleDiGraph,
    ):
        raise TypeError(
            "请传入 build_full_graph() 或 "
            "build_disease_subgraph() 的返回值。"
        )

    single = (
        graph.graph.get("layout")
        == "single"
    )

    options: Dict[str, Any] = {
        "autoResize": True,
        "nodes": {
            "chosen": True,
            "widthConstraint": {
                "maximum": 220
            },
        },
        "edges": {
            "chosen": True,
            "smooth": {
                "enabled": True,
                "type": (
                    "cubicBezier"
                    if single
                    else "dynamic"
                ),
                "roundness": 0.2,
            },
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 100,
            "navigationButtons": True,
            "keyboard": True,
            "hideEdgesOnDrag": True,
            "zoomView": True,
            "dragView": True,
        },
    }

    if single:
        options.update({
            "physics": {
                "enabled": False
            },
            "layout": {
                "hierarchical": {
                    "enabled": True,
                    "direction": "LR",
                    "sortMethod": "directed",
                    "levelSeparation": 320,
                    "nodeSpacing": 105,
                    "treeSpacing": 170,
                    "blockShifting": True,
                    "edgeMinimization": True,
                    "parentCentralization": True,
                }
            },
        })

    else:
        options.update({
            "physics": {
                "enabled": True,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                    "gravitationalConstant": -76,
                    "centralGravity": 0.008,
                    "springLength": 190,
                    "springConstant": 0.055,
                    "damping": 0.46,
                    "avoidOverlap": 0.82,
                },
                "stabilization": {
                    "enabled": True,
                    "iterations": 650,
                    "fit": True,
                },
                "minVelocity": 0.55,
                "maxVelocity": 30,
            },
        })

    nodes = [
        dict(attrs)
        for _, attrs
        in graph.nodes(data=True)
    ]

    edges = [
        dict(attrs)
        for _, _, attrs
        in graph.edges(data=True)
    ]

    return _render(
        nodes=nodes,
        edges=edges,
        options=options,
        title=str(
            graph.graph.get(
                "title",
                "急腹症知识图谱",
            )
        ),
        height=height,
        width=width,
        freeze=not single,
    )


def _ys(
    count: int,
    height: int,
) -> List[int]:
    """计算对比图纵向位置。"""

    if count <= 0:
        return []

    if count == 1:
        return [0]

    gap = min(
        90,
        max(
            58,
            (height - 180)
            // (count - 1),
        ),
    )

    start = (
        -(gap * (count - 1))
        / 2
    )

    return [
        round(start + index * gap)
        for index in range(count)
    ]


def render_comparison_graph(
    knowledge_base: Dict[str, Dict],
    disease1: str,
    disease2: str,
    height: str = "700px",
    width: str = "100%",
) -> Optional[str]:
    """生成两个疾病的鉴别诊断图。"""

    if (
        disease1 not in knowledge_base
        or disease2 not in knowledge_base
    ):
        return None

    if disease1 == disease2:
        graph = build_disease_subgraph(
            knowledge_base,
            disease1,
        )

        if graph is None:
            return None

        return render_graph_html(
            graph,
            height,
            width,
        )

    map1 = _emap(
        knowledge_base[disease1]
    )

    map2 = _emap(
        knowledge_base[disease2]
    )

    shared = sorted(
        set(map1) & set(map2),
        key=lambda evidence: -max(
            abs(map1[evidence][1]),
            abs(map2[evidence][1]),
        ),
    )

    only1 = sorted(
        set(map1) - set(map2),
        key=lambda evidence: (
            ORDER.get(
                map1[evidence][0],
                9,
            ),
            -abs(map1[evidence][1]),
            evidence,
        ),
    )

    only2 = sorted(
        set(map2) - set(map1),
        key=lambda evidence: (
            ORDER.get(
                map2[evidence][0],
                9,
            ),
            -abs(map2[evidence][1]),
            evidence,
        ),
    )

    try:
        canvas_height = max(
            380,
            int(
                float(
                    height.lower()
                    .replace(
                        "px",
                        "",
                    )
                    .strip()
                )
            ),
        )

    except ValueError:
        canvas_height = 700

    graph = SimpleDiGraph()

    left_id = (
        f"disease:{disease1}"
    )

    right_id = (
        f"disease:{disease2}"
    )

    graph.add_node(
        left_id,
        **_node(
            left_id,
            disease1,
            "disease",
            x=-650,
            y=0,
            fixed=True,
            physics=False,
        ),
    )

    graph.add_node(
        right_id,
        **_node(
            right_id,
            disease2,
            "disease",
            x=650,
            y=0,
            fixed=True,
            physics=False,
        ),
    )

    for evidence, y in zip(
        only1,
        _ys(
            len(only1),
            canvas_height,
        ),
    ):
        category, weight = (
            map1[evidence]
        )

        node_id = (
            f"left:{evidence}"
        )

        graph.add_node(
            node_id,
            **_node(
                node_id,
                evidence,
                category,
                weight,
                x=-330,
                y=y,
                fixed=True,
                physics=False,
            ),
        )

        graph.add_edge(
            left_id,
            node_id,
            **_edge(
                left_id,
                node_id,
                category,
                weight,
            ),
        )

    for evidence, y in zip(
        only2,
        _ys(
            len(only2),
            canvas_height,
        ),
    ):
        category, weight = (
            map2[evidence]
        )

        node_id = (
            f"right:{evidence}"
        )

        graph.add_node(
            node_id,
            **_node(
                node_id,
                evidence,
                category,
                weight,
                x=330,
                y=y,
                fixed=True,
                physics=False,
            ),
        )

        graph.add_edge(
            right_id,
            node_id,
            **_edge(
                right_id,
                node_id,
                category,
                weight,
            ),
        )

    for evidence, y in zip(
        shared,
        _ys(
            len(shared),
            canvas_height,
        ),
    ):
        cat1, weight1 = (
            map1[evidence]
        )

        cat2, weight2 = (
            map2[evidence]
        )

        node_id = (
            f"shared:{evidence}"
        )

        shared_node = _node(
            node_id,
            evidence,
            "shared",
            max(
                abs(weight1),
                abs(weight2),
            ),
            x=0,
            y=y,
            fixed=True,
            physics=False,
        )

        shared_node["title"] = (
            f"<b>{html.escape(evidence)}</b>"
            "<br>共享证据"
            f"<br>{html.escape(disease1)}："
            f"{STYLE[cat1][0]}，权重 {weight1}"
            f"<br>{html.escape(disease2)}："
            f"{STYLE[cat2][0]}，权重 {weight2}"
        )

        graph.add_node(
            node_id,
            **shared_node,
        )

        purple = (
            STYLE["shared"][4]
        )

        graph.add_edge(
            left_id,
            node_id,
            **_edge(
                left_id,
                node_id,
                cat1,
                weight1,
                purple,
            ),
        )

        graph.add_edge(
            right_id,
            node_id,
            **_edge(
                right_id,
                node_id,
                cat2,
                weight2,
                purple,
            ),
        )

    options = {
        "autoResize": True,
        "physics": {
            "enabled": False
        },
        "nodes": {
            "chosen": True,
            "widthConstraint": {
                "maximum": 220
            },
        },
        "edges": {
            "chosen": True,
            "smooth": {
                "enabled": True,
                "type": "cubicBezier",
                "roundness": 0.18,
            },
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 100,
            "navigationButtons": True,
            "keyboard": True,
            "hideEdgesOnDrag": True,
            "zoomView": True,
            "dragView": True,
        },
    }

    nodes = [
        dict(attrs)
        for _, attrs
        in graph.nodes(data=True)
    ]

    edges = [
        dict(attrs)
        for _, _, attrs
        in graph.edges(data=True)
    ]

    return _render(
        nodes=nodes,
        edges=edges,
        options=options,
        title=(
            f"鉴别诊断："
            f"{disease1} vs {disease2}"
        ),
        height=height,
        width=width,
        freeze=False,
    )


if __name__ == "__main__":
    demo = {
        "急性阑尾炎": {
            "core": {
                "转移性右下腹痛": 24,
                "麦氏点压痛": 20,
            },
            "supportive": {
                "右下腹痛": 8,
                "发热": 5,
                "恶心、呕吐": 4,
            },
            "opposing": {
                "血尿": 5,
            },
        },
        "右侧输尿管结石": {
            "core": {
                "阵发性绞痛": 18,
                "血尿": 22,
            },
            "supportive": {
                "腰部或侧腹部疼痛": 9,
                "恶心、呕吐": 4,
            },
            "opposing": {
                "麦氏点压痛": 4,
            },
        },
    }

    demo_graph = build_full_graph(
        demo
    )

    with open(
        "knowledge_graph_demo.html",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            render_graph_html(
                demo_graph
            )
        )

    comparison_html = (
        render_comparison_graph(
            demo,
            "急性阑尾炎",
            "右侧输尿管结石",
        )
    )

    with open(
        "knowledge_graph_compare_demo.html",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(
            comparison_html or ""
        )

    print(
        f"测试通过："
        f"{demo_graph.number_of_nodes()} 个节点，"
        f"{demo_graph.number_of_edges()} 条边"
    )
