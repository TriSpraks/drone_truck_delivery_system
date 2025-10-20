"""
Analytics Dashboard Widget - LOADS LIVE SOLUTION.JSON FROM BACKEND
Displays all feasible delivery performance analytics graphs
"""
import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


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
            self.container_layout.setSpacing(20)
            
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
        """Continuously check for updated solution.json"""
        if self._widget_destroyed:
            return
        
        try:
            solution = self._load_solution_file()
            if solution:
                solution_str = json.dumps(solution, sort_keys=True)
                solution_hash = hash(solution_str)
                
                if solution_hash != self.last_solution_hash:
                    self.last_solution_hash = solution_hash
                    self.current_solution = solution
                    self.refresh_all_graphs()
        except Exception as e:
            pass  # Silent fail for polling
    
    def load_solution_data(self):
        """Load solution.json from backend folder"""
        try:
            if self._widget_destroyed:
                return
            
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
        """Load solution.json from backend folder"""
        try:
            backend_folder = self.get_backend_folder_path()
            if not backend_folder:
                return None
            
            solution_file = os.path.join(backend_folder, 'solution.json')
            if os.path.exists(solution_file):
                with open(solution_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[AnalyticsDashboard] Error reading solution file: {e}")
        
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
            
            # Create graph sections
            self._create_efficiency_section(analytics)
            self._create_wave_metrics_section(analytics)
            self._create_distribution_section(analytics)
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
    
    def _create_efficiency_section(self, analytics):
        """Create efficiency metrics section"""
        try:
            group = self._create_group_box("Comparison of Efficiency Metrics (Drone vs. Truck)")
            
            efficiency = analytics['efficiency']
            if not efficiency.get('Drone'):
                group.layout().addWidget(QLabel("No efficiency data available"))
                self.container_layout.addWidget(group)
                return
            
            # Average Cost per Delivery
            fig = Figure(figsize=(12, 4), dpi=80, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            types = []
            costs = []
            for vtype in ['Drone', 'E-Truck', 'F-Truck']:
                if vtype in efficiency:
                    types.append(vtype)
                    costs.append(efficiency[vtype].get('avg_cost_per_node', 0))
            
            bars = ax.bar(types, costs, color=['#3b82f6', '#10b981', '#f97316'], width=0.6)
            ax.set_ylabel('Avg Cost per Node ($)', color='#cccccc', fontsize=11, fontweight='bold')
            ax.set_title('Average Cost per Delivery', color='#ff6b35', fontsize=12, fontweight='bold', pad=15)
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#cccccc', labelsize=10)
            ax.grid(axis='y', alpha=0.3, color='#444444', linestyle='--')
            for spine in ax.spines.values():
                spine.set_color('#444444')
            fig.tight_layout()
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(280)
            group.layout().addWidget(canvas)
            
            # Average Distance per Delivery
            fig2 = Figure(figsize=(12, 4), dpi=80, facecolor='#2a2a2a')
            ax2 = fig2.add_subplot(111)
            
            distances = []
            for vtype in types:
                distances.append(efficiency[vtype].get('avg_distance_per_node', 0))
            
            ax2.bar(types, distances, color=['#3b82f6', '#10b981', '#f97316'], width=0.6)
            ax2.set_ylabel('Avg Distance per Node (km)', color='#cccccc', fontsize=11, fontweight='bold')
            ax2.set_title('Average Distance per Delivery', color='#ff6b35', fontsize=12, fontweight='bold', pad=15)
            ax2.set_facecolor('#1a1a1a')
            ax2.tick_params(colors='#cccccc', labelsize=10)
            ax2.grid(axis='y', alpha=0.3, color='#444444', linestyle='--')
            for spine in ax2.spines.values():
                spine.set_color('#444444')
            fig2.tight_layout()
            
            canvas2 = FigureCanvas(fig2)
            canvas2.setMinimumHeight(280)
            group.layout().addWidget(canvas2)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating efficiency section: {e}")
    
    def _create_wave_metrics_section(self, analytics):
        """Create wave metrics section"""
        try:
            group = self._create_group_box("Breakdown of Total Delivery Metrics (Waves)")
            
            waves = analytics['waves']
            if not waves:
                group.layout().addWidget(QLabel("No wave data available"))
                self.container_layout.addWidget(group)
                return
            
            fig = Figure(figsize=(12, 5), dpi=80, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            wave_names = list(waves.keys())
            distances = [waves[w]['distance'] for w in wave_names]
            costs = [waves[w]['cost'] for w in wave_names]
            
            x = range(len(wave_names))
            ax.bar([i - 0.2 for i in x], distances, width=0.4, label='Distance (km)', color='#3b82f6', edgecolor='#555555')
            ax2 = ax.twinx()
            ax2.plot([i + 0.2 for i in x], costs, 'o-', label='Cost ($)', color='#f97316', linewidth=2.5, markersize=10)
            
            ax.set_ylabel('Distance (km)', color='#cccccc', fontsize=11, fontweight='bold')
            ax2.set_ylabel('Cost ($)', color='#cccccc', fontsize=11, fontweight='bold')
            ax.set_title('Total Distance & Cost per Wave', color='#ff6b35', fontsize=12, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(wave_names, fontsize=10)
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#cccccc', labelsize=10)
            ax2.tick_params(colors='#cccccc', labelsize=10)
            ax.grid(axis='y', alpha=0.3, color='#444444', linestyle='--')
            for spine in ax.spines.values():
                spine.set_color('#444444')
            for spine in ax2.spines.values():
                spine.set_color('#444444')
            
            # Add legend
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9, facecolor='#2a2a2a', edgecolor='#555555')
            
            fig.tight_layout()
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(320)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating wave metrics section: {e}")
    
    def _create_distribution_section(self, analytics):
        """Create distribution analysis section"""
        try:
            group = self._create_group_box("Distribution-focused Analysis")
            
            efficiency = analytics['efficiency']
            routes = efficiency.get('all_routes', [])
            
            if not routes:
                group.layout().addWidget(QLabel("No route data available"))
                self.container_layout.addWidget(group)
                return
            
            distances = [r['distance'] / max(1, r['nodes']) for r in routes]
            
            fig = Figure(figsize=(12, 4.5), dpi=80, facecolor='#2a2a2a')
            ax = fig.add_subplot(111)
            
            n, bins, patches = ax.hist(distances, bins=8, color='#8b5cf6', edgecolor='#cccccc', alpha=0.85)
            ax.set_xlabel('Distance per Node (km)', color='#cccccc', fontsize=11, fontweight='bold')
            ax.set_ylabel('Frequency', color='#cccccc', fontsize=11, fontweight='bold')
            ax.set_title('Distribution of Delivery Distances', color='#ff6b35', fontsize=12, fontweight='bold', pad=15)
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#cccccc', labelsize=10)
            ax.grid(axis='y', alpha=0.3, color='#444444', linestyle='--')
            for spine in ax.spines.values():
                spine.set_color('#444444')
            fig.tight_layout()
            
            canvas = FigureCanvas(fig)
            canvas.setMinimumHeight(300)
            group.layout().addWidget(canvas)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating distribution section: {e}")
    
    def _create_summary_section(self, analytics):
        """Create summary metrics section"""
        try:
            group = self._create_group_box("Overall Summary Metrics")
            
            summary = analytics['summary']
            
            metrics_html = f"""
            <table style='width:100%; color:#cccccc; background-color:#1a1a1a; border-collapse: collapse;'>
                <tr style='border-bottom: 1px solid #444444;'>
                    <td style='padding: 12px; font-weight: bold;'>Total Distance</td>
                    <td style='padding: 12px; color:#3b82f6; text-align: right; font-weight: bold;'>{summary['total_distance']:.2f} km</td>
                </tr>
                <tr style='border-bottom: 1px solid #444444;'>
                    <td style='padding: 12px; font-weight: bold;'>Total Cost</td>
                    <td style='padding: 12px; color:#10b981; text-align: right; font-weight: bold;'>${summary['total_cost']:.2f}</td>
                </tr>
                <tr style='border-bottom: 1px solid #444444;'>
                    <td style='padding: 12px; font-weight: bold;'>Total Nodes</td>
                    <td style='padding: 12px; color:#8b5cf6; text-align: right; font-weight: bold;'>{summary['total_nodes']}</td>
                </tr>
                <tr style='border-bottom: 1px solid #444444;'>
                    <td style='padding: 12px; font-weight: bold;'>Avg Cost/Node</td>
                    <td style='padding: 12px; color:#f97316; text-align: right; font-weight: bold;'>${summary['avg_cost_per_node']:.2f}</td>
                </tr>
                <tr>
                    <td style='padding: 12px; font-weight: bold;'>Success Rate</td>
                    <td style='padding: 12px; color:#10b981; text-align: right; font-weight: bold;'>{summary['success_rate']:.1f}%</td>
                </tr>
            </table>
            """
            
            label = QLabel(metrics_html)
            label.setStyleSheet("background-color: #1a1a1a; padding: 0px; border-radius: 0px;")
            group.layout().addWidget(label)
            
            self.container_layout.addWidget(group)
            
        except Exception as e:
            print(f"Error creating summary section: {e}")
    
    def _create_group_box(self, title):
        """Create styled group box"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #ff6b35;
                background-color: #2a2a2a;
                padding: 15px;
                border: 1px solid #444444;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        return group
    
    def show_waiting_message(self):
        """Show waiting message"""
        try:
            while self.container_layout.count():
                self.container_layout.takeAt(0).widget().deleteLater()
            
            waiting_group = self._create_group_box("Waiting for Solution Data")
            label = QLabel("Waiting for backend solution.json...\n\nBackend optimization is processing")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #cccccc; padding: 30px;")
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