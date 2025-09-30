
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>India Airspace Management - Optimized</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body { height: 100%; margin: 0; background: #0b1220; }
  #map { 
    height: 100%; 
    margin: 0; 
    background: #0b1220; 
    border-radius: 12px;
    overflow: hidden;
  }
  
  /* OPTIMIZED LEGEND - No conflicts with Leaflet */
  .performance-legend {
    position: absolute !important;
    bottom: 15px !important;
    left: 15px !important;
    background: rgba(20, 20, 20, 0.95) !important;
    border: 2px solid #ff6b35 !important;
    border-radius: 10px !important;
    padding: 15px !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
    font-size: 13px !important;
    color: #ffffff !important;
    z-index: 1001 !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.7) !important;
    max-width: 220px !important;
    backdrop-filter: blur(15px) !important;
    pointer-events: none !important;
    user-select: none !important;
  }

  .performance-legend h4 {
    margin: 0 0 12px 0 !important;
    color: #ff6b35 !important;
    font-size: 15px !important;
    font-weight: bold !important;
    text-align: center !important;
  }

  .legend-row {
    display: flex !important;
    align-items: center !important;
    margin: 6px 0 !important;
    white-space: nowrap !important;
  }

  .legend-icon {
    width: 14px !important;
    height: 14px !important;
    border-radius: 50% !important;
    margin-right: 10px !important;
    border: 2px solid rgba(255,255,255,0.4) !important;
    flex-shrink: 0 !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
  }

  .legend-icon.drone { background: linear-gradient(45deg, #3b82f6, #1d4ed8) !important; }
  .legend-icon.electric { background: linear-gradient(45deg, #22c55e, #16a34a) !important; }
  .legend-icon.fuel { background: linear-gradient(45deg, #ef4444, #dc2626) !important; }
  .legend-icon.depot { background: linear-gradient(45deg, #f59e0b, #d97706) !important; }
  .legend-icon.delivery { background: linear-gradient(45deg, #8b5cf6, #7c3aed) !important; }
  .legend-icon.nfz { background: linear-gradient(45deg, #ef4444, #dc2626) !important; }

  .legend-text {
    font-size: 12px !important;
    color: #e5e5e5 !important;
    font-weight: 500 !important;
  }

  /* Loading overlay for better UX */
  #loadingOverlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(11, 18, 32, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    backdrop-filter: blur(5px);
  }

  .loading-content {
    text-align: center;
    color: white;
    font-family: 'Segoe UI', Arial, sans-serif;
  }

  .spinner {
    border: 4px solid rgba(255, 107, 53, 0.3);
    border-top: 4px solid #ff6b35;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style>
</head>
<body>
<div id="loadingOverlay">
  <div class="loading-content">
    <div class="spinner"></div>
    <h3 style="color: #ff6b35; margin: 0;">Optimizing Fleet System...</h3>
    <p style="margin: 10px 0 0 0; color: #cccccc;">Loading enhanced map performance</p>
  </div>
</div>

<div id="map"></div>

<script>
  // PERFORMANCE OPTIMIZATIONS
  let map;
  let vehicleMarkers = {};
  let routeLines = {};
  let trailLines = {};
  let depotMarker;
  let deliveryMarkers = [];
  let showVehicles = true;
  let showNFZ = true;
  let nfzLayers = [];
  let legendContainer = null;
  
  // Performance tracking
  let lastUpdateTime = 0;
  let updateQueue = [];
  let batchUpdateTimer = null;
  let isMapReady = false;
  
  // Cached elements for better performance
  let vehicleMarkersCache = new Map();
  let positionUpdateBuffer = new Map();
  
  // OPTIMIZED: Create persistent legend with no Leaflet conflicts
  function createOptimizedLegend() {
    if (legendContainer) {
      try {
        document.body.removeChild(legendContainer);
      } catch(e) {}
    }

    legendContainer = document.createElement('div');
    legendContainer.className = 'performance-legend';
    
    legendContainer.innerHTML = `
      <h4>Fleet Legend</h4>
      <div class="legend-row">
        <div class="legend-icon drone"></div>
        <span class="legend-text">Drones (aerial route)</span>
      </div>
      <div class="legend-row">
        <div class="legend-icon electric"></div>
        <span class="legend-text">Electric Trucks</span>
      </div>
      <div class="legend-row">
        <div class="legend-icon fuel"></div>
        <span class="legend-text">Fuel Trucks</span>
      </div>
      <div class="legend-row">
        <div class="legend-icon depot"></div>
        <span class="legend-text">Selected Depot</span>
      </div>
      <div class="legend-row">
        <div class="legend-icon delivery"></div>
        <span class="legend-text">Delivery Points</span>
      </div>
      <div class="legend-row">
        <div class="legend-icon nfz"></div>
        <span class="legend-text">No-Fly Zones</span>
      </div>
    `;
    
    document.body.appendChild(legendContainer);
    return legendContainer;
  }

  // OPTIMIZED: Initialize map with performance enhancements
  function initializeOptimizedMap(mapData) {
    console.log('🚀 Initializing optimized map system...');
    
    // Create map with performance settings
    map = L.map('map', {
      preferCanvas: true,  // Use Canvas for better performance
      zoomAnimation: false, // Disable zoom animation for speed
      fadeAnimation: false, // Disable fade animation
      markerZoomAnimation: false // Disable marker zoom animation
    }).setView([mapData.center[0], mapData.center[1]], mapData.zoom);
    
    // Optimized tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,  // Reduced from 19 for better performance
      attribution: '&copy; OpenStreetMap contributors',
      noWrap: true,
      updateWhenIdle: true,  // Only update tiles when map is idle
      keepBuffer: 2  // Reduced buffer for memory efficiency
    }).addTo(map);

    // Initialize components in optimized order
    setTimeout(() => {
      initializeDepotOptimized(mapData.depot);
      initializeDeliveryPointsOptimized(mapData.deliveries);
      initializeNoFlyZonesOptimized(mapData.nfzones);
      createOptimizedLegend();
      hideLoadingOverlay();
      isMapReady = true;
      console.log('✅ Map optimization completed');
    }, 100);

    // Set up performance monitoring
    setupPerformanceMonitoring();
  }

  function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
      overlay.style.opacity = '0';
      setTimeout(() => overlay.remove(), 500);
    }
  }

  // OPTIMIZED: Depot initialization
  function initializeDepotOptimized(depotCoords) {
    if (!depotCoords) return;
    
    depotMarker = L.marker([depotCoords[0], depotCoords[1]], {
      icon: L.divIcon({
        className: 'custom-div-icon',
        html: '<div style="background: linear-gradient(45deg, #f59e0b, #d97706); color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);"><i class="fa fa-home"></i></div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      }),
      riseOnHover: true
    }).addTo(map);
    
    depotMarker.bindTooltip('Depot Location', { permanent: false, direction: 'top' });
  }

  // OPTIMIZED: Delivery points with batching
  function initializeDeliveryPointsOptimized(deliveries) {
    if (!deliveries || deliveries.length === 0) return;
    
    const batchSize = 25; // Process 25 at a time
    let batchIndex = 0;
    
    function processBatch() {
      const start = batchIndex * batchSize;
      const end = Math.min(start + batchSize, deliveries.length);
      
      for (let i = start; i < end; i++) {
        const delivery = deliveries[i];
        const marker = L.marker([delivery[0], delivery[1]], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background: linear-gradient(45deg, #8b5cf6, #7c3aed); color: white; border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; border: 2px solid white; font-size: 10px; font-weight: bold;">${i+1}</div>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9]
          }),
          riseOnHover: true
        });
        
        marker.addTo(map);
        marker.bindTooltip(`Delivery #${i+1}`, { direction: 'top' });
        deliveryMarkers.push(marker);
      }
      
      batchIndex++;
      if (end < deliveries.length) {
        setTimeout(processBatch, 50); // 50ms delay between batches
      } else {
        console.log(`✅ Loaded ${deliveries.length} delivery points in ${batchIndex} batches`);
      }
    }
    
    processBatch();
  }

  // CORRECTED: No-fly zones with proper radius display like depot selection
  function initializeNoFlyZonesOptimized(nfzones) {
    if (!nfzones || !showNFZ) return;
    
    const colors = {
      'military': '#ef4444',
      'airport': '#f97316', 
      'nuclear': '#dc2626',
      'government': '#a855f7',
      'border': '#374151',
      'space': '#3b82f6'
    };

    // Process in batches to avoid blocking
    const batchSize = 10;
    let processed = 0;
    
    function processNFZBatch() {
      const end = Math.min(processed + batchSize, nfzones.length);
      
      for (let i = processed; i < end; i++) {
        const nfz = nfzones[i];
        const color = colors[nfz.type] || '#6b7280';
        
        // Create circle with proper radius (same as depot selection)
        const circle = L.circle([nfz.center[0], nfz.center[1]], {
          color: color,
          weight: 2,
          fillColor: color,
          fillOpacity: 0.3,
          radius: nfz.radius
        }).addTo(map);
        
        // Create marker (same as depot selection)
        const marker = L.marker([nfz.center[0], nfz.center[1]], {
          icon: L.divIcon({
            className: 'nfz-marker',
            html: `<div style="background-color: ${color}; color: white; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border: 2px solid white;"><i class="fa fa-ban" style="font-size: 8px;"></i></div>`,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          })
        }).addTo(map);
        
        const popupContent = `
          <div style="width:200px;">
            <h4 style="color: ${color}; margin: 0 0 8px 0;">⚠️ NO-FLY ZONE</h4>
            <p style="margin: 4px 0;"><strong>Name:</strong> ${nfz.name}</p>
            <p style="margin: 4px 0;"><strong>Type:</strong> ${nfz.type}</p>
            <p style="margin: 4px 0;"><strong>Radius:</strong> ${(nfz.radius/1000).toFixed(1)} km</p>
          </div>
        `;
        
        circle.bindPopup(popupContent);
        marker.bindPopup(popupContent);
        
        nfzLayers.push(circle);
        nfzLayers.push(marker);
      }
      
      processed = end;
      if (processed < nfzones.length) {
        setTimeout(processNFZBatch, 100);
      } else {
        console.log(`✅ Loaded ${nfzones.length} no-fly zones`);
      }
    }
    
    processNFZBatch();
  }

  // OPTIMIZED: Vehicle icon creation with caching
  function createVehicleIcon(name, type) {
    const cacheKey = type;
    if (vehicleMarkersCache.has(cacheKey)) {
      return vehicleMarkersCache.get(cacheKey);
    }
    
    let iconHtml, iconColor;
    
    if (type === 'Drone') {
      iconHtml = '<i class="fa fa-plane"></i>';
      iconColor = 'linear-gradient(45deg, #3b82f6, #1d4ed8)';
    } else if (type === 'Electric Truck') {
      iconHtml = '<i class="fa fa-truck"></i>';
      iconColor = 'linear-gradient(45deg, #22c55e, #16a34a)';
    } else if (type === 'Fuel Truck') {
      iconHtml = '<i class="fa fa-truck"></i>';
      iconColor = 'linear-gradient(45deg, #ef4444, #dc2626)';
    }
    
    const icon = L.divIcon({
      className: 'custom-div-icon',
      html: `<div style="background: ${iconColor}; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; border: 2px solid white; box-shadow: 0 3px 6px rgba(0,0,0,0.4);">${iconHtml}</div>`,
      iconSize: [26, 26],
      iconAnchor: [13, 13]
    });
    
    vehicleMarkersCache.set(cacheKey, icon);
    return icon;
  }

  // OPTIMIZED: Add vehicle batch with performance improvements
  function addVehicleBatch(vehicleData) {
    if (!showVehicles || !isMapReady) return;

    const vehicles = vehicleData.vehicles || [vehicleData];
    
    vehicles.forEach(v => {
      const icon = createVehicleIcon(v.name, v.type);
      const vehicleColor = getVehicleColor(v.type);
      
      // Create vehicle marker with performance options
      const marker = L.marker([v.pos[0], v.pos[1]], { 
        icon: icon,
        riseOnHover: true
      }).addTo(map);
      
      const tooltipText = `${v.name}\n${v.type}\nWeight: ${v.weight}kg\nVolume: ${v.volume || 'N/A'}cm³\nSpeed: ${v.speed}km/h`;
      marker.bindTooltip(tooltipText, { direction: 'top' });
      
      vehicleMarkers[v.name] = marker;

      // OPTIMIZED: Route line with reduced points for performance
      const optimizedRoute = optimizeRouteForDisplay(v.route);
      let routeStyle = {
        color: vehicleColor, 
        weight: 3, 
        opacity: 0.7,
        smoothFactor: 2.0 // Smooth the line for better performance
      };
      
      if (v.type === 'Drone') { 
        routeStyle.dashArray = '8,12';
        routeStyle.weight = 2;
      }
      
      routeLines[v.name] = L.polyline(optimizedRoute, routeStyle).addTo(map);

      // OPTIMIZED: Trail line initialization
      const trail = L.polyline([v.pos], {
        color: vehicleColor, 
        weight: 4, 
        opacity: 0.9,
        smoothFactor: 1.5
      });
      
      if (v.type === 'Drone') { 
        trail.setStyle({dashArray: '6,6'}); 
      }
      
      trailLines[v.name] = trail.addTo(map);
    });

    console.log(`✅ Added ${vehicles.length} vehicles to map`);
  }

  // OPTIMIZED: Route optimization for display
  function optimizeRouteForDisplay(route) {
    if (route.length <= 50) return route;
    
    // Douglas-Peucker-like simplification
    const optimized = [route[0]]; // Always keep first point
    const step = Math.ceil(route.length / 30); // Reduce to ~30 points max
    
    for (let i = step; i < route.length - 1; i += step) {
      optimized.push(route[i]);
    }
    
    optimized.push(route[route.length - 1]); // Always keep last point
    return optimized;
  }

  function getVehicleColor(type) {
    switch(type) {
      case 'Drone': return '#3b82f6';
      case 'Electric Truck': return '#22c55e';
      case 'Fuel Truck': return '#ef4444';
      default: return '#6b7280';
    }
  }

  // OPTIMIZED: Position updates with buffering
  function updateVehiclePositionsOptimized(positionData) {
    if (!showVehicles || !isMapReady) return;
    
    const currentTime = Date.now();
    
    // Buffer updates to prevent too frequent DOM manipulation
    positionData.position_updates.forEach(update => {
      positionUpdateBuffer.set(update.name, {
        pos: update.pos,
        speed: update.speed,
        timestamp: currentTime
      });
    });
    
    // Process buffered updates
    if (!batchUpdateTimer) {
      batchUpdateTimer = setTimeout(() => {
        processBatchedPositionUpdates();
        batchUpdateTimer = null;
      }, 100); // 100ms batching delay
    }
  }

  function processBatchedPositionUpdates() {
    const updateCount = positionUpdateBuffer.size;
    
    positionUpdateBuffer.forEach((update, vehicleName) => {
      const marker = vehicleMarkers[vehicleName];
      const trail = trailLines[vehicleName];
      
      if (marker) {
        marker.setLatLng([update.pos[0], update.pos[1]]);
      }
      
      if (trail) {
        const latlngs = trail.getLatLngs();
        const newPos = [update.pos[0], update.pos[1]];
        
        // Only add if position actually changed
        const lastPos = latlngs[latlngs.length - 1];
        if (!lastPos || lastPos.lat !== newPos[0] || lastPos.lng !== newPos[1]) {
          latlngs.push(newPos);
          
          // Limit trail length for performance
          if (latlngs.length > 150) {
            latlngs.splice(0, latlngs.length - 150);
          }
          
          trail.setLatLngs(latlngs);
        }
      }
    });
    
    positionUpdateBuffer.clear();
    
    if (updateCount > 0) {
      console.log(`📍 Updated ${updateCount} vehicle positions`);
    }
  }

  // OPTIMIZED: Clear vehicles with performance improvements
  function clearAllVehicles() {
    // Use requestAnimationFrame for smooth removal
    requestAnimationFrame(() => {
      Object.values(vehicleMarkers).forEach(m => {
        try { map.removeLayer(m); } catch(e) {}
      });
      Object.values(routeLines).forEach(l => {
        try { map.removeLayer(l); } catch(e) {}
      });
      Object.values(trailLines).forEach(l => {
        try { map.removeLayer(l); } catch(e) {}
      });
      
      vehicleMarkers = {};
      routeLines = {};
      trailLines = {};
      positionUpdateBuffer.clear();
      
      if (batchUpdateTimer) {
        clearTimeout(batchUpdateTimer);
        batchUpdateTimer = null;
      }
      
      console.log('🧹 Cleared all vehicles from map');
    });
  }

  // OPTIMIZED: Toggle functions with performance considerations
  function toggleVehiclesOptimized(show) {
    showVehicles = show;
    if (!show) {
      clearAllVehicles();
    }
  }

  function toggleNoFlyZonesOptimized(show) {
    showNFZ = show;
    nfzLayers.forEach(layer => {
      if (show) {
        try {
          map.addLayer(layer);
        } catch(e) {
          // Layer might already be added
        }
      } else {
        try {
          map.removeLayer(layer);
        } catch(e) {
          // Layer might already be removed
        }
      }
    });
    console.log(`🚫 No-fly zones ${show ? 'shown' : 'hidden'}`);
  }

  // Performance monitoring
  function setupPerformanceMonitoring() {
    let frameCount = 0;
    let lastTime = performance.now();
    
    function measurePerformance() {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= 5000) { // Every 5 seconds
        const fps = Math.round(frameCount / ((currentTime - lastTime) / 1000));
        console.log(`🔥 Map Performance: ${fps} FPS, ${Object.keys(vehicleMarkers).length} vehicles`);
        frameCount = 0;
        lastTime = currentTime;
      }
      
      requestAnimationFrame(measurePerformance);
    }
    
    measurePerformance();
  }

  // Update map configuration for depot changes
  function updateMapConfiguration(configData) {
    console.log('🔄 Updating map configuration...');
    
    // Clear existing elements
    if (depotMarker) {
      map.removeLayer(depotMarker);
    }
    deliveryMarkers.forEach(m => map.removeLayer(m));
    deliveryMarkers = [];
    
    // Add new configuration
    initializeDepotOptimized(configData.depot);
    initializeDeliveryPointsOptimized(configData.deliveries);
    
    // Center map on new depot
    if (configData.depot) {
      map.setView([configData.depot[0], configData.depot[1]], 8);
    }
    
    console.log(`✅ Updated: ${configData.total_deliveries} delivery points`);
  }

  // Fallback initialization for compatibility
  function initializeMap(mapData) {
    initializeOptimizedMap(mapData);
  }

  function setVehicles(vehicleData) {
    addVehicleBatch(vehicleData);
  }

  function updateVehiclePositions(vehicleData) {
    updateVehiclePositionsOptimized(vehicleData);
  }

  function toggleVehicles(show) {
    toggleVehiclesOptimized(show);
  }

  function toggleNoFlyZones(show) {
    toggleNoFlyZonesOptimized(show);
  }

  // Expose optimized functions
  window.initializeOptimizedMap = initializeOptimizedMap;
  window.addVehicleBatch = addVehicleBatch;
  window.updateVehiclePositionsOptimized = updateVehiclePositionsOptimized;
  window.toggleVehiclesOptimized = toggleVehiclesOptimized;
  window.toggleNoFlyZonesOptimized = toggleNoFlyZonesOptimized;
  window.clearAllVehicles = clearAllVehicles;
  window.updateMapConfiguration = updateMapConfiguration;

  // Backward compatibility
  window.initializeMap = initializeMap;
  window.setVehicles = setVehicles;
  window.updateVehiclePositions = updateVehiclePositions;
  window.toggleVehicles = toggleVehicles;
  window.toggleNoFlyZones = toggleNoFlyZones;
</script>
</body>
</html>
"""
# Keep the depot selection template unchanged
DEPOT_SELECTION_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Select Depot Location - India Airspace Management</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body { 
    height: 100%; 
    margin: 0; 
    background: #0b1220; 
    font-family: 'Segoe UI', Arial, sans-serif;
  }
  #map { 
    height: calc(120vh - 120px); 
    min-height: 800px;
    margin: 0; 
    background: #0b1220; 
    border-radius: 12px;
    overflow: hidden;
  }
  .info-panel {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(45, 45, 45, 0.95);
    color: white;
    padding: 20px;
    border-radius: 10px;
    width: 300px;
    backdrop-filter: blur(10px);
    border: 1px solid #404040;
  }
  .info-panel h3 {
    color: #ff6b35;
    margin-top: 0;
    font-size: 18px;
  }
  .info-panel p {
    margin: 8px 0;
    font-size: 14px;
    line-height: 1.4;
  }
  .selected-location {
    background: rgba(255, 107, 53, 0.1);
    border: 1px solid #ff6b35;
    padding: 10px;
    border-radius: 6px;
    margin: 10px 0;
  }
  .customer-info {
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid #8b5cf6;
    padding: 10px;
    border-radius: 6px;
    margin: 10px 0;
  }
  .legend {
    position: fixed !important; 
    bottom: 20px !important; 
    left: 20px !important;
    background: rgba(45, 45, 45, 0.95) !important;
    color: white !important;
    padding: 15px !important;
    border-radius: 8px !important;
    font: 12px/1.4 system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid #404040 !important;
    z-index: 9999 !important;
  }
  .legend .dot { 
    display: inline-block; 
    width: 12px; 
    height: 12px; 
    border-radius: 50%; 
    margin-right: 8px; 
  }
  .legend h4 {
    color: #ff6b35;
    margin: 0 0 10px 0;
    font-size: 14px;
  }
</style>
</head>
<body>
<div id="map"></div>



<div class="legend">
  <h4>Map Legend</h4>
  <div><span class="dot" style="background:#ef4444"></span> No-Fly Zones</div>
  <div><span class="dot" style="background:#f59e0b"></span> Major Cities</div>
  <div><span class="dot" style="background:#22c55e"></span> Your Depot</div>
  <div><span class="dot" style="background:#8b5cf6"></span> Suggested Locations</div>
</div>

<script>
  let map;
  let depotMarker = null;
  let selectedCoords = null;
  let nfzLayers = [];
  let customerCount = 0;

  function initializeDepotMap(mapData) {
    map = L.map('map').setView([mapData.center[0], mapData.center[1]], mapData.zoom);
    
    // Use same OpenStreetMap tiles as main window
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, 
      attribution: '&copy; OpenStreetMap contributors',
      noWrap: true
    }).addTo(map);

    // Add major cities
    if (mapData.cities) {
      mapData.cities.forEach(city => {
        L.marker([city.coords[0], city.coords[1]], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: '<div style="background-color: #f59e0b; color: white; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border: 2px solid white;"><i class="fa fa-city" style="font-size: 8px;"></i></div>',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          })
        }).addTo(map).bindTooltip(city.name, {permanent: false, direction: 'top'});
      });
    }

    // Add no-fly zones
    if (mapData.nfzones) {
      addNoFlyZones(mapData.nfzones);
    }

    // Add suggested depot locations
    if (mapData.suggested) {
      mapData.suggested.forEach((location, index) => {
        L.marker([location.coords[0], location.coords[1]], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: '<div style="background-color: #8b5cf6; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; border: 2px solid white;"><i class="fa fa-warehouse" style="font-size: 10px;"></i></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
          })
        }).addTo(map)
        .bindPopup(`<strong>Suggested Location:</strong><br>${location.name}<br><small>${location.description}</small>`)
        .bindTooltip(location.name);
      });
    }

    // Map click handler
    map.on('click', function(e) {
      selectDepotLocation(e.latlng.lat, e.latlng.lng);
    });
  }

  function addNoFlyZones(nfzones) {
    const colors = {
      'military': '#ef4444',
      'airport': '#f97316', 
      'nuclear': '#dc2626',
      'government': '#a855f7',
      'border': '#374151',
      'space': '#3b82f6'
    };

    nfzones.forEach(nfz => {
      const color = colors[nfz.type] || '#6b7280';
      
      // Create circle
      const circle = L.circle([nfz.center[0], nfz.center[1]], {
        color: color,
        weight: 2,
        fillColor: color,
        fillOpacity: 0.3,
        radius: nfz.radius
      }).addTo(map);
      
      // Create marker
      const marker = L.marker([nfz.center[0], nfz.center[1]], {
        icon: L.divIcon({
          className: 'nfz-marker',
          html: `<div style="background-color: ${color}; color: white; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border: 2px solid white;"><i class="fa fa-ban" style="font-size: 8px;"></i></div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        })
      }).addTo(map);
      
      const popupContent = `
        <div style="width:200px;">
          <h4 style="color: ${color}; margin: 0 0 8px 0;">⚠️ NO-FLY ZONE</h4>
          <p style="margin: 4px 0;"><strong>Name:</strong> ${nfz.name}</p>
          <p style="margin: 4px 0;"><strong>Type:</strong> ${nfz.type}</p>
          <p style="margin: 4px 0;"><strong>Radius:</strong> ${(nfz.radius/1000).toFixed(1)} km</p>
        </div>
      `;
      
      circle.bindPopup(popupContent);
      marker.bindPopup(popupContent);
      
      nfzLayers.push(circle);
      nfzLayers.push(marker);
    });
  }

  function selectDepotLocation(lat, lng) {
    // Remove existing depot marker
    if (depotMarker) {
      map.removeLayer(depotMarker);
    }

    // Add new depot marker
    depotMarker = L.marker([lat, lng], {
      icon: L.divIcon({
        className: 'custom-div-icon',
        html: '<div style="background-color: #22c55e; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(34,197,94,0.5);"><i class="fa fa-home"></i></div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      })
    }).addTo(map);

    depotMarker.bindPopup(`<strong>Selected Depot Location</strong><br>Lat: ${lat.toFixed(6)}<br>Lng: ${lng.toFixed(6)}<br><br><strong>Delivery Points:</strong> ${customerCount}`);
    depotMarker.bindTooltip('Your Depot Location', {permanent: true, direction: 'top'});

    // Update UI
    selectedCoords = [lat, lng];
    document.getElementById('selectedLocation').style.display = 'block';
    document.getElementById('locationText').textContent = `Latitude: ${lat.toFixed(6)}, Longitude: ${lng.toFixed(6)}`;
    document.getElementById('coordsText').textContent = `${customerCount} delivery points will be generated`;

    // Notify Python
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.depot_selected(lat, lng);
    }
  }

  function updateCustomerCount(count) {
    customerCount = count;
    document.getElementById('customerCount').textContent = count;
    
    // Update selected location info if depot is selected
    if (selectedCoords) {
      document.getElementById('coordsText').textContent = `${count} delivery points will be generated`;
      if (depotMarker) {
        depotMarker.bindPopup(`<strong>Selected Depot Location</strong><br>Lat: ${selectedCoords[0].toFixed(6)}<br>Lng: ${selectedCoords[1].toFixed(6)}<br><br><strong>Delivery Points:</strong> ${count}`);
      }
    }
  }

  function getSelectedLocation() {
    return selectedCoords;
  }

  function getCustomerCount() {
    return customerCount;
  }

  // Expose functions
  window.initializeDepotMap = initializeDepotMap;
  window.selectDepotLocation = selectDepotLocation;
  window.updateCustomerCount = updateCustomerCount;
  window.getSelectedLocation = getSelectedLocation;
  window.getCustomerCount = getCustomerCount;
</script>
</body>
</html>
"""