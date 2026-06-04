import urllib.request
import json
import time
import csv
import re

# 版本映射字典
VERSION_MAP = {
    "195850": "人教版",
    "61673": "人教版（2012）",
    "198828": "外研版",
    "61894": "外研版（2012）",
    "198829": "译林版",
    "61541": "译林版（2012）",
    "199895": "沪教版",
    "61413": "沪教牛津版（广州深圳沈阳通用）（2012）",
    "199897": "冀教版",
    "60997": "冀教版（2012）",
    "208571": "仁爱科普版",
    "61772": "仁爱科普版（2012）",
    "199896": "沪教版（五四学制）",
    "60477": "牛津上海版（试用本）（2007）",
    "198831": "鲁教版（五四学制）",
    "60309": "鲁教版（五四学制）（2012）",
    "198830": "北师大版",
    "60723": "北师大版（2013）",
    "209647": "教科版（五四学制）",
    "62523": "教科版（五四学制）（2012）",
    "209648": "沪外教版",
    "62445": "北京课改版（北京出版社）（2007）",
    "60653": "人教版（五四学制）（2012）",
    "62626": "新世纪版（试用本）（2016）"
}

# 读取 API 列表
with open(r'C:\Users\13652\Desktop\初中英语.txt', 'r', encoding='utf-8') as f:
    urls = [line.strip() for line in f if line.strip()]

print(f"总共 {len(urls)} 个 API 接口需要请求")

# 存储所有数据
all_data = []

def parse_node(node, data_list, xueduan, xueke, version, ceci, chapter1, chapter2="", chapter3=""):
    """递归解析树形节点"""
    title = node.get('title', '')
    children = node.get('children', [])

    # 判断层级
    if not chapter1:
        # 一级目录（章）
        if children:
            for child in children:
                parse_node(child, data_list, xueduan, xueke, version, ceci, title, "", "")
        else:
            # 叶子节点
            data_list.append({
                '学段': xueduan,
                '学科': xueke,
                '教材版本': version,
                '册次': ceci,
                '一级目录(章)': title,
                '二级目录(节)': '',
                '三级目录(小节)': '',
                '四级目录(子内容)': ''
            })
    elif not chapter2:
        # 二级目录（节）
        if children:
            for child in children:
                parse_node(child, data_list, xueduan, xueke, version, ceci, chapter1, title, "")
        else:
            data_list.append({
                '学段': xueduan,
                '学科': xueke,
                '教材版本': version,
                '册次': ceci,
                '一级目录(章)': chapter1,
                '二级目录(节)': title,
                '三级目录(小节)': '',
                '四级目录(子内容)': ''
            })
    elif not chapter3:
        # 三级目录（小节）
        if children:
            for child in children:
                parse_node(child, data_list, xueduan, xueke, version, ceci, chapter1, chapter2, title)
        else:
            data_list.append({
                '学段': xueduan,
                '学科': xueke,
                '教材版本': version,
                '册次': ceci,
                '一级目录(章)': chapter1,
                '二级目录(节)': chapter2,
                '三级目录(小节)': title,
                '四级目录(子内容)': ''
            })
    else:
        # 四级目录（子内容）
        data_list.append({
            '学段': xueduan,
            '学科': xueke,
            '教材版本': version,
            '册次': ceci,
            '一级目录(章)': chapter1,
            '二级目录(节)': chapter2,
            '三级目录(小节)': chapter3,
            '四级目录(子内容)': title
        })

# 请求每个 API
for idx, url in enumerate(urls, 1):
    try:
        print(f"[{idx}/{len(urls)}] 请求: {url}")

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        # 获取册次（最外层的 title）
        ceci = data.get('title', '')

        # 获取教材版本（最外层的 parentId）
        parent_id = data.get('parentId', '')
        version = VERSION_MAP.get(parent_id, '')

        print(f"  -> 册次: {ceci}, 版本: {version}, parentId: {parent_id}")

        # 解析数据结构
        if 'children' in data:
            for child in data['children']:
                parse_node(child, all_data, "初中", "英语", version, ceci, "")

        # 间隔 1.5 秒
        if idx < len(urls):
            time.sleep(1.5)

    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
        continue

print(f"\n总共收集到 {len(all_data)} 条记录")

# 保存为 CSV 文件
output_path = r'C:\Users\13652\Desktop\初中英语目录结构.csv'

headers = ['学段', '学科', '教材版本', '册次', '一级目录(章)', '二级目录(节)', '三级目录(小节)', '四级目录(子内容)']

with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(all_data)

print(f"数据已保存到: {output_path}")

# 转换为 Excel
print("正在转换为 Excel 格式...")
import subprocess
result = subprocess.run([
    r'D:\PyCharm\conda_forge\python.exe', '-c',
    f"import pandas as pd; df = pd.read_csv(r'{output_path}', encoding='utf-8-sig'); "
    f"df.to_excel(r'C:\\Users\\13652\\Desktop\\初中英语目录结构.xlsx', index=False, engine='openpyxl'); "
    f"print(f'转换完成，共 {{len(df)}} 行数据')"
], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("错误:", result.stderr)
