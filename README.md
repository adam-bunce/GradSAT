# GradSat 🪄 📚



An intelligent course scheduling system powered by [Google OR-Tools](https://developers.google.com/optimization) CP-SAT solver that helps students plan their academic journey while respecting complex academic constraints.

## Constraints
### Implicit Constraints

- Prerequisites (concurrent, before, post-requisites)
- Credit hour limits per semester
- Courses can be taken at most once
- Maximum number of courses per semester
- Core vs. elective classification

### Program-Defined Constraints

- Required courses (must take all)
- One-of groups (must take exactly one from each group)
- Filter constraints (e.g., "9 credits from upper year science courses")

### User-Defined Constraints

- Course placements ("I'm taking this course in this semester")
- Course preferences (star ratings from -2 to +2)

## Feedback on Infeasible Schedules
When no solution exists, the system provides helpful feedback:

1. It creates an alternative model where constraints are optional
2. It maximizes the number of constraints that are "turned on" (Maximum Satisfiable Subset)
3. It reports which specific constraints are causing the infeasibility (constraints that are "turned off")

This helps users understand why their desired schedule isn't possible and guides them toward feasible alternatives.

## Video


https://github.com/user-attachments/assets/d7788565-b824-407f-a3ce-fac6bf3e1844

