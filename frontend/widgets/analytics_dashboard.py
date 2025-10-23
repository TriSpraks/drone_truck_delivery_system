"""
Analytics Dashboard Widget - PERFECTLY FIXED VERSION
All text labels properly visible, sized, and positioned
NO overlapping, NO cutoff text, consistent styling
"""
import os
import json
import numpy as np
import pandas as pd
import seaborn as sns
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Set seaborn style
sns.set_theme(style="darkgrid")
sns.set_palette("husl")


class AnalyticsDashboard(QWidget):
    """Display delivery performance analytics from backend solution.json"""
    
    data_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.current_solution = None
        self.last_solution_hash = None
        self._widget_destroyed = False

        self.init_ui()

        # Setup continuous polling for solution.json updates
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.periodic_check_solution)
        self.refresh_timer.start(2000)  # Check every 2 seconds

        # Initial load
        QTimer.singleShot(1000, self.load_solution_data)
    
    def init_ui(self):
        """Initialize analytics UI"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Create scrollable area
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    background-color: #1a1a1a;
                    border: none;
                }
                QScrollBar:vertical {
                    width: 10px;
                    background: #1a1a1a;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #555555;
                    border-radius: 5px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #777777;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    border: none;
                    background: none;
                }
            """)
            
            # Container widget
            self.container = QWidget()
            self.container_layout = QVBoxLayout(self.container)
            self.container_layout.setContentsMargins(10, 10, 10, 10)
            self.container_layout.setSpacing(15)
            
            scroll_area.setWidget(self.container)
            layout.addWidget(scroll_area)
            
        except Exception as e:
            print(f"Error initializing AnalyticsDashboard UI: {e}")
            self._widget_destroyed = True
    
    def get_backend_folder_path(self):
        """Get backend folder path"""
        try:
            if self.parent_window:
                return self.parent_window.get_backend_folder_path()
            
            current_file = os.path.abspath(__file__)
            widgets_dir = os.path.dirname(current_file)
            frontend_dir = os.path.dirname(widgets_dir)
            project_root = os.path.dirname(frontend_dir)
            return os.path.join(project_root, 'backend')
        except Exception as e:
            return None
    
    def periodic_check_solution(self):
        """Fetch solution once after backend completion, no polling during processing"""
        if self._widget_destroyed:
            return

        try:
            # Only fetch when backend is complete
            if hasattr(self.parent_window, '_backend_ready') and self.parent_window._backend_ready:
                # If we already have solution data, stop polling
                if self.current_solution and self.refresh_timer.isActive():
                    self.refresh_timer.stop()
                    return

                # Fetch solution data once
                solution = None

                # First priority: shared solution data from main window
                if hasattr(self.parent_window, 'shared_solution_data') and self.parent_window.shared_solution_data:
                    solution = self.parent_window.shared_solution_data
                # Second priority: API fetch
                else:
                    solution = self._load_solution_file()

                if solution:
                    solution_str = json.dumps(solution, sort_keys=True)
                    solution_hash = hash(solution_str)

                    if solution_hash != self.last_solution_hash:
                        self.last_solution_hash = solution_hash
                        self.current_solution = solution
                        self.refresh_all_graphs()

                    # Stop polling after fetching
                    if self.refresh_timer.isActive():
                        self.refresh_timer.stop()
        except Exception as e:
            pass  # Silent fail for polling
    
    def load_solution_data(self):
        """Load solution.json from backend folder"""
        try:
            if self._widget_destroyed:
                return

            # First try to get shared solution data from main window
            if hasattr(self.parent_window, 'shared_solution_data') and self.parent_window.shared_solution_data:
                solution = self.parent_window.shared_solution_data
            else:
                # Fallback to API fetch if shared data not available
                solution = self._load_solution_file()

            if solution:
                self.current_solution = solution
                self.last_solution_hash = hash(json.dumps(solution, sort_keys=True))
                self.refresh_all_graphs()
            else:
                self.show_waiting_message()
        except Exception as e:
            print(f"[AnalyticsDashboard] Error loading solution: {e}")
            self.show_waiting_message()
    
    def _load_solution_file(self):
        """Load solution.json from backend API after backend processing completes"""
        try:
            # Check if backend processing is still in progress
            if hasattr(self.parent_window, '_backend_processing') and self.parent_window._backend_processing:
                print("[AnalyticsDashboard] Backend still processing, skipping solution fetch")
                return None

            import aiohttp
            import asyncio

            async def fetch_solution():
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "https://trispark.onrender.com/api/solution",
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            print(f"[AnalyticsDashboard] API error: {response.status}")
                            return None

            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(fetch_solution())
            finally:
                loop.close()

        except Exception as e:
            print(f"[AnalyticsDashboard] Error fetching solution from API: {e}")

        return None
    
    def refresh_all_graphs(self):
        """Refresh all analytics graphs"""
        try:
            if not self.current_solution or self._widget_destroyed:
                return
            
            # Clear existing graphs safely
            while self.container_layout.count():
                item = self.container_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            
            # Build analytics data
            analytics = self._process_analytics()
            
            # Create graph sections with properly sized charts
            self._create_vehicle_distribution_pie(analytics)
            self._create_efficiency_comparison_bar(analytics)
            self._create_distance_histogram(analytics)
            self._create_wave_metrics_line(analytics)
            self._create_noise_analysis_bar(analytics)  # ← ADD THIS LINE
            self._create_cost_analysis_box(analytics)
            self._create_capacity_utilization_heatmap(analytics)
            self._create_summary_section(analytics)
            
            # Add stretch
            self.container_layout.addStretch()
            
            print("[AnalyticsDashboard] All graphs refreshed successfully")
            
        except Exception as e:
            print(f"[AnalyticsDashboard] Error refreshing graphs: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_analytics(self):
        """Process solution data into analytics"""
        solution = self.current_solution
        analytics = {
            'efficiency': {},
            'waves': {},
            'summary': {}
        }
        
        try:
            # Process efficiency metrics
            all_routes = []
            
            # Collect all wave data
            waves_list = self._get_waves_list(solution)
            
            for wave in waves_list:
                # Process drones
                for drone in wave.get('drones', []):
                    all_routes.append({
                        'type': 'Drone',
                        'vehicle': drone.get('vehicle_id', 'Unknown'),
                        'nodes': len(drone.get('node_ids', [])),
                        'distance': float(drone.get('distance', 0)),
                        'cost': float(drone.get('cost', 0)),
                        'weight': float(drone.get('total_weight', 0)),
                        'volume': float(drone.get('total_volume', 0))
                    })
                
                # Process trucks
                for truck in wave.get('trucks', []):
                    vehicle_id = truck.get('vehicle_id', 'Unknown')
                    is_electric = 'E_Truck' in vehicle_id or 'electric' in vehicle_id.lower()
                    
                    all_routes.append({
                        'type': 'E-Truck' if is_electric else 'F-Truck',
                        'vehicle': vehicle_id,
                        'nodes': len(truck.get('node_ids', [])),
                        'distance': float(truck.get('distance', 0)),
                        'cost': float(truck.get('cost', 0)),
                        'weight': float(truck.get('total_weight', 0)),
                        'volume': float(truck.get('total_volume', 0)),
                        'weight_util': truck.get('capacity_utilization', {}).get('weight_percent', 0),
                        'volume_util': truck.get('capacity_utilization', {}).get('volume_percent', 0)
                    })
            
            analytics['efficiency']['all_routes'] = all_routes
            
            # Calculate averages by type
            for vehicle_type in ['Drone', 'E-Truck', 'F-Truck']:
                routes = [r for r in all_routes if r['type'] == vehicle_type]
                if routes:
                    analytics['efficiency'][vehicle_type] = {
                        'count': len(routes),
                        'avg_cost_per_node': sum(r['cost'] / max(1, r['nodes']) for r in routes) / len(routes),
                        'avg_distance_per_node': sum(r['distance'] / max(1, r['nodes']) for r in routes) / len(routes),
                        'total_distance': sum(r['distance'] for r in routes),
                        'total_cost': sum(r['cost'] for r in routes)
                    }
            
            # Wave breakdown
            waves_summary = solution.get('summary', {}).get('wave_breakdown', {})
            for wave_key, wave_data in waves_summary.items():
                analytics['waves'][wave_key] = {
                    'distance': wave_data.get('total_distance', 0),
                    'cost': wave_data.get('total_cost', 0),
                    'nodes': wave_data.get('nodes_assigned', 0),
                    'drones': wave_data.get('drone_routes', 0),
                    'trucks': wave_data.get('truck_routes', 0)
                }
            
            # Summary
            summary = solution.get('summary', {})
            analytics['summary'] = {
                'total_distance': summary.get('total_distance', 0),
                'total_cost': summary.get('total_cost', 0),
                'total_nodes': summary.get('total_nodes_assigned', 0),
                'avg_cost_per_node': summary.get('efficiency_metrics', {}).get('average_cost_per_node', 0),
                'avg_distance_per_node': summary.get('efficiency_metrics', {}).get('average_distance_per_node', 0),
                'success_rate': summary.get('assignment_success_rate', 0)
            }
            
            return analytics
            
        except Exception as e:
            print(f"[AnalyticsDashboard] Error processing analytics: {e}")
            return analytics
    
    def _get_waves_list(self, solution):
        """Extract waves from solution"""
        waves = []
        
        # Try waves array
        if 'waves' in solution and isinstance(solution['waves'], list):
            waves = solution['waves']
        else:
            # Try wave_X structure
            wave_keys = sorted([k for k in solution.keys() if k.startswith('wave_')])
            for key in wave_keys:
                waves.append(solution[key])
        
        return waves
    
    def _create_vehicle_distribution_pie(self, analytics):
        """Create pie chart - COMPACT SIZE"""
        try:
            group = self._create_group_box("Vehicle Type Distribution")
            
            efficiency = analytics['efficiency']
            routes = efficiency.get('all_routes', [])
            
            if not routes:
                group.layout().addWidget(QLabel("No data available"))
                self.container_layout.addWidget(group)
                return
            
            df = pd.DataFrame(routes)
            type_counts = df['type'].value_counts()
            
            fig = Figure(figsize=(8, 4), dpi=100, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            colors = ['#3b82f6', '#10b981', '#f97316']
            
            
            wedges, texts, autotexts = ax.pie(
                type_counts.values, 
                labels=type_counts.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 9, 'weight': 'bold'},
                pctdistance=0.75
            )
            
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_weight('bold')
            
            for text in texts:
                text.set_color('white')
                text.set_fontsize(9)
                text.set_weight('bold')
            
            ax.set_title('Vehicle Type Distribution', 
                        color='#ff6b35', fontsize=12, fontweight='bold', pad=10)
            
            fig.tight_layout(pad=0.8)
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(280)
            canvas.setMaximumHeight(280)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating vehicle distribution pie: {e}")
    
    def _create_efficiency_comparison_bar(self, analytics):
        """Create horizontal bar charts - FIXED LEFT MARGIN"""
        try:
            group = self._create_group_box("Efficiency Metrics")
            
            efficiency = analytics['efficiency']
            
            data = []
            for vtype in ['Drone', 'E-Truck', 'F-Truck']:
                if vtype in efficiency:
                    data.append({
                        'Vehicle': vtype,
                        'Cost': efficiency[vtype].get('avg_cost_per_node', 0),
                        'Distance': efficiency[vtype].get('avg_distance_per_node', 0)
                    })
            
            if not data:
                group.layout().addWidget(QLabel("No efficiency data available"))
                self.container_layout.addWidget(group)
                return
            
            df = pd.DataFrame(data)
            
            # Keep original size but fix margins
            fig = Figure(figsize=(8, 7), dpi=100, facecolor='#2a2a2a')
            
            # Cost comparison - TOP
            ax1 = fig.add_subplot(211)
            bars1 = ax1.barh(df['Vehicle'], df['Cost'],
                            color=['#3b82f6', '#10b981', '#f97316'],
                            height=0.5, edgecolor='white', linewidth=1.2)
            
            # Value labels inside bars
            for bar in bars1:
                width = bar.get_width()
                ax1.text(width/2, bar.get_y() + bar.get_height()/2,
                        f'${width:.1f}',
                        ha='center', va='center',
                        color='white', fontsize=8, fontweight='bold')
            
            ax1.set_xlabel('Cost per Node ', 
                          color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax1.set_title('Cost Efficiency', 
                         color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            ax1.set_facecolor('#1a1a1a')
            ax1.tick_params(colors='#ffffff', labelsize=8, pad=3)
            ax1.grid(axis='x', alpha=0.3, color='#555555', linestyle='--')
            ax1.set_xlim(0, max(df['Cost']) * 1.15)
            
            for spine in ax1.spines.values():
                spine.set_color('#555555')
            
            # Distance comparison - BOTTOM
            ax2 = fig.add_subplot(212)
            bars2 = ax2.barh(df['Vehicle'], df['Distance'],
                            color=['#3b82f6', '#10b981', '#f97316'],
                            height=0.5, edgecolor='white', linewidth=1.2)
            
            # Value labels inside bars
            for bar in bars2:
                width = bar.get_width()
                ax2.text(width/2, bar.get_y() + bar.get_height()/2,
                        f'{width:.1f}km',
                        ha='center', va='center',
                        color='white', fontsize=8, fontweight='bold')
            
            ax2.set_xlabel('Distance per Node (km)',
                          color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax2.set_title('Distance Efficiency',
                         color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            ax2.set_facecolor('#1a1a1a')
            ax2.tick_params(colors='#ffffff', labelsize=8, pad=3)
            ax2.grid(axis='x', alpha=0.3, color='#555555', linestyle='--')
            ax2.set_xlim(0, max(df['Distance']) * 1.15)
            
            for spine in ax2.spines.values():
                spine.set_color('#555555')
            
            # FIXED: More left margin to show y-axis labels
            fig.subplots_adjust(left=0.18, right=0.97, top=0.94, bottom=0.08, hspace=0.40)
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(550)
            canvas.setMaximumHeight(550)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating efficiency comparison: {e}")
    
    def _create_distance_histogram(self, analytics):
        """Create histogram - FIXED LEFT MARGIN"""
        try:
            group = self._create_group_box("Distance Distribution")
            
            efficiency = analytics['efficiency']
            routes = efficiency.get('all_routes', [])
            
            if not routes:
                group.layout().addWidget(QLabel("No route data available"))
                self.container_layout.addWidget(group)
                return
            
            df = pd.DataFrame(routes)
            df['distance_per_node'] = df['distance'] / df['nodes'].replace(0, 1)
            
            fig = Figure(figsize=(8, 4), dpi=100, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            sns.histplot(data=df, x='distance_per_node', bins=15, kde=True,
                        color='#8b5cf6', edgecolor='white', linewidth=0.8, 
                        alpha=0.7, ax=ax,
                        line_kws={'linewidth': 2, 'color': '#00ff88'})
            
            ax.set_xlabel('Distance per Node (km)', 
                         color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax.set_ylabel('Frequency', 
                         color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax.set_title('Delivery Distance Distribution', 
                        color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#ffffff', labelsize=7, pad=2)
            ax.grid(axis='both', alpha=0.3, color='#555555', linestyle='--')
            
            for spine in ax.spines.values():
                spine.set_color('#555555')
            
            # FIXED: More left margin for y-axis label
            fig.subplots_adjust(left=0.18, right=0.97, top=0.90, bottom=0.15)
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(380)
            canvas.setMaximumHeight(380)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating distance histogram: {e}")
    
    def _create_wave_metrics_line(self, analytics):
        """Create line plot - FIXED MARGINS"""
        try:
            group = self._create_group_box("Wave Performance")
            
            waves = analytics['waves']
            if not waves:
                group.layout().addWidget(QLabel("No wave data available"))
                self.container_layout.addWidget(group)
                return
            
            wave_data = []
            for wave_name, data in sorted(waves.items()):
                wave_data.append({
                    'Wave': wave_name.replace('wave_', 'W'),
                    'Distance': data['distance'],
                    'Cost': data['cost']
                })
            
            df = pd.DataFrame(wave_data)
            
            fig = Figure(figsize=(8, 4.5), dpi=100, facecolor='#2a2a2a')
            ax1 = fig.add_subplot(111)
            
            x_pos = range(len(df))
            
            # Plot Distance
            line1 = ax1.plot(x_pos, df['Distance'], 
                    marker='o', linewidth=2.5, markersize=8,
                    color='#3b82f6', label='Distance (km)',
                    markeredgecolor='white', markeredgewidth=1.5)
            
            # Create second y-axis
            ax2 = ax1.twinx()
            line2 = ax2.plot(x_pos, df['Cost'],
                    marker='s', linewidth=2.5, markersize=8,
                    color='#f97316', label='Cost ',
                    markeredgecolor='white', markeredgewidth=1.5)
            
            # Compact labels positioned smartly
            for i, (idx, row) in enumerate(df.iterrows()):
                ax1.annotate(f"{row['Distance']:.1f}", 
                           xy=(i, row['Distance']), 
                           xytext=(0, 10),
                           textcoords='offset points',
                           ha='center', va='bottom',
                           color='white', fontsize=7, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2',
                                   facecolor='#3b82f6', alpha=0.85,
                                   edgecolor='white', linewidth=0.5))
            
            for i, (idx, row) in enumerate(df.iterrows()):
                ax2.annotate(f"${row['Cost']:.0f}",
                           xy=(i, row['Cost']),
                           xytext=(0, -10),
                           textcoords='offset points',
                           ha='center', va='top',
                           color='white', fontsize=7, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.2',
                                   facecolor='#f97316', alpha=0.85,
                                   edgecolor='white', linewidth=0.5))
            
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels(df['Wave'], fontsize=8)
            ax1.set_xlabel('Wave', color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax1.set_ylabel('Distance (km)', color='#3b82f6', fontsize=9, fontweight='bold', labelpad=5)
            ax2.set_ylabel('Cost ', color='#f97316', fontsize=9, fontweight='bold', labelpad=5)
            
            ax1.set_title('Distance & Cost Trends', 
                         color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            
            ax1.set_ylim(0, max(df['Distance']) * 1.3)
            ax2.set_ylim(0, max(df['Cost']) * 1.3)
            
            ax1.set_facecolor('#1a1a1a')
            ax1.tick_params(colors='#ffffff', labelsize=7, pad=2)
            ax2.tick_params(colors='#ffffff', labelsize=7, pad=2)
            ax1.tick_params(axis='y', labelcolor='#3b82f6')
            ax2.tick_params(axis='y', labelcolor='#f97316')
            ax1.grid(alpha=0.3, color='#555555', linestyle='--')
            
            for spine in ax1.spines.values():
                spine.set_color('#555555')
            for spine in ax2.spines.values():
                spine.set_color('#555555')
            
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels,
                      loc='upper left', fontsize=8,
                      facecolor='#2a2a2a', edgecolor='#555555',
                      framealpha=0.95)
            
            # FIXED: More space on right for Cost y-axis label
            fig.subplots_adjust(left=0.15, right=0.85, top=0.90, bottom=0.15)
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(450)
            canvas.setMaximumHeight(450)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating wave metrics: {e}")
    
    def _create_cost_analysis_box(self, analytics):
        """Create box plot - FIXED LEFT MARGIN"""
        try:
            group = self._create_group_box("Cost Distribution")
            
            efficiency = analytics['efficiency']
            routes = efficiency.get('all_routes', [])
            
            if not routes:
                group.layout().addWidget(QLabel("No route data available"))
                self.container_layout.addWidget(group)
                return
            
            df = pd.DataFrame(routes)
            df['cost_per_node'] = df['cost'] / df['nodes'].replace(0, 1)
            df = df[df['cost_per_node'] > 0]
            
            if len(df) == 0:
                group.layout().addWidget(QLabel("No valid cost data"))
                self.container_layout.addWidget(group)
                return
            
            fig = Figure(figsize=(8, 4.5), dpi=100, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            vehicle_types = ['Drone', 'E-Truck', 'F-Truck']
            data_to_plot = [df[df['type'] == vt]['cost_per_node'].values 
                           for vt in vehicle_types if vt in df['type'].values]
            labels = [vt for vt in vehicle_types if vt in df['type'].values]
            
            bp = ax.boxplot(data_to_plot, labels=labels,
                           patch_artist=True, widths=0.5,
                           showmeans=True,
                           meanprops=dict(marker='D', markerfacecolor='yellow',
                                        markeredgecolor='black', markersize=6))
            
            colors_dict = {'Drone': '#3b82f6', 'E-Truck': '#10b981', 'F-Truck': '#f97316'}
            for i, label in enumerate(labels):
                bp['boxes'][i].set_facecolor(colors_dict[label])
                bp['boxes'][i].set_alpha(0.7)
                bp['boxes'][i].set_linewidth(1.2)
                bp['boxes'][i].set_edgecolor('white')
                bp['medians'][i].set_color('yellow')
                bp['medians'][i].set_linewidth(2)
            
            for i, vtype in enumerate(labels):
                y_data = df[df['type'] == vtype]['cost_per_node'].values
                x_data = np.random.normal(i+1, 0.04, size=len(y_data))
                ax.scatter(x_data, y_data, alpha=0.3, s=20,
                          color='white', edgecolor='black', linewidth=0.3)
            
            for i, label in enumerate(labels):
                median_val = np.median(df[df['type'] == label]['cost_per_node'])
                ax.text(i+1.2, median_val, f'${median_val:.1f}',
                       ha='left', va='center',
                       color='white', fontsize=7, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.25',
                               facecolor='#ff6b35', alpha=0.85,
                               edgecolor='white', linewidth=0.8))
            
            ax.set_xlabel('Vehicle Type', color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax.set_ylabel('Cost per Node ', color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax.set_title('Cost Distribution',
                        color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#ffffff', labelsize=8, pad=2)
            ax.grid(axis='y', alpha=0.3, color='#555555', linestyle='--')
            ax.set_ylim(bottom=0)
            
            for spine in ax.spines.values():
                spine.set_color('#555555')
            
            # FIXED: More left margin for y-axis label
            fig.subplots_adjust(left=0.18, right=0.97, top=0.90, bottom=0.15)
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(420)
            canvas.setMaximumHeight(420)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating cost box plot: {e}")
    
    def _create_capacity_utilization_heatmap(self, analytics):
        """Create heatmap - FIXED MARGINS"""
        try:
            group = self._create_group_box("Capacity Utilization")
            
            efficiency = analytics['efficiency']
            routes = efficiency.get('all_routes', [])
            
            truck_routes = [r for r in routes if r['type'] in ['E-Truck','F-Truck']
                          and 'weight_util' in r and 'volume_util' in r]
            
            if not truck_routes:
                group.layout().addWidget(QLabel("No capacity data"))
                self.container_layout.addWidget(group)
                return
            
            df = pd.DataFrame(truck_routes)
            util_data = df.groupby('type')[['weight_util', 'volume_util']].mean()
            util_data = util_data.T
            util_data.index = ['Weight %', 'Volume %']
            
            fig = Figure(figsize=(8, 4), dpi=100, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            im = ax.imshow(util_data.values, cmap='RdYlGn', aspect='auto',
                          vmin=0, vmax=100)
            
            for i in range(len(util_data.index)):
                for j in range(len(util_data.columns)):
                    value = util_data.values[i, j]
                    text = ax.text(j, i, f'{value:.1f}%',
                                 ha="center", va="center",
                                 color="black", fontsize=12, fontweight='bold')
            
            ax.set_xticks(range(len(util_data.columns)))
            ax.set_yticks(range(len(util_data.index)))
            ax.set_xticklabels(util_data.columns, fontsize=9, fontweight='bold', color='white')
            ax.set_yticklabels(util_data.index, fontsize=9, fontweight='bold', color='white')
            
            ax.set_xlabel('Vehicle Type', color='#ffffff', fontsize=9, fontweight='bold', labelpad=8)
            ax.set_ylabel('Metric', color='#ffffff', fontsize=9, fontweight='bold', labelpad=8)
            ax.set_title('Capacity Utilization (%)',
                        color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            
            cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
            cbar.set_label('Utilization %', color='white', fontsize=8, fontweight='bold')
            cbar.ax.tick_params(colors='white', labelsize=7)
            cbar.outline.set_edgecolor('#555555')
            cbar.outline.set_linewidth(1.2)
            
            ax.set_facecolor('#1a1a1a')
            fig.patch.set_facecolor('#2a2a2a')
            
            # FIXED: More left margin for Weight % and Volume % labels
            fig.subplots_adjust(left=0.22, right=0.88, top=0.88, bottom=0.15)
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(350)
            canvas.setMaximumHeight(350)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating capacity heatmap: {e}")
        
    def _create_noise_analysis_bar(self, analytics):
        """Create noise analysis bar chart - FIXED LABEL POSITIONING"""
        try:
            group = self._create_group_box("Noise Analysis")
            
            waves = analytics['waves']
            if not waves:
                group.layout().addWidget(QLabel("No wave data available"))
                self.container_layout.addWidget(group)
                return
            
            # Calculate noise levels for each wave
            noise_data = []
            NOISE_CONSTANT = 90  # dB per drone
            
            for wave_name, data in sorted(waves.items()):
                num_drones = data.get('drones', 0)
                noise_level = num_drones * NOISE_CONSTANT
                noise_data.append({
                    'Wave': wave_name.replace('wave_', 'Wave '),
                    'Drones': num_drones,
                    'Noise': noise_level
                })
            
            if not noise_data:
                group.layout().addWidget(QLabel("No noise data available"))
                self.container_layout.addWidget(group)
                return
            
            df = pd.DataFrame(noise_data)
            
            fig = Figure(figsize=(8, 4.5), dpi=100, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            # Create gradient colors based on noise levels
            colors = []
            max_noise = df['Noise'].max() if df['Noise'].max() > 0 else 1
            for noise in df['Noise']:
                if noise == 0:
                    colors.append('#2a2a2a')  # Dark for no noise
                elif noise < max_noise * 0.33:
                    colors.append('#10b981')  # Green for low
                elif noise < max_noise * 0.66:
                    colors.append('#f59e0b')  # Yellow for medium
                else:
                    colors.append('#ef4444')  # Red for high
            
            bars = ax.bar(range(len(df)), df['Noise'],
                        color=colors, edgecolor='white', linewidth=1.5,
                        width=0.6, alpha=0.9)
            
            # FIXED: Better label positioning - above bar with proper offset
            for i, (bar, row) in enumerate(zip(bars, df.itertuples())):
                height = bar.get_height()
                if height > 0:
                    # Position label above the bar
                    label_y = height + (max_noise * 0.05)  # 5% offset above bar
                    
                    ax.text(bar.get_x() + bar.get_width()/2, label_y,
                        f'{int(height)} dB',
                        ha='center', va='bottom',
                        color='white', fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3',
                                facecolor='#1a1a1a', alpha=0.85,
                                edgecolor='white', linewidth=1))
                    
                    # Add drone count inside the bar
                    if height > 20:  # Only if bar is tall enough
                        ax.text(bar.get_x() + bar.get_width()/2, height/2,
                            f'{row.Drones} drone{"s" if row.Drones != 1 else ""}',
                            ha='center', va='center',
                            color='white', fontsize=8, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.25',
                                    facecolor='black', alpha=0.6,
                                    edgecolor='none'))
            
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['Wave'], fontsize=9, fontweight='bold')
            ax.set_xlabel('Wave', color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax.set_ylabel('Noise Level (dB)', color='#ffffff', fontsize=9, fontweight='bold', labelpad=5)
            ax.set_title('Noise Levels by Wave (90 dB per Drone)',
                        color='#ff6b35', fontsize=11, fontweight='bold', pad=15)
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#ffffff', labelsize=8, pad=2)
            ax.grid(axis='y', alpha=0.3, color='#555555', linestyle='--')
            
            # Add reference lines for noise levels
            if df['Noise'].max() > 0:
                max_val = df['Noise'].max()
                if max_val >= 270:
                    ax.axhline(y=270, color='#ef4444', linestyle='--', linewidth=1.5, alpha=0.5, label='High Noise (270+ dB)')
                if max_val >= 180:
                    ax.axhline(y=180, color='#f59e0b', linestyle='--', linewidth=1.5, alpha=0.5, label='Medium Noise (180+ dB)')
                
                # Only show legend if we have reference lines
                if max_val >= 180:
                    ax.legend(loc='upper right', fontsize=7, facecolor='#2a2a2a', 
                            edgecolor='#555555', framealpha=0.9)
            
            # FIXED: Set y-limit to accommodate labels above bars (add 15% extra space)
            ax.set_ylim(0, df['Noise'].max() * 1.25 if df['Noise'].max() > 0 else 100)
            
            for spine in ax.spines.values():
                spine.set_color('#555555')
            
            # FIXED: More left margin for y-axis label
            fig.subplots_adjust(left=0.18, right=0.97, top=0.88, bottom=0.15)
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(420)
            canvas.setMaximumHeight(420)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating noise analysis bar chart: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_summary_section(self, analytics):
        """Create summary metrics section - STYLED BOARD"""
        try:
            group = self._create_group_box("Overall Summary")
            
            summary = analytics['summary']
            
            metrics_html = f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; 
                        border: 2px solid #3a3a3a; max-width: 100%;'>
                <table style='width:100%; color:#ffffff; border-collapse: separate; 
                              border-spacing: 0 10px; font-size: 14px;'>
                    <tr style='background: linear-gradient(135deg, #2d2d2d 0%, #252525 100%);'>
                        <td style='padding: 15px 20px; font-weight: bold; border-radius: 8px 0 0 8px; 
                                   border-left: 4px solid #3b82f6;'>
                            Total Distance
                        </td>
                        <td style='padding: 15px 20px; color:#3b82f6; text-align: right; 
                                   font-weight: bold; font-size: 16px; border-radius: 0 8px 8px 0;'>
                            {summary['total_distance']:.2f} km
                        </td>
                    </tr>
                    <tr style='background: linear-gradient(135deg, #2d2d2d 0%, #252525 100%);'>
                        <td style='padding: 15px 20px; font-weight: bold; border-radius: 8px 0 0 8px;
                                   border-left: 4px solid #10b981;'>
                            Total Cost
                        </td>
                        <td style='padding: 15px 20px; color:#10b981; text-align: right; 
                                   font-weight: bold; font-size: 16px; border-radius: 0 8px 8px 0;'>
                            {summary['total_cost']:.2f}
                        </td>
                    </tr>
                    <tr style='background: linear-gradient(135deg, #2d2d2d 0%, #252525 100%);'>
                        <td style='padding: 15px 20px; font-weight: bold; border-radius: 8px 0 0 8px;
                                   border-left: 4px solid #8b5cf6;'>
                            Total Nodes
                        </td>
                        <td style='padding: 15px 20px; color:#8b5cf6; text-align: right; 
                                   font-weight: bold; font-size: 16px; border-radius: 0 8px 8px 0;'>
                            {summary['total_nodes']}
                        </td>
                    </tr>
                    <tr style='background: linear-gradient(135deg, #2d2d2d 0%, #252525 100%);'>
                        <td style='padding: 15px 20px; font-weight: bold; border-radius: 8px 0 0 8px;
                                   border-left: 4px solid #f97316;'>
                            Avg Cost per Node
                        </td>
                        <td style='padding: 15px 20px; color:#f97316; text-align: right; 
                                   font-weight: bold; font-size: 16px; border-radius: 0 8px 8px 0;'>
                            {summary['avg_cost_per_node']:.2f}
                        </td>
                    </tr>
                    <tr style='background: linear-gradient(135deg, #2d2d2d 0%, #252525 100%);'>
                        <td style='padding: 15px 20px; font-weight: bold; border-radius: 8px 0 0 8px;
                                   border-left: 4px solid #10b981;'>
                            Success Rate
                        </td>
                        <td style='padding: 15px 20px; color:#10b981; text-align: right; 
                                   font-weight: bold; font-size: 16px; border-radius: 0 8px 8px 0;'>
                            {summary['success_rate']:.1f}%
                        </td>
                    </tr>
                </table>
            </div>
            """
            
            label = QLabel(metrics_html)
            label.setStyleSheet("background-color: transparent;")
            label.setWordWrap(True)
            group.layout().addWidget(label)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating summary section: {e}")
    
    def _create_group_box(self, title):
        """Create styled group box - FIT TO SIDEBAR WIDTH"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #ff6b35;
                background-color: #2a2a2a;
                padding: 20px;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                margin-top: 10px;
                min-width: 350px;
                max-width: 450px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(15, 25, 15, 15)
        layout.setSpacing(10)
        return group
    
    def show_waiting_message(self):
        """Show waiting message"""
        try:
            while self.container_layout.count():
                item = self.container_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            
            waiting_group = self._create_group_box("Waiting for Solution Data")
            label = QLabel("Waiting for backend solution.json...\n\n"
                          "Backend optimization is processing your data.\n"
                          "Charts will appear automatically once data is ready.")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                color: #ffffff; 
                padding: 35px; 
                font-size: 13px;
                font-weight: bold;
                line-height: 1.5;
            """)
            waiting_group.layout().addWidget(label)
            self.container_layout.addWidget(waiting_group)
            self.container_layout.addStretch()
            
        except Exception as e:
            print(f"Error showing waiting message: {e}")
    
    def refresh_data(self):
        """Manual refresh"""
        self.load_solution_data()
    
    def closeEvent(self, event):
        """Handle close"""
        self._widget_destroyed = True
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)
    
    def deleteLater(self):
        """Override deleteLater"""
        self._widget_destroyed = True
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().deleteLater()