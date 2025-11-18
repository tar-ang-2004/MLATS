// Enhanced script to handle structured data properly
function displayResumeResults(data) {
    // Display basic info
    displayContactInfo(data.contact_info);
    
    if (data.parsed_sections) {
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

        // Skills
        const skills = data.parsed_sections.skills || [];
        document.getElementById("detectedSkills").innerHTML = skills.length > 0 
            ? skills.map(skill => `<span class="inline-block px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-100 mr-2 mb-2">${escapeHtml(skill)}</span>`).join("")
            : "<p class=\"italic text-gray-500 dark:text-gray-400\">No skills detected in resume</p>";

        // Experience - Handle structured objects
        const experience = data.parsed_sections.experience || [];
        if (experience.length === 0) {
            document.getElementById("detectedExperience").innerHTML = "<p class=\"italic text-gray-500 dark:text-gray-400\">No experience detected in resume</p>";
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

        // Education - Handle structured objects
        const education = data.parsed_sections.education || [];
        if (education.length === 0) {
            document.getElementById("detectedEducation").innerHTML = "<p class=\"italic text-gray-500 dark:text-gray-400\">No education information detected in resume</p>";
        } else {
            let html = '<div class="space-y-3">';
            education.forEach(edu => {
                if (typeof edu === 'object') {
                    html += `<div>`;
                    html += `<p class="text-sm text-gray-900 dark:text-gray-100 font-semibold">${escapeHtml(edu.institution || 'Unknown Institution')}</p>`;
                    if (edu.dates) {
                        html += `<p class="text-sm text-gray-400 mt-1">${escapeHtml(edu.dates)}</p>`;
                    }
                    if (edu.degree && edu.degree !== 'Degree not specified') {
                        html += `<p class="text-sm text-gray-600 dark:text-gray-300 mt-1">${escapeHtml(edu.degree)}</p>`;
                    } else {
                        html += `<p class="text-sm text-gray-500 dark:text-gray-400 mt-1 italic">Degree not specified</p>`;
                    }
                    html += `</div>`;
                }
            });
            html += '</div>';
            document.getElementById("detectedEducation").innerHTML = html;
        }

        // Projects - Handle structured objects
        const projects = data.parsed_sections.projects || [];
        if (projects.length === 0) {
            document.getElementById("detectedProjects").innerHTML = "<p class=\"italic text-gray-500 dark:text-gray-400\">No projects detected in resume</p>";
        } else {
            let html = '<div class="space-y-4">';
            projects.forEach(proj => {
                if (typeof proj === 'object') {
                    html += `<div>`;
                    let projectTitle = escapeHtml(proj.name || 'Unnamed Project');
                    if (proj.technologies) {
                        projectTitle += ` (${escapeHtml(proj.technologies)})`;
                    }
                    html += `<p class="text-sm text-gray-900 dark:text-gray-100 font-semibold">${projectTitle}</p>`;
                    
                    // Add achievements/description with bullet points
                    if (proj.achievements && proj.achievements.length > 0) {
                        html += '<div class="mt-2 text-sm text-gray-700 dark:text-gray-300">';
                        proj.achievements.forEach(achievement => {
                            html += `<p class="flex items-start mb-1"><span class="text-teal-500 mr-2 mt-0.5">□</span><span>${escapeHtml(achievement)}</span></p>`;
                        });
                        html += '</div>';
                    } else if (proj.description) {
                        html += `<p class="mt-2 text-sm text-gray-600 dark:text-gray-400"><span class="text-teal-500 mr-2">□</span>${escapeHtml(proj.description)}</p>`;
                    }
                    
                    html += `</div>`;
                }
            });
            html += '</div>';
            document.getElementById("detectedProjects").innerHTML = html;
        }

        // Certifications
        const certifications = data.parsed_sections.certifications || [];
        document.getElementById("detectedCertifications").innerHTML = certifications.length > 0
            ? certifications.map(cert => {
                const certText = typeof cert === 'string' ? cert : (cert.name || cert.text || JSON.stringify(cert));
                return `<div class="mb-2 pb-2 border-b border-gray-200 dark:border-gray-600 last:border-0"><p class="text-sm text-gray-900 dark:text-gray-100">□ ${escapeHtml(certText)}</p></div>`;
            }).join("")
            : "<p class=\"italic text-gray-500 dark:text-gray-400\">No certifications or achievements detected</p>";
    }
    
    // Display Score Comparison
    displayScoreComparison(data.overall_score, data.average_score || null);
    
    // Display Recommendations
    displayRecommendations(data);
    
    // Log data for debugging
    console.log("Resume Analysis Data:", data);
    console.log("Parsed Sections:", data.parsed_sections);
}