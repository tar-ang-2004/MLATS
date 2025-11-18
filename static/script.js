// Professional Resume Analyzer

// Dark Mode Toggle (safe initialization + legacy support)
const darkModeToggle = document.getElementById("darkModeToggle");
const sunIcon = document.getElementById("sunIcon");
const moonIcon = document.getElementById("moonIcon");
const htmlElement = document.documentElement;

// Support both current key ('darkMode') and legacy key ('theme')
const darkMode = localStorage.getItem("darkMode");
const legacyTheme = localStorage.getItem("theme");
const shouldBeDark = (darkMode === "enabled") || (legacyTheme === "dark");
if (shouldBeDark) {
    htmlElement.classList.add("dark");
    if (sunIcon) sunIcon.classList.add("hidden");
    if (moonIcon) moonIcon.classList.remove("hidden");
}

if (darkModeToggle) {
    darkModeToggle.addEventListener("click", () => {
        const nowDark = htmlElement.classList.toggle("dark");
        if (nowDark) {
            localStorage.setItem("darkMode", "enabled");
            localStorage.setItem("theme", "dark");
            if (sunIcon) sunIcon.classList.add("hidden");
            if (moonIcon) moonIcon.classList.remove("hidden");
        } else {
            localStorage.setItem("darkMode", "disabled");
            localStorage.setItem("theme", "light");
            if (sunIcon) sunIcon.classList.remove("hidden");
            if (moonIcon) moonIcon.classList.add("hidden");
        }
    });
}

// Drag and Drop Functionality
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("resumeFile");

if (dropZone && fileInput) {
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, e => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add("border-brand-500", "bg-brand-50", "dark:bg-brand-900/20");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove("border-brand-500", "bg-brand-50", "dark:bg-brand-900/20");
        }, false);
    });

    dropZone.addEventListener("drop", e => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileStatus(files[0]);
        }
    }, false);

    fileInput.addEventListener("change", e => {
        const file = e.target.files[0];
        if (file) updateFileStatus(file);
    });

    function updateFileStatus(file) {
        const fileSize = file.size / 1024 / 1024;
        const fileStatus = document.getElementById("fileStatus");
        if (fileSize > 16) {
            showError("File size exceeds 16MB limit.");
            fileInput.value = "";
            fileStatus.textContent = "PDF or DOCX up to 16MB";
        } else {
            fileStatus.textContent = `${file.name} (${fileSize.toFixed(2)} MB)`;
            fileStatus.classList.add("text-brand-600", "font-medium");
        }
    }
}

document.getElementById("uploadForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    document.getElementById("loadingSpinner").classList.remove("hidden");
    document.getElementById("resultsSection").classList.add("hidden");
    document.getElementById("errorAlert").classList.add("hidden");
    
    const analyzeBtn = document.getElementById("analyzeBtn");
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = "<svg class=\"animate-spin h-5 w-5 mr-3 inline\" viewBox=\"0 0 24 24\"><circle class=\"opacity-25\" cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" stroke-width=\"4\" fill=\"none\"></circle><path class=\"opacity-75\" fill=\"currentColor\" d=\"M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z\"></path></svg>Analyzing...";
    
    setTimeout(() => {
        document.getElementById("loadingSpinner").scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
    
    const formData = new FormData();
    formData.append("resume", document.getElementById("resumeFile").files[0]);
    formData.append("job_description", document.getElementById("jobDescription").value);
    
    try {
        const response = await fetch("/analyze", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "An error occurred");
        setTimeout(() => displayResults(data), 300);
    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById("loadingSpinner").classList.add("hidden");
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = "Analyze Resume";
    }
});

function displayResults(data) {
    document.getElementById("resultsSection").classList.remove("hidden");
    setTimeout(() => {
        document.getElementById("resultsSection").scrollIntoView({ behavior: "smooth", block: "start" });
    }, 200);
    
    animateScore(data.overall_score);
    document.getElementById("fileName").textContent = data.filename;
    
    const badgeClasses = {
        "success": "inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-100",
        "warning": "inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-yellow-100 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-100",
        "danger": "inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-red-100 dark:bg-red-800 text-red-800 dark:text-red-100"
    };
    document.getElementById("classificationBadge").innerHTML = `<span class="${badgeClasses[data.badge_color]}">${data.classification}</span>`;
    
    const sectionsHtml = Object.entries(data.scores).map(([section, score]) => {
        const barColor = getScoreColor(score);
        return `<div><div class="flex justify-between items-center mb-2"><span class="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">${section.replace(/_/g, " ")}</span><span class="text-sm font-semibold ${getScoreTextColor(score)}">${score}%</span></div><div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5"><div class="${barColor} h-2.5 rounded-full transition-all duration-1000 ease-out" style="width: 0%" data-width="${score}%"></div></div></div>`;
    }).join("");
    document.getElementById("sectionScores").innerHTML = sectionsHtml;
    
    setTimeout(() => {
        document.querySelectorAll("#sectionScores [data-width]").forEach(bar => {
            bar.style.width = bar.getAttribute("data-width");
        });
    }, 100);
    
    document.getElementById("matchedCount").textContent = data.details.matched_count;
    document.getElementById("matchedSkills").innerHTML = data.details.matched_skills.length > 0 
        ? data.details.matched_skills.map(skill => `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-100">${skill}</span>`).join("")
        : "<p class=\"text-gray-500 dark:text-gray-400 text-sm\">No skills matched</p>";
    
    document.getElementById("missingCount").textContent = data.details.missing_count;
    document.getElementById("missingSkills").innerHTML = data.details.missing_skills.length > 0 
        ? data.details.missing_skills.map(skill => `<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 dark:bg-amber-800 text-amber-800 dark:text-amber-100">${skill}</span>`).join("")
        : "<p class=\"text-green-600 dark:text-green-400 text-sm font-medium\">All required skills found!</p>";
    
    // Prefer a full phone number: if contact_info.phone is just a country code or very short,
    // search parsed_sections recursively for a phone-like string and use it as a fallback.
    function findPhoneInParsed(obj) {
        const phoneRegex = /\+?\d[\d\s().\-]{6,}\d/; // fairly permissive: looks for 7+ digits with separators
        if (!obj) return null;
        if (typeof obj === 'string') {
            const m = obj.match(phoneRegex);
            return m ? m[0].trim() : null;
        }
        if (Array.isArray(obj)) {
            for (const el of obj) {
                const found = findPhoneInParsed(el);
                if (found) return found;
            }
            return null;
        }
        if (typeof obj === 'object') {
            for (const k of Object.keys(obj)) {
                const found = findPhoneInParsed(obj[k]);
                if (found) return found;
            }
            return null;
        }
        return null;
    }

    let phoneValue = (data.contact_info && data.contact_info.phone) || '';
    if (phoneValue && phoneValue.toString().trim().length <= 4) {
        // probable country code only like "+91" or similar — try to find a longer match
        console.debug("Phone appears short (likely country code). Searching parsed_sections and full payload for candidates...");
        console.debug("Original contact_info.phone:", phoneValue);
        let alt = findPhoneInParsed(data.parsed_sections);
        console.debug("Candidate from parsed_sections:", alt);
        // If not found in parsed_sections, try scanning the entire JSON payload as a last resort
        if (!alt) {
            try {
                const asString = JSON.stringify(data);
                const broadRegex = /\+?\d[\d\s().\-]{6,}\d/g;
                const m = asString.match(broadRegex);
                console.debug("Broad regex matches in payload:", m);
                if (m && m.length > 0) {
                    // choose the first reasonable candidate that's longer than a country code
                    alt = m.find(s => s.replace(/[^0-9]/g, '').length >= 7) || m[0];
                    console.debug("Selected broad candidate:", alt);
                }
            } catch (e) {
                console.debug("Error stringifying data for broad phone search:", e);
            }
        }
        if (alt) {
            console.debug("Using fallback phone candidate:", alt);
            phoneValue = alt;
        } else {
            console.debug("No fallback phone candidate found in payload.");
        }
    }

    // If still not found or still very short, try a digits-only fallback across the whole payload
    if ((!phoneValue || phoneValue.toString().trim().length <= 4)) {
        try {
            const s = JSON.stringify(data);
            // find digit sequences of length >=7
            const digitMatches = s.match(/\d{7,}/g);
            console.debug('Digit-only matches in payload:', digitMatches);
            if (digitMatches && digitMatches.length > 0) {
                // choose the longest match
                const longest = digitMatches.reduce((a,b) => a.length >= b.length ? a : b);
                // try to find a plus sign immediately before the match in the original stringified payload
                const idx = s.indexOf(longest);
                let formatted = longest;
                if (idx > 0 && s[idx-1] === '+') formatted = '+' + longest;
                phoneValue = formatted;
                console.debug('Using digit-only fallback phone:', phoneValue);
            }
        } catch (e) {
            console.debug('Error during digit-only phone fallback:', e);
        }
    }

    // Phone debug overlay removed — no UI debug overlay shown in production

    const contactItems = [
        { label: "Email", value: data.contact_info.email },
        { label: "Phone", value: phoneValue },
        { label: "LinkedIn", value: data.contact_info.linkedin },
        { label: "GitHub", value: data.contact_info.github }
    ];
    const contactHtml = contactItems.map(item => `<div class="border border-gray-200 dark:border-gray-600 rounded-lg p-4"><div class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide mb-1">${item.label}</div><div class="text-sm font-medium text-gray-900 dark:text-gray-100 ${item.value ? "" : "text-gray-400 dark:text-gray-500 italic"}">${item.value || "Not found"}</div></div>`).join("");
    document.getElementById("contactInfo").innerHTML = contactHtml;
    
    // Display parsed sections
    if (data.parsed_sections) {
        // Skills
        const skills = data.parsed_sections.skills || [];
        document.getElementById("detectedSkills").innerHTML = skills.length > 0 
            ? skills.map(skill => `<span class="inline-block px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-100 mr-2 mb-2">${skill}</span>`).join("")
            : "<p class=\"italic text-gray-500 dark:text-gray-400\">No skills detected in resume</p>";
        
        // Helper function for HTML escaping
        function escapeHtml(str) {
            if (!str && str !== 0) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        // Experience - Handle structured objects
        const experience = data.parsed_sections.experience || [];
        if (experience.length === 0) {
            document.getElementById("detectedExperience").innerHTML = "<p class=\\"italic text-gray-500 dark:text-gray-400\\">No experience detected in resume</p>";
        } else {
            let html = '<div class="space-y-4">';
            experience.forEach(exp => {
                if (typeof exp === 'object' && exp.company && exp.title) {
                    html += `<div>`;
                    html += `<p class="text-sm text-gray-900 dark:text-gray-100 font-semibold">${escapeHtml(exp.company)} — ${escapeHtml(exp.title)}</p>`;
                    
                    // Add location and dates
                    let details = [];
                    if (exp.location) details.push(escapeHtml(exp.location));
                    if (exp.dates) details.push(escapeHtml(exp.dates));
                    if (details.length > 0) {
                        html += `<p class="text-sm text-gray-400 mt-1">${details.join(' · ')}</p>`;
                    }
                    
                    // Add achievements with bullet points
                    if (exp.achievements && exp.achievements.length > 0) {
                        html += '<div class="mt-2 text-sm text-gray-700 dark:text-gray-300">';
                        exp.achievements.forEach(achievement => {
                            html += `<p class="flex items-start mb-1"><span class="text-blue-500 mr-2 mt-0.5">□</span><span>${escapeHtml(achievement)}</span></p>`;
                        });
                        html += '</div>';
                    } else if (exp.description) {
                        html += `<p class="mt-2 text-sm text-gray-600 dark:text-gray-400"><span class="text-blue-500 mr-2">□</span>${escapeHtml(exp.description)}</p>`;
                    }
                    
                    html += `</div>`;
                }
            });
            html += '</div>';
            document.getElementById("detectedExperience").innerHTML = html;
        }
                


        function calculateTenure(duration) {
            if (!duration) return '';
            
            // Extract dates like "07/2025 – 12/2025" or "06/2025 – 09/2025"
            const dateMatch = duration.match(/(\d{2})\/(\d{4})\s*[–-]\s*(\d{2})\/(\d{4})/);
            if (dateMatch) {
                const startMonth = parseInt(dateMatch[1]);
                const startYear = parseInt(dateMatch[2]);
                const endMonth = parseInt(dateMatch[3]);
                const endYear = parseInt(dateMatch[4]);
                
                const totalMonths = (endYear - startYear) * 12 + (endMonth - startMonth) + 1;
                
                if (totalMonths < 12) {
                    return ` [${totalMonths} months]`;
                } else {
                    const years = Math.floor(totalMonths / 12);
                    const months = totalMonths % 12;
                    if (months === 0) {
                        return ` [${years} ${years === 1 ? 'year' : 'years'}]`;
                    } else {
                        return ` [${years}.${Math.round(months / 12 * 10)} years]`;
                    }
                }
            }
            
            return '';
        }

        // Process all experience entries
        let allExperiences = [];
        for (const exp of experience) {
            const expText = typeof exp === 'string' ? exp : (exp.text || JSON.stringify(exp));
        }

        // Render experiences with achievements and bullet points
        if (allExperiences.length === 0) {
            document.getElementById("detectedExperience").innerHTML = "<p class=\"italic text-gray-500 dark:text-gray-400\">No experience detected in resume</p>";
        } else {
            let html = '<div class="space-y-4">';
            allExperiences.forEach((exp, index) => {
                const tenure = calculateTenure(exp.duration);
                html += `<div>`;
                html += `<p class="text-sm text-gray-900 dark:text-gray-100 font-semibold">${escapeHtml(exp.company)} — ${escapeHtml(exp.title)}</p>`;
                html += `<p class="text-sm text-gray-400 mt-1">${escapeHtml(exp.location)}${exp.location && exp.duration ? ' · ' : ''}${escapeHtml(exp.duration)}${tenure}</p>`;
                
                // Add achievements with bullet points
                if (exp.achievements && exp.achievements.length > 0) {
                    html += '<ul class="mt-2 text-sm text-gray-700 dark:text-gray-300">';
                    exp.achievements.forEach(achievement => {
                        html += `<li class="flex items-start mb-1"><span class="text-blue-500 mr-2">□</span>${escapeHtml(achievement)}</li>`;
                    });
                    html += '</ul>';
                } else if (exp.description) {
                    html += `<p class="mt-2 text-sm text-gray-600 dark:text-gray-400">□ ${escapeHtml(exp.description)}</p>`;
                }
                
                html += `</div>`;
            });
            html += '</div>';
            document.getElementById("detectedExperience").innerHTML = html;
        }
        
        console.debug('Parsed ATS Experiences:', allExperiences);
        
        // Education - handle structured education objects
        const education = data.parsed_sections.education || [];

        // Handle structured education objects
        let allEducation = [];
        if (education && education.length > 0) {
            allEducation = education.map(edu => {
                if (typeof edu === 'object') {
                    return {
                        institution: edu.institution || 'Unknown Institution',
                        degree: edu.degree || 'Degree not specified',
                        dates: edu.dates || '',
                        field: edu.field || ''
                    };
                }
                return null;
            }).filter(Boolean);
        }


        const filteredEducation = education.filter(edu => {
            const eduText = typeof edu === 'string' ? edu : (edu.text || JSON.stringify(edu));
            return !looksLikeCertification(eduText);
        });

        // Parse and render education
        if (filteredEducation.length === 0) {
            document.getElementById("detectedEducation").innerHTML = "<p class=\"italic text-gray-500 dark:text-gray-400\">No education detected in resume</p>";
        } else {
            let html = '';
            filteredEducation.forEach(edu => {
                const eduText = typeof edu === 'string' ? edu : (edu.text || JSON.stringify(edu));
                const parsed = parseATSEducation(eduText);
                
                if (parsed) {
                    html += '<div class="mb-3 pb-3 border-b border-gray-200 dark:border-gray-600 last:border-0">';
                    html += `<p class="text-sm text-gray-900 dark:text-gray-100 font-semibold">${escapeHtml(parsed.institution)}</p>`;
                    if (parsed.location || parsed.duration) {
                        html += `<p class="text-sm text-gray-400 mt-1">${escapeHtml(parsed.location)}${parsed.location && parsed.duration ? ' · ' : ''}${escapeHtml(parsed.duration)}</p>`;
                    }
                    html += `<p class="text-sm text-gray-900 dark:text-gray-100 mt-2">${escapeHtml(parsed.degree)}</p>`;
                    html += '</div>';
                } else {
                    // Fallback to original display
                    html += `<div class="mb-3 pb-3 border-b border-gray-200 dark:border-gray-600 last:border-0"><p class="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-line">${escapeHtml(eduText)}</p></div>`;
                }
            });
            document.getElementById("detectedEducation").innerHTML = html;
        }
        
        console.debug('Parsed ATS Education:', filteredEducation.map(edu => parseATSEducation(typeof edu === 'string' ? edu : (edu.text || JSON.stringify(edu)))));
        
        // Projects - Advanced parsing for ATS resume format
        const projects = data.parsed_sections.projects || [];
        
        function parseATSProjects(rawText) {
            if (!rawText) return [];
            
            const text = String(rawText).replace(/\u00A0/g, ' ');
            const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
            
            const projectList = [];
            let currentProject = null;
            
            for (const line of lines) {
                // COMPLETELY SKIP ALL bullet points and description lines
                if (/^[\s\-\u2022\*•·]+/.test(line) || 
                    /attained|built|enhanced|developed|implemented|analyzed|achieved|created|designed/i.test(line)) {
                    continue;
                }
                
                // Detect project header with technologies in parentheses
                // Pattern: "Project Name (Technology, Stack, Framework)"
                const projectMatch = line.match(/^(.+?)\s*\(([^)]+)\)\s*(\[.*\])?$/);
                if (projectMatch) {
                    if (currentProject) projectList.push(currentProject);
                    
                    currentProject = {
                        name: projectMatch[1].trim(),
                        technologies: projectMatch[2].trim(),
                        link: projectMatch[3] ? projectMatch[3].trim() : ''
                    };
                    continue;
                }
                
                // Alternative: detect project by keywords (System, Analysis, etc.)
                if (/\b(System|Analysis|Platform|API|Dashboard|Tool|Application|Model|Framework|Engine|Generator|Analyzer|Predictor)\b/i.test(line) && 
                    line.length > 10 && line.length < 100) {
                    if (currentProject) projectList.push(currentProject);
                    
                    // Extract technologies if mentioned in the same line
                    const techMatch = line.match(/\b(Python|Java|JavaScript|React|Node|ML|AI|PyTorch|TensorFlow|Tableau|SQL|MongoDB|Flask|Django|Machine Learning|Deep Learning|NLP|Computer Vision|Matplotlib|Pandas|NumPy|Scikit-learn|Seaborn)\b/gi);
                    
                    currentProject = {
                        name: line.trim(),
                        technologies: techMatch ? [...new Set(techMatch)].join(', ') : '',
                        link: ''
                    };
                }
                
                // Add GitHub links if they appear after a project header
                else if (currentProject && !currentProject.link && (/github|gitlab|\[.*\]/i.test(line))) {
                    currentProject.link = line.trim();
                }
            }
            
            // Add the last project
            if (currentProject) projectList.push(currentProject);
            
            return projectList;
        }

        // Process all project entries
        let allProjects = [];
        for (const proj of projects) {
            const projText = typeof proj === 'string' ? proj : (proj.text || JSON.stringify(proj));
            const parsed = parseATSProjects(projText);
            allProjects = allProjects.concat(parsed);
        }

        // Render projects in numbered format with technologies
        if (allProjects.length === 0) {
            document.getElementById("detectedProjects").innerHTML = "<p class=\"italic text-gray-500 dark:text-gray-400\">No projects detected in resume</p>";
        } else {
            let html = '<div class="space-y-2">';
            allProjects.forEach(proj => {
                const techDisplay = proj.technologies ? ` (${proj.technologies})` : '';
                const linkDisplay = proj.link ? ` ${proj.link}` : '';
                html += `<p class="text-sm text-gray-900 dark:text-gray-100">${escapeHtml(proj.name)}${escapeHtml(techDisplay)}${escapeHtml(linkDisplay)}</p>`;
            });
            html += '</div>';
            document.getElementById("detectedProjects").innerHTML = html;
        }
        
        console.debug('Parsed ATS Projects:', allProjects);
        
        // Certifications
        const certifications = data.parsed_sections.certifications || [];
        document.getElementById("detectedCertifications").innerHTML = certifications.length > 0
            ? certifications.map(cert => {
                const certText = typeof cert === 'string' ? cert : (cert.text || JSON.stringify(cert));
                return `<div class="mb-2 pb-2 border-b border-gray-200 dark:border-gray-600 last:border-0"><p class="text-sm text-gray-900 dark:text-gray-100">${certText}</p></div>`;
            }).join("")
            : "<p class=\"italic text-gray-500 dark:text-gray-400\">No certifications or achievements detected</p>";
    }
    
    // Display Score Comparison
    displayScoreComparison(data.overall_score, data.average_score || null);
    
    // Display Recommendations
    displayRecommendations(data);
    
    // Log data for debugging
    console.log("Resume Analysis Data:", data);
    console.log("Contact Info:", data.contact_info);
    console.log("Parsed Sections:", data.parsed_sections);
    console.log("Scores:", data.scores);
}

function displayScoreComparison(currentScore, averageScore) {
    const comparisonDiv = document.getElementById("scoreComparison");
    
    // If no average score available yet, show message
    if (!averageScore) {
        comparisonDiv.innerHTML = `
            <div class="col-span-3 text-center py-8">
                <p class="text-gray-600 dark:text-gray-400 italic">
                    This is the first resume analyzed. Future analyses will show comparison with average scores.
                </p>
            </div>
        `;
        return;
    }
    
    const difference = currentScore - averageScore;
    const percentageDiff = ((difference / averageScore) * 100).toFixed(1);
    const isAbove = difference >= 0;
    
        comparisonDiv.innerHTML = `
        <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">Your Score</p>
            <p class="text-3xl font-bold text-brand-600 dark:text-brand-400">${currentScore.toFixed(1)}</p>
        </div>
        <div class="text-center p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">Average Score</p>
            <p class="text-3xl font-bold text-amber-700 dark:text-amber-300">${averageScore.toFixed(1)}</p>
        </div>
        <div class="text-center p-4 bg-${isAbove ? 'green' : 'red'}-50 dark:bg-${isAbove ? 'green' : 'red'}-900/20 rounded-lg">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">Difference</p>
            <p class="text-3xl font-bold text-${isAbove ? 'green' : 'red'}-600 dark:text-${isAbove ? 'green' : 'red'}-400">
                ${isAbove ? '+' : ''}${difference.toFixed(1)} (${isAbove ? '+' : ''}${percentageDiff}%)
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                ${isAbove ? '🎉 Above' : '📈 Below'} average
            </p>
        </div>
    `;
}

function displayRecommendations(data) {
    const recommendationsDiv = document.getElementById("recommendations");
    const score = data.overall_score;
    const missingSkills = data.details.missing_skills || [];
    const recommendations = [];
    
    // Score-based recommendations
    if (score < 50) {
        recommendations.push({
            icon: "fa-exclamation-circle",
            title: "Critical: Major Resume Overhaul Needed",
            text: "Your resume needs significant improvements. Consider professional resume writing services or comprehensive restructuring."
        });
    } else if (score < 70) {
        recommendations.push({
            icon: "fa-edit",
            title: "Important: Enhance Your Resume",
            text: "Your resume has good foundation but needs optimization. Focus on adding relevant keywords and improving formatting."
        });
    } else {
        recommendations.push({
            icon: "fa-check-circle",
            title: "Great Job! Minor Refinements",
            text: "Your resume is well-optimized for ATS. Focus on fine-tuning and adding any missing relevant skills."
        });
    }
    
    // Skills recommendations
    if (missingSkills.length > 5) {
        recommendations.push({
            icon: "fa-lightbulb",
            title: `Add ${missingSkills.length} Missing Skills`,
            text: `Your resume is missing several key skills from the job description. Incorporate these skills: ${missingSkills.slice(0, 3).join(", ")}, and ${missingSkills.length - 3} more.`
        });
    } else if (missingSkills.length > 0) {
        recommendations.push({
            icon: "fa-plus-circle",
            title: "Add Missing Keywords",
            text: `Include these relevant skills in your resume: ${missingSkills.join(", ")}`
        });
    }
    
    // Section-specific recommendations
    const scores = data.scores;
    if (scores.experience < 70) {
        recommendations.push({
            icon: "fa-briefcase",
            title: "Strengthen Experience Section",
            text: "Add more quantifiable achievements, use action verbs, and include relevant metrics (e.g., 'Increased sales by 25%')."
        });
    }
    
    if (scores.skills < 70) {
        recommendations.push({
            icon: "fa-code",
            title: "Expand Skills Section",
            text: "Create a dedicated skills section with technical and soft skills relevant to the job description."
        });
    }
    
    if (scores.format < 70) {
        recommendations.push({
            icon: "fa-file-alt",
            title: "Improve Formatting",
            text: "Use clear section headers, bullet points, and consistent formatting. Avoid tables, images, and complex layouts."
        });
    }
    
    // Contact info recommendations
    if (!data.contact_info.email) {
        recommendations.push({
            icon: "fa-envelope",
            title: "Add Contact Information",
            text: "Ensure your email address is clearly visible at the top of your resume."
        });
    }
    
    if (!data.contact_info.linkedin) {
        recommendations.push({
            icon: "fa-linkedin",
            title: "Include LinkedIn Profile",
            text: "Add your LinkedIn profile URL to increase your professional visibility."
        });
    }
    
    // Render recommendations
    recommendationsDiv.innerHTML = recommendations.map((rec, index) => `
        <div class="flex items-start p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition" style="animation: slideUp 0.4s ease-out ${index * 0.1}s both;">
            <div class="flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mr-4">
                <i class="fas ${rec.icon} text-blue-600 dark:text-blue-400"></i>
            </div>
            <div class="flex-1">
                <h4 class="font-semibold text-gray-900 dark:text-gray-100 mb-1">${rec.title}</h4>
                <p class="text-sm text-gray-600 dark:text-gray-400">${rec.text}</p>
            </div>
        </div>
    `).join("");
}

function animateScore(score) {
    const scoreText = document.getElementById("scoreText");
    const scoreCircle = document.getElementById("scoreCircle");
    const circumference = 2 * Math.PI * 70;
    let currentScore = 0;
    const duration = 2000;
    const startTime = Date.now();
    
    const animateNumber = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        currentScore = Math.round(score * easeOut);
        scoreText.textContent = currentScore;
        if (progress < 1) requestAnimationFrame(animateNumber);
    };
    requestAnimationFrame(animateNumber);
    
    const offset = circumference - (score / 100) * circumference;
    setTimeout(() => { scoreCircle.style.strokeDashoffset = offset; }, 100);
    
    let strokeColor = score >= 70 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
    scoreCircle.setAttribute("stroke", strokeColor);
}

function getScoreColor(score) {
    return score >= 70 ? "bg-green-500" : score >= 50 ? "bg-yellow-500" : "bg-red-500";
}

function getScoreTextColor(score) {
    return score >= 70 ? "text-green-600 dark:text-green-400" : score >= 50 ? "text-yellow-600 dark:text-yellow-400" : "text-red-600 dark:text-red-400";
}

function showError(message) {
    document.getElementById("errorMessage").textContent = message;
    document.getElementById("errorAlert").classList.remove("hidden");
    setTimeout(() => {
        document.getElementById("errorAlert").scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
}

/* Starlight background initializer
   - Creates a number of small .star elements positioned randomly
   - Randomizes size, position, animation duration and delay
   - Respects prefers-reduced-motion and only runs when #starlight exists
*/
function initStarlight(options = {}) {
    const container = document.getElementById('starlight');
    if (!container) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const count = options.count || 80;
    const maxSize = options.maxSize || 3; // px
    // Clear any existing stars
    container.innerHTML = '';

    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        const size = (Math.random() * (maxSize - 0.8) + 0.8).toFixed(2);
        const left = (Math.random() * 100).toFixed(2) + '%';
        const top = (Math.random() * 100).toFixed(2) + '%';
    const twinkleDuration = (Math.random() * 3 + 1.5).toFixed(2); // 1.5-4.5s for more visible twinkle
    const twinkleDelay = (Math.random() * 3).toFixed(2);
    const driftDuration = (Math.random() * 40 + 20).toFixed(2); // 20-60s
    const driftDelay = (Math.random() * 10).toFixed(2);
    // Bias drift so movement is generally from SW to NE: positive X, positive Y used as magnitude
    const driftX = (Math.random() * 550 + 150).toFixed(2); // 150 - 700 px horizontal travel (magnitude)
    const driftY = (Math.random() * 220 + 80).toFixed(2);  // 80 - 300 px vertical travel (magnitude)

        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.left = left;
        star.style.top = top;
        // Slight variation in opacity for visual richness
        star.style.opacity = (Math.random() * 0.8 + 0.15).toFixed(2);

        // Color tint (subtle warm/cool variation)
        const hue = Math.floor(Math.random() * 160 + 20); // 20-180
        star.style.background = `radial-gradient(circle at 30% 30%, rgba(255,255,255,1) 0%, hsla(${hue},90%,85%,0.6) 30%, rgba(255,255,255,0) 70%)`;


        // Set CSS variables for drift used by keyframes
        // We'll set positive magnitudes and also negative counterparts so CSS can move from SW to NE
        star.style.setProperty('--drift-x', `${driftX}px`);      // positive X (right)
        star.style.setProperty('--drift-y', `${driftY}px`);      // positive Y (down)
        star.style.setProperty('--drift-x-neg', `-${driftX}px`); // negative X (left)
        star.style.setProperty('--drift-y-neg', `-${driftY}px`); // negative Y (up)

        // Compose animations: twinkle + slow driftNE (linear so direction feels steady)
        if (!prefersReduced) {
            star.style.animation = `twinkle ${twinkleDuration}s ease-in-out ${twinkleDelay}s infinite, driftNE ${driftDuration}s linear ${driftDelay}s infinite`;
        } else {
            star.style.animation = 'none';
        }

        // Slight drop shadow on larger stars
        if (parseFloat(size) > 2.2) star.style.filter = 'drop-shadow(0 0 6px rgba(255,255,255,0.06))';

        container.appendChild(star);
    }
}

// Initialize starlight once on load
window.addEventListener('load', () => {
    try { initStarlight({ count: 80, maxSize: 3 }); } catch (e) { /* ignore */ }
});