<?php 
// Include the header file which contains the site's navigation and opening HTML structure
include 'includes/header.php'; 
?>

<!-- Hero Section: Main introductory banner with title, subtitle, and search/filter form -->
<section class="hero">
    <div class="container">
        <!-- Main title of the page -->
        <h2 class="section-title">CICT Thesis Repository</h2>
        
        <!-- Subtitle giving more context -->
        <p class="section-subtitle">
            Discover outstanding research from the College of Information and Communications Technology
        </p>
        
        <!-- Search bar for querying thesis titles -->
        <div class="search-container">
            <form action="#" method="GET" class="search-form">
                <input type="text" name="search" id="search" placeholder="Search for theses..." class="search-input">
                <button type="submit" class="search-button">
                    <span>search</span>
                </button>
            </form>
        </div>
        
        <!-- Filter options for narrowing down thesis results -->
        <div class="filter-container">
            <!-- Filter by specialization -->
            <div class="filter-dropdown">
                <select name="specialization" id="specialization">
                    <option value="">All specialization</option>
                    <option value="cs">Computer Science</option>
                    <option value="it">Information Technology</option>
                    <option value="is">Information Systems</option>
                    <option value="net">Networking</option>
                </select>
            </div>

            <!-- Filter by year -->
            <div class="filter-dropdown">
                <select name="year" id="year">
                    <option value="">All Years</option>
                    <option value="2025">2025</option>
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                    <option value="2022">2022</option>
                    <option value="2021">2021</option>
                </select>
            </div>

            <!-- Filter by relevance or sorting order -->
            <div class="filter-dropdown">
                <select name="relevance" id="relevance">
                    <option value="relevance">Relevance</option>
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                    <option value="a-z">A-Z</option>
                    <option value="z-a">Z-A</option>
                </select>
            </div>
        </div>
    </div>
</section>

<!-- Recently Added Section: Displays a set of the most recently added theses -->
<section class="recently-added">
    <div class="container">
        <h2 class="section-title">Recently Added Thesis</h2>
        
        <!-- Grid layout for thesis cards -->
        <div class="thesis-grid">
            <?php for($i = 1; $i <= 6; $i++): ?>
            <div class="thesis-card">
                <!-- Placeholder for thesis cover image -->
                <div class="thesis-cover">
                    <div class="thesis-cover-placeholder">Thesis Cover Picture</div>
                </div>
                
                <!-- Thesis details (title, author, metadata, view link) -->
                <div class="thesis-info">
                    <h3 class="thesis-title">Title</h3>
                    <p class="thesis-author">By Name</p>
                    <p class="thesis-meta">Specialization | Year</p>
                    <a href="#" class="view-button">View</a>
                </div>
            </div>
            <?php endfor; ?>
        </div>

        <!-- Link to full thesis listing -->
        <div class="pagination">
            <a href="thesis.html" class="pagination-button">View Thesis</a>
        </div>
    </div>
</section>

<!-- Categories Section: Allows browsing by thesis categories -->
<section class="categories">
    <div class="container">
        <h2 class="section-title">Browse by Category</h2>
        
        <!-- Grid layout for category cards -->
        <div class="category-grid">
            <?php for($i = 1; $i <= 6; $i++): ?>
            <div class="category-card">
                <!-- Icon representing the category -->
                <div class="category-icon">
                    <i class="fas fa-book"></i>
                </div>

                <!-- Short category description -->
                <div class="category-description">Category Description</div>

                <!-- Link to browse theses in this category -->
                <a href="#" class="browse-button">Browse</a>
            </div>
            <?php endfor; ?>
        </div>
    </div>
</section>

<!-- Resources Section: Helpful links for researchers -->
<section class="resources">
    <div class="container">
        <h2 class="section-title">Resources for Researchers</h2>
        
        <!-- Grid layout for resources -->
        <div class="resources-grid">
            <!-- Card for thesis submission info -->
            <div class="resource-card">
                <h3>Submit Your Thesis</h3>
                <p>Are you a student looking to publish your research? Learn about our submission process and guidelines.</p>
                <a href="#" class="resource-button">Submit now</a>
            </div>

            <!-- Card for research assistance -->
            <div class="resource-card">
                <h3>Research Assistance</h3>
                <p>Need help with your research? Connect with faculty advisors and research specialists.</p>
                <a href="#" class="resource-button">Get help</a>
            </div>
        </div>
    </div>
</section>

<?php 
// Include the footer file which contains closing HTML tags and scripts
include 'includes/footer.php'; 
?>
