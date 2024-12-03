import json
from app.core.utils.Logger import Logger

logger = Logger(name="FileMaker", log_file="logs/utils/FileMaker.log").get_logger()


class FileMaker:
    def __init__():

        pass

    @staticmethod
    def save_list_to_json(list):
        if len(list) == 0:
            logger.info("json파일저장실패, 저장된 링크 없음")
            return False

        json_file_path = ".data/musinsa_event_links.json"

        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(list, json_file, ensure_ascii=False, indent=4)

        print(f"총 {len(list)}개의 링크를 {json_file_path} 파일에 저장완료")
