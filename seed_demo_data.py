#!/usr/bin/env python
"""
seed_demo_data.py
Populates the Thesis Library database with realistic sample records,
categories, departments, courses, and demo accounts (Admin, Librarian, Professor, Student).
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thesis_site.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import call_command
from authapp.models import Profile
from main.models import Category, Department, Course, Thesis, CoAuthor

def seed():
    print("--> Applying database migrations...")
    call_command('migrate', interactive=False)

    print("--> Seeding demo users...")
    demo_users = [
        {
            'username': 'admin',
            'email': 'admin@tcu.edu.ph',
            'password': 'admin12345',
            'first_name': 'TCU',
            'last_name': 'Administrator',
            'role': Profile.ADMIN,
            'is_superuser': True,
            'is_staff': True,
        },
        {
            'username': 'librarian',
            'email': 'librarian@tcu.edu.ph',
            'password': 'librarian12345',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'role': Profile.LIBRARIAN,
            'is_superuser': False,
            'is_staff': True,
        },
        {
            'username': 'professor',
            'email': 'professor@tcu.edu.ph',
            'password': 'professor12345',
            'first_name': 'Dr. Ramon',
            'last_name': 'Del Rosario',
            'role': Profile.PROFESSOR,
            'is_superuser': False,
            'is_staff': False,
        },
        {
            'username': 'student',
            'email': 'student@tcu.edu.ph',
            'password': 'student12345',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'role': Profile.STUDENT,
            'is_superuser': False,
            'is_staff': False,
        },
    ]

    for u_info in demo_users:
        user, created = User.objects.get_or_create(username=u_info['username'], defaults={
            'email': u_info['email'],
            'first_name': u_info['first_name'],
            'last_name': u_info['last_name'],
            'is_superuser': u_info['is_superuser'],
            'is_staff': u_info['is_staff'],
        })
        user.set_password(u_info['password'])
        user.first_name = u_info['first_name']
        user.last_name = u_info['last_name']
        user.email = u_info['email']
        user.is_superuser = u_info['is_superuser']
        user.is_staff = u_info['is_staff']
        user.save()

        # Update profile role
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = u_info['role']
        profile.save()
        status = "Created" if created else "Updated"
        print(f"    [{status}] {u_info['role'].capitalize()} user: {user.username} (Password: {u_info['password']})")

    print("\n--> Seeding categories & departments...")
    cat_undergrad, _ = Category.objects.get_or_create(name='Undergraduate')
    cat_grad, _ = Category.objects.get_or_create(name='Graduate')

    dept_defs = [
        (cat_undergrad, "College of Information and Communications Technology (CICT)"),
        (cat_undergrad, "College of Arts and Sciences (CAS)"),
        (cat_undergrad, "College of Business and Administration (CBA)"),
        (cat_undergrad, "College of Education (CED)"),
        (cat_undergrad, "College of Engineering and Technology (COE)"),
        (cat_undergrad, "College of Hospitality and Tourism Management (CHTM)"),
        (cat_undergrad, "College of Criminology (CCJ)"),
        (cat_grad, "Graduate Studies (GS)"),
    ]

    departments = {}
    for cat, dept_name in dept_defs:
        dept, _ = Department.objects.get_or_create(name=dept_name, category=cat)
        departments[dept_name] = dept

    print(f"    Loaded {len(departments)} departments across {Category.objects.count()} categories.")

    print("\n--> Seeding courses...")
    course_defs = [
        ("Bachelor of Science in Information Technology (BSIT)", "College of Information and Communications Technology (CICT)"),
        ("Bachelor of Science in Computer Science (BSCS)", "College of Information and Communications Technology (CICT)"),
        ("Bachelor of Science in Psychology (BSP)", "College of Arts and Sciences (CAS)"),
        ("Bachelor of Science in Business Administration (BSBA)", "College of Business and Administration (CBA)"),
        ("Bachelor of Science in Accountancy (BSA)", "College of Business and Administration (CBA)"),
        ("Bachelor of Secondary Education (BSED)", "College of Education (CED)"),
        ("Bachelor of Science in Industrial Engineering (BSIE)", "College of Engineering and Technology (COE)"),
        ("Bachelor of Science in Hospitality Management (BSHM)", "College of Hospitality and Tourism Management (CHTM)"),
        ("Bachelor of Science in Criminology (BSCrim)", "College of Criminology (CCJ)"),
        ("Master in Information Technology (MIT)", "Graduate Studies (GS)"),
    ]

    courses = {}
    for c_name, d_name in course_defs:
        dept = departments[d_name]
        course, _ = Course.objects.get_or_create(name=c_name, department=dept)
        courses[c_name] = course

    print(f"    Loaded {len(courses)} courses.")

    print("\n--> Seeding sample academic research theses...")
    sample_theses = [
        {
            'title': 'Autonomous Disaster Response Navigation Using Edge AI and Low-Power LoRa Mesh Networks',
            'author': 'Althea Nicole Santos',
            'coauthors': [('Angelo Cruz', '2021-00214', 'acruz@tcu.edu.ph'), ('Christian David Reyes', '2021-00389', 'creyes@tcu.edu.ph')],
            'year': 2025,
            'abstract': 'This capstone project introduces an emergency communication and telemetry mesh powered by edge compute micro-controllers and LoRa transceivers. By analyzing real-time sensor packets during simulated flood evacuations in Taguig City barangays, the model identifies optimal rescue paths with a 94.6% pathfinding efficiency even under cellular grid blackouts.',
            'thesis_type': 'Capstone Project',
            'specialization': 'Network Systems & Embedded AI',
            'keywords': 'Edge AI, LoRa Mesh, Disaster Risk Reduction, Embedded Systems, IoT',
            'research_category': 'Applied Technology',
            'supervisor_name': 'Prof. Manuel Bautista',
            'supervisor_email': 'mbautista@tcu.edu.ph',
            'supervisor_department': 'College of Information and Communications Technology (CICT)',
            'supervisor_title': 'Associate Professor',
            'category': cat_undergrad,
            'department': departments["College of Information and Communications Technology (CICT)"],
            'course': courses["Bachelor of Science in Information Technology (BSIT)"],
            'lc_classification': 'QA76.9.E33 S26 2025',
        },
        {
            'title': 'Deep Learning Framework for Automated Early Detection of Retinopathy in Community Health Units',
            'author': 'Mark Jason Gutierrez',
            'coauthors': [('Patricia Joy Mendoza', '2021-00512', 'pmendoza@tcu.edu.ph')],
            'year': 2025,
            'abstract': 'Investigating diabetic retinopathy detection in decentralized healthcare clinics with limited ophthalmology specialists. A lightweight Convolutional Neural Network (CNN) trained with augmented fundus photography achieved a 92.4% sensitivity and 96.1% specificity, offering a feasible web-assisted diagnostic screening tool for local health workers.',
            'thesis_type': 'Undergraduate Thesis',
            'specialization': 'Artificial Intelligence & Biomedical Informatics',
            'keywords': 'Deep Learning, Medical Imaging, CNN, Ophthalmology, Public Health',
            'research_category': 'Medical Informatics',
            'supervisor_name': 'Dr. Ramon Del Rosario',
            'supervisor_email': 'professor@tcu.edu.ph',
            'supervisor_department': 'College of Information and Communications Technology (CICT)',
            'supervisor_title': 'Professor III',
            'category': cat_undergrad,
            'department': departments["College of Information and Communications Technology (CICT)"],
            'course': courses["Bachelor of Science in Computer Science (BSCS)"],
            'lc_classification': 'RE661.D5 G88 2025',
        },
        {
            'title': 'Psychological Resilience, Coping Strategies, and Academic Burnout among First-Generation College Students',
            'author': 'Camille Anne Fernandez',
            'coauthors': [('Jerome Kyle Villanueva', '2021-00891', 'jvillanueva@tcu.edu.ph')],
            'year': 2024,
            'abstract': 'A correlational assessment examining the relationship between trait resilience, social support systems, and burnout dimensions among 380 first-generation university scholars. Findings revealed that cognitive reframing and institutional peer mentoring significantly moderated emotional exhaustion and cynicism.',
            'thesis_type': 'Undergraduate Thesis',
            'specialization': 'Educational & Clinical Psychology',
            'keywords': 'Academic Burnout, Resilience, First-Generation Students, Mental Health, Coping Mechanisms',
            'research_category': 'Behavioral Sciences',
            'supervisor_name': 'Dr. Elena Garcia',
            'supervisor_email': 'egarcia@tcu.edu.ph',
            'supervisor_department': 'College of Arts and Sciences (CAS)',
            'supervisor_title': 'Dean, College of Arts and Sciences',
            'category': cat_undergrad,
            'department': departments["College of Arts and Sciences (CAS)"],
            'course': courses["Bachelor of Science in Psychology (BSP)"],
            'lc_classification': 'BF575.S75 F47 2024',
        },
        {
            'title': 'Financial Resilience and Digital Payment Adoption among Micro-Enterprises in Urban Public Markets',
            'author': 'Joshua Paul Lim',
            'coauthors': [('Bernadette Flores', '2021-00104', 'bflores@tcu.edu.ph')],
            'year': 2024,
            'abstract': 'This study analyzes factors driving QR and mobile wallet adoption among vendor cooperatives in Taguig City. Utilizing the Extended Unified Theory of Acceptance and Use of Technology (UTAUT2), results indicate transaction transparency and low settlement fees as the greatest positive drivers for micro-vendor financial inclusion.',
            'thesis_type': 'Feasibility & Market Research',
            'specialization': 'Financial Management & FinTech',
            'keywords': 'Digital Payments, FinTech, Micro-enterprises, Financial Inclusion, Public Market',
            'research_category': 'Business & Economics',
            'supervisor_name': 'Prof. Arthur Soriano',
            'supervisor_email': 'asoriano@tcu.edu.ph',
            'supervisor_department': 'College of Business and Administration (CBA)',
            'supervisor_title': 'Associate Professor',
            'category': cat_undergrad,
            'department': departments["College of Business and Administration (CBA)"],
            'course': courses["Bachelor of Science in Business Administration (BSBA)"],
            'lc_classification': 'HG1710 .L56 2024',
        },
        {
            'title': 'Hybrid Gamification Framework to Enhance Mathematical Literacy in High School Blended Learning',
            'author': 'Katherine Rose Dimatulac',
            'coauthors': [],
            'year': 2025,
            'abstract': 'An action research project detailing the design, deployment, and psychometric evaluation of a gamified learning management companion for Grade 10 Trigonometry. Pre-test and post-test analyses demonstrated a statistically significant 28% increase in conceptual retention compared to traditional instructional delivery.',
            'thesis_type': 'Action Research',
            'specialization': 'Curriculum & Educational Technology',
            'keywords': 'Gamification, Mathematics Education, Instructional Design, Blended Learning, Retention',
            'research_category': 'Education',
            'supervisor_name': 'Dr. Cristina Valenzuela',
            'supervisor_email': 'cvalenzuela@tcu.edu.ph',
            'supervisor_department': 'College of Education (CED)',
            'supervisor_title': 'Professor I',
            'category': cat_undergrad,
            'department': departments["College of Education (CED)"],
            'course': courses["Bachelor of Secondary Education (BSED)"],
            'lc_classification': 'QA11 .D56 2025',
        },
        {
            'title': 'Ergonomic Optimization and Lean Line Balancing in Semiconductor Packaging Assembly Lines',
            'author': 'Dominic Kyle Ocampo',
            'coauthors': [('Vincent Paul Mercado', '2021-00445', 'vmercado@tcu.edu.ph')],
            'year': 2024,
            'abstract': 'A systems engineering intervention combining Rapid Upper Limb Assessment (RULA) with Ranked Positional Weight line balancing algorithms to minimize repetitive strain injuries and bottleneck idle times in electronics assembly, yielding a 17.5% throughput increase and 34% reduction in postural ergonomic risk.',
            'thesis_type': 'Undergraduate Thesis',
            'specialization': 'Ergonomics & Operations Research',
            'keywords': 'Industrial Engineering, Ergonomics, Lean Manufacturing, Line Balancing, Assembly Optimization',
            'research_category': 'Engineering',
            'supervisor_name': 'Engr. Roberto Aguilar',
            'supervisor_email': 'raguilar@tcu.edu.ph',
            'supervisor_department': 'College of Engineering and Technology (COE)',
            'supervisor_title': 'Department Chair',
            'category': cat_undergrad,
            'department': departments["College of Engineering and Technology (COE)"],
            'course': courses["Bachelor of Science in Industrial Engineering (BSIE)"],
            'lc_classification': 'T59.7 .O33 2024',
        },
        {
            'title': 'Predictive Geospatial Modeling of Street-Level Crime Hotspots Using Spatial-Temporal Point Processes',
            'author': 'Police Corporal Rafael Medina',
            'coauthors': [('Sgt. Leah Marie Navarro', '2020-00912', 'lnavarro@tcu.edu.ph')],
            'year': 2025,
            'abstract': 'Applying Kernel Density Estimation (KDE) and spatial econometric clustering to five years of barangay blotter records. The resulting tactical patrol allocation maps provided local police precincts with proactive patrol guidance, correlating with a notable dip in opportunistic property theft incidents.',
            'thesis_type': 'Applied Thesis',
            'specialization': 'Crime Mapping & Quantitative Criminology',
            'keywords': 'Crime Mapping, GIS, Spatial Statistics, Predictive Policing, Law Enforcement',
            'research_category': 'Criminal Justice',
            'supervisor_name': 'Dr. Vicente Manlapaz',
            'supervisor_email': 'vmanlapaz@tcu.edu.ph',
            'supervisor_department': 'College of Criminology (CCJ)',
            'supervisor_title': 'Professor II',
            'category': cat_undergrad,
            'department': departments["College of Criminology (CCJ)"],
            'course': courses["Bachelor of Science in Criminology (BSCrim)"],
            'lc_classification': 'HV7936.C88 M43 2025',
        },
        {
            'title': 'Zero-Trust Security Architecture for Multi-Campus Higher Education Cloud Repositories',
            'author': 'Kristine Joy Macaraeg',
            'coauthors': [],
            'year': 2025,
            'abstract': 'This masteral thesis formulates a defense-in-depth Zero-Trust Architecture (ZTA) tailored for distributed state universities. By embedding micro-segmentation, continuous identity attestation, and role-based cryptographic document access controls, the prototype demonstrates robust resistance against lateral movement attacks and credential stuffing threats.',
            'thesis_type': "Master's Dissertation",
            'specialization': 'Cloud Security & Enterprise Architecture',
            'keywords': 'Zero Trust, Information Security, Cloud Architecture, Access Control, Enterprise Repository',
            'research_category': 'Cybersecurity',
            'supervisor_name': 'Dr. Ramon Del Rosario',
            'supervisor_email': 'professor@tcu.edu.ph',
            'supervisor_department': 'Graduate Studies (GS)',
            'supervisor_title': 'Graduate Program Director',
            'category': cat_grad,
            'department': departments["Graduate Studies (GS)"],
            'course': courses["Master in Information Technology (MIT)"],
            'lc_classification': 'QA76.9.A25 M33 2025',
        },
    ]

    for item in sample_theses:
        coauthors_data = item.pop('coauthors')
        thesis, created = Thesis.objects.get_or_create(title=item['title'], defaults=item)
        if created:
            for c_name, c_id, c_email in coauthors_data:
                parts = c_name.split(' ', 1)
                first = parts[0]
                last = parts[1] if len(parts) > 1 else ''
                CoAuthor.objects.create(
                    thesis=thesis,
                    first_name=first,
                    last_name=last,
                    student_id=c_id,
                    email=c_email,
                )
            print(f"    [Created] Thesis: '{thesis.title[:50]}...' ({thesis.year})")
        else:
            print(f"    [Exists] Thesis: '{thesis.title[:50]}...'")

    print("\n========================================================")
    print("DEMO SEEDING COMPLETE!")
    print("========================================================")
    print("Demo Credentials:")
    print("  • Admin:     admin     / admin12345")
    print("  • Librarian: librarian / librarian12345")
    print("  • Professor: professor / professor12345")
    print("  • Student:   student   / student12345")
    print("========================================================\n")

if __name__ == '__main__':
    seed()
