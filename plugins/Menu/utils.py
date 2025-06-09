import sys
import os
import logging
from pathlib import Path
import importlib

def get_plugin_info(plugin_path):
    logging.getLogger().setLevel(logging.WARNING)
    directory_path = os.path.abspath(plugin_path)
    sys.path.append(os.path.dirname(directory_path))
    filename = Path(plugin_path).stem
    module = importlib.import_module(filename)

    for plugin_class_name in module.__all__:
        plugin_class = getattr(module, plugin_class_name)

        name = plugin_class.name
        version = plugin_class.version
        meta = {
            "name": name,
            "version": version,
            "plugin_dependencies": (
                plugin_class.dependencies
                if hasattr(plugin_class, "dependencies")
                else {}
            ),
            "description": getattr(
                plugin_class,
                "description",
                "这个作者很懒且神秘,没有写一点点描述,真是一个神秘的插件",
            ),
            "author": getattr(plugin_class, "author", "Unknown"),
            "info": getattr(plugin_class, "info", ""),
            "funcs": [],
            "configs": [],
        }
        return name, version, meta