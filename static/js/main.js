// DegreeLabs Discover - Interactive JS & AI Coach Trigger

document.addEventListener('DOMContentLoaded', () => {
    // 0. Auto-dismiss Flash Alerts / Toast Popups after 10 seconds
    const dismissAlert = (alertElem) => {
        if (!alertElem) return;
        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alertElem);
                if (bsAlert) {
                    bsAlert.close();
                    return;
                }
            } catch (e) {
                // Fallback below
            }
        }
        alertElem.classList.remove('show');
        setTimeout(() => alertElem.remove(), 300);
    };

    const initialAlerts = document.querySelectorAll('#toastContainer .alert');
    initialAlerts.forEach(alert => {
        setTimeout(() => {
            dismissAlert(alert);
        }, 10000); // 10 seconds
    });

    // 1. AI Coach Runner
    const btnRunAICoach = document.getElementById('btnRunAICoach');
    if (btnRunAICoach) {
        btnRunAICoach.addEventListener('click', async (e) => {
            e.preventDefault();
            const submissionId = btnRunAICoach.getAttribute('data-submission-id');
            const aiLoading = document.getElementById('aiLoadingState');
            const aiResults = document.getElementById('aiResultsContainer');
            const aiEmpty = document.getElementById('aiEmptyState');

            // Collect current unsaved text inputs to send to API
            const titleInput = document.getElementById('submissionTitle');
            const summaryInput = document.getElementById('submissionSummary');
            const contentInput = document.getElementById('submissionContent');

            btnRunAICoach.disabled = true;
            btnRunAICoach.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Discover Proposal Coach is reasoning...';
            
            if (aiEmpty) aiEmpty.style.display = 'none';
            if (aiLoading) aiLoading.style.display = 'block';

            try {
                const response = await fetch(`/api/ai-coach/run/${submissionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: titleInput ? titleInput.value : '',
                        executive_summary: summaryInput ? summaryInput.value : '',
                        content: contentInput ? contentInput.value : ''
                    })
                });

                const data = await response.json();

                if (aiLoading) aiLoading.style.display = 'none';
                if (aiResults) aiResults.style.display = 'block';

                if (data.success) {
                    // Update Readiness Score
                    const scoreElem = document.getElementById('aiReadinessScore');
                    const scoreBar = document.getElementById('aiReadinessProgressBar');
                    if (scoreElem) scoreElem.innerText = data.feedback.readiness_score;
                    if (scoreBar) {
                        scoreBar.style.width = `${data.feedback.readiness_score}%`;
                        scoreBar.innerText = `${data.feedback.readiness_score}%`;
                        if (data.feedback.readiness_score >= 85) {
                            scoreBar.className = 'progress-bar bg-success';
                        } else if (data.feedback.readiness_score >= 65) {
                            scoreBar.className = 'progress-bar bg-warning';
                        } else {
                            scoreBar.className = 'progress-bar bg-danger';
                        }
                    }

                    // Update Summary
                    const summaryElem = document.getElementById('aiSummaryText');
                    if (summaryElem) summaryElem.innerText = data.summary;

                    // Update Strengths
                    const strengthsList = document.getElementById('aiStrengthsList');
                    if (strengthsList) {
                        strengthsList.innerHTML = '';
                        (data.feedback.strengths || []).forEach(str => {
                            const li = document.createElement('li');
                            li.className = 'ai-coach-list-item text-success';
                            li.innerHTML = `<i class="bi bi-check-circle-fill mt-1 flex-shrink-0"></i><span>${str}</span>`;
                            strengthsList.appendChild(li);
                        });
                    }

                    // Update Gaps
                    const gapsList = document.getElementById('aiGapsList');
                    if (gapsList) {
                        gapsList.innerHTML = '';
                        (data.feedback.gaps || []).forEach(gap => {
                            const li = document.createElement('li');
                            li.className = 'ai-coach-list-item text-warning';
                            li.innerHTML = `<i class="bi bi-exclamation-triangle-fill mt-1 flex-shrink-0"></i><span>${gap}</span>`;
                            gapsList.appendChild(li);
                        });
                    }

                    // Update Next Steps
                    const stepsList = document.getElementById('aiNextStepsList');
                    if (stepsList) {
                        stepsList.innerHTML = '';
                        (data.feedback.suggested_next_steps || []).forEach(step => {
                            const li = document.createElement('li');
                            li.className = 'ai-coach-list-item text-light';
                            li.innerHTML = `<i class="bi bi-arrow-right-circle text-info mt-1 flex-shrink-0"></i><span>${step}</span>`;
                            stepsList.appendChild(li);
                        });
                    }

                    // Update To-Do Items
                    const todosContainer = document.getElementById('aiTodosContainer');
                    if (todosContainer && data.todos) {
                        todosContainer.innerHTML = '';
                        if (data.todos.length === 0) {
                            todosContainer.innerHTML = '<p class="text-success small mb-0"><i class="bi bi-check-all me-1"></i>All rubric criteria addressed!</p>';
                        } else {
                            data.todos.forEach(todo => {
                                const card = document.createElement('div');
                                card.className = 'card bg-dark border-secondary border-opacity-50 mb-2 p-3 rounded-2';
                                card.innerHTML = `
                                    <div class="d-flex align-items-start gap-3">
                                        <i class="bi bi-flag-fill text-warning mt-1"></i>
                                        <div>
                                            <strong class="text-white small">${todo.section_name}</strong>
                                            <p class="text-secondary small mb-0 mt-1">${todo.prompt}</p>
                                        </div>
                                    </div>
                                `;
                                todosContainer.appendChild(card);
                            });
                        }
                    }

                    // Show notification banner
                    showToast("Proposal Coach evaluation updated successfully!", "success", 10000);
                } else {
                    showToast("Error running AI Coach: " + (data.error || "Unknown error"), "danger", 10000);
                }
            } catch (err) {
                console.error("AI Coach Fetch Error:", err);
                if (aiLoading) aiLoading.style.display = 'none';
                showToast("Network error executing Proposal Coach.", "danger", 10000);
            } finally {
                btnRunAICoach.disabled = false;
                btnRunAICoach.innerHTML = '<i class="bi bi-stars me-2"></i>Get AI Feedback (Proposal Coach)';
            }
        });
    }

    // 2. To-Do Item Checkbox Toggle
    document.querySelectorAll('.todo-checkbox').forEach(cb => {
        cb.addEventListener('change', async (e) => {
            const todoId = e.target.getAttribute('data-todo-id');
            try {
                const res = await fetch(`/api/todo/${todoId}/toggle`, { method: 'POST' });
                const json = await res.json();
                if (json.status === 'success') {
                    const label = document.getElementById(`todo-label-${todoId}`);
                    if (label) {
                        if (json.is_resolved) {
                            label.classList.add('text-decoration-line-through', 'text-muted');
                        } else {
                            label.classList.remove('text-decoration-line-through', 'text-muted');
                        }
                    }
                }
            } catch (err) {
                console.error("Toggle error:", err);
            }
        });
    });
});

function showToast(message, type = 'info', timeout = 10000) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toastDiv = document.createElement('div');
    toastDiv.className = `alert alert-${type} alert-dismissible fade show shadow-sm`;
    toastDiv.role = 'alert';
    toastDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    toastContainer.appendChild(toastDiv);

    setTimeout(() => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(toastDiv);
                if (bsAlert) {
                    bsAlert.close();
                    return;
                }
            } catch (e) {
                // Fallback below
            }
        }
        toastDiv.classList.remove('show');
        setTimeout(() => toastDiv.remove(), 300);
    }, timeout);
}

