from enum import Enum


class Programs(Enum):
    # somehow this is failing to parse even though i put everything lower case
    academic_learning_and_success = "academic learning and success"
    automotive_engineering = "automotive engineering"
    biology = "biology"
    business = "business"
    chemistry = "chemistry"
    communication = "communication"
    computer_science = "computer science"
    criminology_and_justice = "criminology and justice"
    curriculum_studies = "curriculum studies"
    economics = "economics"
    education = "education"
    esadt = "educational studies and digital technology"
    electrical_engineering = "electrical engineering"
    energy_sys_and_nuclear = "energy systems and nuclear science"
    engineering = "engineering"
    environmental_science = "environmental science"
    forensic_psychology = "forensic psychology"
    forensic_science = "forensic science"
    health_science = "health science"
    indigenous = "indigenous"
    information_technology = "information technology"
    integrated_mathematics_and_computer_science = (
        "integrated mathematics and computer science"
    )
    kinesiology = "kinesiology"
    legal_studies = "legal studies"
    liberal_studies = "liberal studies"
    manufacturing_engineering = "manufacturing engineering"
    mathematics = "mathematics"
    mechanical_engineering = "mechanical engineering"
    mechatronics_engineering = "mechatronics engineering"
    medical_laboratory_science = "medical laboratory science"
    neuroscience = "neuroscience"
    nuclear = "nuclear"
    nursing = "nursing"
    physics = "physics"
    political_science = "political science"
    psychology = "psychology"
    radiation_science = "radiation science"
    science = "science"
    science_coop = "science co-op"
    social_science = "social science"
    sociology = "sociology"
    software_engineering = "software engineering"
    statistics = "statistics"
    sustainable_energy_systems = "sustainable energy systems"


years = ["y1", "Y2", "Y3", "Y4"]
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
