from model import (
    GraduationRequirementsInstance,
    ProgramMap,
    GraduationRequirementsConfig,
    GraduationRequirementsSolver,
    FilterConstraint,
    CourseType,
)

# https://calendar.ontariotechu.ca/preview_program.php?catoid=62&poid=13141&returnto=2811


def main():
    # 45 credit hours in electives
    min_elective_ch = FilterConstraint(gte=45, type=CourseType.Elective)

    # No more than 42 credit hours may be taken at the first-year level
    max_42_credit_hours_at_first_year_level = FilterConstraint(
        lte=42, year_levels=[1], type=CourseType.All
    )

    # Students are required to complete at least 12 credit hours in Computer Science courses at the 4000 level
    year_4_cs_min_12ch = FilterConstraint(
        program=["CSCI"], year_levels=[4], gte=12, type=CourseType.All
    )

    science = ["BIOL", "CHEM", "CSCI", "ENVS", "FSCI", "MATH", "NCSI", "PHY", "STAT"]
    # 27 credit hours must be in courses offered by the Faculty of Science
    min_27ch_science = FilterConstraint(
        program=science, gte=27, type=CourseType.Elective
    )

    # at least 12 credit hours must be in Senior Computer Science electives, with no more than 15 credit hours being in Computer Science
    year_4_cs_min_12ch_max_15ch = FilterConstraint(
        program=["CSCI"], year_levels=[4], lte=15, gte=12, type=CourseType.Elective
    )

    cs_program_map = ProgramMap(
        required_courses=[
            "CSCI1030U",
            "CSCI1060U",
            "CSCI1061U",
            "CSCI2050U",
            "MATH1020U",
            "PHY1020U",
            "CSCI2000U",
            "CSCI2010U",
            "CSCI2020U",
            "CSCI2040U",
            "CSCI2072U",
            "CSCI2110U",
            "MATH2050U",
            "STAT2010U",
            "CSCI3070U",
            "CSCI4040U",
        ],
        one_of=[
            ["PHY1010U", "PHY1030U"],
            ["MATH1010U", "MATH1000U"],
            ["CSCI3010U", "CSCI3030U", "CSCI4030U", "CSCI4050U", "CSCI4610U"],
            ["CSCI3090U", "CSCI4110U", "CSCI4210U", "CSCI4220U"],
            ["CSCI3230U", "CSCI4100U", "CSCI4160U", "CSCI4620U"],
            ["CSCI3055U", "CSCI3060U", "CSCI4020U", "CSCI4060U"],
            ["CSCI3020U", "CSCI3150U", "CSCI3310U", "CSCI4310U"],
            [
                "BUSI1600U",
                "BUSI1700U",
                "BUSI2000U",
                "BUSI2200U",
                "BUSI2311U",
            ],
            [
                "COMM1050U",
                "COMM1100U",
                "COMM1320U",
                "COMM2311U",
                "COMM2620U",
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

    gr_instance = GraduationRequirementsInstance(program_map=cs_program_map)
    gr_config = GraduationRequirementsConfig()
    solver = GraduationRequirementsSolver(
        problem_instance=gr_instance, config=gr_config, csv_path="none"
    )

    solver.take_class("CSCI4160U")  # forces csci3090, CSCI2010, (MATH2050U or MATH1850)
    taken_classes = solver.solve()
    print(taken_classes)


if __name__ == "__main__":
    main()
