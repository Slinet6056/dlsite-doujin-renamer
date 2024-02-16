import argparse
import logging
import os
from json import JSONDecodeError

from config_file import ConfigFile
from renamer import Renamer
from scaner import Scaner
from scraper import Locale, CachedScraper

VERSION = "0.2.8"

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def run_renamer(root_path_list: list[str], config_file_path: str):
    # 加载配置文件
    try:
        config_file = ConfigFile(config_file_path)
        config = config_file.load_config()
    except JSONDecodeError as err:
        logging.error(f'配置文件解析失败："{os.path.normpath(config_file_path)}"')
        logging.error(f"JSONDecodeError: {str(err)}")
        return
    except FileNotFoundError as err:
        logging.error(f'配置文件加载失败："{os.path.normpath(config_file_path)}"')
        logging.error(f"FileNotFoundError: {err.strerror}")
        return

    # 检查配置是否合法
    strerror_list = ConfigFile.verify_config(config)
    if len(strerror_list) > 0:
        logging.error(f'配置文件验证失败："{os.path.normpath(config_file_path)}"')
        for strerror in strerror_list:
            logging.error(strerror)
        return

    # 配置 scaner
    scaner_max_depth = config["scaner_max_depth"]
    scaner = Scaner(max_depth=scaner_max_depth)

    # 配置 scraper
    scraper_locale = config["scraper_locale"]
    scraper_http_proxy = config["scraper_http_proxy"]
    proxies = (
        {"http": scraper_http_proxy, "https": scraper_http_proxy}
        if scraper_http_proxy
        else None
    )
    scraper_connect_timeout = config["scraper_connect_timeout"]
    scraper_read_timeout = config["scraper_read_timeout"]
    scraper_sleep_interval = config["scraper_sleep_interval"]
    cached_scraper = CachedScraper(
        locale=Locale[scraper_locale],
        connect_timeout=scraper_connect_timeout,
        read_timeout=scraper_read_timeout,
        sleep_interval=scraper_sleep_interval,
        proxies=proxies,
    )

    tags_option = {
        "ordered_list": config["renamer_tags_ordered_list"],
        "max_number": (
            999999
            if config["renamer_tags_max_number"] == 0
            else config["renamer_tags_max_number"]
        ),
    }

    # 配置 renamer
    renamer = Renamer(
        scaner=scaner,
        scraper=cached_scraper,
        template=config["renamer_template"],
        release_date_format=config["renamer_release_date_format"],
        delimiter=config["renamer_delimiter"],
        cv_list_left=config["cv_list_left"],
        cv_list_right=config["cv_list_right"],
        exclude_square_brackets_in_work_name_flag=config[
            "renamer_exclude_square_brackets_in_work_name_flag"
        ],
        renamer_illegal_character_to_full_width_flag=config[
            "renamer_illegal_character_to_full_width_flag"
        ],
        make_folder_icon=config["make_folder_icon"],
        remove_jpg_file=config["remove_jpg_file"],
        tags_option=tags_option,
    )

    # 执行重命名
    for root_path in root_path_list:
        renamer.rename(root_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DLSite 同人作品重命名工具")
    parser.add_argument(
        "paths", metavar="PATH", type=str, nargs="+", help="要重命名的目录路径"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.json",
        help="配置文件路径，默认为当前目录下的config.json",
    )
    args = parser.parse_args()

    run_renamer(args.paths, args.config)
