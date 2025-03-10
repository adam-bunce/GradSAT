from sqlalchemy.dialects.postgresql import insert

from grad_sat.scraper.uoit_courses import Scraper
from grad_sat.scraper.models import Model, ClassInfoList, ClassInfo
from grad_sat.db.database import get_db, create_url
from grad_sat.db.schema import Course


def main():
    try:
        sc = Scraper(
            cookie="",
            unique_session_id="",
        )

        limit = 50
        offset = 1000
        returned = 50
        TERM = 202501  # winter 2025
        total = 0

        while returned == 50 and total < 1000:
            res: Model = sc.get_courses(limit=limit, offset=offset)
            returned = len(res.data)
            # courses.extend(res.data)
            courses = res.data
            total += len(res.data)

            tmp = ClassInfoList(class_list=courses)

            offset += limit

            with get_db(create_url()) as db:
                for course in tmp.class_list:
                    # insert or update
                    stmt = insert(Course).values(
                        id=course.id,
                        data=course.model_dump_json()
                    )

                    stmt.on_conflict_do_update(
                        index_elements=['id'],
                        set_=dict(data=course.model_dump_json())
                    )

                    db.execute(stmt)

            print(f"Done iteration: limit={limit}, offset={offset}")

    except Exception as e:
        print("------ SCRAPER FAILED ------")
        print(e)


if __name__ == "__main__":
    main()
