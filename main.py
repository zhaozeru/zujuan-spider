from lxml import html
import urllib.request
import json
import time
import pandas as pd
import traceback
import os
import re
import gzip
import random
delay = random.uniform(1.5, 3.0)

def get_user_input():
    """
    获取用户输入的配置信息
    """
    print("\n" + "=" * 60)
    print("请填写以下配置信息：")
    print("=" * 60)

    # 学段选择
    print("\n学段选项：")
    print("  1. 小学")
    print("  2. 初中")
    print("  3. 高中")
    xueduan_choice = input("请选择学段 (1/2/3，默认2): ").strip()
    xueduan_map = {'1': '小学', '2': '初中', '3': '高中'}
    xueduan = xueduan_map.get(xueduan_choice, '初中')

    # 学科选择
    print("\n学科选项：")
    print("  1. 语文")
    print("  2. 数学")
    print("  3. 英语")
    print("  4. 物理")
    print("  5. 化学")
    print("  6. 生物")
    print("  7. 历史")
    print("  8. 地理")
    print("  9. 政治")
    xueke_choice = input("请选择学科 (1-9，默认4物理): ").strip()
    xueke_map = {
        '1': '语文', '2': '数学', '3': '英语', '4': '物理',
        '5': '化学', '6': '生物', '7': '历史', '8': '地理', '9': '政治'
    }
    xueke = xueke_map.get(xueke_choice, '物理')

    # 学科对应的数字ID（用于组装API）
    xueke_id_map = {
        '语文': 1, '数学': 2, '英语': 3, '物理': 4,
        '化学': 5, '生物': 6, '历史': 7, '地理': 8, '政治': 9
    }
    xueke_id = xueke_id_map.get(xueke, 4)

    # 版本URL文件路径
    default_url_file = os.path.join('data', f'{xueduan}{xueke}各版本网址.txt')
    print(f"\n版本URL文件路径 (默认: {default_url_file})")
    url_file_path = input("请输入路径 (直接回车使用默认): ").strip()
    if not url_file_path:
        url_file_path = default_url_file

    # 输出文件路径（相对路径）
    default_output = os.path.join('output', f'{xueduan}{xueke}目录结构.xlsx')
    print(f"\n输出文件路径 (默认: {default_output})")
    output_path = input("请输入路径 (直接回车使用默认): ").strip()
    if not output_path:
        output_path = default_output

    # 请求延迟
    delay_input = input("\n请求间隔秒数 (默认1.5秒，建议0.5-2秒): ").strip()
    delay = float(delay_input) if delay_input else 1.5

    # Cookie（可选）
    print("\n" + "-" * 40)
    print("提示：如果版本页面需要登录，请提供Cookie")
    print("获取方法：浏览器F12 -> 网络 -> 任意请求 -> 复制Cookie")
    cookie = input("请粘贴Cookie值（直接回车跳过）: ").strip()
    if not cookie:
        cookie = None

    return {
        'xueduan': xueduan,
        'xueke': xueke,
        'xueke_id': xueke_id,
        'url_file_path': url_file_path,
        'output_path': output_path,
        'delay': delay,
        'cookie': cookie
    }


def load_version_urls(file_path):
    """
    从文件读取版本URL列表
    每行一个URL，支持#注释
    """
    try:
        file_dir = os.path.dirname(file_path)
        if file_dir and not os.path.exists(file_dir):
            os.makedirs(file_dir, exist_ok=True)
            print(f"提示: 目录 '{file_dir}' 已创建，请放入URL文件后重新运行")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            urls = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)

        print(f"成功读取 {len(urls)} 个版本URL")
        return urls
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {file_path}")
        print(f"请创建该文件，每行一个版本URL")
        return []
    except Exception as e:
        print(f"读取文件失败: {e}")
        return []




USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def fetch_version_page(url, cookie=None, delay=1.5):
    time.sleep(delay)

    headers = {
        'User-Agent': random.choice(USER_AGENTS),  # 随机选择UA
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://zujuan.xkw.com/',
    }

    if cookie:
        headers['Cookie'] = cookie

    req = urllib.request.Request(url, headers=headers)

    # 添加重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                compressed_data = response.read()
                content_encoding = response.headers.get('Content-Encoding', '')

                if 'gzip' in content_encoding:
                    html_content = gzip.decompress(compressed_data).decode('utf-8')
                else:
                    html_content = compressed_data.decode('utf-8', errors='ignore')

                # 验证是否获取到完整内容
                if 'chapter_textbooks' in html_content:
                    return html_content
                else:
                    print(f"    警告: HTML中缺少chapter_textbooks，尝试 {attempt + 1}/{max_retries}")
                    time.sleep(2)  # 等待后重试

        except Exception as e:
            print(f"    请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(3)  # 等待后重试
            else:
                return None

    return None


def parse_version_and_ceci_from_html(html_content, url):
    """
    从HTML中解析版本名称和册次列表
    返回: (version_name, ceci_list)
    """
    tree = html.fromstring(html_content)

    # 从URL中提取版本ID
    version_id_match = re.search(r'/zj(\d+)/', url)
    version_id = version_id_match.group(1) if version_id_match else ''

    # 获取版本名称：从版本容器中找到当前选中的版本（class包含selected）
    version_name = ''

    # 查找版本容器
    version_container = tree.xpath('//div[@id="chapter_textbook_version"]')
    if version_container:
        # 查找选中的版本（class包含selected）
        selected_link = version_container[0].xpath('.//a[contains(@class, "selected")]')
        if selected_link:
            version_name = selected_link[0].text_content().strip()

        # 如果没找到选中的版本，尝试获取第一个非空版本（可选）
        if not version_name:
            first_link = version_container[0].xpath('.//a[@versionid]')
            if first_link:
                version_name = first_link[0].text_content().strip()

    # 如果还是没找到，使用默认名称
    if not version_name:
        version_name = f"版本_{version_id}"

    # 解析册次列表：从册次容器中提取所有册次
    ceci_list = []

    # 查找册次容器（直接通过id查找）
    ceci_container = tree.xpath('//div[@id="chapter_textbooks"]')

    if ceci_container:
        # 在册次容器内查找所有带有chapter-id属性的a标签
        ceci_links = ceci_container[0].xpath('.//a[@chapter-id]')
        for link in ceci_links:
            ceci_id = link.get('chapter-id')
            ceci_name = link.text_content().strip()
            if ceci_id and ceci_name:
                ceci_list.append({
                    'ceci_id': ceci_id,
                    'ceci_name': ceci_name
                })

        # 调试输出（可选）
        if ceci_list:
            print(f"  找到册次: {', '.join([c['ceci_name'] for c in ceci_list])}")
        else:
            print(f"  警告: 在chapter_textbooks容器中未找到带chapter-id的a标签")
            # 可选：输出容器内容以便调试
            container_html = html.tostring(ceci_container[0], encoding='unicode')
            print(f"  容器内容: {container_html[:200]}...")

    return version_name, ceci_list

def save_all_version_ceci_mapping(all_version_ceci, xueduan, xueke):
    """
    保存所有版本的册次映射到txt文件
    """
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'{xueduan}{xueke}_所有版本册次映射.txt')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {xueduan}{xueke} 所有教材版本与册次映射表\n")
        f.write("# " + "=" * 50 + "\n\n")

        for version_url, version_data in all_version_ceci.items():
            f.write(f"【{version_data['name']}】\n")
            f.write(f"  URL: {version_url}\n")
            for ceci in version_data['ceci_list']:
                f.write(f"  ├─ {ceci['ceci_name']} (ID: {ceci['ceci_id']})\n")
            f.write("\n")

    print(f"所有版本册次映射已保存到: {output_path}")
    return output_path


def generate_api_urls(version_name, ceci_list, xueke_id):
    """
    根据版本名称、册次列表和学科ID生成API URL列表
    """
    api_urls = []
    url_info = []

    for ceci in ceci_list:
        ceci_id = ceci['ceci_id']
        ceci_name = ceci['ceci_name']

        # 组装API URL
        api_url = f"https://static.zxxk.com/zujuan/tree/ct_{xueke_id}_{ceci_id}.json"

        api_urls.append(api_url)
        url_info.append({
            'version_name': version_name,
            'ceci_name': ceci_name,
            'ceci_id': ceci_id,
            'api_url': api_url
        })

        print(f"  生成API: {api_url}")

    return api_urls, url_info


def save_all_api_urls_to_txt(all_url_info, xueduan, xueke):
    """
    保存所有API URL列表到txt文件
    """
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f'{xueduan}{xueke}_所有API接口.txt')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {xueduan}{xueke} 所有API接口列表\n")
        f.write("# " + "=" * 80 + "\n\n")

        # 按版本分组写入
        current_version = None
        for info in all_url_info:
            if info['version_name'] != current_version:
                current_version = info['version_name']
                f.write(f"\n## 版本: {current_version}\n")
                f.write("-" * 60 + "\n")

            f.write(f"册次: {info['ceci_name']} (ID: {info['ceci_id']})\n")
            f.write(f"API: {info['api_url']}\n\n")

        # 单独列出所有API URL
        f.write("\n# 纯API URL列表（每行一个）\n")
        f.write("# " + "=" * 80 + "\n")
        for info in all_url_info:
            f.write(f"{info['api_url']}\n")

    print(f"所有API列表已保存到: {output_path}")
    return output_path


def fetch_all_api_data(urls, url_info, xueduan, xueke, delay=1.5):
    """
    批量请求所有API并解析数据
    """
    all_data = []

    for idx, (url, info) in enumerate(zip(urls, url_info), 1):
        try:
            print(f"[{idx}/{len(urls)}] 请求: {info['version_name']} - {info['ceci_name']}")
            print(f"  URL: {url}")
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Referer': 'https://zujuan.xkw.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            parsed_data = parse_api_data(data, info['version_name'], info['ceci_name'], xueduan, xueke)
            all_data.extend(parsed_data)

            print(f"  -> 解析到 {len(parsed_data)} 条记录")

            if idx < len(urls):
                time.sleep(delay)

        except Exception as e:
            print(f"  错误: {e}")
            traceback.print_exc()
            continue

    return all_data


def parse_api_data(data, version, ceci, xueduan, xueke):
    """
    解析单个API返回的数据
    """
    results = []

    if 'children' in data:
        for child in data['children']:
            leaf_paths = extract_path_until_no_children(child, [])

            for path in leaf_paths:
                record = {
                    '学段': xueduan,
                    '学科': xueke,
                    '教材版本': version,
                    '册次': ceci,
                }

                # 动态添加层级
                level_names = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
                               '十一', '十二', '十三', '十四', '十五']
                for level_idx, level_name in enumerate(path, start=1):
                    if level_idx <= len(level_names):
                        record[f'{level_names[level_idx - 1]}级目录'] = level_name
                    else:
                        record[f'{level_idx}级目录'] = level_name

                results.append(record)

    return results


def extract_path_until_no_children(node, current_path):
    """
    递归提取节点路径，直到没有children为止
    """
    title = node.get('title', '')
    children = node.get('children', [])

    new_path = current_path + [title] if title else current_path

    if not children:
        return [new_path]
    else:
        all_paths = []
        for child in children:
            all_paths.extend(extract_path_until_no_children(child, new_path))
        return all_paths


def save_to_excel(data, output_path):
    """
    将数据保存为Excel文件
    """
    if not data:
        print("没有数据可保存")
        return False

    df = pd.DataFrame(data)

    def get_level_order(col_name):
        level_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                     '七': 7, '八': 8, '九': 9, '十': 10}
        if '级目录' in col_name:
            for key in level_map:
                if col_name.startswith(key):
                    return level_map[key]
            match = re.match(r'(\d+)级目录', col_name)
            if match:
                return int(match.group(1))
        return 999

    fixed_cols = ['学段', '学科', '教材版本', '册次']
    existing_fixed = [col for col in fixed_cols if col in df.columns]
    dynamic_cols = [col for col in df.columns if col not in fixed_cols]
    dynamic_cols.sort(key=get_level_order)

    df = df[existing_fixed + dynamic_cols]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"数据已保存到: {output_path}")
    print(f"共 {len(df)} 行数据，最大层级: {len(dynamic_cols)} 级")
    return True


# ==================== 主程序 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("通用目录结构抓取工具")
    print("=" * 60)

    # 第一步：获取用户配置
    config = get_user_input()

    # 第二步：读取版本URL列表
    print("\n" + "=" * 60)
    print("第一步：读取版本URL列表")
    print("=" * 60)

    version_urls = load_version_urls(config['url_file_path'])
    if not version_urls:
        print("没有找到版本URL，程序退出")
        exit()

    print(f"共找到 {len(version_urls)} 个版本URL")

    # 第三步：遍历每个URL，请求并解析版本和册次
    print("\n" + "=" * 60)
    print("第二步：请求并解析每个版本的册次信息")
    print("=" * 60)

    all_version_ceci = {}  # {url: {'name': version_name, 'ceci_list': [...]}}

    for idx, url in enumerate(version_urls, 1):
        print(f"\n[{idx}/{len(version_urls)}] 处理: {url}")

        html_content = fetch_version_page(url, config['cookie'], 0 if idx == 1 else config['delay'])
        if not html_content:
            print(f"  警告: 请求失败，跳过")
            continue

        version_name, ceci_list = parse_version_and_ceci_from_html(html_content, url)

        if ceci_list:
            all_version_ceci[url] = {
                'name': version_name,
                'ceci_list': ceci_list
            }
            print(f"  版本名称: {version_name}")
            print(f"  册次数量: {len(ceci_list)}")
        else:
            print(f"  警告: 未解析到册次信息，跳过")

    if not all_version_ceci:
        print("\n错误: 没有成功获取到任何版本的册次信息")
        exit()

    # 第四步：保存所有版本的册次映射
    print("\n" + "=" * 60)
    print("第三步：保存版本册次映射")
    print("=" * 60)

    mapping_file = save_all_version_ceci_mapping(all_version_ceci, config['xueduan'], config['xueke'])

    # 第五步：生成所有API URL
    print("\n" + "=" * 60)
    print("第四步：生成所有API接口列表")
    print("=" * 60)

    all_api_urls = []
    all_url_info = []

    for version_url, version_data in all_version_ceci.items():
        api_urls, url_info = generate_api_urls(version_data['name'], version_data['ceci_list'], config['xueke_id'])
        all_api_urls.extend(api_urls)
        all_url_info.extend(url_info)

    print(f"\n共生成 {len(all_api_urls)} 个API接口")

    # 保存API列表
    api_file = save_all_api_urls_to_txt(all_url_info, config['xueduan'], config['xueke'])

    # 第六步：批量请求所有API
    print("\n" + "=" * 60)
    print("第五步：批量请求API并解析目录结构")
    print("=" * 60)

    all_data = fetch_all_api_data(
        urls=all_api_urls,
        url_info=all_url_info,
        xueduan=config['xueduan'],
        xueke=config['xueke'],
        delay=config['delay']
    )

    # 第七步：保存为Excel
    print("\n" + "=" * 60)
    print("第六步：保存结果")
    print("=" * 60)

    if save_to_excel(all_data, config['output_path']):
        print("\n" + "=" * 60)
        print("处理完成！")
        print(f"生成的文件：")
        print(f"  1. 版本册次映射: {mapping_file}")
        print(f"  2. API列表: {api_file}")
        print(f"  3. 目录结构: {config['output_path']}")
        print(f"\n统计信息：")
        print(f"  - 处理版本数: {len(all_version_ceci)}")
        print(f"  - 生成API数: {len(all_api_urls)}")
        print(f"  - 目录记录数: {len(all_data)}")
        print("=" * 60)
    else:
        print("\n保存失败，请检查数据")