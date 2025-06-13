import requests
from bs4 import BeautifulSoup, Tag
import time
import os
import re
from urllib.parse import urlparse
import csv
import zhconv
import glob
import pandas as pd
import pymysql
from pymysql.constants import CLIENT
import yaml
from pathlib import Path

def load_config_from_yaml(config_file):
    """从 YAML 文件加载配置"""
    try:
        with Path(config_file).open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件时出错: {e}")
        return {}

def import_csv_to_mysql(csv_file):
    config = load_config_from_yaml("config.yaml")
    try:
        host = config.get('host', 'localhost')
        user = config.get('user')
        password = config.get('password')
        database = config.get('database')
        table = 'history_affair'

        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            client_flag=CLIENT.LOCAL_FILES,
            local_infile=True  # 显式启用本地加载
        )

        with conn.cursor() as cursor:
            cursor.execute("SHOW VARIABLES LIKE 'local_infile'")
            result = cursor.fetchone()
            print(f"当前local_infile状态: {result[1]}")
            if result[1] != 'ON':
                print("正在启用local_infile...")
                cursor.execute("SET GLOBAL local_infile = ON")
                cursor.execute("SET SESSION local_infile = ON")
                cursor.execute("SHOW VARIABLES LIKE 'local_infile'")
                new_result = cursor.fetchone()
                print(f"启用后状态: {new_result[1]}")

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table}` (
                `year` INT,
                `month` INT,
                `day` INT,
                `affair` VARCHAR(255) NOT NULL,
                `type` VARCHAR(16) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
            """
            cursor.execute(create_table_sql)
            # 构建导入SQL（注意处理日期和字符类型）
            load_data_sql = f"""
            LOAD DATA LOCAL INFILE '{csv_file}'
            INTO TABLE `{table}`
            FIELDS TERMINATED BY ','
            ENCLOSED BY '"'
            LINES TERMINATED BY '\r\n'
            IGNORE 1 ROWS
            (`year`, `month`, `day`, `affair`, `type`)
            """
            cursor.execute(load_data_sql)

            cursor.execute("""update history_affair
            set type = 'affair'
            where type = ''
            """)

            # 提交事务并获取导入行数
            conn.commit()
            print("插入成功")

    except pymysql.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
    except Exception as e:
        print(f"导入失败: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("数据库连接已关闭")

def get_wikipedia_content(month, day):
    url = f"https://zh.wikipedia.org/wiki/{month}月{day}日"
    type_dict = {
        "大事记": "affair",
        "大事纪": "affair",
        "出生": "birth",
        "逝世": "death",
        "节假日和习俗": "festival",
        "节假日与习俗": "festival",
    }
    affair_list = []
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 发送HTTP请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        text = re.sub(r'<link([^>]+)>', r'<link\1/>', response.text)
        # 解析HTML内容
        soup = BeautifulSoup(text, 'html.parser')
        main_content = soup.find('div', class_='mw-content-ltr mw-parser-output').find('meta')
        affair_type = ""
        for child in main_content.children:
            if not isinstance(child, Tag):
                continue
            name = None
            ul = None
            if child.name == 'div' and child.get('class', 'null')[-1] == 'mw-heading2':
                name = child.find('h2')
            if child.name == 'ul':
                ul = child
            if name is not None:
                if zhconv.convert(name.get('id'), 'zh-cn') not in type_dict:
                    break
                affair_type = type_dict[zhconv.convert(name.get('id'), 'zh-cn')]
            if ul is not None:
                for li in ul.children:
                    affair = zhconv.convert(li.get_text(strip=True), 'zh-cn')
                    if affair == "":
                        continue
                    if affair == '1':
                        return affair_list
                    affair_list.append(line_praser(affair, affair_type, month, day))

        return affair_list

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return "错误", str(e)
    except Exception as e:
        print(f"处理页面时出错: {e}")
        return "错误", str(e)

def line_praser(text, affair_type, month, day):
    if affair_type != "festival":
        result = text.split("年：", 1)
        return {
            "year": "" if result[0] == result[-1] else result[0].replace('前', '-'),
            "month": month,
            "day": day,
            "affair": result[-1],
            "type": affair_type
        }
    else:
        return {
            "year": "",
            "month": month,
            "day": day,
            "affair": text,
            "type": affair_type
        }

def json_to_csv(json_data, csv_file_path, month ,day, bad_list):
    """将JSON数据写入CSV文件"""
    if not json_data:
        print("错误：JSON数据为空")
        return False

    try:
        # 获取JSON数据的键作为CSV的列名
        fieldnames = json_data[0].keys() if json_data else []

        # 打开CSV文件并写入数据
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 写入表头
            writer.writeheader()

            # 写入数据行
            writer.writerows(json_data)
        return True

    except Exception as e:
        bad_list.append([month, day])
        print(f"写入CSV时出错: {e}, {month}月{day}日")
        return False

def merge_affair_csvs(input_dir, output_file='merged_affair.csv'):
    input_dir = os.path.join(input_dir, '')
    csv_files = glob.glob(f"{input_dir}/affair*.csv")
    if not csv_files:
        print(f"在目录 {input_dir} 中没有找到以'affair'开头的CSV文件")
        return False

    print(f"找到 {len(csv_files)} 个CSV文件需要合并")
    all_data = pd.DataFrame()
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            if df.empty:
                print(f"文件 {file} 为空，已跳过")
                continue
            expected_columns = ['year', 'month', 'day', 'affair', 'type']
            if not all(col in df.columns for col in expected_columns):
                print(f"文件 {file} 的列格式不符合预期，已跳过")
                continue
            all_data = pd.concat([all_data, df], ignore_index=True)

        except Exception as e:
            print(f"处理文件 {file} 时出错: {str(e)}")

    # 如果合并后的数据不为空，则保存到输出文件
    if not all_data.empty:
        all_data.to_csv(output_file, index=False)
        print(f"合并完成! 数据已保存到 {output_file}")
        print(f"合并后的数据包含 {len(all_data)} 行")
        return True
    else:
        print("没有数据可合并")
        return False

def main():
    # bad_list = []
    # retry_list = []
    # for month in range(1, 13):
    #     if month == 2:
    #         days_in_month = 29
    #     else:
    #         days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
    #     for day in range(1, days_in_month + 1):
    #         json_list = get_wikipedia_content(month, day)
    #         json_to_csv(json_list, f'./csvs/affair_{month}_{day}.csv', month, day, bad_list)
    # for kv in bad_list:
    #     month = kv[0]
    #     day = kv[1]
    #     json_list = get_wikipedia_content(month, day)
    #     json_to_csv(json_list, f'./csvs/affair_{month}_{day}.csv', month, day, retry_list)
    # print(retry_list)
    # merge_affair_csvs('./csvs')
    import_csv_to_mysql('merged_affair.csv')

if __name__ == "__main__":
    main()