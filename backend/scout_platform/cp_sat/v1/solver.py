import pandas as pd
from ortools.sat.python import cp_model
from static import *
from util import *

# https://calendar.ontariotechu.ca/preview_program.php?catoid=62&poid=13141&returnto=2811


def init_model(m: cp_model.CpModel) -> pd.DataFrame:
    variables = [
        {
            "y1": m.new_bool_var(f"{c}_taken_in_y1"),
            "y2": m.new_bool_var(f"{c}_taken_in_y2"),
            "y3": m.new_bool_var(f"{c}_taken_in_y3"),
            "y4": m.new_bool_var(f"{c}_taken_in_y4"),
            "y1_elective": m.new_bool_var(f"{c}_y1_elective"),
            "y2_elective": m.new_bool_var(f"{c}_y2_elective"),
            "y3_elective": m.new_bool_var(f"{c}_y3_elective"),
            "y4_elective": m.new_bool_var(f"{c}_y4_elective"),
            # used in indexing to apply constraints
            "is_science": is_science(c),
            "is_business": c.startswith("BUSI"),
            "is_communication": c.startswith("COMM"),
            "is_cs": c.startswith("CSCI"),
            "is_first_year": course_level(c) == 1,
            "is_second_year": course_level(c) == 2,
            "is_third_year": course_level(c) == 3,
            "is_fourth_year": course_level(c) == 4,
            "code": get_code(c),
        }
        for c in all_courses
    ]

    df = pd.DataFrame(data=variables)
    df.index = all_courses

    return df


# Year 1 constraints
def apply_first_year_constraints(m: cp_model.CpModel, data: pd.DataFrame):
    mandatory_year_1_classes = [
        "CSCI1030U",
        "CSCI1060U",
        "CSCI1061U",
        "CSCI2050U",
        "MATH1020U",
        "PHY1020U",
    ]
    # Constraint 1: in year 1 we have to take all the mandatory classes
    required_first_year_courses = [
        data.loc[course, "y1"] for course in mandatory_year_1_classes
    ]
    m.add_bool_and(required_first_year_courses)

    # Constraint 2: in year 1 we take two electives
    first_year_electives = data[["y1_elective"]].values.flatten()
    m.add(sum(first_year_electives) == 2)

    # Constraint 3: we have to take either physics 1 or into to physics
    physics_courses = data.loc[["PHY1010U", "PHY1030U"], ["y1"]]["y1"].to_list()
    m.add(sum(physics_courses) == 1)

    phy_1010u = data.loc[["PHY1010U"], :][all_decision_vars].values.flatten()
    phy1030u = data.loc[["PHY1030U"], :][all_decision_vars].values.flatten()
    # if we take math1000 we cant take math 1010u
    m.add(sum(phy1030u + phy_1010u) == 1)

    # Constraint 4: we have to take calc 1 or into to calc
    math_courses = data.loc[["MATH1010U", "MATH1000U"], ["y1"]]["y1"].to_list()
    m.add(sum(math_courses) == 1)

    math_1000u = data.loc[["MATH1000U"], :][all_decision_vars].values.flatten()
    math_1010u = data.loc[["MATH1010U"], :][all_decision_vars].values.flatten()
    # if we take math1000 we cant take math 1010u
    m.add(sum(math_1010u + math_1000u) == 1)


def apply_second_year_constraints(m: cp_model.CpModel, data: pd.DataFrame):
    mandatory_year_2_classes = [
        "CSCI2000U",
        "CSCI2010U",
        "CSCI2020U",
        "CSCI2040U",
        "CSCI2072U",
        "CSCI2110U",
        "MATH2050U",
        "STAT2010U",
    ]

    # Constraint 1: in year 2 we have to take the mandatory classes
    year_2_mandatory_classes = [
        data.loc[course, "y2"] for course in mandatory_year_2_classes
    ]
    m.add_bool_and(year_2_mandatory_classes)

    # Constraint 2: in year 2 we take two electives
    year_2_electives = data[["y2_elective"]].values.flatten()
    m.add(sum(year_2_electives) == 2)


def apply_third_and_fourth_year_constraints(m: cp_model.CpModel, data: pd.DataFrame):
    # Year 3/4 constraints

    # Constraint 1:  algorithms must be taken in y3/y4
    m.add(sum(data.loc["CSCI3070U", ["y3", "y4"]].values) == 1)

    # Constraint 2: Ethics must be taken in y3/y4
    m.add(sum(data.loc["CSCI4040U", ["y3", "y4"]].values) == 1)

    m.add_exactly_one(
        data.loc[
            ["CSCI3010U", "CSCI3030U", "CSCI4030U", "CSCI4050U", "CSCI4610U"],
            ["y3", "y4"],
        ].values.flatten()
    )
    m.add_exactly_one(
        data.loc[
            ["CSCI3090U", "CSCI4110U", "CSCI4210U", "CSCI4220U"], ["y3", "y4"]
        ].values.flatten()
    )
    m.add_exactly_one(
        data.loc[
            ["CSCI3230U", "CSCI4100U", "CSCI4160U", "CSCI4620U"], ["y3", "y4"]
        ].values.flatten()
    )
    m.add_exactly_one(
        data.loc[
            ["CSCI3055U", "CSCI3060U", "CSCI4020U", "CSCI4060U"], ["y3", "y4"]
        ].values.flatten()
    )
    m.add_exactly_one(
        data.loc[
            ["CSCI3020U", "CSCI3150U", "CSCI3310U", "CSCI4310U"], ["y3", "y4"]
        ].values.flatten()
    )

    # thesis is counted as upper year cs elective, dont set them in y3/y4 core slots
    m.add(sum(data.loc[["CSCI4420U", "CSCI4410U"], ["y3", "y4"]].values.flatten()) == 0)


def apply_misc_constraints(m: cp_model.CpModel, data: pd.DataFrame):
    # No more than 42 credit hours may be taken at the first-year level
    first_year_courses = data[data["is_first_year"] == True][
        all_decision_vars
    ].values.flatten()
    m.add(sum(first_year_courses) <= 42 // 3)

    # Students must complete a total of 45 credit hours such that the following elective requirements are satisfied
    all_electives = data[
        ["y1_elective", "y2_elective", "y3_elective", "y4_elective"]
    ].values.flatten()
    m.add(sum(all_electives) >= 45 // 3)

    # Students are required to complete at least 12 credit hours in Computer Science courses at the 4000 level
    fourth_year_cs_courses = data[
        (data["is_fourth_year"] == True) & (data["is_cs"] == True)
    ][elective_decision_vars].values.flatten()
    m.add(sum(fourth_year_cs_courses) >= 12 // 3)

    # 27 credit hours must be in courses offered by the Faculty of Science
    science_courses = data[data["is_science"] == True][
        elective_decision_vars
    ].values.flatten()
    m.add(sum(science_courses) >= 27 // 3)

    # of which at least 12 credit hours must be in Senior Computer Science electives
    # ALSO: we have to take either thesis or two more, thesis is an upper year cs elective though so effectively 18 credit hours
    upper_cs_courses = data[
        data["is_cs"] & (data["is_fourth_year"] | data["is_third_year"])
    ][elective_decision_vars].values.flatten()
    m.add(sum(upper_cs_courses) >= 18 // 3)

    # with no more than 15 credit hours being in Computer Science
    # 27 - 15 = 12
    # need 12 non-cs science
    non_cs_science = data[(data["is_cs"] == False) & (data["is_science"] == True)][
        elective_decision_vars
    ].values.flatten()
    m.add(sum(non_cs_science) >= 12 // 3)

    # 12 credit hours must be in courses from outside the Faculty of Science
    non_sci_electives = data[data["is_science"] != True][
        elective_decision_vars
    ].values.flatten()
    m.add(sum(non_sci_electives) >= 12 // 3)

    business_electives = [
        "BUSI1600U",
        "BUSI1700U",
        "BUSI2000U",
        "BUSI2200U",
        "BUSI2311U",
    ]
    # at least 3 credit hours must be in business electives
    req_business_courses = data.loc[data.index.isin(business_electives)][
        all_decision_vars
    ].values.flatten()
    m.add_at_least_one(req_business_courses)

    communication_electives = [
        "COMM1050U",
        "COMM1100U",
        "COMM1320U",
        "COMM2311U",
        "COMM2620U",
    ]
    req_communication_courses = data.loc[data.index.isin(communication_electives)][
        all_decision_vars
    ].values.flatten()
    m.add_at_least_one(req_communication_courses)

    # 6 credit hours in general electives (offered by the Faculty of Science or outside the Faculty of Science)
    # this is encoded in the "45 electives" condition so nothing needed


# this is not good! i think that it is working though
def apply_prerequisites(
    m: cp_model.CpModel, data: pd.DataFrame
) -> (list[list[any]], list[any]):
    res = []
    res2 = []
    for taken_class, prereqs in prerequisites.items():
        class_vars = data.loc[taken_class][all_decision_vars]

        # merge into 1 var (this works fine)
        took_class = m.new_bool_var(f"took_{taken_class}")
        m.add_bool_or(class_vars).only_enforce_if(took_class)
        m.add_bool_and([cv.Not() for cv in class_vars]).only_enforce_if(
            took_class.Not()
        )

        res2.append(took_class)

        prerequsite_options_vars = []
        for i, prereq_options in enumerate(prereqs):
            took_classes = []
            for j, prereq_class in enumerate(prereq_options):
                took_prereq = m.new_bool_var(
                    f"took_prereq_option_{i}_{prereq_class}_for_{taken_class}"
                )
                prereq_vars = data.loc[prereq_class][all_decision_vars].values.flatten()
                m.add_bool_or(prereq_vars).only_enforce_if(took_prereq)
                m.add_bool_and([~p for p in prereq_vars]).only_enforce_if(
                    took_prereq.Not()
                )

                took_classes.append(took_prereq)

            res.append(took_classes)

            # create variable to keep track of if we met the pre-req or not
            met_prereq = m.new_bool_var(f"met_{i}_{taken_class}_prereq(s)")
            # scope issue?
            m.add_bool_and(took_classes).only_enforce_if(met_prereq)
            prerequsite_options_vars.append(met_prereq)

        # if we took the class, we should have fulfilled one of the pre-requisite options
        # res[took_class].extend(prerequsite_options_vars)
        m.add(sum(prerequsite_options_vars) >= 1).only_enforce_if(took_class)

    return res, res2


def evenly_distribute_course_load(m: cp_model.CpModel, data: pd.DataFrame):
    # each year is 30 credit hours which is ~= 10 courses
    all_y1 = data[["y1", "y1_elective"]].values.flatten()
    all_y2 = data[["y2", "y2_elective"]].values.flatten()
    all_y3 = data[["y3", "y3_elective"]].values.flatten()
    all_y4 = data[["y4", "y4_elective"]].values.flatten()

    m.add(sum(all_y1) == sum(all_y2))
    m.add(sum(all_y2) == sum(all_y3))
    m.add(sum(all_y3) == sum(all_y4))


if __name__ == "__main__":

    model = cp_model.CpModel()
    model_vars = init_model(model)

    apply_first_year_constraints(model, model_vars)
    apply_second_year_constraints(model, model_vars)
    apply_third_and_fourth_year_constraints(model, model_vars)
    apply_misc_constraints(model, model_vars)
    evenly_distribute_course_load(model, model_vars)
    prereq_variables, taken_classes = apply_prerequisites(model, model_vars)

    # minimize courses taken (not really needed doing this for variation)
    model.minimize(sum(model_vars[all_decision_vars].values.flatten()))

    # TESTING:
    # force us to take adv. grapics -> forces intro to graphics (seems to work)??
    adv_graphics_y4 = model_vars.loc[["CSCI4110U"]][["y4_elective"]].values.flatten()
    print(adv_graphics_y4)
    model.add(adv_graphics_y4[0] == 1)

    # You can't take the same course twice (for credits)
    all_courses = model_vars[
        [
            "y1",
            "y2",
            "y3",
            "y4",
            "y1_elective",
            "y2_elective",
            "y3_elective",
            "y4_elective",
        ]
    ].values
    for course in all_courses:
        model.add(sum(course) <= 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.StatusName(status))

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"Solved")
        solved_courses = model_vars.loc[
            :,
            [
                "y1",
                "y2",
                "y3",
                "y4",
                "y1_elective",
                "y2_elective",
                "y3_elective",
                "y4_elective",
            ],
        ]
        # replace values in df w/ cp_sat values
        solved_courses = solved_courses.map(lambda x: solver.Value(x))

        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            courses_taken = solved_courses[
                (solved_courses["y1"] == 1)
                | (solved_courses["y2"] == 1)
                | (solved_courses["y3"] == 1)
                | (solved_courses["y4"] == 1)
                | (solved_courses["y1_elective"] == 1)
                | (solved_courses["y2_elective"] == 1)
                | (solved_courses["y3_elective"] == 1)
                | (solved_courses["y4_elective"] == 1)
            ]

            print(f"{len(courses_taken)} courses taken")
            print(
                "year 1:", sum(courses_taken["y1"]) + sum(courses_taken["y1_elective"])
            )
            print(
                "year 2:", sum(courses_taken["y2"]) + sum(courses_taken["y2_elective"])
            )
            print(
                "year 3:", sum(courses_taken["y3"]) + sum(courses_taken["y3_elective"])
            )
            print(
                "year 4:", sum(courses_taken["y4"]) + sum(courses_taken["y4_elective"])
            )
            print(courses_taken.columns)

            model_vars.to_html("tmp_2.html")
            courses_taken.to_html("tmp.html")

            for _class in taken_classes:
                print(f"{_class}, {solver.Value(_class)}")

            print("=" * 20)

            for v in prereq_variables:
                values = [solver.value(t) for t in v]
                print(f"we took {v}? {values}")

    else:
        print(f"No Solution Found")
