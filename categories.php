<?php
session_start();
require_once 'auth/validate-session.php';
require_once 'config.php';

include BASE_PATH . 'header.php';
?>

    <!-- Main Content -->
    <main class="categories-main">
        <div class="container">
            <div class="categories-header">
                <h1 class="section-title">Browse Categories</h1>
                <p class="section-subtitle">Explore our vast collection of academic theses by category and filter</p>
                
                <!-- Search Form -->
                <div class="search-container">
                    <form class="search-form">
                        <input type="text" class="search-input" placeholder="Search by title, author, keyword...">
                        <button type="submit" class="search-button">
                            <i class="fas fa-search"></i> Search
                        </button>
                    </form>
                </div>
            </div>

            <div class="categories-content">
                <!-- Filter Sidebar -->
                <aside class="filter-sidebar">
                    <div class="filter-section">
                        <h3>Publication Date</h3>
                        <ul class="filter-list">
                            <li>
                                <label>
                                    <input type="checkbox" name="year" value="2025">
                                    <span>2025</span>
                                    <span class="count">(12)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="year" value="2024">
                                    <span>2024</span>
                                    <span class="count">(45)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="year" value="2023">
                                    <span>2023</span>
                                    <span class="count">(78)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="year" value="2022">
                                    <span>2022</span>
                                    <span class="count">(64)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="year" value="2021">
                                    <span>2021</span>
                                    <span class="count">(56)</span>
                                </label>
                            </li>
                        </ul>
                        <a href="#" class="show-more">Show more</a>
                    </div>

                    <div class="filter-section">
                        <h3>Descriptor</h3>
                        <ul class="filter-list">
                            <li>
                                <label>
                                    <input type="checkbox" name="descriptor" value="Computer Science">
                                    <span>Computer Science</span>
                                    <span class="count">(42)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="descriptor" value="Engineering">
                                    <span>Engineering</span>
                                    <span class="count">(36)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="descriptor" value="Biology">
                                    <span>Biology</span>
                                    <span class="count">(29)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="descriptor" value="Psychology">
                                    <span>Psychology</span>
                                    <span class="count">(24)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="descriptor" value="Education">
                                    <span>Education</span>
                                    <span class="count">(18)</span>
                                </label>
                            </li>
                        </ul>
                        <a href="#" class="show-more">Show more</a>
                    </div>

                    <div class="filter-section">
                        <h3>Author</h3>
                        <ul class="filter-list">
                            <li>
                                <label>
                                    <input type="checkbox" name="author" value="Johnson, M.">
                                    <span>Johnson, M.</span>
                                    <span class="count">(15)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="author" value="Smith, J.">
                                    <span>Smith, J.</span>
                                    <span class="count">(12)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="author" value="Williams, D.">
                                    <span>Williams, D.</span>
                                    <span class="count">(10)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="author" value="Brown, K.">
                                    <span>Brown, K.</span>
                                    <span class="count">(8)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="author" value="Miller, A.">
                                    <span>Miller, A.</span>
                                    <span class="count">(7)</span>
                                </label>
                            </li>
                        </ul>
                        <a href="#" class="show-more">Show more</a>
                    </div>

                    <div class="filter-section">
                        <h3>Publication Type</h3>
                        <ul class="filter-list">
                            <li>
                                <label>
                                    <input type="checkbox" name="type" value="PhD Dissertation">
                                    <span>PhD Dissertation</span>
                                    <span class="count">(87)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="type" value="Master's Thesis">
                                    <span>Master's Thesis</span>
                                    <span class="count">(124)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="type" value="Undergraduate Thesis">
                                    <span>Undergraduate Thesis</span>
                                    <span class="count">(56)</span>
                                </label>
                            </li>
                            <li>
                                <label>
                                    <input type="checkbox" name="type" value="Research Paper">
                                    <span>Research Paper</span>
                                    <span class="count">(43)</span>
                                </label>
                            </li>
                        </ul>
                    </div>

                    <button class="apply-filters-button">
                        <i class="fas fa-filter"></i> Apply Filters
                    </button>
                    <button class="clear-filters-button">
                        <i class="fas fa-times"></i> Clear All
                    </button>
                </aside>

                <!-- Thesis Results -->
                <div class="thesis-results">
                    <div class="results-header">
                        <h2>Results <span class="results-count">(255)</span></h2>
                        <div class="sort-options">
                            <label for="sort-by">Sort by:</label>
                            <select id="sort-by" class="sort-select">
                                <option value="date-desc">Date (Newest First)</option>
                                <option value="date-asc">Date (Oldest First)</option>
                                <option value="title-asc">Title (A-Z)</option>
                                <option value="title-desc">Title (Z-A)</option>
                            </select>
                        </div>
                    </div>

                    <div class="thesis-list">
                        <!-- Thesis Item 1 -->
                        <div class="thesis-item">
                            <div class="thesis-item-cover">
                                <div class="thesis-cover-placeholder">
                                    <i class="fas fa-file-alt"></i>
                                </div>
                            </div>
                            <div class="thesis-item-content">
                                <h3 class="thesis-item-title">Machine Learning Applications in Healthcare: A Comprehensive Review</h3>
                                <p class="thesis-item-author">Johnson, Michael R.</p>
                                <div class="thesis-item-meta">
                                    <span><i class="far fa-calendar-alt"></i> May 2025</span>
                                    <span><i class="fas fa-graduation-cap"></i> PhD Dissertation</span>
                                    <span><i class="fas fa-tag"></i> Computer Science, Healthcare</span>
                                </div>
                                <p class="thesis-item-abstract">This dissertation explores the applications of machine learning algorithms in healthcare settings, focusing on diagnostic accuracy, treatment optimization, and patient outcome prediction.</p>
                                <div class="thesis-item-actions">
                                    <a href="#" class="view-button"><i class="fas fa-eye"></i> View</a>
                                    <a href="#" class="download-button"><i class="fas fa-download"></i> Download</a>
                                </div>
                            </div>
                        </div>

                        <!-- Thesis Item 2 -->
                        <div class="thesis-item">
                            <div class="thesis-item-cover">
                                <div class="thesis-cover-placeholder">
                                    <i class="fas fa-file-alt"></i>
                                </div>
                            </div>
                            <div class="thesis-item-content">
                                <h3 class="thesis-item-title">Sustainable Urban Development: Case Studies from Global Cities</h3>
                                <p class="thesis-item-author">Smith, Jennifer K.</p>
                                <div class="thesis-item-meta">
                                    <span><i class="far fa-calendar-alt"></i> April 2025</span>
                                    <span><i class="fas fa-graduation-cap"></i> Master's Thesis</span>
                                    <span><i class="fas fa-tag"></i> Urban Planning, Sustainability</span>
                                </div>
                                <p class="thesis-item-abstract">This thesis examines sustainable urban development practices across major global cities, with a focus on green infrastructure, energy efficiency, and social equity considerations.</p>
                                <div class="thesis-item-actions">
                                    <a href="#" class="view-button"><i class="fas fa-eye"></i> View</a>
                                    <a href="#" class="download-button"><i class="fas fa-download"></i> Download</a>
                                </div>
                            </div>
                        </div>

                        <!-- Thesis Item 3 -->
                        <div class="thesis-item">
                            <div class="thesis-item-cover">
                                <div class="thesis-cover-placeholder">
                                    <i class="fas fa-file-alt"></i>
                                </div>
                            </div>
                            <div class="thesis-item-content">
                                <h3 class="thesis-item-title">Neural Correlates of Decision-Making in Uncertain Environments</h3>
                                <p class="thesis-item-author">Williams, David A.</p>
                                <div class="thesis-item-meta">
                                    <span><i class="far fa-calendar-alt"></i> March 2025</span>
                                    <span><i class="fas fa-graduation-cap"></i> PhD Dissertation</span>
                                    <span><i class="fas fa-tag"></i> Neuroscience, Psychology</span>
                                </div>
                                <p class="thesis-item-abstract">This dissertation investigates the neural mechanisms underlying decision-making processes in environments characterized by uncertainty, utilizing fMRI and computational modeling approaches.</p>
                                <div class="thesis-item-actions">
                                    <a href="#" class="view-button"><i class="fas fa-eye"></i> View</a>
                                    <a href="#" class="download-button"><i class="fas fa-download"></i> Download</a>
                                </div>
                            </div>
                        </div>

                        <!-- Thesis Item 4 -->
                        <div class="thesis-item">
                            <div class="thesis-item-cover">
                                <div class="thesis-cover-placeholder">
                                    <i class="fas fa-file-alt"></i>
                                </div>
                            </div>
                            <div class="thesis-item-content">
                                <h3 class="thesis-item-title">Biodiversity Conservation Strategies in Tropical Ecosystems</h3>
                                <p class="thesis-item-author">Brown, Katherine L.</p>
                                <div class="thesis-item-meta">
                                    <span><i class="far fa-calendar-alt"></i> February 2025</span>
                                    <span><i class="fas fa-graduation-cap"></i> Master's Thesis</span>
                                    <span><i class="fas fa-tag"></i> Biology, Environmental Science</span>
                                </div>
                                <p class="thesis-item-abstract">This thesis evaluates various conservation strategies employed to preserve biodiversity in tropical ecosystems, with emphasis on community-based approaches and policy interventions.</p>
                                <div class="thesis-item-actions">
                                    <a href="#" class="view-button"><i class="fas fa-eye"></i> View</a>
                                    <a href="#" class="download-button"><i class="fas fa-download"></i> Download</a>
                                </div>
                            </div>
                        </div>

                        <!-- Thesis Item 5 -->
                        <div class="thesis-item">
                            <div class="thesis-item-cover">
                                <div class="thesis-cover-placeholder">
                                    <i class="fas fa-file-alt"></i>
                                </div>
                            </div>
                            <div class="thesis-item-content">
                                <h3 class="thesis-item-title">Quantum Computing Algorithms for Optimization Problems</h3>
                                <p class="thesis-item-author">Miller, Alex P.</p>
                                <div class="thesis-item-meta">
                                    <span><i class="far fa-calendar-alt"></i> January 2025</span>
                                    <span><i class="fas fa-graduation-cap"></i> PhD Dissertation</span>
                                    <span><i class="fas fa-tag"></i> Computer Science, Quantum Physics</span>
                                </div>
                                <p class="thesis-item-abstract">This dissertation develops novel quantum computing algorithms designed to address complex optimization problems in logistics, finance, and computational biology.</p>
                                <div class="thesis-item-actions">
                                    <a href="#" class="view-button"><i class="fas fa-eye"></i> View</a>
                                    <a href="#" class="download-button"><i class="fas fa-download"></i> Download</a>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Pagination -->
                    <div class="results-pagination">
                        <a href="#" class="pagination-item active">1</a>
                        <a href="#" class="pagination-item">2</a>
                        <a href="#" class="pagination-item">3</a>
                        <a href="#" class="pagination-item">4</a>
                        <a href="#" class="pagination-item">5</a>
                        <a href="#" class="pagination-item next">
                            <i class="fas fa-chevron-right"></i>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </main>

<?php 

include BASE_PATH . 'footer.php';
?>
