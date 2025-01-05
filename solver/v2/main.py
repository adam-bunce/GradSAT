import json
import os

from model import (
    GraduationRequirementsInstance,
    ProgramMap,
    GraduationRequirementsConfig,
    GraduationRequirementsSolver,
    FilterConstraint,
    CourseType,
    Filter,
)
from solver.v2.static import (
    all_semesters,
    Programs,
)

from parser.csv_parser import CourseCsvParser


# https://calendar.ontariotechu.ca/preview_program.php?catoid=62&poid=13141&returnto=2811


def parse_and_pickle_csv(csv_path: str):
    """parse_and_pickle_csv("../../misc/uoit_courses.csv")"""
    csv_parser = CourseCsvParser(path=csv_path)
    df = csv_parser.parse()
    path = csv_path.replace(".csv", ".pickle")
    # fix most frequent parse failures
    tmp = dict(
        sorted(
            csv_parser.failed_exprs.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )
    )

    with open("out.json", "w") as fp:
        json.dump(tmp, fp)

    print(f"saving df to {path}")

    if os.path.exists(path):
        os.remove(path)

    df.to_pickle(path)
    print(df.iloc[0])


def main():
    parse_and_pickle_csv("../../misc/uoit_courses.csv")
    # 45 credit hours in electives
    min_elective_ch = FilterConstraint(gte=45, filter=Filter(type=CourseType.Elective))

    # No more than 42 credit hours may be taken at the first-year level
    max_42_credit_hours_at_first_year_level = FilterConstraint(
        lte=42, filter=Filter(year_levels=[1], type=CourseType.All)
    )

    # Students are required to complete at least 12 credit hours in Computer Science courses at the 4000 level
    year_4_cs_min_12ch = FilterConstraint(
        gte=12,
        filter=Filter(
            programs=[Programs.computer_science],
            year_levels=[4],
            type=CourseType.All,
        ),
    )

    science = [
        Programs.biology,
        Programs.chemistry,
        Programs.computer_science,
        Programs.environmental_science,
        Programs.forensic_science,
        Programs.neuroscience,
        Programs.physics,
        Programs.statistics,
    ]
    # 27 credit hours must be in courses offered by the Faculty of Science
    min_27ch_science = FilterConstraint(
        gte=27, filter=Filter(type=CourseType.Elective, programs=science)
    )

    # at least 12 credit hours must be in Senior Computer Science electives, with no more than 15 credit hours being in Computer Science
    year_4_cs_min_12ch_max_15ch = FilterConstraint(
        lte=15,
        gte=12,
        filter=Filter(
            programs=[Programs.computer_science],
            year_levels=[4],
            type=CourseType.Elective,
        ),
    )

    cs_program_map = ProgramMap(
        required_courses=[
            "csci1030u",
            "csci1060u",
            "csci1061u",
            "csci2050u",
            "math1020u",
            "phy1020u",
            "csci2000u",
            "csci2010u",
            "csci2020u",
            "csci2040u",
            "csci2072u",
            "csci2110u",
            "math2050u",
            "stat2010u",
            "csci3070u",
            "csci4040u",
        ],
        one_of=[
            ["phy1010u", "phy1030u"],
            ["math1010u", "math1000u"],
            ["csci3010u", "csci3030u", "csci4030u", "csci4050u", "csci4610u"],
            ["csci3090u", "csci4110u", "csci4210u", "csci4220u"],
            ["csci3230u", "csci4100u", "csci4160u", "csci4620u"],
            ["csci3055u", "csci3060u", "csci4020u", "csci4060u"],
            ["csci3020u", "csci3150u", "csci3310u", "csci4310u"],
            [
                "busi1600u",
                "busi1700u",
                "busi2000u",
                "busi2200u",
                "busi2311u",
            ],
            [
                "comm1050u",
                "comm1100u",
                "comm1320u",
                "comm2311u",
                "comm2620u",
            ],
        ],
        filter_constraints=[
            min_elective_ch,
            max_42_credit_hours_at_first_year_level,
            year_4_cs_min_12ch,
            min_27ch_science,
            year_4_cs_min_12ch_max_15ch,
        ],
    )

    gr_instance = GraduationRequirementsInstance(
        program_map=cs_program_map,
        semesters=all_semesters,
        pickle_path="../../misc/uoit_courses.pickle",
    )
    gr_config = GraduationRequirementsConfig(print_stats=True)
    solver = GraduationRequirementsSolver(
        problem_instance=gr_instance,
        config=gr_config,
    )

    solver.take_class(
        "csci4160u"
    )  # forces csci3090, CSCI2010(+ CSCI1060U), (MATH2050U or MATH1850),

    print("program map valid?:", solver.validate_program_map())
    solver.take_class("csci4410u")  # thesis forces CSCI4420U after it
    solver.take_class_in("busi2000u", 2)

    # infeasible if year standing constraint work (need 2nd year standing)
    # solver.take_class_in("busi2312u", 2)
    solver.take_class_in("busi2312u", 3)

    solver.set_maximization_target(
        Filter(
            programs=[Programs.mathematics],
            year_levels=[3, 4],
            type=CourseType.Elective,
        )
    )

    solver.set_minimization_target(Filter(programs=[Programs.biology]))

    taken_classes = solver.solve()
    print(taken_classes)


if __name__ == "__main__":
    main()
