from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import streamlit as st
import streamlit.components.v1 as components

from graph_viz import (
    build_full_graph,
    build_disease_subgraph,
    render_graph_html,
    render_comparison_graph,
)


st.set_page_config(
    page_title="急腹症智能辅助决策系统",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 急腹症智能辅助决策系统")
st.warning(
    "本系统为医学竞赛与教学演示原型。输出为可解释规则匹配结果，不是疾病概率，"
    "不能替代急诊分诊、专科查体、实验室及影像学检查。"
)


# =============================================================================
# 1. 临床证据：阳性 / 明确阴性 / 未知
# =============================================================================
EVIDENCE_GROUPS: Dict[str, List[str]] = {
    "腹痛部位": [
        "上腹部疼痛",
        "右上腹痛",
        "左上腹痛",
        "脐周痛",
        "右下腹痛",
        "左下腹痛",
        "双侧下腹痛",
        "耻骨上区疼痛",
        "全腹痛",
        "腰部或侧腹部疼痛",
    ],
    "起病方式与疼痛性质": [
        "腹痛突然发生",
        "腹痛逐渐加重",
        "阵发性绞痛",
        "持续性剧烈腹痛",
        "持续痛伴阵发性加剧",
        "刀割样腹痛",
        "钻顶样绞痛",
        "束带样上腹痛",
        "腹痛程度与查体不相符",
    ],
    "腹痛演变与放射": [
        "上腹部或脐周疼痛转移至右下腹",
        "上腹痛迅速扩散至全腹",
        "阵发性腹痛转为持续性腹痛",
        "腹痛短暂缓解后再次加重",
        "疼痛向右肩或右肩胛区放射",
        "疼痛向左肩放射",
        "疼痛向腰背部放射",
        "疼痛向腹股沟放射",
        "疼痛向会阴或外生殖器放射",
    ],
    "消化道及全身伴随症状": [
        "恶心、呕吐",
        "呕吐后腹痛不缓解",
        "早期频繁呕吐",
        "较晚出现呕吐",
        "呕吐不含胆汁的宿食",
        "粪水样呕吐",
        "腹胀",
        "停止排气排便",
        "腹泻",
        "血便",
        "果酱样血便",
        "发热",
        "寒战、高热",
        "黄疸",
        "晕厥或晕厥前状态",
    ],
    "泌尿及妇科症状": [
        "血尿",
        "尿频、尿急或尿痛",
        "阴道流血",
        "阴道分泌物增多",
    ],
    "体格检查与生命体征": [
        "麦氏点压痛",
        "右上腹压痛",
        "Murphy征阳性",
        "肋脊角叩击痛",
        "宫颈举痛",
        "局限性腹部压痛",
        "压痛位置随体位改变",
        "腹肌紧张",
        "反跳痛",
        "板状腹",
        "肠鸣音亢进或高调",
        "肠鸣音明显减弱或消失",
        "不对称性腹胀",
        "可触及压痛性腹部肿块",
        "可触及搏动性腹部肿块",
        "Grey-Turner征或Cullen征",
        "低血压",
        "休克",
        "意识状态改变",
    ],
    "病史、实验室与影像学": [
        "停经史",
        "已知妊娠或妊娠试验阳性",
        "近期上呼吸道感染史",
        "胆囊结石病史",
        "消化性溃疡病史",
        "腹部手术史",
        "卵巢囊肿或附件区肿物病史",
        "房颤病史",
        "动脉粥样硬化性血管病史",
        "近期大量饮酒",
        "油腻饮食后发作",
        "暴饮暴食后发作",
        "近期腹部外伤",
        "白细胞计数升高",
        "血清淀粉酶或脂肪酶超过正常上限3倍",
        "胆红素或胆汁淤积酶升高",
        "影像学发现腹腔游离气体",
        "影像学提示胰腺炎症",
        "影像学提示胆道结石或胆囊炎",
        "影像学提示肠管扩张或气液平面",
    ],
}

ALL_EVIDENCE_OPTIONS: Set[str] = {
    item
    for group in EVIDENCE_GROUPS.values()
    for item in group
}


def disease(
    core: Dict[str, int],
    supportive: Dict[str, int],
    opposing: Optional[Dict[str, int]] = None,
    synergy_rules: Optional[List[Dict]] = None,
    context_rules: Optional[List[Dict]] = None,
    applicable_sex: Optional[Set[str]] = None,
) -> Dict:
    return {
        "core": core,
        "supportive": supportive,
        "opposing": opposing or {},
        "synergy_rules": synergy_rules or [],
        "context_rules": context_rules or [],
        "applicable_sex": applicable_sex or {"男", "女"},
    }


def combo(
    label: str,
    weight: int,
    all_of: Optional[List[str]] = None,
    any_of: Optional[List[str]] = None,
) -> Dict:
    return {
        "label": label,
        "weight": weight,
        "all_of": all_of or [],
        "any_of": any_of or [],
    }


# =============================================================================
# 2. 知识库
# =============================================================================
KNOWLEDGE_BASE: Dict[str, Dict] = {
    "急性阑尾炎": disease(
        core={
            "上腹部或脐周疼痛转移至右下腹": 24,
            "麦氏点压痛": 20,
        },
        supportive={
            "右下腹痛": 8,
            "腹痛逐渐加重": 6,
            "恶心、呕吐": 4,
            "发热": 5,
            "白细胞计数升高": 6,
            "局限性腹部压痛": 4,
            "反跳痛": 6,
            "腹肌紧张": 5,
        },
        opposing={
            "血尿": 5,
            "疼痛向会阴或外生殖器放射": 7,
            "果酱样血便": 8,
            "Murphy征阳性": 4,
        },
        synergy_rules=[
            combo(
                "典型转移性右下腹痛并麦氏点压痛",
                16,
                all_of=[
                    "上腹部或脐周疼痛转移至右下腹",
                    "麦氏点压痛",
                ],
            ),
            combo(
                "右下腹局限炎症组合",
                8,
                all_of=[
                    "右下腹痛",
                    "白细胞计数升高",
                ],
                any_of=[
                    "发热",
                    "反跳痛",
                    "腹肌紧张",
                ],
            ),
        ],
    ),

    "右侧输尿管结石": disease(
        core={
            "阵发性绞痛": 18,
            "血尿": 22,
            "疼痛向会阴或外生殖器放射": 18,
            "肋脊角叩击痛": 16,
        },
        supportive={
            "腰部或侧腹部疼痛": 9,
            "右下腹痛": 4,
            "腹痛突然发生": 7,
            "疼痛向腹股沟放射": 10,
            "恶心、呕吐": 4,
            "尿频、尿急或尿痛": 6,
        },
        opposing={
            "板状腹": 9,
            "上腹痛迅速扩散至全腹": 7,
            "麦氏点压痛": 4,
            "宫颈举痛": 5,
        },
        synergy_rules=[
            combo(
                "典型输尿管绞痛放射模式",
                16,
                all_of=[
                    "阵发性绞痛",
                    "血尿",
                ],
                any_of=[
                    "疼痛向腹股沟放射",
                    "疼痛向会阴或外生殖器放射",
                ],
            )
        ],
    ),

    "胃十二指肠溃疡穿孔": disease(
        core={
            "刀割样腹痛": 22,
            "板状腹": 22,
            "影像学发现腹腔游离气体": 26,
            "上腹痛迅速扩散至全腹": 18,
        },
        supportive={
            "上腹部疼痛": 7,
            "腹痛突然发生": 8,
            "全腹痛": 6,
            "反跳痛": 8,
            "腹肌紧张": 7,
            "肠鸣音明显减弱或消失": 6,
            "消化性溃疡病史": 7,
            "低血压": 5,
            "休克": 7,
        },
        opposing={
            "血尿": 5,
            "疼痛向会阴或外生殖器放射": 5,
            "肠鸣音亢进或高调": 4,
        },
        synergy_rules=[
            combo(
                "消化道穿孔典型腹膜炎组合",
                20,
                all_of=[
                    "腹痛突然发生",
                    "刀割样腹痛",
                ],
                any_of=[
                    "板状腹",
                    "上腹痛迅速扩散至全腹",
                    "影像学发现腹腔游离气体",
                ],
            )
        ],
    ),

    "急性胆囊炎": disease(
        core={
            "右上腹痛": 16,
            "Murphy征阳性": 24,
            "影像学提示胆道结石或胆囊炎": 22,
        },
        supportive={
            "上腹部疼痛": 4,
            "持续痛伴阵发性加剧": 8,
            "疼痛向右肩或右肩胛区放射": 10,
            "油腻饮食后发作": 8,
            "恶心、呕吐": 4,
            "发热": 5,
            "右上腹压痛": 10,
            "胆囊结石病史": 7,
            "白细胞计数升高": 5,
        },
        opposing={
            "血尿": 5,
            "宫颈举痛": 5,
            "疼痛向会阴或外生殖器放射": 5,
        },
        synergy_rules=[
            combo(
                "典型胆囊炎组合",
                16,
                all_of=[
                    "右上腹痛",
                    "Murphy征阳性",
                ],
                any_of=[
                    "油腻饮食后发作",
                    "发热",
                    "影像学提示胆道结石或胆囊炎",
                ],
            )
        ],
    ),

    "急性胆管炎": disease(
        core={
            "右上腹痛": 14,
            "寒战、高热": 20,
            "黄疸": 20,
            "胆红素或胆汁淤积酶升高": 16,
        },
        supportive={
            "上腹部疼痛": 4,
            "右上腹压痛": 7,
            "胆囊结石病史": 7,
            "影像学提示胆道结石或胆囊炎": 9,
            "低血压": 8,
            "休克": 10,
            "意识状态改变": 10,
        },
        opposing={
            "血尿": 4,
            "疼痛向会阴或外生殖器放射": 4,
        },
        synergy_rules=[
            combo(
                "Charcot三联征",
                20,
                all_of=[
                    "右上腹痛",
                    "寒战、高热",
                    "黄疸",
                ],
            ),
            combo(
                "重症胆管炎循环或神经功能异常",
                12,
                all_of=[
                    "寒战、高热",
                    "黄疸",
                ],
                any_of=[
                    "低血压",
                    "休克",
                    "意识状态改变",
                ],
            ),
        ],
    ),

    "急性胰腺炎": disease(
        core={
            "持续性剧烈腹痛": 16,
            "疼痛向腰背部放射": 18,
            "血清淀粉酶或脂肪酶超过正常上限3倍": 24,
            "影像学提示胰腺炎症": 24,
        },
        supportive={
            "上腹部疼痛": 9,
            "左上腹痛": 7,
            "束带样上腹痛": 10,
            "疼痛向左肩放射": 4,
            "恶心、呕吐": 5,
            "呕吐后腹痛不缓解": 9,
            "腹胀": 5,
            "肠鸣音明显减弱或消失": 4,
            "近期大量饮酒": 7,
            "暴饮暴食后发作": 6,
            "胆囊结石病史": 6,
            "Grey-Turner征或Cullen征": 12,
        },
        opposing={
            "血尿": 5,
            "疼痛向会阴或外生殖器放射": 5,
            "麦氏点压痛": 4,
        },
        synergy_rules=[
            combo(
                "典型胰腺炎疼痛组合",
                15,
                all_of=[
                    "上腹部疼痛",
                    "呕吐后腹痛不缓解",
                ],
                any_of=[
                    "疼痛向腰背部放射",
                    "束带样上腹痛",
                ],
            ),
            combo(
                "胰腺炎客观检查支持",
                10,
                any_of=[
                    "血清淀粉酶或脂肪酶超过正常上限3倍",
                    "影像学提示胰腺炎症",
                ],
            ),
        ],
    ),

    "机械性肠梗阻": disease(
        core={
            "腹胀": 14,
            "停止排气排便": 22,
            "肠鸣音亢进或高调": 16,
            "影像学提示肠管扩张或气液平面": 22,
        },
        supportive={
            "阵发性绞痛": 12,
            "脐周痛": 5,
            "全腹痛": 5,
            "恶心、呕吐": 5,
            "早期频繁呕吐": 5,
            "较晚出现呕吐": 4,
            "粪水样呕吐": 9,
            "腹部手术史": 7,
        },
        opposing={
            "血尿": 5,
            "Murphy征阳性": 4,
            "宫颈举痛": 4,
        },
        synergy_rules=[
            combo(
                "机械性肠梗阻典型组合",
                18,
                all_of=[
                    "腹胀",
                    "停止排气排便",
                ],
                any_of=[
                    "阵发性绞痛",
                    "恶心、呕吐",
                    "影像学提示肠管扩张或气液平面",
                ],
            )
        ],
    ),

    "绞窄性肠梗阻": disease(
        core={
            "阵发性腹痛转为持续性腹痛": 22,
            "持续性剧烈腹痛": 16,
            "血便": 18,
            "反跳痛": 14,
            "腹肌紧张": 12,
        },
        supportive={
            "持续痛伴阵发性加剧": 10,
            "腹胀": 8,
            "停止排气排便": 10,
            "不对称性腹胀": 10,
            "可触及压痛性腹部肿块": 8,
            "肠鸣音明显减弱或消失": 7,
            "低血压": 8,
            "休克": 10,
            "影像学提示肠管扩张或气液平面": 8,
        },
        opposing={
            "血尿": 4,
            "疼痛向会阴或外生殖器放射": 4,
        },
        synergy_rules=[
            combo(
                "肠梗阻并肠缺血危险组合",
                20,
                all_of=[
                    "停止排气排便",
                ],
                any_of=[
                    "阵发性腹痛转为持续性腹痛",
                    "血便",
                    "反跳痛",
                    "腹肌紧张",
                    "休克",
                ],
            )
        ],
    ),

    "肠扭转": disease(
        core={
            "持续痛伴阵发性加剧": 18,
            "不对称性腹胀": 20,
            "影像学提示肠管扩张或气液平面": 16,
        },
        supportive={
            "腹痛突然发生": 8,
            "疼痛向腰背部放射": 5,
            "恶心、呕吐": 5,
            "腹胀": 8,
            "停止排气排便": 9,
            "可触及压痛性腹部肿块": 8,
            "低血压": 6,
            "休克": 8,
        },
        opposing={
            "血尿": 5,
            "Murphy征阳性": 4,
        },
        synergy_rules=[
            combo(
                "肠扭转梗阻组合",
                18,
                all_of=[
                    "持续痛伴阵发性加剧",
                    "不对称性腹胀",
                ],
                any_of=[
                    "停止排气排便",
                    "影像学提示肠管扩张或气液平面",
                ],
            )
        ],
    ),

    "肠套叠": disease(
        core={
            "阵发性绞痛": 18,
            "果酱样血便": 26,
            "可触及压痛性腹部肿块": 20,
        },
        supportive={
            "恶心、呕吐": 5,
            "腹胀": 4,
        },
        opposing={
            "血尿": 5,
            "黄疸": 5,
            "板状腹": 4,
        },
        synergy_rules=[
            combo(
                "肠套叠典型三联征",
                22,
                all_of=[
                    "阵发性绞痛",
                    "果酱样血便",
                    "可触及压痛性腹部肿块",
                ],
            )
        ],
        context_rules=[
            {
                "label": "儿童年龄组",
                "weight": 10,
                "min_age": 0,
                "max_age": 6,
            }
        ],
    ),

    "急性肠系膜缺血": disease(
        core={
            "腹痛程度与查体不相符": 26,
            "持续性剧烈腹痛": 18,
            "房颤病史": 20,
            "动脉粥样硬化性血管病史": 14,
        },
        supportive={
            "腹痛突然发生": 10,
            "全腹痛": 6,
            "恶心、呕吐": 4,
            "血便": 10,
            "肠鸣音明显减弱或消失": 6,
            "低血压": 7,
            "休克": 9,
        },
        opposing={
            "麦氏点压痛": 4,
            "Murphy征阳性": 4,
            "肋脊角叩击痛": 4,
        },
        synergy_rules=[
            combo(
                "肠系膜缺血高危组合",
                22,
                all_of=[
                    "腹痛突然发生",
                    "持续性剧烈腹痛",
                    "腹痛程度与查体不相符",
                ],
                any_of=[
                    "房颤病史",
                    "动脉粥样硬化性血管病史",
                    "血便",
                ],
            )
        ],
        context_rules=[
            {
                "label": "年龄≥60岁",
                "weight": 8,
                "min_age": 60,
                "max_age": 120,
            }
        ],
    ),

    "异位妊娠破裂": disease(
        core={
            "停经史": 22,
            "已知妊娠或妊娠试验阳性": 26,
            "阴道流血": 20,
            "低血压": 16,
            "休克": 22,
        },
        supportive={
            "耻骨上区疼痛": 7,
            "腹痛突然发生": 9,
            "持续性剧烈腹痛": 9,
            "宫颈举痛": 12,
            "晕厥或晕厥前状态": 10,
        },
        opposing={
            "上腹部或脐周疼痛转移至右下腹": 5,
            "血尿": 5,
            "Murphy征阳性": 4,
        },
        synergy_rules=[
            combo(
                "异位妊娠典型危险组合",
                22,
                all_of=[
                    "停经史",
                    "阴道流血",
                ],
                any_of=[
                    "腹痛突然发生",
                    "耻骨上区疼痛",
                    "晕厥或晕厥前状态",
                    "低血压",
                    "休克",
                ],
            )
        ],
        context_rules=[
            {
                "label": "育龄期女性",
                "weight": 5,
                "min_age": 12,
                "max_age": 55,
            }
        ],
        applicable_sex={"女"},
    ),

    "急性盆腔炎": disease(
        core={
            "双侧下腹痛": 16,
            "宫颈举痛": 22,
            "阴道分泌物增多": 20,
        },
        supportive={
            "耻骨上区疼痛": 7,
            "腹痛逐渐加重": 7,
            "发热": 8,
            "白细胞计数升高": 6,
        },
        opposing={
            "血尿": 5,
            "上腹部或脐周疼痛转移至右下腹": 5,
            "板状腹": 7,
            "休克": 5,
        },
        synergy_rules=[
            combo(
                "盆腔炎典型组合",
                18,
                all_of=[
                    "宫颈举痛",
                    "阴道分泌物增多",
                ],
                any_of=[
                    "双侧下腹痛",
                    "发热",
                    "白细胞计数升高",
                ],
            )
        ],
        context_rules=[
            {
                "label": "育龄期女性",
                "weight": 4,
                "min_age": 12,
                "max_age": 55,
            }
        ],
        applicable_sex={"女"},
    ),

    "卵巢蒂扭转": disease(
        core={
            "腹痛突然发生": 14,
            "持续性剧烈腹痛": 16,
            "卵巢囊肿或附件区肿物病史": 24,
            "局限性腹部压痛": 10,
        },
        supportive={
            "右下腹痛": 7,
            "左下腹痛": 7,
            "耻骨上区疼痛": 6,
            "恶心、呕吐": 7,
            "反跳痛": 5,
        },
        opposing={
            "血尿": 5,
            "黄疸": 5,
            "上腹痛迅速扩散至全腹": 4,
        },
        synergy_rules=[
            combo(
                "卵巢蒂扭转典型组合",
                18,
                all_of=[
                    "腹痛突然发生",
                    "持续性剧烈腹痛",
                ],
                any_of=[
                    "卵巢囊肿或附件区肿物病史",
                    "右下腹痛",
                    "左下腹痛",
                    "恶心、呕吐",
                ],
            )
        ],
        context_rules=[
            {
                "label": "育龄期女性",
                "weight": 5,
                "min_age": 10,
                "max_age": 55,
            }
        ],
        applicable_sex={"女"},
    ),

    "急性肠系膜淋巴结炎": disease(
        core={
            "近期上呼吸道感染史": 20,
            "压痛位置随体位改变": 18,
        },
        supportive={
            "脐周痛": 7,
            "右下腹痛": 6,
            "发热": 5,
        },
        opposing={
            "板状腹": 9,
            "休克": 8,
            "腹痛程度与查体不相符": 7,
            "影像学发现腹腔游离气体": 8,
            "麦氏点压痛": 4,
        },
        synergy_rules=[
            combo(
                "儿童上呼吸道感染后非固定右下腹痛",
                14,
                all_of=[
                    "近期上呼吸道感染史",
                ],
                any_of=[
                    "压痛位置随体位改变",
                    "脐周痛",
                    "右下腹痛",
                ],
            )
        ],
        context_rules=[
            {
                "label": "年龄≤18岁",
                "weight": 10,
                "min_age": 0,
                "max_age": 18,
            }
        ],
    ),

    "瘢痕性幽门梗阻": disease(
        core={
            "呕吐不含胆汁的宿食": 26,
            "消化性溃疡病史": 18,
        },
        supportive={
            "上腹部疼痛": 7,
            "腹胀": 8,
            "恶心、呕吐": 5,
            "较晚出现呕吐": 5,
        },
        opposing={
            "血尿": 5,
            "血便": 4,
            "疼痛向会阴或外生殖器放射": 5,
            "板状腹": 6,
        },
        synergy_rules=[
            combo(
                "幽门梗阻典型呕吐模式",
                18,
                all_of=[
                    "呕吐不含胆汁的宿食",
                    "消化性溃疡病史",
                ],
            )
        ],
    ),
}


# =============================================================================
# 3. 下一步检查建议
# =============================================================================
EVIDENCE_ACTIONS: Dict[str, str] = {
    "麦氏点压痛": "复查右下腹固定压痛及麦氏点压痛",
    "Murphy征阳性": "规范检查Murphy征并结合胆囊超声",
    "肋脊角叩击痛": "检查肋脊角叩击痛并完善尿常规",
    "宫颈举痛": "进行妇科查体，评估宫颈举痛",
    "血尿": "完善尿常规及泌尿系影像学检查",
    "停经史": "询问末次月经及停经时间",
    "已知妊娠或妊娠试验阳性": "立即完善血或尿妊娠试验",
    "阴道流血": "询问阴道流血量并进行妇科评估",
    "影像学发现腹腔游离气体": "尽快完善立位胸腹片或腹部CT",
    "血清淀粉酶或脂肪酶超过正常上限3倍": "检测血清淀粉酶和脂肪酶",
    "影像学提示胰腺炎症": "完善腹部增强CT或胰腺相关影像学",
    "影像学提示胆道结石或胆囊炎": "完善肝胆超声，必要时行MRCP或CT",
    "胆红素或胆汁淤积酶升高": "完善肝功能、胆红素和胆汁淤积酶检查",
    "影像学提示肠管扩张或气液平面": "尽快完善腹部CT或腹部立位平片",
    "房颤病史": "询问房颤史并检查心电图",
    "腹痛程度与查体不相符": "重新评估疼痛程度与腹部体征是否不匹配",
    "停止排气排便": "明确末次排气排便时间",
    "果酱样血便": "观察大便性状并进行直肠指检或相关检查",
    "卵巢囊肿或附件区肿物病史": "完善妇科超声检查附件区",
}


# =============================================================================
# 4. 统一评分框架
#
# 综合得分 =
# 核心证据分（最高45）
# + 一般支持证据分（最高25）
# + 组合规则分（最高20）
# + 背景修正分（最高10）
# - 明确阴性证据扣分（最高25）
# - 替代诊断证据扣分（最高20）
# =============================================================================
CORE_CAP = 45.0
SUPPORT_CAP = 25.0
SYNERGY_CAP = 20.0
CONTEXT_CAP = 10.0
NEGATIVE_CAP = 25.0
OPPOSING_CAP = 20.0


@dataclass
class TriageAlert:
    level: str
    title: str
    message: str


@dataclass
class DiagnosisResult:
    disease: str
    score: float
    match_level: str
    evidence_sufficiency: str
    completeness: float

    core_points: float
    supportive_points: float
    synergy_points: float
    context_points: float
    explicit_negative_penalty: float
    opposing_penalty: float

    matched_core: List[str]
    matched_supportive: List[str]
    matched_synergy: List[str]
    matched_context: List[str]
    explicit_negative_findings: List[str]
    opposing_findings: List[str]


def validate_knowledge_base() -> None:
    unknown: Set[str] = set()

    for info in KNOWLEDGE_BASE.values():
        for section in (
            "core",
            "supportive",
            "opposing",
        ):
            unknown.update(
                set(info.get(section, {}))
                - ALL_EVIDENCE_OPTIONS
            )

        for rule in info.get("synergy_rules", []):
            labels = (
                set(rule.get("all_of", []))
                | set(rule.get("any_of", []))
            )
            unknown.update(
                labels - ALL_EVIDENCE_OPTIONS
            )

    if unknown:
        raise ValueError(
            f"知识库中存在未定义证据：{sorted(unknown)}"
        )


def context_matches(
    rule: Dict,
    age: int,
) -> bool:
    return (
        rule.get("min_age", 0)
        <= age
        <= rule.get("max_age", 120)
    )


def synergy_matches(
    rule: Dict,
    positive: Set[str],
) -> bool:
    all_of = set(rule.get("all_of", []))
    any_of = set(rule.get("any_of", []))

    return (
        all_of.issubset(positive)
        and (
            not any_of
            or bool(any_of & positive)
        )
    )


# =============================================================================
# 5. 急症分诊通道
# =============================================================================
def emergency_check(
    age: int,
    sex: str,
    positive: Set[str],
) -> List[TriageAlert]:
    alerts: List[TriageAlert] = []

    def all_(*items: str) -> bool:
        return set(items).issubset(positive)

    def any_(*items: str) -> bool:
        return bool(set(items) & positive)

    if any_(
        "休克",
        "低血压",
    ):
        alerts.append(
            TriageAlert(
                "红色",
                "血流动力学不稳定",
                "应立即监测生命体征、建立静脉通路并根据病情进行复苏和急诊病因评估。",
            )
        )

    if (
        all_(
            "腹痛突然发生",
            "刀割样腹痛",
        )
        and any_(
            "板状腹",
            "上腹痛迅速扩散至全腹",
            "影像学发现腹腔游离气体",
        )
    ):
        alerts.append(
            TriageAlert(
                "红色",
                "高度警惕消化道穿孔",
                "应立即禁食、复苏并紧急联系普通外科。",
            )
        )

    if (
        sex == "女"
        and any_(
            "停经史",
            "已知妊娠或妊娠试验阳性",
        )
        and any_(
            "腹痛突然发生",
            "阴道流血",
            "晕厥或晕厥前状态",
            "低血压",
            "休克",
        )
    ):
        alerts.append(
            TriageAlert(
                "红色",
                "高度警惕异位妊娠破裂",
                "应立即完善妊娠试验、床旁超声并紧急联系妇产科。",
            )
        )

    biliary_pain = any_(
        "右上腹痛",
        "上腹部疼痛",
    )

    if (
        biliary_pain
        and all_(
            "寒战、高热",
            "黄疸",
        )
    ):
        if any_(
            "低血压",
            "休克",
            "意识状态改变",
        ):
            alerts.append(
                TriageAlert(
                    "红色",
                    "重症急性胆管炎危险模式",
                    "应立即复苏、抗感染并尽快评估胆道减压引流。",
                )
            )
        else:
            alerts.append(
                TriageAlert(
                    "橙色",
                    "急性胆管炎危险模式",
                    "应紧急完善感染、肝功能和胆道影像学检查。",
                )
            )

    if all_(
        "腹胀",
        "停止排气排便",
    ):
        alerts.append(
            TriageAlert(
                "橙色",
                "肠梗阻危险模式",
                "建议立即禁食、纠正水电解质紊乱，完善腹部影像学并请外科会诊。",
            )
        )

    elif (
        age >= 60
        and "停止排气排便" in positive
    ):
        alerts.append(
            TriageAlert(
                "橙色",
                "老年患者肠梗阻风险",
                "应尽快完善腹部影像学并进行外科评估。",
            )
        )

    strangulation_pain = any_(
        "阵发性腹痛转为持续性腹痛",
        "持续性剧烈腹痛",
        "持续痛伴阵发性加剧",
    )

    strangulation_sign = any_(
        "血便",
        "反跳痛",
        "腹肌紧张",
        "不对称性腹胀",
        "休克",
    )

    if (
        "停止排气排便" in positive
        and strangulation_pain
        and strangulation_sign
    ):
        alerts.append(
            TriageAlert(
                "红色",
                "绞窄性肠梗阻或肠坏死风险",
                "应立即进行急诊外科评估。",
            )
        )

    mesenteric_pattern = (
        all_(
            "腹痛突然发生",
            "持续性剧烈腹痛",
        )
        and any_(
            "腹痛程度与查体不相符",
            "血便",
        )
        and (
            any_(
                "房颤病史",
                "动脉粥样硬化性血管病史",
            )
            or age >= 60
        )
    )

    if mesenteric_pattern:
        alerts.append(
            TriageAlert(
                "红色",
                "急性肠系膜缺血危险模式",
                "应尽快完善增强CT血管成像并紧急联系外科或血管外科。",
            )
        )

    pancreatitis_pattern = (
        any_(
            "上腹部疼痛",
            "左上腹痛",
        )
        and any_(
            "疼痛向腰背部放射",
            "束带样上腹痛",
        )
        and "呕吐后腹痛不缓解" in positive
    )

    if (
        pancreatitis_pattern
        and any_(
            "低血压",
            "休克",
            "Grey-Turner征或Cullen征",
            "意识状态改变",
        )
    ):
        alerts.append(
            TriageAlert(
                "红色",
                "重症急性胰腺炎风险",
                "应立即评估器官功能并考虑重症监护。",
            )
        )

    if (
        all_(
            "腹痛突然发生",
            "可触及搏动性腹部肿块",
        )
        and any_(
            "低血压",
            "休克",
            "疼痛向腰背部放射",
        )
    ):
        alerts.append(
            TriageAlert(
                "红色",
                "腹部血管破裂风险",
                "应立即进行血管急诊评估和复苏。",
            )
        )

    unique = {
        (alert.level, alert.title): alert
        for alert in alerts
    }

    priority = {
        "红色": 2,
        "橙色": 1,
    }

    return sorted(
        unique.values(),
        key=lambda item: priority.get(
            item.level,
            0,
        ),
        reverse=True,
    )


# =============================================================================
# 6. 评分与排序
# =============================================================================
def get_match_level(
    score: float,
) -> str:
    if score >= 75:
        return "高度匹配"

    if score >= 55:
        return "中度匹配"

    if score >= 35:
        return "低度匹配"

    return "初步线索"


def get_sufficiency(
    core_hits: int,
    positive_hits: int,
    score: float,
) -> str:

    # 有多个关键证据，并且综合得分较高
    if (
        core_hits >= 2
        and score >= 70
    ):
        return "较充分"

    # 有核心证据，同时有一定支持证据
    if (
        core_hits >= 1
        and positive_hits >= 3
        and score >= 50
    ):
        return "一般"

    # 有一些临床线索，但尚不足以形成强支持
    if (
        positive_hits >= 2
        and score >= 35
    ):
        return "初步线索"

    return "不足"


def calculate_scores(
    positive: Set[str],
    negative: Set[str],
    age: int,
    sex: str,
) -> List[DiagnosisResult]:
    results: List[DiagnosisResult] = []

    for disease_name, info in KNOWLEDGE_BASE.items():
        if sex not in info["applicable_sex"]:
            continue

        core = info["core"]
        support = info["supportive"]
        opposing = info["opposing"]

        matched_core = [
            item
            for item in core
            if item in positive
        ]

        matched_support = [
            item
            for item in support
            if item in positive
        ]

        opposing_findings = [
            item
            for item in opposing
            if item in positive
        ]

        negative_core = [
            item
            for item in core
            if item in negative
        ]

        negative_support = [
            item
            for item in support
            if item in negative
        ]

        # 未命中核心证据且仅有一项普通证据时，不参与排名
        if (
            not matched_core
            and len(matched_support) < 2
        ):
            continue

        core_points = min(
            CORE_CAP,
            sum(
                core[item]
                for item in matched_core
            ),
        )

        support_points = min(
            SUPPORT_CAP,
            sum(
                support[item]
                for item in matched_support
            ),
        )

        matched_synergy: List[str] = []
        synergy_raw = 0.0

        for rule in info["synergy_rules"]:
            if synergy_matches(
                rule,
                positive,
            ):
                matched_synergy.append(
                    rule["label"]
                )
                synergy_raw += rule["weight"]

        synergy_points = min(
            SYNERGY_CAP,
            synergy_raw,
        )

        matched_context: List[str] = []
        context_raw = 0.0

        for rule in info["context_rules"]:
            if context_matches(
                rule,
                age,
            ):
                matched_context.append(
                    rule["label"]
                )
                context_raw += rule["weight"]

        context_points = min(
            CONTEXT_CAP,
            context_raw,
        )

        # 核心证据明确阴性时按原权重60%扣分
        # 一般证据明确阴性时按原权重35%扣分
        negative_penalty = min(
            NEGATIVE_CAP,
            sum(
                core[item] * 0.60
                for item in negative_core
            )
            + sum(
                support[item] * 0.35
                for item in negative_support
            ),
        )

        opposing_penalty = min(
            OPPOSING_CAP,
            sum(
                opposing[item]
                for item in opposing_findings
            ),
        )

        score = (
            core_points
            + support_points
            + synergy_points
            + context_points
            - negative_penalty
            - opposing_penalty
        )

        score = max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

        # 无核心证据时，最高不超过49分
        if not matched_core:
            score = min(
                score,
                49.0,
            )

        relevant = (
            set(core)
            | set(support)
        )

        assessed = (
            relevant
            & (
                positive
                | negative
            )
        )

        completeness = (
            len(assessed) / len(relevant)
            if relevant
            else 0.0
        )

        results.append(
            DiagnosisResult(
                disease=disease_name,
                score=score,
                match_level=get_match_level(
                    score
                ),
                evidence_sufficiency=get_sufficiency(
                    len(matched_core),
                    len(matched_core)
                    + len(matched_support),
                    score,
                ),
                completeness=completeness,
                core_points=core_points,
                supportive_points=support_points,
                synergy_points=synergy_points,
                context_points=context_points,
                explicit_negative_penalty=negative_penalty,
                opposing_penalty=opposing_penalty,
                matched_core=matched_core,
                matched_supportive=matched_support,
                matched_synergy=matched_synergy,
                matched_context=matched_context,
                explicit_negative_findings=(
                    negative_core
                    + negative_support
                ),
                opposing_findings=opposing_findings,
            )
        )

    return sorted(
        results,
        key=lambda result: (
            result.score,
            len(result.matched_core),
            len(result.matched_synergy),
            len(result.matched_supportive),
            result.completeness,
            -result.explicit_negative_penalty,
            -result.opposing_penalty,
        ),
        reverse=True,
    )


# =============================================================================
# 7. 下一步鉴别信息推荐
# =============================================================================
def signed_weight(
    info: Dict,
    evidence: str,
) -> float:
    if evidence in info["core"]:
        return info["core"][evidence]

    if evidence in info["supportive"]:
        return info["supportive"][evidence]

    if evidence in info["opposing"]:
        return -info["opposing"][evidence]

    return 0.0


def recommend_next_evidence(
    results: List[DiagnosisResult],
    positive: Set[str],
    negative: Set[str],
    top_n: int = 5,
) -> List[Dict[str, str]]:
    if not results:
        return []

    first_name = results[0].disease
    first = KNOWLEDGE_BASE[first_name]

    if len(results) >= 2:
        second_name = results[1].disease
        second = KNOWLEDGE_BASE[
            second_name
        ]
    else:
        second_name = "其他诊断"
        second = {
            "core": {},
            "supportive": {},
            "opposing": {},
        }

    assessed = (
        positive
        | negative
    )

    candidates = (
        set(first["core"])
        | set(first["supportive"])
        | set(first["opposing"])
        | set(second["core"])
        | set(second["supportive"])
        | set(second["opposing"])
    ) - assessed

    ranking: List[
        Tuple[
            float,
            str,
            float,
            float,
        ]
    ] = []

    for item in candidates:
        weight_1 = signed_weight(
            first,
            item,
        )

        weight_2 = signed_weight(
            second,
            item,
        )

        difference = abs(
            weight_1
            - weight_2
        )

        importance = max(
            abs(weight_1),
            abs(weight_2),
        )

        core_bonus = (
            8
            if (
                item in first["core"]
                or item in second["core"]
            )
            else 0
        )

        ranking.append(
            (
                difference * 2
                + importance
                + core_bonus,
                item,
                weight_1,
                weight_2,
            )
        )

    ranking.sort(
        reverse=True
    )

    recommendations = []

    for (
        _,
        item,
        weight_1,
        weight_2,
    ) in ranking[:top_n]:
        recommendations.append(
            {
                "待补充证据": item,
                "建议动作": EVIDENCE_ACTIONS.get(
                    item,
                    f"补充询问或检查：{item}",
                ),
                "区分意义": (
                    f"对“{first_name}”方向权重"
                    f"{weight_1:+.0f}；"
                    f"对“{second_name}”方向权重"
                    f"{weight_2:+.0f}"
                ),
            }
        )

    return recommendations


def diagnose(
    positive: Set[str],
    negative: Set[str],
    age: int,
    sex: str,
) -> Tuple[
    List[TriageAlert],
    List[DiagnosisResult],
]:
    alerts = emergency_check(
        age,
        sex,
        positive,
    )

    results = calculate_scores(
        positive,
        negative,
        age,
        sex,
    )

    return alerts, results


validate_knowledge_base()



# =============================================================================
# 7.1 页面状态与知识图谱局部刷新
# =============================================================================
# Streamlit 中，radio、selectbox、checkbox 等控件发生变化时，
# 都会重新执行当前 Python 脚本。
#
# 因此诊断结果不能只保存在普通变量中，
# 必须保存进 st.session_state，否则切换知识图谱模式后结果会丢失。

if "diagnosis_ready" not in st.session_state:
    st.session_state.diagnosis_ready = False

if "diagnosis_positive" not in st.session_state:
    st.session_state.diagnosis_positive = set()

if "diagnosis_negative" not in st.session_state:
    st.session_state.diagnosis_negative = set()

if "diagnosis_alerts" not in st.session_state:
    st.session_state.diagnosis_alerts = []

if "diagnosis_results" not in st.session_state:
    st.session_state.diagnosis_results = []


# 新版 Streamlit 使用 st.fragment，
# 点击知识图谱内部控件时只重新运行知识图谱区域。
#
# 旧版本 Streamlit 如果没有 st.fragment，
# 会自动退化为普通函数，不会因此报错。
_fragment = getattr(
    st,
    "fragment",
    lambda function: function,
)


@_fragment
def render_knowledge_graph_panel(
    results: List[DiagnosisResult],
) -> None:
    """独立渲染知识图谱区域。"""

    st.divider()
    st.subheader("🧠 知识图谱")

    graph_mode = st.radio(
        "图谱模式",
        [
            "完整知识图谱",
            "Top1疾病证据网络",
            "鉴别对比图",
        ],
        horizontal=True,
        key="graph_mode",
    )

    # -------------------------------------------------------------------------
    # 模式一：完整知识图谱
    # -------------------------------------------------------------------------
    if graph_mode == "完整知识图谱":
        col1, col2 = st.columns([1, 3])

        with col1:
            disease_names = list(
                KNOWLEDGE_BASE.keys()
            )

            selected_disease = st.selectbox(
                "🔍 跳转到疾病",
                [
                    "（全部疾病）",
                    *disease_names,
                ],
                key="kb_select_disease",
            )

        with col2:
            st.caption(
                "🟢 核心证据　"
                "🟩 支持证据　"
                "🟥 反向证据　"
                "粗线表示核心关系，"
                "细线表示一般支持，"
                "虚线表示反向关系。"
            )

            if selected_disease == "（全部疾病）":
                graph = build_full_graph(
                    KNOWLEDGE_BASE
                )

            else:
                graph = build_disease_subgraph(
                    KNOWLEDGE_BASE,
                    selected_disease,
                )

            if graph is None:
                st.warning(
                    "没有找到对应的疾病图谱。"
                )
                return

            graph_html = render_graph_html(
                graph,
                height="580px",
                width="100%",
            )

            components.html(
                graph_html,
                height=600,
                scrolling=False,
            )

    # -------------------------------------------------------------------------
    # 模式二：Top1疾病证据网络
    # -------------------------------------------------------------------------
    elif graph_mode == "Top1疾病证据网络":
        if not results:
            st.info(
                "当前没有可用于展示的诊断结果。"
            )
            return

        top1 = results[0]

        graph = build_disease_subgraph(
            KNOWLEDGE_BASE,
            top1.disease,
        )

        if graph is None:
            st.warning(
                f"没有找到“{top1.disease}”的知识图谱。"
            )
            return

        st.caption(
            f"排名第1：**{top1.disease}**　"
            f"{top1.match_level}　"
            f"{top1.score:.1f} 分"
        )

        graph_html = render_graph_html(
            graph,
            height="550px",
            width="100%",
        )

        components.html(
            graph_html,
            height=570,
            scrolling=False,
        )

    # -------------------------------------------------------------------------
    # 模式三：鉴别诊断对比图
    # -------------------------------------------------------------------------
    else:
        if len(results) < 2:
            st.info(
                "需要至少两个鉴别诊断结果才能进行对比。"
            )
            return

        disease1 = results[0].disease
        disease2 = results[1].disease

        graph_html = render_comparison_graph(
            KNOWLEDGE_BASE,
            disease1,
            disease2,
            height="580px",
            width="100%",
        )

        st.caption(
            f"对比：**{disease1}**　vs　"
            f"**{disease2}**　"
            "（🟣 紫色表示两种疾病的共享证据）"
        )

        if graph_html is None:
            st.warning(
                "无法生成鉴别诊断对比图。"
            )
            return

        components.html(
            graph_html,
            height=600,
            scrolling=False,
        )



# =============================================================================
# 8. 医生录入界面
# =============================================================================
with st.sidebar:
    st.header("患者资料录入")

    st.caption(
        "阳性＝确认存在；明确阴性＝已经询问或检查且确认不存在；"
        "未选择＝未知或尚未检查。"
    )

    with st.form("patient_form"):
        sex = st.radio(
            "性别",
            [
                "男",
                "女",
            ],
            horizontal=True,
        )

        age = st.number_input(
            "年龄",
            min_value=0,
            max_value=120,
            value=30,
            step=1,
        )

        positive_list: List[str] = []
        negative_list: List[str] = []

        for index, (
            group_name,
            options,
        ) in enumerate(
            EVIDENCE_GROUPS.items()
        ):
            with st.expander(
                group_name,
                expanded=(
                    index == 0
                ),
            ):
                positive_items = st.multiselect(
                    "阳性证据",
                    options,
                    key=f"positive_{index}",
                    help="选择已经确认存在的症状、体征或检查结果。",
                )

                negative_items = st.multiselect(
                    "明确阴性证据",
                    options,
                    key=f"negative_{index}",
                    help="仅选择已询问或检查且明确不存在的项目。",
                )

                positive_list.extend(
                    positive_items
                )

                negative_list.extend(
                    negative_items
                )

        diagnose_btn = st.form_submit_button(
            "🚑 开始智能辅助评估",
            type="primary",
            use_container_width=True,
        )

    # ── 侧边栏：知识图谱开关 ──
    st.divider()
    st.checkbox("🧠 显示知识图谱", key="show_knowledge_graph")


# =============================================================================
# 9. 结果计算与持久化
# =============================================================================
if diagnose_btn:
    submitted_positive = set(
        positive_list
    )

    submitted_negative = set(
        negative_list
    )

    overlap = (
        submitted_positive
        & submitted_negative
    )

    if overlap:
        # 本次录入无效，不展示旧结果
        st.session_state.diagnosis_ready = False

        st.error(
            "以下项目同时被选为阳性和阴性："
            f"{'、'.join(sorted(overlap))}"
        )

    elif (
        not submitted_positive
        and not submitted_negative
    ):
        # 本次没有录入任何证据
        st.session_state.diagnosis_ready = False

        st.warning(
            "请至少录入一项阳性或明确阴性证据。"
        )

    else:
        submitted_alerts, submitted_results = diagnose(
            submitted_positive,
            submitted_negative,
            int(age),
            sex,
        )

        # 将诊断输入和诊断结果永久保存到当前会话
        st.session_state.diagnosis_positive = (
            submitted_positive
        )

        st.session_state.diagnosis_negative = (
            submitted_negative
        )

        st.session_state.diagnosis_alerts = (
            submitted_alerts
        )

        st.session_state.diagnosis_results = (
            submitted_results
        )

        st.session_state.diagnosis_ready = True


# =============================================================================
# 10. 结果展示
# =============================================================================
if st.session_state.diagnosis_ready:
    # 每次页面重新执行时，都从 session_state 读取上一次诊断结果
    positive = st.session_state.diagnosis_positive
    negative = st.session_state.diagnosis_negative
    alerts = st.session_state.diagnosis_alerts
    results = st.session_state.diagnosis_results

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "阳性证据",
        len(positive),
    )

    col2.metric(
        "明确阴性证据",
        len(negative),
    )

    col3.metric(
        "急症预警",
        len(alerts),
    )

    col4.metric(
        "进入排序的疾病",
        len(results),
    )

    # -------------------------------------------------------------------------
    # 急症预警
    # -------------------------------------------------------------------------
    if alerts:
        st.subheader(
            "🚨 急症分诊预警"
        )

        for alert in alerts:
            content = (
                f"**{alert.title}**\n\n"
                f"{alert.message}"
            )

            if alert.level == "红色":
                st.error(content)
            else:
                st.warning(content)

        st.caption(
            "急症分诊优先于疾病排序，不能因排序结果延误急救和会诊。"
        )

    # -------------------------------------------------------------------------
    # 排名总表
    # -------------------------------------------------------------------------
    st.subheader(
        "📊 可解释鉴别诊断排序"
    )

    st.caption(
        "综合规则得分采用统一100分框架，不是患病概率。"
        "排名依据为核心证据、一般证据、组合模式、背景修正及扣分证据。"
    )

    if not results:
        st.info(
            "当前证据不足以形成有效排序，"
            "请补充关键查体、病史或辅助检查。"
        )

    else:
        table = []

        for rank, result in enumerate(
            results[:8],
            start=1,
        ):
            table.append(
                {
                    "排名": rank,
                    "疾病": result.disease,
                    "综合规则得分": round(
                        result.score,
                        1,
                    ),
                    "匹配等级": result.match_level,
                    "证据充分度": result.evidence_sufficiency,
                    "核心证据命中": len(
                        result.matched_core
                    ),
                    "组合规则命中": len(
                        result.matched_synergy
                    ),
                }
            )

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
        )

        # ---------------------------------------------------------------------
        # 证据链
        # ---------------------------------------------------------------------
        st.subheader(
            "🔍 排名前列疾病的证据链"
        )

        for rank, result in enumerate(
            results[:5],
            start=1,
        ):
            with st.container(
                border=True
            ):
                st.markdown(
                    f"### 第 {rank} 名："
                    f"{result.disease}"
                )

                st.progress(
                    result.score / 100,
                    text=(
                        f"综合规则得分："
                        f"{result.score:.1f}/100　"
                        f"匹配等级："
                        f"{result.match_level}　"
                        f"证据充分度："
                        f"{result.evidence_sufficiency}"
                    ),
                )

                score_col1, score_col2, score_col3, score_col4 = st.columns(4)

                score_col1.metric(
                    "核心证据分",
                    f"{result.core_points:.1f}",
                )

                score_col2.metric(
                    "一般支持分",
                    f"{result.supportive_points:.1f}",
                )

                score_col3.metric(
                    "组合与背景分",
                    (
                        f"{result.synergy_points + result.context_points:.1f}"
                    ),
                )

                score_col4.metric(
                    "总扣分",
                    (
                        f"{result.explicit_negative_penalty + result.opposing_penalty:.1f}"
                    ),
                )

                if result.matched_core:
                    st.markdown(
                        "**核心支持证据**"
                    )

                    for item in result.matched_core:
                        weight = KNOWLEDGE_BASE[
                            result.disease
                        ]["core"][item]

                        st.markdown(
                            f"- ✅ {item} "
                            f"`核心 +{weight}`"
                        )

                if result.matched_supportive:
                    st.markdown(
                        "**一般支持证据**"
                    )

                    for item in result.matched_supportive:
                        weight = KNOWLEDGE_BASE[
                            result.disease
                        ]["supportive"][item]

                        st.markdown(
                            f"- ➕ {item} "
                            f"`+{weight}`"
                        )

                if result.matched_synergy:
                    st.markdown(
                        "**已触发的组合模式**"
                    )

                    for item in result.matched_synergy:
                        st.markdown(
                            f"- 🔗 {item}"
                        )

                if result.matched_context:
                    st.markdown(
                        "**人口学背景修正**"
                    )

                    for item in result.matched_context:
                        st.markdown(
                            f"- ℹ️ {item}"
                        )

                if result.explicit_negative_findings:
                    st.markdown(
                        "**明确阴性且降低匹配度的证据**"
                    )

                    for item in result.explicit_negative_findings:
                        st.markdown(
                            f"- ⛔ {item}"
                        )

                if result.opposing_findings:
                    st.markdown(
                        "**更支持其他诊断的阳性证据**"
                    )

                    for item in result.opposing_findings:
                        weight = KNOWLEDGE_BASE[
                            result.disease
                        ]["opposing"][item]

                        st.markdown(
                            f"- ⚖️ {item} "
                            f"`相对扣分 -{weight}`"
                        )

                if (
                    result.evidence_sufficiency
                    == "不足"
                ):
                    st.warning(
                        "当前证据充分度不足，"
                        "该排名只能作为初步线索。"
                    )

        # ---------------------------------------------------------------------
        # 下一步检查推荐
        # ---------------------------------------------------------------------
        recommendations = recommend_next_evidence(
            results,
            positive,
            negative,
        )

        if recommendations:
            st.subheader(
                "🧭 下一步最具区分度的信息"
            )

            st.caption(
                "系统根据排名前两位疾病的规则差异，"
                "推荐尚未评估的关键项目。"
            )

            st.dataframe(
                recommendations,
                use_container_width=True,
                hide_index=True,
            )

    # -------------------------------------------------------------------------
    # 查看全部证据
    # -------------------------------------------------------------------------
    with st.expander(
        "查看全部已录入证据"
    ):
        left, right = st.columns(2)

        with left:
            st.markdown(
                "#### 阳性证据"
            )

            if positive:
                for item in sorted(
                    positive
                ):
                    st.markdown(
                        f"- ✅ {item}"
                    )
            else:
                st.caption("无")

        with right:
            st.markdown(
                "#### 明确阴性证据"
            )

            if negative:
                for item in sorted(
                    negative
                ):
                    st.markdown(
                        f"- ⛔ {item}"
                    )
            else:
                st.caption("无")

    # =====================================================================
    # 知识图谱展示
    # =====================================================================
    if st.session_state.get(
            "show_knowledge_graph",
            False,
    ):
        render_knowledge_graph_panel(
            results
        )

else:
    st.info(
        "👈 请在左侧录入患者信息，"
        "然后点击“开始智能辅助评估”。"
    )


st.divider()

st.caption(
    "⚠️ 竞赛原型采用双通道架构：急症分诊＋可解释鉴别诊断，"
    "并提供三态证据、组合规则、证据充分度和下一步检查推荐。"
    "真实临床部署前必须完成伦理、数据安全、专家评审和前瞻性验证。"
)
