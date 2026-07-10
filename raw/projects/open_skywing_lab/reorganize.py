#!/usr/bin/env python3
"""
根据预定义的五个类别重新组织 Markdown 文档中的二级标题（##）及内容。
自动清理标题中的加粗标记（**），支持输出目录自动创建。

用法:
    python reorganize.py <source.md> <target.md>
"""

import sys
import re
import os
from collections import defaultdict
from pathlib import Path

# ---------- 定义一级标题（顺序固定） ----------
CATEGORIES = [
    "一、课程理念、资源评估与总体设计",
    "二、具体课时教案与教学实施（含插件初步使用）",
    "三、飞行模拟插件调试与底层机制分析",
    "四、AI语音驾驶与自主飞行系统架构",
    "五、项目阶段实施与测试（含返航修复）",
]

# ---------- 二级标题 → 一级类别索引（0~4）的映射 ----------
TITLE_MAP = {
    # 类别一
    "评估从Python/C++转向Godot教学的可行性": 0,
    "AI编程时代教手动编程是否过时": 0,
    "能否让学生直接用AI Agent编码，教师只讲Godot知识": 0,
    "关于不让学生编码、只教Godot操作的教学方案评估": 0,
    "评估“Clear Code”Godot视频作为课程参考": 0,
    "对比Godotneers与Clear Code教程，并提出结合使用建议": 0,
    "评估改用Godot教学的价值及与Unreal Engine的对比": 0,
    "关于以模拟飞行项目为导向进行Godot教学的分析": 0,
    "评估“Simplified Flight Simulation Library”的教学价值": 0,
    "以飞行项目为载体学习Godot的课程设计": 0,
    "确认以飞行项目为主线而非视频课程": 0,
    "教师自身对飞行库的理解不足及其对教学的影响": 0,
    "课程轮替安排及对教学的影响": 0,
    "明确Blender与Godot课程的联动关系及个人开发角色": 0,
    "确认“课程领先于项目”及角色定位": 0,
    "教学顺序：先Godot基础，再用AI生成脚本做示范，最后进入飞行项目": 0,
    "根据飞行项目需求反推第1阶段教学内容并确认": 0,
    "用户重申飞行模拟项目背景及Claude确认课程方向": 0,
    "课程进度确认：当前教学方向正确": 0,
    "第1～9课课程总览": 0,
    "第10课起的课程总体规划": 0,
    "课程设计与“南天门”路线图的匹配度评价": 0,
    "修订版整体课程地图（第1-26课）": 0,
    "整合现有9课的整体课程地图（第1-33课）": 0,
    "课程方向确认：通过4个Example学习插件架构": 0,
    "示例迁移策略：不能只复制.gd和.tscn": 0,
    "评估当前课程设计是否在正确轨道上（含纠偏建议）": 0,

    # 类别二
    "第1节课教案：认识Godot编辑器与场景树": 1,
    "用户要求教案具体化及Claude提供带详细步骤的教案": 1,
    "第1课更新后的完整教案（含具体操作）": 1,
    "第2节完整教案：光照、Inspector与相机系统": 1,
    "纠正课程偏差并提供符合总体方案的第3课教案": 1,
    "第4课教案：@export 与属性面板的关系": 1,
    "第4课教案修订版：增加print调试与内容充实": 1,
    "第5课教案：变量、类型与表达式——读懂GDScript的第一步": 1,
    "第6课教案：函数——读懂飞行库代码的骨架": 1,
    "第8课教学方案（自定义函数）": 1,
    "第8课内容充实度评估与调整建议": 1,
    "第8课扩充版教案（自定义函数）": 1,
    "第6课练习代码的性质：飞行插件核心的基石而非临时练习": 1,
    "第8课设计疏漏：未复用第6课飞行模拟代码": 1,
    "第8课修订版教案：基于第6课飞行代码的函数教学": 1,
    "第9课教案：信号（Signal）——用广播代替直接调用": 1,
    "第10课教案：插件安装与场景搭建": 1,
    "第10课实践问题：对接真实插件脚本的调整方案": 1,
    "引擎模块代码分析与启动问题解决方案": 1,
    "引擎模块代码分析与启动问题解决": 1,   # 重复/变体，归入第二类
    "真实插件信号与属性命名不匹配的调整方案": 1,
    "第11课完整教案：插件核心结构导读": 1,
    "课程进度调整：实际课堂仅完成舵面设置与作用讲解": 1,
    "单独整理四大舵面操作入门教案（操作层面）": 1,

    # 类别三
    "飞行模拟调试：飞机朝向下方坠落（气动力方向错误）": 2,
    "修复后仍然振荡：气动力矩远超控制力矩": 2,
    "改用`apply_force`+力臂控制俯仰（参考官方示例）": 2,
    "锁定`Steering`模块冲突，禁用后仍无效": 2,
    "改用`steering_module.set_x/cmd`仍无效：舵面指令无作用": 2,
    "诊断：axis值写入成功但飞机无响应": 2,
    "最终方案：绕过Steering模块，直接`apply_torque`控制俯仰": 2,
    "课程设计方向偏离的反思与纠正": 2,
    "按下F键后飞机飞起来的完整调用链分析": 2,

    # 类别四
    "AI语音驾机架构方案可行性评估：架构正确但关键风险被低估": 3,
    "AI驾驶方案的核心风险不是LLM速度，而是分层架构——LLM不应进入实时控制回路": 3,
    "三层架构与黑板模式：LLM、状态机、PID的握手边界": 3,
    "语音模块复用分析：现有voice_bridge.py可复用，仅需替换业务接缝": 3,
    "Kimi2.7实施方案评审：方向正确，但需前置修正三项风险": 3,
    "抽象正确性框架对飞行项目的启示：控制≠学习，转换是真正痛点": 3,
    "系统架构价值评估与强化学习定位：三层执行栈+空置策略层，RL是可热插拔的屋顶设备而非地基": 3,

    # 类别五
    "阶段-1与阶段0实现：基础代码与MVP自动起飞平飞已验证完成": 4,
    "阶段2（航线与盘旋）技术评审：质变而非增量，需降级首轮验收目标": 4,
    "阶段2实施：横向串级PID与盘旋返航——首轮测试暴露速率失配问题并修复": 4,
    "返航测试失败：滚转发散集中在±90°航向，诊断为角度测量公式缺陷而非气动问题": 4,
    "诊断确认与修复验证：航向公式缺陷导致滚转发散，修正后返航成功": 4,
}

def clean_title(title: str) -> str:
    """去除标题首尾的加粗星号（**）及空白，并处理单侧星号的情况。"""
    # 移除首尾的 ** 或 *，并 strip
    title = re.sub(r'^\*\*|\*\*$', '', title)
    title = title.strip('*').strip()
    return title

def parse_blocks(lines):
    """
    解析所有行，返回 (前置文本, 二级标题块列表)
    每个块为 (title, content_lines)
    title 是清理后的完整标题行（去除 ** 和空白）
    content_lines 是标题行之后直到下一个二级标题或文件结束的所有行（不包括标题行）
    """
    blocks = []
    preamble = []
    i = 0
    # 提取前置内容（第一个二级标题之前）
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("## "):
            break
        preamble.append(line)
        i += 1

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("## "):
            raw_title = line.strip()[3:].strip()  # 去掉 "## "
            title = clean_title(raw_title)
            i += 1
            content = []
            while i < len(lines) and not lines[i].strip().startswith("## "):
                content.append(lines[i])
                i += 1
            blocks.append((title, content))
        else:
            i += 1
    return preamble, blocks

def main():
    if len(sys.argv) >= 3:
        src = sys.argv[1]
        dst = sys.argv[2]
    elif len(sys.argv) == 2:
        src = sys.argv[1]
        dst = "output.md"
    else:
        src = "input.md"
        dst = "output.md"

    # 确保输出目录存在
    out_dir = os.path.dirname(dst)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        with open(src, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"错误：文件 '{src}' 不存在。")
        sys.exit(1)

    preamble, blocks = parse_blocks(lines)

    # 按类别分组
    grouped = defaultdict(list)
    unknown = []

    for title, content in blocks:
        idx = TITLE_MAP.get(title)
        if idx is None:
            # 尝试进一步清理（如果还有残留星号）
            title_clean = title.strip('*').strip()
            idx = TITLE_MAP.get(title_clean)
            if idx is None:
                print(f"警告：未找到映射的标题 '{title}'，将归入第一类。")
                idx = 0
        grouped[idx].append((title, content))

    # 写入输出文件
    with open(dst, 'w', encoding='utf-8') as f:
        if preamble:
            f.writelines(preamble)
            if preamble and not preamble[-1].endswith('\n'):
                f.write('\n')
            f.write('\n')

        for cat_idx, cat_title in enumerate(CATEGORIES):
            f.write(f"# {cat_title}\n\n")
            blocks_in_cat = grouped.get(cat_idx, [])
            if not blocks_in_cat:
                f.write("（本节暂无内容）\n\n")
                continue
            for title, content in blocks_in_cat:
                f.write(f"## {title}\n")
                if content:
                    f.writelines(content)
                if content and not content[-1].endswith('\n'):
                    f.write('\n')
                f.write('\n')  # 块间空行

    print(f"成功重组文件，输出至 '{dst}'")

if __name__ == "__main__":
    main()