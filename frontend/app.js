const API_BASE = "http://localhost:8000/api";

document.addEventListener("DOMContentLoaded", () => {
    // Tab Switching logic
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanels = document.querySelectorAll(".tab-panel");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanels.forEach(p => p.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(`panel-${btn.dataset.tab}`).classList.add("active");

            // Auto-load leaderboard when tab is clicked
            if (btn.dataset.tab === "ranking") {
                fetchLeaderboard();
            }
        });
    });

    // Handle Transaction Submission
    const txnForm = document.getElementById("transaction-form");
    const txnResult = document.getElementById("txn-result");

    txnForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const payload = {
            user_id: document.getElementById("input-user-id").value,
            idempotency_key: document.getElementById("input-idem-key").value,
            transaction_type: document.getElementById("input-type").value,
            amount: document.getElementById("input-amount").value,
            descriptions: document.getElementById("input-desc").value
        };

        try {
            const res = await fetch(`${API_BASE}/transaction/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            txnResult.classList.remove("hidden");
            if (res.ok) {
                txnResult.innerHTML = `<div style="color: #10b981; margin-bottom: 10px;">✅ Transaction Successful (Status: ${data.status})</div><pre>${JSON.stringify(data.transaction, null, 2)}</pre>`;
            } else {
                txnResult.innerHTML = `<div style="color: #ef4444; margin-bottom: 10px;">❌ Error: ${data.message || 'Validation failed'}</div><pre>${JSON.stringify(data.details || data, null, 2)}</pre>`;
            }
        } catch (err) {
            txnResult.classList.remove("hidden");
            txnResult.innerHTML = `<div style="color: #ef4444;">❌ Network Error: Could not connect to API. Is the server running?</div>`;
        }
    });

    // Handle User Summary Lookup
    const btnLookup = document.getElementById("btn-lookup");
    const inputLookup = document.getElementById("input-lookup-user");
    const summaryResult = document.getElementById("summary-result");

    const fetchSummary = async (userId) => {
        if (!userId) return;
        inputLookup.value = userId;
        summaryResult.classList.remove("hidden");
        summaryResult.innerHTML = 'Loading...';
        
        try {
            const res = await fetch(`${API_BASE}/summary/${userId}/`);
            const data = await res.json();
            
            if (res.ok) {
                summaryResult.innerHTML = `
                    <h3 style="margin-top: 0;">${data.user_name} (${data.user_id})</h3>
                    <div style="display: flex; gap: 2rem; margin-bottom: 1.5rem;">
                        <div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">Net Balance</div>
                            <div style="font-size: 1.25rem; font-weight: bold;">₹${data.net_balance}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">Rank Score</div>
                            <div style="font-size: 1.25rem; font-weight: bold;">${data.rank_score}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.8rem; color: #94a3b8;">Transactions</div>
                            <div style="font-size: 1.25rem; font-weight: bold;">${data.transaction_count}</div>
                        </div>
                    </div>
                    <h4 style="margin-bottom: 0.5rem; color: #cbd5e1;">Recent Transactions</h4>
                    <pre style="background: rgba(15, 23, 42, 0.5); padding: 1rem; border-radius: 0.5rem;">${JSON.stringify(data.recent_transactions, null, 2)}</pre>
                `;
            } else {
                summaryResult.innerHTML = `<div style="color: #ef4444;">❌ ${data.message || 'User not found'}</div>`;
            }
        } catch (err) {
            summaryResult.innerHTML = `<div style="color: #ef4444;">❌ Network Error: Could not connect to API</div>`;
        }
    };

    btnLookup.addEventListener("click", () => fetchSummary(inputLookup.value));

    // Listen for enter key on lookup input
    inputLookup.addEventListener("keypress", (e) => {
        if (e.key === 'Enter') {
            fetchSummary(inputLookup.value);
        }
    });

    // Handle Quick access chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => fetchSummary(chip.dataset.user));
    });

    // Handle Leaderboard Loading
    const btnRefreshRanking = document.getElementById("btn-refresh-ranking");
    const rankingResult = document.getElementById("ranking-result");

    const fetchLeaderboard = async () => {
        rankingResult.innerHTML = '<div style="padding: 1rem;">Loading leaderboard...</div>';
        try {
            const res = await fetch(`${API_BASE}/ranking/`);
            const data = await res.json();
            
            if (res.ok) {
                if (data.ranking.length === 0) {
                    rankingResult.innerHTML = '<div style="padding: 1rem;">No users found. Try adding some transactions.</div>';
                    return;
                }

                let html = `<table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>User</th>
                            <th>Balance</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>`;
                
                data.ranking.forEach(user => {
                    let badgeClass = user.rank <= 3 ? `rank-${user.rank}` : '';
                    html += `
                        <tr>
                            <td><span class="rank-badge ${badgeClass}">${user.rank}</span></td>
                            <td>
                                <strong>${user.user_name}</strong><br>
                                <small style="color: #94a3b8;">${user.user_id}</small>
                            </td>
                            <td>₹${user.net_balance}</td>
                            <td>${user.rank_score}</td>
                        </tr>
                    `;
                });
                
                html += `</tbody></table>`;
                rankingResult.innerHTML = html;
            } else {
                rankingResult.innerHTML = `<div style="color: #ef4444; padding: 1rem;">❌ Error loading leaderboard</div>`;
            }
        } catch (err) {
            rankingResult.innerHTML = `<div style="color: #ef4444; padding: 1rem;">❌ Network Error: Could not connect to API</div>`;
        }
    };

    btnRefreshRanking.addEventListener("click", fetchLeaderboard);
    
    // Load leaderboard initially if the tab is already active
    if (document.getElementById("tab-ranking").classList.contains("active")) {
        fetchLeaderboard();
    }
});
