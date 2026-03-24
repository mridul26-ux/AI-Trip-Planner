// Automatically point to the live server URL, falling back to localhost during local dev
const BACKEND_URL = window.location.origin.includes("127.0.0.1:5500") || window.location.protocol === "file:" 
    ? "http://127.0.0.1:8000" 
    : window.location.origin;

const form = document.getElementById('trip-form');
const btn = document.getElementById('generate-btn');
const btnText = document.querySelector('.btn-text');
const loader = document.getElementById('btn-loader');
const errorMsg = document.getElementById('error-message');
const resultsSection = document.getElementById('results-section');
const timelineContainer = document.getElementById('timeline-container');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI Loading state
    btn.disabled = true;
    btnText.textContent = "Architecting your perfect journey...";
    loader.style.display = "block";
    errorMsg.style.display = "none";
    resultsSection.style.display = "none";

    // Gather payload data
    const payload = {
        city: document.getElementById('city').value,
        days: parseInt(document.getElementById('days').value, 10),
        budget: document.getElementById('budget').value,
        interests: document.getElementById('interests').value
    };

    try {
        const response = await fetch(`${BACKEND_URL}/generate-itinerary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.status === "success") {
            const tripData = data.itinerary; 
            document.getElementById('budget-amount').textContent = tripData.estimated_budget_inr;
            
            if (data.weather) {
                document.getElementById('weather-icon').textContent = data.weather.icon || '☀️';
                document.getElementById('weather-text').textContent = data.weather.forecast || 'Sunny';
            }
            
            // Dynamically change the entire app's background theme to the destination!
            if (data.destination_image) {
                document.body.style.backgroundImage = `linear-gradient(rgba(255, 252, 240, 0.1), rgba(255, 252, 240, 0.15)), url('${data.destination_image}')`;
            }
            
            // Set the main city overview map dynamically
            const targetCity = document.getElementById('city').value;
            document.getElementById('city-map').src = `https://maps.google.com/maps?q=${encodeURIComponent(targetCity)}&t=&z=12&ie=UTF8&iwloc=&output=embed`;
            
            renderItinerary(tripData.itinerary);
        } else {
            throw new Error(data.detail || data.message || "Failed to generate itinerary.");
        }
    } catch (err) {
        errorMsg.textContent = "Error: " + err.message;
        errorMsg.style.display = "block";
    } finally {
        // Reset button UI
        btn.disabled = false;
        btnText.textContent = "Generate Elegant Itinerary";
        loader.style.display = "none";
    }
});

function renderItinerary(itineraryArray) {
    timelineContainer.innerHTML = ''; // Clear previous results

    if (!Array.isArray(itineraryArray)) {
        throw new Error("Invalid itinerary format received. Expected array.");
    }

    itineraryArray.forEach(day => {
        const card = document.createElement('div');
        card.className = 'day-card';
        card.style.animation = `fadeInUp 0.5s ease backwards`;
        card.style.animationDelay = `${day.day * 0.1}s`;
        
        let activitiesHtml = '';
        if (Array.isArray(day.activities)) {
            day.activities.forEach(act => {
                activitiesHtml += `
                    <div class="activity">
                        <div class="activity-time">${act.time || '--:--'}</div>
                        <div class="activity-details">
                            ${act.image_url ? `<img src="${act.image_url}" alt="${act.place}" class="activity-image">` : ''}
                            <h4 style="margin-bottom: 0.2rem;">${act.place || 'Unknown Place'}</h4>
                            ${act.city ? `<span style="font-size: 0.85rem; color: #6b7280; font-weight: 500; display: block; margin-bottom: 0.5rem;">📍 ${act.city}</span>` : ''}
                        <p>${act.description || ''}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.6rem;">
                            <div>
                        ${act.type ? `<span class="activity-tag" style="margin-top:0;">${act.type}</span>` : '<span></span>'}
                        ${act.cost_inr ? `<span class="activity-cost" style="margin-left: 10px;">${act.cost_inr}</span>` : ''}
                    </div>
                    <div>
                        <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(act.place + ' ' + document.getElementById('city').value)}" target="_blank" class="map-btn">📍 Map</a>
                        <button class="swap-btn" onclick='handleSwap(this, ${JSON.stringify(act).replace(/'/g, "&apos;")})'>🔄 Swap</button>
                    </div>
                        </div>
                    </div>
                </div>
                `;
            });
        }

        card.innerHTML = `
            <h3>Day ${day.day}</h3>
            ${activitiesHtml}
        `;
        
        timelineContainer.appendChild(card);
    });

    resultsSection.style.display = "block";
    
    // Smooth scroll to results after a short delay to allow DOM to render
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

window.handleSwap = async function(btnElement, currentActData) {
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = "⏳ Swapping...";
    btnElement.disabled = true;

    const payload = {
        city: document.getElementById('city').value,
        interests: document.getElementById('interests').value,
        current_activity: currentActData
    };

    try {
        const response = await fetch(`${BACKEND_URL}/swap-activity`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (response.ok && data.status === "success") {
            const newAct = data.activity;
            const detailsDiv = btnElement.closest('.activity-details');
            
            // Re-render the activity block inside detailsDiv
            detailsDiv.innerHTML = `
                ${newAct.image_url ? `<img src="${newAct.image_url}" alt="${newAct.place}" class="activity-image">` : ''}
                <h4 style="margin-bottom: 0.2rem;">${newAct.place || 'Unknown Place'}</h4>
                ${newAct.city ? `<span style="font-size: 0.85rem; color: #6b7280; font-weight: 500; display: block; margin-bottom: 0.5rem;">📍 ${newAct.city}</span>` : ''}
                <p>${newAct.description || ''}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.6rem;">
                    <div>
                        ${newAct.type ? `<span class="activity-tag" style="margin-top:0;">${newAct.type}</span>` : '<span></span>'}
                        ${newAct.cost_inr ? `<span class="activity-cost" style="margin-left: 10px;">${newAct.cost_inr}</span>` : ''}
                    </div>
                    <div>
                        <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(newAct.place + ' ' + document.getElementById('city').value)}" target="_blank" class="map-btn">📍 Map</a>
                        <button class="swap-btn" onclick='handleSwap(this, ${JSON.stringify(newAct).replace(/'/g, "&apos;")})'>🔄 Swap</button>
                    </div>
                </div>
            `;
        } else {
            throw new Error(data.detail || "Failed to swap");
        }
    } catch (e) {
        alert("Swap failed: " + e.message);
        btnElement.innerHTML = originalText;
        btnElement.disabled = false;
    }
};
