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
        offset = 1550  # tmp
        returned = 50
        TERM = 202501  # winter 2025
        total = 0

        courses: list[ClassInfo] = []
        while returned == 50 and total < 1000:
            res: Model = sc.get_courses(limit=limit, offset=offset)
            returned = len(res.data)
            # courses.extend(res.data)
            courses = res.data
            total += len(res.data)

            tmp = ClassInfoList(class_list=courses)

            offset += limit

            with open(f"limit={limit}_offset={offset}.json", "w") as f:
                json.dump(tmp.model_dump(), f, indent=4)

            print(f"Done iteration: limit={limit}, offset={offset}")

    except Exception as e:
        print("------ SCRAPER FAILED ------")
        print(e)
