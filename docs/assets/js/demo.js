/**
 * demo.js - Institutional Repository Controller for TCU Thesis Library
 * Conforms to Dublin Core, Library of Congress Classification (LCC), and Academic Repository Standards
 */

const SAMPLE_THESES = [
    {
        id: 1,
        title: "Autonomous Disaster Response Navigation Using Edge AI and Low-Power LoRa Mesh Networks",
        author: "Santos, Althea Nicole M.",
        author_plain: "Althea Nicole Santos",
        author_id: "2021-00214",
        coauthors: [
            { name: "Cruz, Angelo R.", id: "2021-00318", email: "acruz@tcu.edu.ph" },
            { name: "Reyes, Christian David T.", id: "2021-00389", email: "creyes@tcu.edu.ph" }
        ],
        year: 2025,
        date_accepted: "March 24, 2025",
        department: "CICT",
        dept_name: "College of Information and Communications Technology (CICT)",
        dept_code: "cict",
        course: "Bachelor of Science in Information Technology (BSIT)",
        degree: "Bachelor of Science in Information Technology",
        category: "Undergraduate",
        thesis_type: "Undergraduate Capstone Project",
        abstract: "This capstone project introduces an emergency communication and telemetry mesh powered by edge compute micro-controllers and LoRa transceivers. By analyzing real-time sensor packets during simulated flood evacuations in Taguig City barangays, the model identifies optimal rescue paths with a 94.6% pathfinding efficiency even under cellular grid blackouts.",
        keywords: ["Edge AI", "LoRa Mesh", "Disaster Risk Reduction", "Embedded Systems", "IoT"],
        lcsh_subjects: [
            "Emergency communication systems -- Philippines -- Taguig City",
            "Artificial intelligence -- Edge computing",
            "Wireless sensor networks"
        ],
        supervisor: "Prof. Manuel Bautista, M.S.I.T.",
        supervisor_email: "mbautista@tcu.edu.ph",
        supervisor_role: "Thesis Adviser",
        co_supervisor: "Engr. Lorna P. Dizon",
        lc_classification: "QA76.9.E33 S26 2025",
        dewey_classification: "004.65",
        accession_no: "TCU-CICT-2025-001",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2025-001",
        pagination: "xvi, 142 leaves : color illustrations, maps ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Network Systems & Embedded AI",
        views_count: 614,
        downloads_prevented: 182
    },
    {
        id: 2,
        title: "Deep Learning Framework for Automated Early Detection of Retinopathy in Community Health Units",
        author: "Gutierrez, Mark Jason S.",
        author_plain: "Mark Jason Gutierrez",
        author_id: "2021-00412",
        coauthors: [
            { name: "Mendoza, Patricia Joy C.", id: "2021-00512", email: "pmendoza@tcu.edu.ph" }
        ],
        year: 2025,
        date_accepted: "February 18, 2025",
        department: "CICT",
        dept_name: "College of Information and Communications Technology (CICT)",
        dept_code: "cict",
        course: "Bachelor of Science in Computer Science (BSCS)",
        degree: "Bachelor of Science in Computer Science",
        category: "Undergraduate",
        thesis_type: "Undergraduate Thesis",
        abstract: "Investigating diabetic retinopathy detection in decentralized healthcare clinics with limited ophthalmology specialists. A lightweight Convolutional Neural Network (CNN) trained with augmented fundus photography achieved a 92.4% sensitivity and 96.1% specificity, offering a feasible web-assisted diagnostic screening tool for local health workers.",
        keywords: ["Deep Learning", "Medical Imaging", "CNN", "Ophthalmology", "Public Health"],
        lcsh_subjects: [
            "Diabetic retinopathy -- Diagnosis -- Computer-assisted",
            "Computer vision -- Medical applications",
            "Convolutional neural networks"
        ],
        supervisor: "Dr. Ramon Del Rosario, Ph.D.",
        supervisor_email: "professor@tcu.edu.ph",
        supervisor_role: "Lead Thesis Adviser",
        co_supervisor: "Dr. Carmela Aquino, M.D.",
        lc_classification: "RE661.D5 G88 2025",
        dewey_classification: "617.735",
        accession_no: "TCU-CICT-2025-002",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2025-002",
        pagination: "xiv, 128 leaves : color illustrations ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Artificial Intelligence & Biomedical Informatics",
        views_count: 842,
        downloads_prevented: 240
    },
    {
        id: 3,
        title: "Psychological Resilience, Coping Strategies, and Academic Burnout among First-Generation College Students",
        author: "Fernandez, Camille Anne V.",
        author_plain: "Camille Anne Fernandez",
        author_id: "2021-00628",
        coauthors: [
            { name: "Villanueva, Jerome Kyle D.", id: "2021-00891", email: "jvillanueva@tcu.edu.ph" }
        ],
        year: 2024,
        date_accepted: "November 12, 2024",
        department: "CAS",
        dept_name: "College of Arts and Sciences (CAS)",
        dept_code: "cas",
        course: "Bachelor of Science in Psychology (BSP)",
        degree: "Bachelor of Science in Psychology",
        category: "Undergraduate",
        thesis_type: "Undergraduate Thesis",
        abstract: "A correlational assessment examining the relationship between trait resilience, social support systems, and burnout dimensions among 380 first-generation university scholars. Findings revealed that cognitive reframing and institutional peer mentoring significantly moderated emotional exhaustion and cynicism.",
        keywords: ["Academic Burnout", "Resilience", "First-Generation Students", "Mental Health", "Coping Mechanisms"],
        lcsh_subjects: [
            "College students -- Psychology -- Philippines",
            "Burn out (Psychology) in adolescence",
            "Resilience (Personality trait)"
        ],
        supervisor: "Dr. Elena Garcia, RPsy",
        supervisor_email: "egarcia@tcu.edu.ph",
        supervisor_role: "Faculty Adviser",
        co_supervisor: "Prof. Melinda Soriano",
        lc_classification: "BF575.S75 F47 2024",
        dewey_classification: "155.9042",
        accession_no: "TCU-CAS-2024-019",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2024-019",
        pagination: "xii, 114 leaves : illustrations ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Educational & Clinical Psychology",
        views_count: 520,
        downloads_prevented: 135
    },
    {
        id: 4,
        title: "Financial Resilience and Digital Payment Adoption among Micro-Enterprises in Urban Public Markets",
        author: "Lim, Joshua Paul E.",
        author_plain: "Joshua Paul Lim",
        author_id: "2021-00104",
        coauthors: [
            { name: "Flores, Bernadette M.", id: "2021-00105", email: "bflores@tcu.edu.ph" }
        ],
        year: 2024,
        date_accepted: "October 30, 2024",
        department: "CBA",
        dept_name: "College of Business and Administration (CBA)",
        dept_code: "cba",
        course: "Bachelor of Science in Business Administration (BSBA)",
        degree: "Bachelor of Science in Business Administration",
        category: "Undergraduate",
        thesis_type: "Feasibility & Market Research",
        abstract: "This study analyzes factors driving QR and mobile wallet adoption among vendor cooperatives in Taguig City. Utilizing the Extended Unified Theory of Acceptance and Use of Technology (UTAUT2), results indicate transaction transparency and low settlement fees as the greatest positive drivers for micro-vendor financial inclusion.",
        keywords: ["Digital Payments", "FinTech", "Micro-enterprises", "Financial Inclusion", "Public Market"],
        lcsh_subjects: [
            "Electronic funds transfers -- Philippines -- Taguig City",
            "Small business -- Finance",
            "Mobile commerce -- Technological innovations"
        ],
        supervisor: "Prof. Arthur Soriano, M.B.A.",
        supervisor_email: "asoriano@tcu.edu.ph",
        supervisor_role: "Research Adviser",
        co_supervisor: "Prof. Cynthia David",
        lc_classification: "HG1710 .L56 2024",
        dewey_classification: "332.10285",
        accession_no: "TCU-CBA-2024-031",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2024-031",
        pagination: "xviii, 160 leaves : charts, tables ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Financial Management & FinTech",
        views_count: 478,
        downloads_prevented: 110
    },
    {
        id: 5,
        title: "Hybrid Gamification Framework to Enhance Mathematical Literacy in High School Blended Learning",
        author: "Dimatulac, Katherine Rose B.",
        author_plain: "Katherine Rose Dimatulac",
        author_id: "2021-00350",
        coauthors: [],
        year: 2025,
        date_accepted: "January 15, 2025",
        department: "CED",
        dept_name: "College of Education (CED)",
        dept_code: "ced",
        course: "Bachelor of Secondary Education (BSED)",
        degree: "Bachelor of Secondary Education major in Mathematics",
        category: "Undergraduate",
        thesis_type: "Action Research",
        abstract: "An action research project detailing the design, deployment, and psychometric evaluation of a gamified learning management companion for Grade 10 Trigonometry. Pre-test and post-test analyses demonstrated a statistically significant 28% increase in conceptual retention compared to traditional instructional delivery.",
        keywords: ["Gamification", "Mathematics Education", "Instructional Design", "Blended Learning", "Retention"],
        lcsh_subjects: [
            "Mathematics -- Study and teaching (Secondary)",
            "Gamification in education",
            "Blended learning -- Evaluation"
        ],
        supervisor: "Dr. Cristina Valenzuela, Ed.D.",
        supervisor_email: "cvalenzuela@tcu.edu.ph",
        supervisor_role: "Thesis Adviser",
        co_supervisor: "Prof. Danilo Santos",
        lc_classification: "QA11 .D56 2025",
        dewey_classification: "510.712",
        accession_no: "TCU-CED-2025-008",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2025-008",
        pagination: "xiv, 134 leaves : illustrations ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Curriculum & Educational Technology",
        views_count: 610,
        downloads_prevented: 145
    },
    {
        id: 6,
        title: "Ergonomic Optimization and Lean Line Balancing in Semiconductor Packaging Assembly Lines",
        author: "Ocampo, Dominic Kyle R.",
        author_plain: "Dominic Kyle Ocampo",
        author_id: "2021-00772",
        coauthors: [
            { name: "Mercado, Vincent Paul K.", id: "2021-00445", email: "vmercado@tcu.edu.ph" }
        ],
        year: 2024,
        date_accepted: "December 04, 2024",
        department: "COE",
        dept_name: "College of Engineering and Technology (COE)",
        dept_code: "coe",
        course: "Bachelor of Science in Industrial Engineering (BSIE)",
        degree: "Bachelor of Science in Industrial Engineering",
        category: "Undergraduate",
        thesis_type: "Undergraduate Thesis",
        abstract: "A systems engineering intervention combining Rapid Upper Limb Assessment (RULA) with Ranked Positional Weight line balancing algorithms to minimize repetitive strain injuries and bottleneck idle times in electronics assembly, yielding a 17.5% throughput increase and 34% reduction in postural ergonomic risk.",
        keywords: ["Industrial Engineering", "Ergonomics", "Lean Manufacturing", "Line Balancing", "Assembly Optimization"],
        lcsh_subjects: [
            "Human engineering -- Industrial applications",
            "Assembly-line methods -- Mathematical models",
            "Semiconductor industry -- Automation"
        ],
        supervisor: "Engr. Roberto Aguilar, P.E.",
        supervisor_email: "raguilar@tcu.edu.ph",
        supervisor_role: "Engineering Project Adviser",
        co_supervisor: "Engr. Maricel Gomez",
        lc_classification: "T59.7 .O33 2024",
        dewey_classification: "620.82",
        accession_no: "TCU-COE-2024-015",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2024-015",
        pagination: "xvi, 172 leaves : illustrations, diagrams ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Ergonomics & Operations Research",
        views_count: 535,
        downloads_prevented: 160
    },
    {
        id: 7,
        title: "Predictive Geospatial Modeling of Street-Level Crime Hotspots Using Spatial-Temporal Point Processes",
        author: "Medina, Rafael C. (PCpl)",
        author_plain: "Rafael Medina",
        author_id: "2020-00812",
        coauthors: [
            { name: "Navarro, Leah Marie S. (PSgt)", id: "2020-00912", email: "lnavarro@tcu.edu.ph" }
        ],
        year: 2025,
        date_accepted: "February 27, 2025",
        department: "CCJ",
        dept_name: "College of Criminology (CCJ)",
        dept_code: "ccj",
        course: "Bachelor of Science in Criminology (BSCrim)",
        degree: "Bachelor of Science in Criminology",
        category: "Undergraduate",
        thesis_type: "Applied Research Manuscript",
        abstract: "Applying Kernel Density Estimation (KDE) and spatial econometric clustering to five years of barangay blotter records. The resulting tactical patrol allocation maps provided local police precincts with proactive patrol guidance, correlating with a notable dip in opportunistic property theft incidents.",
        keywords: ["Crime Mapping", "GIS", "Spatial Statistics", "Predictive Policing", "Law Enforcement"],
        lcsh_subjects: [
            "Crime analysis -- Geographic information systems",
            "Police patrol -- Surveillance",
            "Criminology -- Statistical methods"
        ],
        supervisor: "Dr. Vicente Manlapaz, Ph.D. Crim.",
        supervisor_email: "vmanlapaz@tcu.edu.ph",
        supervisor_role: "Thesis Adviser",
        co_supervisor: "Atty. Fernando Morales",
        lc_classification: "HV7936.C88 M43 2025",
        dewey_classification: "363.232",
        accession_no: "TCU-CCJ-2025-004",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2025-004",
        pagination: "xiv, 150 leaves : maps, color charts ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Crime Mapping & Quantitative Criminology",
        views_count: 722,
        downloads_prevented: 198
    },
    {
        id: 8,
        title: "Zero-Trust Security Architecture for Multi-Campus Higher Education Cloud Repositories",
        author: "Macaraeg, Kristine Joy P.",
        author_plain: "Kristine Joy Macaraeg",
        author_id: "2023-90014",
        coauthors: [],
        year: 2025,
        date_accepted: "April 02, 2025",
        department: "GS",
        dept_name: "Graduate Studies (GS)",
        dept_code: "gs",
        course: "Master in Information Technology (MIT)",
        degree: "Master in Information Technology",
        category: "Graduate",
        thesis_type: "Master's Thesis Dissertation",
        abstract: "This masteral thesis formulates a defense-in-depth Zero-Trust Architecture (ZTA) tailored for distributed state universities. By embedding micro-segmentation, continuous identity attestation, and role-based cryptographic document access controls, the prototype demonstrates robust resistance against lateral movement attacks and credential stuffing threats.",
        keywords: ["Zero Trust", "Information Security", "Cloud Architecture", "Access Control", "Enterprise Repository"],
        lcsh_subjects: [
            "Computer security -- Universities and colleges",
            "Cloud computing -- Security measures",
            "Access control -- Standards"
        ],
        supervisor: "Dr. Ramon Del Rosario, Ph.D.",
        supervisor_email: "professor@tcu.edu.ph",
        supervisor_role: "Dissertation Chair",
        co_supervisor: "Dr. Jonathan Velasco",
        lc_classification: "QA76.9.A25 M33 2025",
        dewey_classification: "005.8",
        accession_no: "TCU-GS-2025-003",
        handle: "http://hdl.handle.net/20.500.12345/TCU-2025-003",
        pagination: "xx, 218 leaves : diagrams, tables ; 28 cm",
        language: "English (en-PH)",
        rights: "In Copyright - Educational Use Permitted (RA 8293 Philippine Intellectual Property Code)",
        specialization: "Cloud Security & Enterprise Architecture",
        views_count: 1040,
        downloads_prevented: 310
    }
];

// Current simulated auth state
let currentDemoUser = JSON.parse(localStorage.getItem('tcu_demo_user')) || {
    role: 'guest',
    name: 'Guest Researcher',
    id: null
};

function setDemoRole(role) {
    if (role === 'guest') {
        currentDemoUser = { role: 'guest', name: 'Guest Researcher', id: null };
    } else if (role === 'admin') {
        currentDemoUser = { role: 'admin', name: 'TCU System Administrator', id: 'TCU-ADMIN-01' };
    } else if (role === 'librarian') {
        currentDemoUser = { role: 'librarian', name: 'Maria Santos, RL (Chief Librarian)', id: 'LIB-2024-001' };
    } else if (role === 'professor') {
        currentDemoUser = { role: 'professor', name: 'Dr. Ramon Del Rosario (Faculty)', id: 'FAC-2024-082' };
    } else if (role === 'student') {
        currentDemoUser = { role: 'student', name: 'Juan Dela Cruz (Student Author)', id: '2024-00412' };
    }
    localStorage.setItem('tcu_demo_user', JSON.stringify(currentDemoUser));
    showDemoNotification(`Switched Active Persona: ${currentDemoUser.name}`, 'success');
    renderDemoUserUI();
}

function showDemoNotification(msg, type = 'info') {
    let container = document.getElementById('demoNotificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'demoNotificationContainer';
        container.style.cssText = 'position:fixed; top:85px; right:20px; z-index:999999; display:flex; flex-direction:column; gap:10px; pointer-events:none;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.style.cssText = 'background:#fff; border-left:4px solid ' + (type === 'success' ? '#22c55e' : '#800000') + '; box-shadow:0 8px 24px rgba(0,0,0,0.18); padding:12px 18px; border-radius:8px; font-size:13px; color:#1e293b; display:flex; align-items:center; gap:10px; pointer-events:auto; animation:slideIn 0.3s ease; font-family:"Atkinson Hyperlegible", sans-serif;';
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}" style="color:${type === 'success' ? '#22c55e' : '#800000'}; font-size:16px;"></i><span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.4s';
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

function renderDemoUserUI() {
    const userRoleBadges = document.querySelectorAll('.demo-user-role-label');
    userRoleBadges.forEach(b => {
        b.textContent = currentDemoUser.name;
    });

    const selector = document.querySelector('.demo-role-select');
    if (selector) {
        selector.value = currentDemoUser.role;
    }

    const authToggles = document.querySelectorAll('.demo-auth-only');
    authToggles.forEach(el => {
        el.style.display = currentDemoUser.role === 'guest' ? 'none' : '';
    });
    const guestOnly = document.querySelectorAll('.demo-guest-only');
    guestOnly.forEach(el => {
        el.style.display = currentDemoUser.role === 'guest' ? '' : 'none';
    });
}

// Generate Bibliographic Citations
function generateCitation(t, style) {
    const coauthorStr = t.coauthors.length > 0 ? (t.coauthors.length === 1 ? ` & ${t.coauthors[0].name}` : ` et al.`) : '';
    if (style === 'apa') {
        return `${t.author}${coauthorStr} (${t.year}). ${t.title} [${t.thesis_type}, Taguig City University]. TCU Institutional Repository. ${t.handle}`;
    } else if (style === 'mla') {
        return `${t.author}${t.coauthors.length ? ', et al' : ''}. "${t.title}." ${t.year}. Taguig City University, ${t.thesis_type}. TCU Institutional Repository, ${t.handle}.`;
    } else if (style === 'ieee') {
        const initials = t.author_plain.split(' ').map(n => n[0] + '.').join(' ');
        return `${initials} ${t.author.split(',')[0]}${t.coauthors.length ? ' et al.' : ''}, "${t.title}," ${t.thesis_type}, Dept. ${t.dept_name}, Taguig City Univ., Taguig, Philippines, ${t.year}.`;
    } else if (style === 'chicago') {
        return `${t.author}. "${t.title}." ${t.thesis_type}, Taguig City University, ${t.year}. ${t.handle}.`;
    } else if (style === 'bibtex') {
        const key = t.author.split(',')[0].toLowerCase() + t.year;
        return `@thesis{${key},
  title={${t.title}},
  author={${t.author}${t.coauthors.length ? ' and others' : ''}},
  year={${t.year}},
  school={Taguig City University},
  type={${t.thesis_type}},
  url={${t.handle}}
}`;
    }
    return '';
}

document.addEventListener('DOMContentLoaded', () => {
    renderDemoUserUI();

    // Modal close handlers
    document.querySelectorAll('.close-modal, .modal-backdrop-close').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.auth-modal, .modal').forEach(m => m.classList.remove('active'));
        });
    });

    // Auth modal trigger
    document.querySelectorAll('.btn-trigger-login, #loginButton').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = document.getElementById('authModal');
            if (modal) modal.classList.add('active');
        });
    });

    // Submission Guide modal
    const openGuideModal = document.getElementById('openGuideModal');
    if (openGuideModal) {
        openGuideModal.addEventListener('click', (e) => {
            e.preventDefault();
            const guideModal = document.getElementById('guideModal');
            if (guideModal) guideModal.classList.add('active');
        });
    }

    // Privacy Modal
    const openPrivacyModal = document.getElementById('openPrivacyModal');
    if (openPrivacyModal) {
        openPrivacyModal.addEventListener('click', (e) => {
            e.preventDefault();
            const privModal = document.getElementById('privacyModal');
            if (privModal) privModal.classList.add('active');
        });
    }
});
