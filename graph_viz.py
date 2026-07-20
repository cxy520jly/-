"""
graph_viz.py — 急腹症知识图谱可视化模块
===========================================
依赖：networkx, pyvis
用法：将 KNOWLEDGE_BASE 字典传入对应函数即可获得可交互 HTML 图。
"""

from __future__ import annotations

from typing import Dict, Optional

import networkx as nx
from pyvis.network import Network


# ──────────────────────────────────────────────────────────────
# 内部常量
# ──────────────────────────────────────────────────────────────

# 疾病节点样式
_DISEASE_SHAPE = "dot"            # pyvis shape: 圆形
_DISEASE_COLOR = "#4A90D9"       # 蓝色
_DISEASE_SIZE = 45               # 较大
_DISEASE_BORDER = "#2A6DB5"

# 证据节点样式 — 按类别
_EVIDENCE_STYLES: Dict[str, Dict] = {
    "core": {
        "shape": "square",
        "color": "#2ECC71",        # 绿色
        "size": 28,
        "border": "#1F9D55",
        "edge_color": "#2ECC71",
        "edge_width": 4,           # 粗实线
        "edge_dashes": False,
    },
    "supportive": {
        "shape": "square",
        "color": "#A8E6CF",        # 浅绿
        "size": 22,
        "border": "#7BC8A4",
        "edge_color": "#94D3B4",
        "edge_width": 2,           # 细实线
        "edge_dashes": False,
    },
    "opposing": {
        "shape": "square",
        "color": "#E74C3C",        # 红色
        "size": 22,
        "border": "#C0392B",
        "edge_color": "#E74C3C",
        "edge_width": 2,           # 红色虚线
        "edge_dashes": True,
    },
}

# 鉴别诊断中共享证据的颜色
_SHARED_COLOR = "#9B59B6"          # 紫色
_SHARED_BORDER = "#7D3C98"


# ──────────────────────────────────────────────────────────────
# 辅助：收集某疾病的所有证据
# ──────────────────────────────────────────────────────────────

def _collect_evidence(info: Dict) -> Dict[str, Dict[str, int]]:
    """从一条 KNOWLEDGE_BASE 条目中取出三类证据。

    Returns
    -------
    {"类别": {证据名: 权重}, ...}
    类别为 "core" / "supportive" / "opposing"
    """
    return {
        "core": dict(info.get("core", {})),
        "supportive": dict(info.get("supportive", {})),
        "opposing": dict(info.get("opposing", {})),
    }


# ──────────────────────────────────────────────────────────────
# 1. 全量图
# ──────────────────────────────────────────────────────────────

def build_full_graph(knowledge_base: Dict[str, Dict]) -> nx.DiGraph:
    """基于整个知识库构建有向图。

    疾病节点：蓝色圆形，较大。
    证据节点：
      - core      → 绿色方形
      - supportive → 浅绿方形
      - opposing  → 红色方形
    边：
      - core      → 粗实线
      - supportive → 细实线
      - opposing  → 红色虚线
    边标签显示权重。

    Returns
    -------
    nx.DiGraph
    """
    G = nx.DiGraph()

    for disease_name, info in knowledge_base.items():
        disease_id = f"disease:{disease_name}"

        # 疾病节点
        G.add_node(
            disease_id,
            label=disease_name,
            node_type="disease",
            shape=_DISEASE_SHAPE,
            color=_DISEASE_COLOR,
            size=_DISEASE_SIZE,
            borderWidth=3,
            borderColor=_DISEASE_BORDER,
            font={"size": 16, "color": "#FFFFFF", "face": "Microsoft YaHei"},
        )

        # 遍历三类证据
        for category in ("core", "supportive", "opposing"):
            cat_info = knowledge_base[disease_name].get(category, {})
            style = _EVIDENCE_STYLES[category]

            for evidence_name, weight in cat_info.items():
                evidence_id = f"evidence:{evidence_name}"

                # 证据节点（幂等：同一证据只建一个节点）
                if not G.has_node(evidence_id):
                    G.add_node(
                        evidence_id,
                        label=evidence_name,
                        node_type="evidence",
                        category=category,
                        shape=style["shape"],
                        color=style["color"],
                        size=style["size"],
                        borderWidth=2,
                        borderColor=style["border"],
                        font={"size": 13, "color": "#222222", "face": "Microsoft YaHei"},
                    )

                # 边：疾病 → 证据
                G.add_edge(
                    disease_id,
                    evidence_id,
                    label=str(weight),
                    category=category,
                    weight=weight,
                    color=style["edge_color"],
                    width=style["edge_width"],
                    dashes=style["edge_dashes"],
                    font={"size": 12, "color": style["edge_color"], "face": "Arial"},
                )

    return G


# ──────────────────────────────────────────────────────────────
# 2. 单疾病子图
# ──────────────────────────────────────────────────────────────

def build_disease_subgraph(
    knowledge_base: Dict[str, Dict],
    disease_name: str,
) -> Optional[nx.DiGraph]:
    """提取指定疾病及其直接关联的所有证据节点。

    Returns
    -------
    nx.DiGraph 或 None（疾病不存在时）
    """
    if disease_name not in knowledge_base:
        return None

    info = knowledge_base[disease_name]
    G = nx.DiGraph()

    disease_id = f"disease:{disease_name}"
    G.add_node(
        disease_id,
        label=disease_name,
        node_type="disease",
        shape=_DISEASE_SHAPE,
        color=_DISEASE_COLOR,
        size=_DISEASE_SIZE,
        borderWidth=3,
        borderColor=_DISEASE_BORDER,
        font={"size": 16, "color": "#FFFFFF", "face": "Microsoft YaHei"},
    )

    for category in ("core", "supportive", "opposing"):
        cat_info = info.get(category, {})
        style = _EVIDENCE_STYLES[category]

        for evidence_name, weight in cat_info.items():
            evidence_id = f"evidence:{evidence_name}"

            G.add_node(
                evidence_id,
                label=evidence_name,
                node_type="evidence",
                category=category,
                shape=style["shape"],
                color=style["color"],
                size=style["size"],
                borderWidth=2,
                borderColor=style["border"],
                font={"size": 13, "color": "#222222", "face": "Microsoft YaHei"},
            )

            G.add_edge(
                disease_id,
                evidence_id,
                label=str(weight),
                category=category,
                weight=weight,
                color=style["edge_color"],
                width=style["edge_width"],
                dashes=style["edge_dashes"],
                font={"size": 12, "color": style["edge_color"], "face": "Arial"},
            )

    return G


# ──────────────────────────────────────────────────────────────
# 3. 渲染为可交互 HTML
# ──────────────────────────────────────────────────────────────

def render_graph_html(
    G: nx.DiGraph,
    height: str = "500px",
    width: str = "100%",
) -> str:
    """将 NetworkX 有向图用 pyvis 渲染为可交互 HTML 字符串。

    - physics=True  让节点自动布局（Barnes-Hut）
    - 自定义斥力参数避免节点重叠
    - 中文节点名正确显示

    Returns
    -------
    str — 完整 HTML 字符串，可直接嵌入 Streamlit 或独立保存
    """
    net = Network(
        height=height,
        width=width,
        directed=True,
        notebook=False,
    )

    net.from_nx(G)

    # 将 nx 节点属性同步到 pyvis
    for node_id in G.nodes:
        node_data = G.nodes[node_id]
        if node_id in net.get_nodes():
            n = net.get_node(node_id)
            # 中文 & 样式
            n["label"] = node_data.get("label", node_id)
            n["shape"] = node_data.get("shape", "dot")
            n["color"] = {
                "background": node_data.get("color", "#CCCCCC"),
                "border": node_data.get("borderColor", "#999999"),
            }
            n["size"] = node_data.get("size", 20)
            n["borderWidth"] = node_data.get("borderWidth", 2)
            if "font" in node_data:
                n["font"] = node_data["font"]

    # 同步边属性
    for u, v, data in G.edges(data=True):
        edge = (u, v)
        if edge in net.get_edges():
            e = net.get_edge(u, v)
            e["label"] = data.get("label", "")
            e["color"] = {"color": data.get("color", "#999999")}
            e["width"] = data.get("width", 2)
            e["dashes"] = data.get("dashes", False)
            if "font" in data:
                e["font"] = data["font"]

    # 物理引擎：Barnes-Hut，增大斥力 & 引力
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "barnesHut",
        "barnesHut": {
          "gravitationalConstant": -5000,
          "centralGravity": 0.3,
          "springLength": 180,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 1.0
        },
        "minVelocity": 0.75,
        "maxVelocity": 30,
        "stabilization": {
          "enabled": true,
          "iterations": 300,
          "updateInterval": 25
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.8
          }
        },
        "smooth": {
          "enabled": true,
          "type": "curvedCW",
          "roundness": 0.2
        },
        "font": {
          "size": 11,
          "align": "horizontal",
          "strokeWidth": 2,
          "strokeColor": "#FFFFFF"
        }
      },
      "nodes": {
        "font": {
          "size": 14
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    return net.generate_html()


# ──────────────────────────────────────────────────────────────
# 4. 鉴别诊断对比图
# ──────────────────────────────────────────────────────────────

def render_comparison_graph(
    knowledge_base: Dict[str, Dict],
    disease1: str,
    disease2: str,
    height: str = "550px",
    width: str = "100%",
) -> Optional[str]:
    """同时展示两个疾病的证据节点。

    - 各自独有的证据用原类别颜色（core/supportive/opposing）
    - 两个疾病共享的证据节点用紫色标记
    - 用于展示鉴别诊断关键区分点

    Returns
    -------
    str — 可交互 HTML 字符串，或 None（任一名不存在时）
    """
    if disease1 not in knowledge_base or disease2 not in knowledge_base:
        return None

    info1 = knowledge_base[disease1]
    info2 = knowledge_base[disease2]

    G = nx.DiGraph()

    # ── 疾病节点 ──
    for dname in (disease1, disease2):
        node_id = f"disease:{dname}"
        G.add_node(
            node_id,
            label=dname,
            node_type="disease",
            shape=_DISEASE_SHAPE,
            color=_DISEASE_COLOR,
            size=_DISEASE_SIZE,
            borderWidth=3,
            borderColor=_DISEASE_BORDER,
            font={"size": 16, "color": "#FFFFFF", "face": "Microsoft YaHei"},
        )

    # ── 收集每个疾病的证据明细 {evidence: (category, weight)} ──
    def evidence_map(info: Dict) -> Dict[str, tuple]:
        m = {}
        for cat in ("core", "supportive", "opposing"):
            for ev, w in info.get(cat, {}).items():
                m[ev] = (cat, w)
        return m

    map1 = evidence_map(info1)
    map2 = evidence_map(info2)

    all_evidence = set(map1) | set(map2)
    shared = set(map1) & set(map2)
    only1 = set(map1) - set(map2)
    only2 = set(map2) - set(map1)

    # ── 证据节点 ──
    def add_evidence_node(evidence_name: str, category: str, is_shared: bool):
        eid = f"evidence:{evidence_name}"
        if G.has_node(eid):
            return

        if is_shared:
            G.add_node(
                eid,
                label=evidence_name,
                node_type="evidence",
                category="shared",
                shape="square",
                color=_SHARED_COLOR,
                size=26,
                borderWidth=3,
                borderColor=_SHARED_BORDER,
                font={"size": 13, "color": "#FFFFFF", "face": "Microsoft YaHei"},
            )
        else:
            style = _EVIDENCE_STYLES[category]
            G.add_node(
                eid,
                label=evidence_name,
                node_type="evidence",
                category=category,
                shape=style["shape"],
                color=style["color"],
                size=style["size"],
                borderWidth=2,
                borderColor=style["border"],
                font={"size": 13, "color": "#222222", "face": "Microsoft YaHei"},
            )

    for ev in all_evidence:
        is_shared = ev in shared
        if is_shared:
            # 取其最高权重类别决定样式
            cat1, _ = map1[ev]
            if cat1 == "core" or (ev in map2 and map2[ev][0] == "core"):
                ref_cat = "core"
            else:
                ref_cat = cat1
        else:
            if ev in map1:
                ref_cat = map1[ev][0]
            else:
                ref_cat = map2[ev][0]

        add_evidence_node(ev, ref_cat, is_shared)

    # ── 边 ──
    def add_edges(disease_name: str, evidence_map_local: Dict[str, tuple]):
        did = f"disease:{disease_name}"
        for ev, (cat, w) in evidence_map_local.items():
            eid = f"evidence:{ev}"
            is_shared = ev in shared

            if is_shared:
                edge_color = _SHARED_COLOR
                edge_width = 3
                edge_dashes = False
            else:
                style = _EVIDENCE_STYLES[cat]
                edge_color = style["edge_color"]
                edge_width = style["edge_width"]
                edge_dashes = style["edge_dashes"]

            G.add_edge(
                did,
                eid,
                label=str(w),
                category="shared" if is_shared else cat,
                weight=w,
                color=edge_color,
                width=edge_width,
                dashes=edge_dashes,
                font={"size": 12, "color": edge_color, "face": "Arial"},
            )

    add_edges(disease1, map1)
    add_edges(disease2, map2)

    # ── 渲染 ──
    net = Network(
        height=height,
        width=width,
        directed=True,
        notebook=False,
    )

    net.from_nx(G)

    # 同步节点属性
    for node_id in G.nodes:
        node_data = G.nodes[node_id]
        if node_id in net.get_nodes():
            n = net.get_node(node_id)
            n["label"] = node_data.get("label", node_id)
            n["shape"] = node_data.get("shape", "dot")
            n["color"] = {
                "background": node_data.get("color", "#CCCCCC"),
                "border": node_data.get("borderColor", "#999999"),
            }
            n["size"] = node_data.get("size", 20)
            n["borderWidth"] = node_data.get("borderWidth", 2)
            if "font" in node_data:
                n["font"] = node_data["font"]

    # 同步边属性
    for u, v, data in G.edges(data=True):
        edge = (u, v)
        if edge in net.get_edges():
            e = net.get_edge(u, v)
            e["label"] = data.get("label", "")
            e["color"] = {"color": data.get("color", "#999999")}
            e["width"] = data.get("width", 2)
            e["dashes"] = data.get("dashes", False)
            if "font" in data:
                e["font"] = data["font"]

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "solver": "barnesHut",
        "barnesHut": {
          "gravitationalConstant": -6000,
          "centralGravity": 0.4,
          "springLength": 200,
          "springConstant": 0.03,
          "damping": 0.09,
          "avoidOverlap": 1.0
        },
        "minVelocity": 0.75,
        "maxVelocity": 30,
        "stabilization": {
          "enabled": true,
          "iterations": 400,
          "updateInterval": 25
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.8
          }
        },
        "smooth": {
          "enabled": true,
          "type": "curvedCW",
          "roundness": 0.2
        },
        "font": {
          "size": 11,
          "align": "horizontal",
          "strokeWidth": 2,
          "strokeColor": "#FFFFFF"
        }
      },
      "nodes": {
        "font": {
          "size": 14
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 200,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """)

    return net.generate_html()


# ──────────────────────────────────────────────────────────────
# 自测入口
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 在此处导入实际 KNOWLEDGE_BASE 以验证
    import sys
    import os

    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from app0 import KNOWLEDGE_BASE   # 使用精简版知识库做测试
    except ImportError:
        print("未找到 app0.py（含 KNOWLEDGE_BASE），跳过自测。")
        sys.exit(0)

    # 1. 全量图
    G_full = build_full_graph(KNOWLEDGE_BASE)
    print(f"全量图：{G_full.number_of_nodes()} 节点, {G_full.number_of_edges()} 边")

    html_full = render_graph_html(G_full, height="600px")
    with open("knowledge_graph_full.html", "w", encoding="utf-8") as f:
        f.write(html_full)
    print("已生成 knowledge_graph_full.html")

    # 2. 子图
    first_disease = list(KNOWLEDGE_BASE.keys())[0]
    G_sub = build_disease_subgraph(KNOWLEDGE_BASE, first_disease)
    if G_sub:
        html_sub = render_graph_html(G_sub, height="450px")
        with open(f"knowledge_graph_{first_disease}.html", "w", encoding="utf-8") as f:
            f.write(html_sub)
        print(f"已生成 knowledge_graph_{first_disease}.html")

    # 3. 对比图
    diseases = list(KNOWLEDGE_BASE.keys())
    if len(diseases) >= 2:
        html_cmp = render_comparison_graph(KNOWLEDGE_BASE, diseases[0], diseases[1])
        if html_cmp:
            with open("knowledge_graph_comparison.html", "w", encoding="utf-8") as f:
                f.write(html_cmp)
            print(f"已生成对比图 {diseases[0]} vs {diseases[1]}")
