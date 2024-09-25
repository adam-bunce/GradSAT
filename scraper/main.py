import json

from scraper import Scraper
from models import Model, ClassInfoList, ClassInfo

if __name__ == "__main__":
    try:
        sc = Scraper(
            cookie="",
            unique_session_id="",
        )

        limit = 50
        offset = 0
        returned = 50
        TERM = 202501  # winter 2025
        total = 0

        courses: list[ClassInfo] = []
        # while returned == 10 and total < 100:
        res: Model = sc.get_courses(limit=limit, offset=1)
        courses.extend(res.data)
        total += len(res.data)

        tmp = ClassInfoList(class_list=courses)

        with open("first_50.json", "w") as f:
            json.dump(tmp.model_dump(), f, indent=4)

    except Exception as e:
        print("------ SCRAPER FAILED ------")
        print(e)
