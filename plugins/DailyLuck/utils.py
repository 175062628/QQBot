import sys

import os
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

def import_csv_to_mysql(csv_file, delimiter='|'):
    config = load_config_from_yaml("config.yaml")
    try:
        host = config.get('host', 'localhost')
        user = config.get('user')
        password = config.get('password')
        database = config.get('database')
        table = 'daily_luck_map'
        end_line = '\r\n' if sys.platform.startswith('win') else '\n'
        print(f"文件是否存在: {os.path.exists(csv_file)}")
        print(f"文件权限: {os.access(csv_file, os.R_OK)}")

        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            client_flag=CLIENT.LOCAL_FILES,
            local_infile=True
        )

        with conn.cursor() as cursor:
            cursor.execute("SHOW VARIABLES LIKE 'local_infile'")
            result = cursor.fetchone()
            print(f"当前local_infile状态: {result[1]}")
            if result[1] != 'ON':
                print("正在启用local_infile...")
                cursor.execute("SET GLOBAL local_infile = ON")
                cursor.execute("SHOW VARIABLES LIKE 'local_infile'")
                new_result = cursor.fetchone()
                print(f"启用后状态: {new_result[1]}")

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table}` (
                `luck` INT,
                `sign` VARCHAR(32),
                `explain` VARCHAR(255),
                `description` VARCHAR(1024)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
            """
            cursor.execute(create_table_sql)
            # 构建导入SQL（注意处理日期和字符类型）
            load_data_sql = f"""
            LOAD DATA LOCAL INFILE '{csv_file}'
            INTO TABLE `{table}`
            FIELDS TERMINATED BY '{delimiter}'
            LINES TERMINATED BY '{end_line}'
            IGNORE 1 ROWS
            """
            cursor.execute(load_data_sql)
            conn.commit()
            row_count = cursor.rowcount
            print(f"插入{row_count}条记录")
            # 提交事务并获取导入行数
            conn.commit()

    except pymysql.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
    except Exception as e:
        print(f"导入失败: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("数据库连接已关闭")

def main():
    import_csv_to_mysql('luck_map.csv')

if __name__ == "__main__":
    main()