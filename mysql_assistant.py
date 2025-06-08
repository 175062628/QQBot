import pymysql
from pymysql.cursors import DictCursor
import yaml
from pathlib import Path
from utils import load_config_from_yaml

class MySQLAssistant:
    def __init__(self, config=None, config_file=None):
        """初始化数据库连接参数

        Args:
            config (dict): 包含数据库配置的字典
            config_file (str): YAML 配置文件路径
        """
        self.connection = None

        # 优先从配置文件加载，否则使用传入的配置字典
        if config_file:
            self.config = load_config_from_yaml(config_file)
        elif config:
            self.config = config
        else:
            raise ValueError("必须提供配置字典或配置文件路径")

        # 提取数据库连接参数
        self.host = self.config.get('host', 'localhost')
        self.user = self.config.get('user')
        self.password = self.config.get('password')
        self.database = self.config.get('database')

    def connect(self):
        """连接到指定的 MySQL 数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                cursorclass=DictCursor
            )
            return True
        except Exception as e:
            print(f'连接数据库时出错: {e}')
            return False

    def disconnect(self):
        """断开与数据库的连接"""
        if self.connection:
            self.connection.close()
            print('已断开数据库连接')

    def create_table_if_not_exists(self, table_name, create_table_sql):
        """如果指定表不存在，则创建它"""
        if not self.connection:
            if not self.connect():
                return False

        try:
            with self.connection.cursor() as cursor:
                # 检查表格是否存在
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                result = cursor.fetchone()

                if not result:
                    cursor.execute(create_table_sql)
                    self.connection.commit()
                    return True
                else:
                    return True
        except Exception as e:
            print(f"创建表时出错: {e}")
            return False

    def execute_query(self, query, params=None):
        """执行查询并返回结果列表"""
        if not self.connection:
            if not self.connect():
                return []

        results = []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
        except Exception as e:
            print(f"执行查询时出错: {e}")
        return results

    def insert_data(self, table_name, data_list):
        if not self.connection:
            if not self.connect():
                return False

        if not isinstance(data_list, list) or not data_list:
            return False

        if not all(isinstance(item, dict) for item in data_list):
            return False

        columns = list(data_list[0].keys())
        columns_sorted = sorted(columns)

        first_keys = set(columns)
        for item in data_list[1:]:
            if set(item.keys()) != first_keys:
                return False

        column_names = ', '.join(columns_sorted)
        placeholders = ', '.join(['%s'] * len(columns_sorted))

        values = [tuple(item[col] for col in columns_sorted) for item in data_list]

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(
                    f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
                    values
                )
                self.connection.commit()
                return True
        except Exception as e:
            print(f"插入多条数据出错: {e}")
            self.connection.rollback()
            return False

    def update_data(self, template, condition, data_list):
        if not self.connection:
            if not self.connect():
                return False

        if not isinstance(data_list, list) or not data_list:
            return False

        if not all(isinstance(item, dict) for item in data_list):
            return False
        set_clause = template.split("SET")[1].split("WHERE")[0].strip()
        set_fields = [field.split("=")[0].strip() for field in set_clause.split(",")]

        for item in data_list:
            for field in set_fields:
                if field not in item:
                    return False
        batch_params = [
            tuple(item[field] for field in set_fields) + condition
            for item in data_list
        ]

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(template, batch_params)
                self.connection.commit()
                return True
        except Exception as e:
            print(f"更新数据失败: {e}")
            self.connection.rollback()
            return False