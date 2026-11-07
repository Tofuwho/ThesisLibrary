/**
 * demo.js - Interactive client-side controller for TCU Thesis Library GitHub Live Demo
 */

const SAMPLE_THESES = [
    {
        id: 1,
        title: "Autonomous Disaster Response Navigation Using Edge AI and Low-Power LoRa Mesh Networks",
        author: "Althea Nicole Santos",
        coauthors: ["Angelo Cruz", "Christian David Reyes"],
        year: 2025,
        department: "CICT",
        dept_name: "College of Information and Communications Technology (CICT)",
        dept_code: "cict",
        course: "Bachelor of Science in Information Technology (BSIT)",
        category: "Undergraduate",
        abstract: "This capstone project introduces an emergency communication and telemetry mesh powered by edge compute micro-controllers and LoRa transceivers. By analyzing real-time sensor packets during simulated flood evacuations in Taguig City barangays, the model identifies optimal rescue paths with a 94.6% pathfinding efficiency even under cellular grid blackouts.",
        keywords: ["Edge AI", "LoRa Mesh", "Disaster Risk Reduction", "Embedded Systems", "IoT"],
        supervisor: "Prof. Manuel Bautista",
        supervisor_email: "mbautista@tcu.edu.ph",
        lc_classification: "QA76.9.E33 S26 2025",
        specialization: "Network Systems & Embedded AI"
    },
    {
        id: 2,
        title: "Deep Learning Framework for Automated Early Detection of Retinopathy in Community Health Units",
        author: "Mark Jason Gutierrez",
        coauthors: ["Patricia Joy Mendoza"],
        year: 2025,
        department: "CICT",
        dept_name: "College of Information and Communications Technology (CICT)",
        dept_code: "cict",
        course: "Bachelor of Science in Computer Science (BSCS)",
        category: "Undergraduate",
        abstract: "Investigating diabetic retinopathy detection in decentralized healthcare clinics with limited ophthalmology specialists. A lightweight Convolutional Neural Network (CNN) trained with augmented fundus photography achieved a 92.4% sensitivity and 96.1% specificity, offering a feasible web-assisted diagnostic screening tool for local health workers.",
        keywords: ["Deep Learning", "Medical Imaging", "CNN", "Ophthalmology", "Public Health"],
        supervisor: "Dr. Ramon Del Rosario",
        supervisor_email: "professor@tcu.edu.ph",
        lc_classification: "RE661.D5 G88 2025",
        specialization: "Artificial Intelligence & Biomedical Informatics"
    },
    {
        id: 3,
        title: "Psychological Resilience, Coping Strategies, and Academic Burnout among First-Generation College Students",
        author: "Camille Anne Fernandez",
        coauthors: ["Jerome Kyle Villanueva"],
        year: 2024,
        department: "CAS",
        dept_name: "College of Arts and Sciences (CAS)",
        dept_code: "cas",
        course: "Bachelor of Science in Psychology (BSP)",
        category: "Undergraduate",
        abstract: "A correlational assessment examining the relationship between trait resilience, social support systems, and burnout dimensions among 380 first-generation university scholars. Findings revealed that cognitive reframing and institutional peer mentoring significantly moderated emotional exhaustion and cynicism.",
        keywords: ["Academic Burnout", "Resilience", "First-Generation Students", "Mental Health", "Coping Mechanisms"],
        supervisor: "Dr. Elena Garcia",
        supervisor_email: "egarcia@tcu.edu.ph",
        lc_classification: "BF575.S75 F47 2024",
        specialization: "Educational & Clinical Psychology"
    },
    {
        id: 4,
        title: "Financial Resilience and Digital Payment Adoption among Micro-Enterprises in Urban Public Markets",
        author: "Joshua Paul Lim",
        coauthors: ["Bernadette Flores"],
        year: 2024,
        department: "CBA",
        dept_name: "College of Business and Administration (CBA)",
        dept_code: "cba",
        course: "Bachelor of Science in Business Administration (BSBA)",
        category: "Undergraduate",
        abstract: "This study analyzes factors driving QR and mobile wallet adoption among vendor cooperatives in Taguig City. Utilizing the Extended Unified Theory of Acceptance and Use of Technology (UTAUT2), results indicate transaction transparency and low settlement fees as the greatest positive drivers for micro-vendor financial inclusion.",
        keywords: ["Digital Payments", "FinTech", "Micro-enterprises", "Financial Inclusion", "Public Market"],
        supervisor: "Prof. Arthur Soriano",
        supervisor_email: "asoriano@tcu.edu.ph",
        lc_classification: "HG1710 .L56 2024",
        specialization: "Financial Management & FinTech"
    },
    {
        id: 5,
        title: "Hybrid Gamification Framework to Enhance Mathematical Literacy in High School Blended Learning",
        author: "Katherine Rose Dimatulac",
        coauthors: [],
        year: 2025,
        department: "CED",
        dept_name: "College of Education (CED)",
        dept_code: "ced",
        course: "Bachelor of Secondary Education (BSED)",
        category: "Undergraduate",
        abstract: "An action research project detailing the design, deployment, and psychometric evaluation of a gamified learning management companion for Grade 10 Trigonometry. Pre-test and post-test analyses demonstrated a statistically significant 28% increase in conceptual retention compared to traditional instructional delivery.",
        keywords: ["Gamification", "Mathematics Education", "Instructional Design", "Blended Learning", "Retention"],
        supervisor: "Dr. Cristina Valenzuela",
        supervisor_email: "cvalenzuela@tcu.edu.ph",
        lc_classification: "QA11 .D56 2025",
        specialization: "Curriculum & Educational Technology"
    },
    {
        id: 6,
        title: "Ergonomic Optimization and Lean Line Balancing in Semiconductor Packaging Assembly Lines",
        author: "Dominic Kyle Ocampo",
        coauthors: ["Vincent Paul Mercado"],
        year: 2024,
        department: "COE",
        dept_name: "College of Engineering and Technology (COE)",
        dept_code: "coe",
        course: "Bachelor of Science in Industrial Engineering (BSIE)",
        category: "Undergraduate",
        abstract: "A systems engineering intervention combining Rapid Upper Limb Assessment (RULA) with Ranked Positional Weight line balancing algorithms to minimize repetitive strain injuries and bottleneck idle times in electronics assembly, yielding a 17.5% throughput increase and 34% reduction in postural ergonomic risk.",
        keywords: ["Industrial Engineering", "Ergonomics", "Lean Manufacturing", "Line Balancing", "Assembly Optimization"],
        supervisor: "Engr. Roberto Aguilar",
        supervisor_email: "raguilar@tcu.edu.ph",
        lc_classification: "T59.7 .O33 2024",
        specialization: "Ergonomics & Operations Research"
    },
    {
        id: 7,
        title: "Predictive Geospatial Modeling of Street-Level Crime Hotspots Using Spatial-Temporal Point Processes",
        author: "Police Corporal Rafael Medina",
        coauthors: ["Sgt. Leah Marie Navarro"],
        year: 2025,
        department: "CCJ",
        dept_name: "College of Criminology (CCJ)",
        dept_code: "ccj",
        course: "Bachelor of Science in Criminology (BSCrim)",
        category: "Undergraduate",
        abstract: "Applying Kernel Density Estimation (KDE) and spatial econometric clustering to five years of barangay blotter records. The resulting tactical patrol allocation maps provided local police precincts with proactive patrol guidance, correlating with a notable dip in opportunistic property theft incidents.",
        keywords: ["Crime Mapping", "GIS", "Spatial Statistics", "Predictive Policing", "Law Enforcement"],
        supervisor: "Dr. Vicente Manlapaz",
        supervisor_email: "vmanlapaz@tcu.edu.ph",
        lc_classification: "HV7936.C88 M43 2025",
        specialization: "Crime Mapping & Quantitative Criminology"
    },
    {
        id: 8,
        title: "Zero-Trust Security Architecture for Multi-Campus Higher Education Cloud Repositories",
        author: "Kristine Joy Macaraeg",
        coauthors: [],
        year: 2025,
        department: "GS",
        dept_name: "Graduate Studies (GS)",
        dept_code: "gs",
        course: "Master in Information Technology (MIT)",
        category: "Graduate",
        abstract: "This masteral thesis formulates a defense-in-depth Zero-Trust Architecture (ZTA) tailored for distributed state universities. By embedding micro-segmentation, continuous identity attestation, and role-based cryptographic document access controls, the prototype demonstrates robust resistance against lateral movement attacks and credential stuffing threats.",
        keywords: ["Zero Trust", "Information Security", "Cloud Architecture", "Access Control", "Enterprise Repository"],
        supervisor: "Dr. Ramon Del Rosario",
        supervisor_email: "professor@tcu.edu.ph",
        lc_classification: "QA76.9.A25 M33 2025",
        specialization: "Cloud Security & Enterprise Architecture"
    }
];

// Current simulated auth state
let currentDemoUser = JSON.parse(localStorage.getItem('tcu_demo_user')) || {
    role: 'guest',
    name: 'Guest User',
    id: null
};

function setDemoRole(role) {
    if (role === 'guest') {
        currentDemoUser = { role: 'guest', name: 'Guest User', id: null };
    } else if (role === 'admin') {
        currentDemoUser = { role: 'admin', name: 'TCU Admin', id: '2024-ADMIN' };
    } else if (role === 'librarian') {
        currentDemoUser = { role: 'librarian', name: 'Maria Santos', id: '2024-LIB' };
    } else if (role === 'professor') {
        currentDemoUser = { role: 'professor', name: 'Dr. Ramon Del Rosario', id: '2024-FACULTY' };
    } else if (role === 'student') {
        currentDemoUser = { role: 'student', name: 'Juan Dela Cruz', id: '2024-00412' };
    }
    localStorage.setItem('tcu_demo_user', JSON.stringify(currentDemoUser));
    showDemoNotification(`Switched demo session to: ${currentDemoUser.role.toUpperCase()}`, 'success');
    renderDemoUserUI();
}

function showDemoNotification(msg, type = 'info') {
    let container = document.getElementById('demoNotificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'demoNotificationContainer';
        container.style.cssText = 'position:fixed; top:75px; right:20px; z-index:99999; display:flex; flex-direction:column; gap:10px; pointer-events:none;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.style.cssText = 'background:#fff; border-left:4px solid ' + (type === 'success' ? '#22c55e' : '#800000') + '; box-shadow:0 8px 24px rgba(0,0,0,0.18); padding:12px 18px; border-radius:8px; font-size:14px; color:#1e293b; display:flex; align-items:center; gap:10px; pointer-events:auto; animation:slideIn 0.3s ease;';
    toast.innerHTML = `<i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}" style="color:${type === 'success' ? '#22c55e' : '#800000'}"></i><span>${msg}</span>`;
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
        b.textContent = currentDemoUser.name + ' (' + currentDemoUser.role.toUpperCase() + ')';
    });
    const authToggles = document.querySelectorAll('.demo-auth-only');
    authToggles.forEach(el => {
        if (currentDemoUser.role === 'guest') {
            el.style.display = 'none';
        } else {
            el.style.display = '';
        }
    });
    const guestOnly = document.querySelectorAll('.demo-guest-only');
    guestOnly.forEach(el => {
        if (currentDemoUser.role === 'guest') {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderDemoUserUI();

    // Modal close handlers
    document.querySelectorAll('.close-modal, .modal-backdrop-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
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
