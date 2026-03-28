// =====================================================
// EVNPARK - Realistic Parking Garage Blueprint Map
// Interactive SVG with pan/zoom, slot selection, path animation
// =====================================================

let currentFloor = 1;
let mapData = { nodes: [], edges: [], slots: [] };
let selectedSlot = null;
let mapScale = 0.35;
let mapPos = { x: 20, y: 20 };
let isDragging = false;
let startDragOffset = { x: 0, y: 0 };

// Garage constants (must match seeder)
const GARAGE = {
    LEFT: 100, TOP: 100, RIGHT: 2900, BOTTOM: 2200,
    get WIDTH() { return this.RIGHT - this.LEFT; },
    get HEIGHT() { return this.BOTTOM - this.TOP; },
    LANE_MARGIN: 180,
    SLOT_W: 70, SLOT_H: 120
};

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById('parkingMap')) {
        loadFloor(currentFloor);
        setupMapInteractions();
    }
});

async function switchFloor(floorNum) {
    currentFloor = floorNum;
    document.getElementById('btn-f1').className = floorNum === 1
        ? 'px-4 py-1.5 rounded-md text-sm font-medium bg-indigo-500 text-white shadow transition-all'
        : 'px-4 py-1.5 rounded-md text-sm font-medium text-slate-400 hover:text-white transition-all cursor-pointer';
    document.getElementById('btn-f2').className = floorNum === 2
        ? 'px-4 py-1.5 rounded-md text-sm font-medium bg-indigo-500 text-white shadow transition-all'
        : 'px-4 py-1.5 rounded-md text-sm font-medium text-slate-400 hover:text-white transition-all cursor-pointer';
    await loadFloor(floorNum);
}

async function loadFloor(floorNum) {
    try {
        const data = await API.get(`/api/parking/map/${floorNum}`);
        mapData = data;
        renderGarageBlueprint();
    } catch (e) {
        console.error("Failed to load map data.", e);
    }
}

function renderGarageBlueprint() {
    const svg = document.getElementById('parkingMap');
    const svgNS = 'http://www.w3.org/2000/svg';

    // Clear dynamic groups
    document.getElementById('map-structure').innerHTML = '';
    document.getElementById('map-lanes').innerHTML = '';
    document.getElementById('map-slots').innerHTML = '';
    document.getElementById('map-labels').innerHTML = '';
    document.getElementById('map-path').innerHTML = '';

    const structure = document.getElementById('map-structure');
    const lanes = document.getElementById('map-lanes');
    const slotsG = document.getElementById('map-slots');
    const labels = document.getElementById('map-labels');

    // ===== 1. GARAGE OUTER WALLS =====
    const wallPath = document.createElementNS(svgNS, 'rect');
    wallPath.setAttribute('x', GARAGE.LEFT);
    wallPath.setAttribute('y', GARAGE.TOP);
    wallPath.setAttribute('width', GARAGE.WIDTH);
    wallPath.setAttribute('height', GARAGE.HEIGHT);
    wallPath.setAttribute('rx', '30');
    wallPath.setAttribute('fill', 'rgba(15, 23, 42, 0.6)');
    wallPath.setAttribute('stroke', '#334155');
    wallPath.setAttribute('stroke-width', '6');
    structure.appendChild(wallPath);

    // Inner shadow / floor fill
    const innerFloor = document.createElementNS(svgNS, 'rect');
    innerFloor.setAttribute('x', GARAGE.LEFT + 10);
    innerFloor.setAttribute('y', GARAGE.TOP + 10);
    innerFloor.setAttribute('width', GARAGE.WIDTH - 20);
    innerFloor.setAttribute('height', GARAGE.HEIGHT - 20);
    innerFloor.setAttribute('rx', '25');
    innerFloor.setAttribute('fill', 'rgba(30, 41, 59, 0.3)');
    innerFloor.setAttribute('stroke', 'rgba(255,255,255,0.05)');
    innerFloor.setAttribute('stroke-width', '1');
    structure.appendChild(innerFloor);

    // ===== 2. DRIVING LANES =====
    // Draw edges as road lanes
    mapData.edges.forEach(edge => {
        const n1 = mapData.nodes.find(n => n.id === edge.from_node_id);
        const n2 = mapData.nodes.find(n => n.id === edge.to_node_id);
        if (n1 && n2 && !n1.linked_slot_id && !n2.linked_slot_id) {
            const line = document.createElementNS(svgNS, 'line');
            line.setAttribute('x1', n1.x_pos);
            line.setAttribute('y1', n1.y_pos);
            line.setAttribute('x2', n2.x_pos);
            line.setAttribute('y2', n2.y_pos);
            line.setAttribute('stroke', 'rgba(71, 85, 105, 0.5)');
            line.setAttribute('stroke-width', '40');
            line.setAttribute('stroke-linecap', 'round');
            lanes.appendChild(line);

            // Center dashed line
            const dash = document.createElementNS(svgNS, 'line');
            dash.setAttribute('x1', n1.x_pos);
            dash.setAttribute('y1', n1.y_pos);
            dash.setAttribute('x2', n2.x_pos);
            dash.setAttribute('y2', n2.y_pos);
            dash.setAttribute('stroke', 'rgba(148, 163, 184, 0.2)');
            dash.setAttribute('stroke-width', '2');
            dash.setAttribute('stroke-dasharray', '15 15');
            lanes.appendChild(dash);
        }
    });

    // ===== 3. ENTRY / EXIT MARKERS =====
    mapData.nodes.filter(n => n.is_entry).forEach(node => {
        const isEntry = node.node_name.includes('ENTRY');
        const g = document.createElementNS(svgNS, 'g');

        const marker = document.createElementNS(svgNS, 'rect');
        marker.setAttribute('x', node.x_pos - 50);
        marker.setAttribute('y', node.y_pos - 20);
        marker.setAttribute('width', '100');
        marker.setAttribute('height', '40');
        marker.setAttribute('rx', '8');
        marker.setAttribute('fill', isEntry ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)');
        marker.setAttribute('stroke', isEntry ? '#10b981' : '#ef4444');
        marker.setAttribute('stroke-width', '2');
        g.appendChild(marker);

        const txt = document.createElementNS(svgNS, 'text');
        txt.setAttribute('x', node.x_pos);
        txt.setAttribute('y', node.y_pos + 5);
        txt.setAttribute('text-anchor', 'middle');
        txt.setAttribute('fill', isEntry ? '#10b981' : '#ef4444');
        txt.setAttribute('font-size', '16');
        txt.setAttribute('font-weight', 'bold');
        txt.setAttribute('font-family', 'Inter, sans-serif');
        txt.textContent = isEntry ? '🅿 ENTRY' : 'EXIT →';
        g.appendChild(txt);

        // Animated glow
        const glow = document.createElementNS(svgNS, 'rect');
        glow.setAttribute('x', node.x_pos - 50);
        glow.setAttribute('y', node.y_pos - 20);
        glow.setAttribute('width', '100');
        glow.setAttribute('height', '40');
        glow.setAttribute('rx', '8');
        glow.setAttribute('fill', 'transparent');
        glow.setAttribute('stroke', isEntry ? '#10b981' : '#ef4444');
        glow.setAttribute('stroke-width', '1');
        glow.setAttribute('opacity', '0.5');
        glow.innerHTML = `<animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>`;
        g.appendChild(glow);

        labels.appendChild(g);
    });

    // ===== 4. PARKING SLOTS (Realistic rectangles with orientation) =====
    mapData.slots.forEach(slot => {
        const g = document.createElementNS(svgNS, 'g');
        g.style.cursor = 'pointer';
        g.setAttribute('data-slot-id', slot.id);
        g.onclick = () => selectSlot(slot);

        // Determine slot orientation based on position
        let slotW = GARAGE.SLOT_W;
        let slotH = GARAGE.SLOT_H;
        let tx = slot.x_pos;
        let ty = slot.y_pos;
        let rotation = 0;

        // Top wall slots (vertical, narrow end at top)
        if (ty < GARAGE.TOP + GARAGE.LANE_MARGIN) {
            // Vertical slot
        }
        // Bottom wall slots
        else if (ty > GARAGE.BOTTOM - GARAGE.LANE_MARGIN) {
            // Vertical slot  
        }
        // Left/right wall slots (horizontal)
        else if (tx < GARAGE.LEFT + GARAGE.LANE_MARGIN || tx > GARAGE.RIGHT - GARAGE.LANE_MARGIN) {
            [slotW, slotH] = [slotH, slotW]; // swap for horizontal
        }
        else {
            // Center aisle slots - vertical
        }

        // Colors
        let fillColor, strokeColor, glowColor;
        if (slot.status === 'AVAILABLE') {
            if (slot.is_ev) {
                fillColor = 'rgba(59, 130, 246, 0.15)';
                strokeColor = '#3b82f6';
                glowColor = '0 0 12px rgba(59, 130, 246, 0.4)';
            } else {
                fillColor = 'rgba(16, 185, 129, 0.1)';
                strokeColor = '#10b981';
                glowColor = '0 0 12px rgba(16, 185, 129, 0.3)';
            }
        } else if (slot.status === 'OCCUPIED') {
            fillColor = 'rgba(239, 68, 68, 0.15)';
            strokeColor = '#ef4444';
            glowColor = 'none';
        } else {
            fillColor = 'rgba(234, 179, 8, 0.15)';
            strokeColor = '#eab308';
            glowColor = 'none';
        }

        // Slot rectangle
        const rect = document.createElementNS(svgNS, 'rect');
        rect.setAttribute('x', tx - slotW / 2);
        rect.setAttribute('y', ty - slotH / 2);
        rect.setAttribute('width', slotW);
        rect.setAttribute('height', slotH);
        rect.setAttribute('rx', '4');
        rect.setAttribute('fill', fillColor);
        rect.setAttribute('stroke', strokeColor);
        rect.setAttribute('stroke-width', '1.5');
        if (glowColor !== 'none') rect.style.filter = `drop-shadow(${glowColor})`;
        g.appendChild(rect);

        // Slot number text
        const text = document.createElementNS(svgNS, 'text');
        text.setAttribute('x', tx);
        text.setAttribute('y', ty + 4);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', strokeColor);
        text.setAttribute('font-size', '11');
        text.setAttribute('font-family', 'Inter, sans-serif');
        text.setAttribute('font-weight', '500');
        text.textContent = slot.slot_number.replace(`F${currentFloor}-`, '');
        g.appendChild(text);

        // EV icon
        if (slot.is_ev) {
            const evIcon = document.createElementNS(svgNS, 'text');
            evIcon.setAttribute('x', tx);
            evIcon.setAttribute('y', ty - slotH / 2 + 16);
            evIcon.setAttribute('text-anchor', 'middle');
            evIcon.setAttribute('fill', '#3b82f6');
            evIcon.setAttribute('font-size', '14');
            evIcon.textContent = '⚡';
            g.appendChild(evIcon);
        }

        // Car icon for occupied slots
        if (slot.status === 'OCCUPIED') {
            const car = document.createElementNS(svgNS, 'text');
            car.setAttribute('x', tx);
            car.setAttribute('y', ty + 20);
            car.setAttribute('text-anchor', 'middle');
            car.setAttribute('font-size', '20');
            car.textContent = '🚗';
            g.appendChild(car);
        }

        // Pulse animation for available slots
        if (slot.status === 'AVAILABLE') {
            const pulse = document.createElementNS(svgNS, 'rect');
            pulse.setAttribute('x', tx - slotW / 2);
            pulse.setAttribute('y', ty - slotH / 2);
            pulse.setAttribute('width', slotW);
            pulse.setAttribute('height', slotH);
            pulse.setAttribute('rx', '4');
            pulse.setAttribute('fill', 'transparent');
            pulse.setAttribute('stroke', strokeColor);
            pulse.setAttribute('stroke-width', '1');
            pulse.innerHTML = `<animate attributeName="opacity" values="0.3;0.8;0.3" dur="3s" repeatCount="indefinite"/>`;
            g.appendChild(pulse);
        }

        // Hover effect via event listeners
        g.addEventListener('mouseenter', () => {
            rect.setAttribute('stroke-width', '3');
            g.style.transform = 'scale(1.05)';
            g.style.transformOrigin = `${tx}px ${ty}px`;
            g.style.transition = 'transform 0.2s ease';
        });
        g.addEventListener('mouseleave', () => {
            rect.setAttribute('stroke-width', '1.5');
            g.style.transform = 'scale(1)';
        });

        slotsG.appendChild(g);
    });

    // ===== 5. FLOOR LABEL =====
    const floorLabel = document.createElementNS(svgNS, 'text');
    floorLabel.setAttribute('x', GARAGE.LEFT + GARAGE.WIDTH / 2);
    floorLabel.setAttribute('y', GARAGE.TOP + GARAGE.HEIGHT / 2);
    floorLabel.setAttribute('text-anchor', 'middle');
    floorLabel.setAttribute('fill', 'rgba(255, 255, 255, 0.04)');
    floorLabel.setAttribute('font-size', '200');
    floorLabel.setAttribute('font-family', 'Inter, sans-serif');
    floorLabel.setAttribute('font-weight', '900');
    floorLabel.textContent = `F${currentFloor}`;
    structure.appendChild(floorLabel);

    // Slot count summary
    const avail = mapData.slots.filter(s => s.status === 'AVAILABLE').length;
    const occ = mapData.slots.filter(s => s.status === 'OCCUPIED').length;
    const ev = mapData.slots.filter(s => s.is_ev && s.status === 'AVAILABLE').length;

    const countLabel = document.createElementNS(svgNS, 'text');
    countLabel.setAttribute('x', GARAGE.LEFT + 40);
    countLabel.setAttribute('y', GARAGE.BOTTOM + 160);
    countLabel.setAttribute('fill', '#94a3b8');
    countLabel.setAttribute('font-size', '18');
    countLabel.setAttribute('font-family', 'Inter, sans-serif');
    countLabel.textContent = `Available: ${avail}  |  Occupied: ${occ}  |  EV Available: ${ev}  |  Total: ${mapData.slots.length}`;
    labels.appendChild(countLabel);
}

// ---- SLOT SELECTION ----
function selectSlot(slot) {
    selectedSlot = slot;
    const panel = document.getElementById('side-panel');
    panel.classList.remove('opacity-50', 'pointer-events-none');

    document.getElementById('sp-slot').innerText = slot.slot_number;
    document.getElementById('sp-type').innerText = slot.is_ev ? 'EV Slot ⚡' : 'Standard';

    const statusEl = document.getElementById('sp-status');
    statusEl.innerText = slot.status;
    statusEl.className = 'font-medium ' + (slot.status === 'AVAILABLE' ? 'text-emerald-400' : slot.status === 'OCCUPIED' ? 'text-red-400' : 'text-yellow-400');

    const bs = document.getElementById('booking-section');
    if (slot.status === 'AVAILABLE') {
        bs.classList.remove('hidden');
        updateEstimate();
        drawPathToSlot(slot);
    } else {
        bs.classList.add('hidden');
        document.getElementById('map-path').innerHTML = '';
    }

    // Highlight selected slot on map
    document.querySelectorAll('#map-slots g').forEach(g => {
        g.querySelector('rect').setAttribute('stroke-width', '1.5');
    });
    const selectedG = document.querySelector(`#map-slots g[data-slot-id="${slot.id}"]`);
    if (selectedG) {
        selectedG.querySelector('rect').setAttribute('stroke-width', '4');
    }
}

async function updateEstimate() {
    if (!selectedSlot) return;
    const hours = document.getElementById('booking-hours').value;
    try {
        const res = await API.post('/api/booking/estimate', { slot_id: selectedSlot.id, hours });
        document.getElementById('sp-price').innerText = res.estimated_price;
    } catch (e) {
        console.error('Failed to get estimate', e);
    }
}

async function confirmBooking() {
    if (!selectedSlot) return;
    const hours = document.getElementById('booking-hours').value;
    try {
        const res = await API.post('/api/booking/create', { slot_id: selectedSlot.id, hours });
        showToast(`Booking confirmed! ₹${res.price} charged.`, 'success');
        loadFloor(currentFloor);
        document.getElementById('side-panel').classList.add('opacity-50', 'pointer-events-none');
        document.getElementById('booking-section').classList.add('hidden');
        document.getElementById('map-path').innerHTML = '';
    } catch (e) {
        showToast('Booking failed. Please try again.', 'error');
    }
}

function showToast(msg, type) {
    const toast = document.createElement('div');
    toast.className = `fixed top-24 right-8 z-50 px-6 py-3 rounded-xl shadow-lg text-sm font-medium border transition-all duration-300 ${
        type === 'success'
            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
            : 'bg-red-500/20 text-red-400 border-red-500/30'
    }`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// ---- PATH ANIMATION ----
async function drawPathToSlot(slot) {
    try {
        const res = await API.get(`/api/parking/navigate/${slot.id}`);
        const svgPath = document.getElementById('map-path');
        svgPath.innerHTML = '';

        if (res.path && res.path.length > 1) {
            const svgNS = 'http://www.w3.org/2000/svg';
            let d = `M ${res.path[0].x} ${res.path[0].y}`;
            for (let i = 1; i < res.path.length; i++) {
                d += ` L ${res.path[i].x} ${res.path[i].y}`;
            }

            // Glowing path
            const pathGlow = document.createElementNS(svgNS, 'path');
            pathGlow.setAttribute('d', d);
            pathGlow.setAttribute('fill', 'none');
            pathGlow.setAttribute('stroke', 'rgba(99, 102, 241, 0.3)');
            pathGlow.setAttribute('stroke-width', '16');
            pathGlow.setAttribute('stroke-linecap', 'round');
            pathGlow.setAttribute('stroke-linejoin', 'round');
            svgPath.appendChild(pathGlow);

            // Main path
            const pathEl = document.createElementNS(svgNS, 'path');
            pathEl.setAttribute('d', d);
            pathEl.setAttribute('fill', 'none');
            pathEl.setAttribute('stroke', '#818cf8');
            pathEl.setAttribute('stroke-width', '5');
            pathEl.setAttribute('stroke-linecap', 'round');
            pathEl.setAttribute('stroke-linejoin', 'round');
            pathEl.setAttribute('stroke-dasharray', '12 8');

            // Animate dash offset
            const totalLen = pathEl.getTotalLength ? pathEl.getTotalLength() : 1000;
            pathEl.setAttribute('stroke-dasharray', totalLen);
            pathEl.setAttribute('stroke-dashoffset', totalLen);
            pathEl.innerHTML = `<animate attributeName="stroke-dashoffset" from="${totalLen}" to="0" dur="2s" fill="freeze"/>`;
            svgPath.appendChild(pathEl);

            // Direction arrows along path
            for (let i = 1; i < res.path.length; i++) {
                const p1 = res.path[i - 1];
                const p2 = res.path[i];
                const mx = (p1.x + p2.x) / 2;
                const my = (p1.y + p2.y) / 2;
                const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180 / Math.PI;

                const arrow = document.createElementNS(svgNS, 'polygon');
                arrow.setAttribute('points', '-6,-4 6,0 -6,4');
                arrow.setAttribute('fill', '#a5b4fc');
                arrow.setAttribute('transform', `translate(${mx}, ${my}) rotate(${angle})`);
                arrow.setAttribute('opacity', '0.7');
                svgPath.appendChild(arrow);
            }
        }
    } catch (e) {
        console.error('Path error:', e);
    }
}

// ---- MAP INTERACTIONS (Zoom & Pan) ----
function setupMapInteractions() {
    const container = document.getElementById('map-container');

    container.addEventListener('mousedown', (e) => {
        if (e.target.closest('#map-slots g')) return;
        isDragging = true;
        startDragOffset = { x: e.clientX - mapPos.x, y: e.clientY - mapPos.y };
        container.style.cursor = 'grabbing';
    });

    container.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        mapPos.x = e.clientX - startDragOffset.x;
        mapPos.y = e.clientY - startDragOffset.y;
        updateMapTransform();
    });

    container.addEventListener('mouseup', () => { isDragging = false; container.style.cursor = 'grab'; });
    container.addEventListener('mouseleave', () => { isDragging = false; container.style.cursor = 'grab'; });

    // Touch support
    container.addEventListener('touchstart', (e) => {
        isDragging = true;
        startDragOffset = { x: e.touches[0].clientX - mapPos.x, y: e.touches[0].clientY - mapPos.y };
    });
    container.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        e.preventDefault();
        mapPos.x = e.touches[0].clientX - startDragOffset.x;
        mapPos.y = e.touches[0].clientY - startDragOffset.y;
        updateMapTransform();
    });
    container.addEventListener('touchend', () => isDragging = false);
}

function zoomMap(e) {
    e.preventDefault();
    const zoomAmount = 0.05;
    if (e.deltaY < 0) mapScale += zoomAmount;
    else mapScale -= zoomAmount;
    mapScale = Math.min(Math.max(0.15, mapScale), 2);
    updateMapTransform();
}

function updateMapTransform() {
    const svg = document.getElementById('parkingMap');
    svg.style.transform = `translate(${mapPos.x}px, ${mapPos.y}px) scale(${mapScale})`;
}
