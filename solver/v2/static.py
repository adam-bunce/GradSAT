from enum import Enum


class Programs(Enum):
    academic_learning_and_success = "Academic Learning and Success"
    automotive_engineering = "Automotive Engineering"
    biology = "Biology"
    business = "Business"
    chemistry = "Chemistry"
    communication = "Communication"
    computer_science = "Computer Science"
    criminology_and_justice = "Criminology and Justice"
    curriculum_studies = "Curriculum Studies"
    economics = "Economics"
    education = "Education"
    esadt = "Educational Studies and Digital Technology"
    electrical_engineering = "Electrical Engineering"
    energy_sys_and_nuclear = "Energy Systems and Nuclear Science"
    engineering = "Engineering"
    environmental_science = "Environmental Science"
    forensic_psychology = "Forensic Psychology"
    forensic_science = "Forensic Science"
    health_science = "Health Science"
    indigenous = "Indigenous"
    information_technology = "Information Technology"
    integrated_mathematics_and_computer_science = (
        "Integrated Mathematics and Computer Science"
    )
    kinesiology = "Kinesiology"
    legal_studies = "Legal Studies"
    liberal_studies = "Liberal Studies"
    manufacturing_engineering = "Manufacturing Engineering"
    mathematics = "Mathematics"
    mechanical_engineering = "Mechanical Engineering"
    mechatronics_engineering = "Mechatronics Engineering"
    medical_laboratory_science = "Medical Laboratory Science"
    neuroscience = "Neuroscience"
    nuclear = "Nuclear"
    nursing = "Nursing"
    physics = "Physics"
    political_science = "Political Science"
    psychology = "Psychology"
    radiation_science = "Radiation Science"
    science = "Science"
    science_coop = "Science Co-op"
    social_science = "Social Science"
    sociology = "Sociology"
    software_engineering = "Software Engineering"
    statistics = "Statistics"
    sustainable_energy_systems = "Sustainable Energy Systems"


years = ["Y1", "Y2", "Y3", "Y4"]
semesters = ["Fall", "Winter"]

all_semesters = [f"{year}_{semester}" for year in years for semester in semesters]

int_to_semester = {
    1: "Y1_Fall",
    2: "Y1_Winter",
    3: "Y2_Fall",
    4: "Y2_Winter",
    5: "Y3_Fall",
    6: "Y3_Winter",
    7: "Y4_Fall",
    8: "Y4_Winter",
    9: "unknown",
}
