from model import (
    GraduationRequirementsInstance,
    ProgramMap,
    CourseFilter,
    GraduationRequirementsConfig,
    GraduationRequirementsSolver,
)


def main():
    # ways to not use strings for everything:
    # enum -> map -> of the courses

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
        min_of_type=[],
        max_of_type=[],
        min_electives=45,
    )

    gr_instance = GraduationRequirementsInstance(program_map=cs_program_map)
    gr_config = GraduationRequirementsConfig()
    solver = GraduationRequirementsSolver(
        instance=gr_instance, config=gr_config, csv_path="none"
    )

    # if we take CSCI3090U we have to take specific prerequisites too
    solver.take_class("CSCI3090U")
    solver.solve()


if __name__ == "__main__":
    main()
