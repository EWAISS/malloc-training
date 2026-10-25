-- brain.db schema. Regenerate with: sqlite3 brain.db .schema > schema.sql
-- (then re-add this header). Applied by init_db.py on a fresh database.
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    number INTEGER,
    name TEXT,
    phase INTEGER,
    lab TEXT,
    course TEXT,
    concept TEXT,
    status TEXT,
    prediction TEXT,
    actual_output TEXT,
    final_code TEXT,
    teaching_angle TEXT,
    what_worked TEXT,
    what_failed TEXT,
    handoff TEXT,
    code_review TEXT,
    key_exchange TEXT,
    appears_in_future_labs TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE concepts (
    id INTEGER PRIMARY KEY,
    name TEXT,
    status TEXT,
    how_it_clicked TEXT,
    struggled_with TEXT,
    resolved_by TEXT,
    connects_to TEXT,
    project_number INTEGER
);
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    pattern TEXT,
    first_seen_project INTEGER,
    last_seen_project INTEGER,
    frequency INTEGER DEFAULT 1,
    severity TEXT
);
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY,
    project_number INTEGER,
    concept TEXT,
    angle_used TEXT,
    analogy_used TEXT,
    result TEXT
);
CREATE TABLE weakness_patterns (
    id INTEGER PRIMARY KEY,
    concept TEXT,
    specific_misconception TEXT,
    sub_projects_that_failed TEXT,
    sub_projects_that_worked TEXT,
    exact_analogy_that_clicked TEXT,
    exact_wording_that_clicked TEXT,
    exact_sub_project_that_worked TEXT,
    watch_for_recurrence TEXT,
    project_number INTEGER
);
CREATE TABLE project_narrative (
    id INTEGER PRIMARY KEY,
    project_number INTEGER,
    why_designed_this_way TEXT,
    gap_it_closes TEXT,
    what_response_revealed TEXT,
    connection_to_lab TEXT,
    what_breaks_without_this TEXT,
    what_next_project_must_do TEXT,
    curriculum_position_reasoning TEXT
);
CREATE TABLE project_full_detail (
    id INTEGER PRIMARY KEY,
    project_number INTEGER,
    full_specification TEXT,
    micro_projects_generated TEXT,
    all_quiz_questions TEXT,
    all_quiz_answers TEXT,
    exact_failure_moments TEXT,
    exact_success_moments TEXT,
    memory_model_evolution TEXT
);
CREATE TABLE mind_model (
    id INTEGER PRIMARY KEY,
    project_number INTEGER,
    update_type TEXT,
    content TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE transfer_exams (
    id INTEGER PRIMARY KEY,
    phase INTEGER,
    lab TEXT,
    course TEXT,
    exam_scenario TEXT,
    your_implementation TEXT,
    evaluation TEXT,
    gaps_found TEXT,
    adversarial_gap_report TEXT,
    status TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE adversarial_exams (
    id INTEGER PRIMARY KEY,
    phase INTEGER,
    lab TEXT,
    course TEXT,
    concepts_tested TEXT,
    questions_asked TEXT,
    your_answers TEXT,
    gap_found TEXT,
    gap_location TEXT,
    resolved TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
, resolution TEXT);
CREATE TABLE quiz_records (
    id INTEGER PRIMARY KEY,
    project_number INTEGER,
    question_number INTEGER,
    question_text TEXT,
    your_answer TEXT,
    evaluation TEXT,
    is_novel_question INTEGER DEFAULT 0,
    result TEXT,
    concept TEXT,
    lab TEXT,
    course TEXT
);
CREATE TABLE lab_handouts (
    id INTEGER PRIMARY KEY,
    course TEXT,
    lab TEXT,
    functions_to_implement TEXT,
    grading_criteria TEXT,
    autograder_behavior TEXT,
    critical_constraints TEXT,
    edge_cases TEXT,
    required_tools TEXT,
    hardest_concept TEXT,
    book_chapters TEXT,
    raw_extraction TEXT,
    stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE external_validation (
            id INTEGER PRIMARY KEY,
            concept TEXT,
            project_number INTEGER,
            source TEXT,
            question TEXT,
            your_answer TEXT,
            correct_answer TEXT,
            result TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE mood_logs (
            id INTEGER PRIMARY KEY,
            sleep_hours REAL,
            ate TEXT,
            days_no_break INTEGER,
            state TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE lab_transitions (
            id INTEGER PRIMARY KEY,
            lab TEXT,
            course TEXT,
            concepts_owned TEXT,
            carried_forward TEXT,
            watch_for TEXT,
            key_analogy TEXT,
            full_summary TEXT,
            next_lab TEXT,
            transitioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
CREATE TABLE gap_gate_clears (
            id INTEGER PRIMARY KEY,
            cleared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
