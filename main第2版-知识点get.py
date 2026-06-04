import requests
import pandas as pd
import json
import os
import random
from typing import List, Dict, Optional



USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]
xiaoxue_url = {
    "小学语文": "https://static.zxxk.com/zujuan/tree/lk_24.json?v=1779092252669&withCredentials=true"
}
chuzhong_url={
    "初中物理":"https://static.zxxk.com/zujuan/tree/lk_4.json?v=1776906282742&withCredentials=true",
    "初中化学":"https://static.zxxk.com/zujuan/tree/lk_5.json?v=1776906282742&withCredentials=true",
    "初中生物":"https://static.zxxk.com/zujuan/tree/lk_6.json?v=1776906282742&withCredentials=true",
    "初中地理":"https://static.zxxk.com/zujuan/tree/lk_9.json?v=1778296900226&withCredentials=true",
    "初中历史":"https://static.zxxk.com/zujuan/tree/lk_8.json?v=1776906282742&withCredentials=true"
}
gaozhong_url={
    "高中语文":"https://static.zxxk.com/zujuan/tree/lk_10.json?v=1776906282742&withCredentials=true",
    "高中数学":"https://static.zxxk.com/zujuan/tree/lk_11.json?v=1776906282742&withCredentials=true",
    "高中英语":"https://static.zxxk.com/zujuan/tree/lk_12.json?v=1776906282742&withCredentials=true",
    "高中物理":"https://static.zxxk.com/zujuan/tree/lk_13.json?v=1776906282742&withCredentials=true",
    "高中化学":"https://static.zxxk.com/zujuan/tree/lk_14.json?v=1776906282742&withCredentials=true",
    "高中生物":"https://static.zxxk.com/zujuan/tree/lk_15.json?v=1776906282742&withCredentials=true",
    "高中政治":"https://static.zxxk.com/zujuan/tree/lk_16.json?v=1776906282742&withCredentials=true",
    "高中历史":"https://static.zxxk.com/zujuan/tree/lk_17.json?v=1776906282742&withCredentials=true",
    "高中地理":"https://static.zxxk.com/zujuan/tree/lk_18.json?v=1776906282742&withCredentials=true"
}


def get_random_user_agent() -> str:
    """随机获取一个User-Agent"""
    return random.choice(USER_AGENTS)


def fetch_knowledge_tree(url: str) -> Optional[Dict]:
    """
    请求API获取知识点树JSON数据

    Args:
        url: API接口地址

    Returns:
        解析后的JSON数据字典，失败返回None
    """
    try:
        headers = {
            'User-Agent': get_random_user_agent()
        }
        print(f"使用User-Agent: {headers['User-Agent'][:50]}...")

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功

        # 尝试解析JSON
        data = response.json()
        print(f"✓ 成功获取知识点树数据")
        return data
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ JSON解析失败: {e}")
        return None


def extract_paths(node: Dict, path_so_far: List[str], all_paths: List[List[str]], max_depth: int = 10) -> None:
    """
    递归遍历知识点树，提取所有路径

    Args:
        node: 当前节点
        path_so_far: 已积累的路径
        all_paths: 存储所有路径的列表
        max_depth: 最大递归深度限制
    """
    # 获取节点标题
    title = node.get("title", "")
    if not title:
        title = node.get("name", "")  # 兼容不同的字段名

    current_path = path_so_far + [title]

    # 检查深度限制
    if len(current_path) > max_depth:
        print(f"警告: 路径深度超过{max_depth}，已截断: {current_path}")
        return

    # 如果有子节点，继续递归
    children = node.get("children", [])
    if children:
        for child in children:
            extract_paths(child, current_path, all_paths, max_depth)
    else:
        # 叶子节点，记录完整路径（前提是路径不为空）
        if current_path and any(current_path):  # 确保路径不为空
            all_paths.append(current_path)

def build_dataframe_from_tree(data: Dict, max_depth: int = 5) -> pd.DataFrame:
    """
    从知识点树构建DataFrame

    Args:
        data: 知识点树JSON数据
        max_depth: 最大深度（默认为5级）

    Returns:
        包含知识点路径的DataFrame
    """
    all_paths = []

    # 获取根节点下的子节点
    children = data.get("children", [])
    if not children:
        # 如果数据本身就是节点
        children = [data]

    # 递归提取所有路径
    for root_child in children:
        extract_paths(root_child, [], all_paths, max_depth)

    if not all_paths:
        print("警告: 未提取到任何知识点路径")
        return pd.DataFrame()

    # 统计最大层级深度
    actual_max_depth = max(len(path) for path in all_paths)
    print(f"实际最大层级深度: {actual_max_depth}")

    # 限制输出深度（如果需要）
    output_depth = min(max_depth, actual_max_depth)
    if output_depth < actual_max_depth:
        print(f"注意: 只输出前{output_depth}级知识点")

    # 生成动态表头
    columns = [f"{i}级知识点" for i in range(1, output_depth + 1)]
    print(f"表头: {columns}")

    # 构建DataFrame行数据
    rows = []
    for path in all_paths:
        # 只取前output_depth级
        truncated_path = path[:output_depth]
        # 补齐列数
        row = truncated_path + [""] * (output_depth - len(truncated_path))
        rows.append(row)

    # 创建DataFrame
    df = pd.DataFrame(rows, columns=columns)

    # 去除全空的行（所有列都为空）
    df = df.dropna(how='all')

    print(f"共提取 {len(df)} 条知识点路径")

    return df


def save_to_excel(df: pd.DataFrame, filename: str) -> bool:
    """
    保存DataFrame到Excel文件

    Args:
        df: 要保存的DataFrame
        filename: 输出文件名

    Returns:
        保存成功返回True，失败返回False
    """
    try:
        # 确保output目录存在
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"✓ 创建目录: {output_dir}")

        # 完整的文件路径
        filepath = os.path.join(output_dir, filename)

        # 保存Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='知识点目录', index=False)

            # 调整列宽
            worksheet = writer.sheets['知识点目录']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"✓ 文件已保存: {filepath}")
        return True
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        return False


def print_sample_data(df: pd.DataFrame, n: int = 5) -> None:
    """
    打印前n行数据示例

    Args:
        df: DataFrame对象
        n: 显示的行数
    """
    if df.empty:
        print("无数据可显示")
        return

    print(f"\n数据示例（前{n}行）:")
    print("=" * 80)
    for idx, row in df.head(n).iterrows():
        path_parts = [str(val) for val in row.values if pd.notna(val) and val]
        if path_parts:
            print(f"{idx + 1}. {' > '.join(path_parts)}")
    print("=" * 80)


def select_subject() -> tuple:
    """
    用户交互选择学段和学科

    Returns:
        (学段, 学科, URL) 的元组
    """
    print("\n" + "=" * 50)
    print("知识点目录抓取工具")
    print("=" * 50)

    # 选择学段
    while True:
        print("\n请选择学段:")
        print("1. 小学")      # 添加这一行
        print("2. 初中")
        print("3. 高中")      # 修改为3
        print("0. 退出")

        choice = input("请输入选项 (0-3): ").strip()  # 修改为0-3

        if choice == "0":
            return None, None, None
        elif choice == "1":
            xueduan = "小学"   # 添加小学
            subject_dict = xiaoxue_url  # 使用小学字典
            break
        elif choice == "2":
            xueduan = "初中"
            subject_dict = chuzhong_url
            break
        elif choice == "3":    # 修改为3
            xueduan = "高中"
            subject_dict = gaozhong_url
            break
        else:
            print("输入无效，请重新选择！")

    # 选择学科
    while True:
        print(f"\n请选择{xueduan}学科:")
        subjects = list(subject_dict.keys())
        for i, subject in enumerate(subjects, 1):
            print(f"{i}. {subject}")
        print("0. 返回上一级")

        choice = input(f"请输入选项 (0-{len(subjects)}): ").strip()

        if choice == "0":
            return select_subject()  # 返回重新选择学段
        elif choice.isdigit() and 1 <= int(choice) <= len(subjects):
            index = int(choice) - 1
            subject = subjects[index]
            url = subject_dict[subject]
            print(f"\n✓ 已选择: {xueduan} - {subject}")
            return xueduan, subject, url
        else:
            print("输入无效，请重新选择！")


if __name__ == "__main__":
    # 配置参数
    max_depth = 10  # 最大深度

    print("\n" + "=" * 50)
    print("知识点目录抓取工具")
    print("=" * 50)

    # 选择执行模式
    print("\n请选择执行模式:")
    print("1. 自动抓取整个学段的所有学科")
    print("2. 手动选择具体学科")
    print("0. 退出")

    mode_choice = input("请输入选项 (0-2): ").strip()

    if mode_choice == "0":
        print("\n程序退出")
        exit(0)

    elif mode_choice == "1":
        # 模式1：自动抓取整个学段
        print("\n请选择学段:")
        print("1. 小学")
        print("2. 初中")
        print("3. 高中")

        xueduan_choice = input("请输入选项 (1-3): ").strip()

        if xueduan_choice == "1":
            xueduan = "小学"
            subject_dict = xiaoxue_url
        elif xueduan_choice == "2":
            xueduan = "初中"
            subject_dict = chuzhong_url
        elif xueduan_choice == "3":
            xueduan = "高中"
            subject_dict = gaozhong_url
        else:
            print("输入无效，程序退出")
            exit(1)

        print(f"\n开始自动抓取{xueduan}所有学科...")

        # 遍历所有学科
        success_count = 0
        for subject, url in subject_dict.items():
            print(f"\n{'=' * 50}")
            print(f"正在抓取: {xueduan} - {subject}")
            print(f"{'=' * 50}")

            # 获取知识点树数据
            tree_data = fetch_knowledge_tree(url)
            if not tree_data:
                print(f"✗ {subject} 抓取失败")
                continue

            # 构建DataFrame
            df = build_dataframe_from_tree(tree_data, max_depth=max_depth)

            if df.empty:
                print(f"✗ {subject} 无有效数据")
                continue

            # 保存到Excel
            filename = f"{xueduan}{subject}知识点.xlsx"
            if save_to_excel(df, filename):
                success_count += 1
                print(f"✓ {subject} 抓取成功")

        print(f"\n{'=' * 50}")
        print(f"自动抓取完成！成功: {success_count}/{len(subject_dict)}")
        print(f"{'=' * 50}")

    elif mode_choice == "2":
        # 模式2：手动选择具体学科
        print("\n请选择学段:")
        print("1. 小学")
        print("2. 初中")
        print("3. 高中")

        xueduan_choice = input("请输入选项 (1-3): ").strip()

        if xueduan_choice == "1":
            xueduan = "小学"
            subject_dict = xiaoxue_url
        elif xueduan_choice == "2":
            xueduan = "初中"
            subject_dict = chuzhong_url
        elif xueduan_choice == "3":
            xueduan = "高中"
            subject_dict = gaozhong_url
        else:
            print("输入无效，程序退出")
            exit(1)

        # 选择学科
        print(f"\n请选择{xueduan}学科:")
        subjects = list(subject_dict.keys())
        for i, subject in enumerate(subjects, 1):
            print(f"{i}. {subject}")

        subject_choice = input(f"请输入选项 (1-{len(subjects)}): ").strip()

        if not subject_choice.isdigit() or not (1 <= int(subject_choice) <= len(subjects)):
            print("输入无效，程序退出")
            exit(1)

        index = int(subject_choice) - 1
        subject = subjects[index]
        url = subject_dict[subject]

        print(f"\n✓ 已选择: {xueduan} - {subject}")
        print(f"\n开始抓取知识点目录...")
        print(f"学段: {xueduan}")
        print(f"学科: {subject}")
        print(f"请求URL: {url}")
        print(f"最大深度: {max_depth}级")

        # 获取知识点树数据
        tree_data = fetch_knowledge_tree(url)
        if not tree_data:
            print("程序终止")
            exit(1)

        # 构建DataFrame
        df = build_dataframe_from_tree(tree_data, max_depth=max_depth)

        if df.empty:
            print("未获取到有效数据，程序终止")
            exit(1)

        # 打印示例数据
        print_sample_data(df)

        # 保存到Excel
        filename = f"{xueduan}{subject}知识点.xlsx"
        save_to_excel(df, filename)

        # 输出统计信息
        print(f"\n统计信息:")
        print(f"- 学段学科: {xueduan}{subject}")
        print(f"- 总知识点路径数: {len(df)}")
        print(f"- 实际深度: {len(df.columns)}级")
        print(f"- 空值率: {(df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100):.1f}%")
        print(f"\n✓ 完成！文件已保存到 output/{filename}")

    else:
        print("输入无效，程序退出")
        exit(1)


