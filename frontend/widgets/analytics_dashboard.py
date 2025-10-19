"""
Analytics Dashboard Widget - PyQt5 Implementation
Displays delivery performance analytics from solution.json

FILE LOCATION: frontend/widgets/analytics_dashboard.py
"""
import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                           QPushButton, QLabel, QTabWidget, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
import pyqtgraph as pg


class AnalyticsDashboard(QWidget):
    """Display delivery performance analytics"""
    
    data_refreshed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.current_solution = None
        self.current_wave = None
        self._widget_destroyed = False
        
        self.init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_data)
        self.refresh_timer.start(3000)  # Refresh every 3 seconds
        
        # Initial load
        QTimer.singleShot(500, self.load_solution_data)
    
    def init_ui(self):
        """Initialize UI with tabs"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)
            
            # Create tab widget
            self.tabs = QTabWidget()
            self.tabs.setStyleSheet("""
                QTabWidget::pane { border: none; }
                QTabBar::tab {
                    background-color: #2a2a2a;
                    color: #cccccc;
                    padding: 8px 15px;
                    margin-right: 2px;
                    border: 1px solid #404040;
                }
                QTabBar::tab:selected {
                    background-color: #ff6b35;
                    color: white;
                    border: 1px solid #ff6b35;
                }
                QTabBar::tab:hover {
                    background-color: #3a3a3a;
                }
            """)
            
            # Tab 1: Cost Analysis
            cost_tab = self.create_cost_tab()
            self.tabs.addTab(cost_tab, "💰 Cost")
            
            # Tab 2: Distance Analysis
            distance_tab = self.create_distance_tab()
            self.tabs.addTab(distance_tab, "📍 Distance")
            
            # Tab 3: Capacity
            capacity_tab = self.create_capacity_tab()
            self.tabs.addTab(capacity_tab, "📦 Capacity")
            
            # Tab 4: Summary
            summary_tab = self.create_summary_tab()
            self.tabs.addTab(summary_tab, "📋 Summary")
            
            layout.addWidget(self.tabs)
            
        except Exception as e:
            print(f"Error initializing analytics UI: {e}")
            import traceback
            traceback.print_exc()
            self._widget_destroyed = True
    
    def create_cost_tab(self):
        """Create cost analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Average Cost per Delivery")
        title.setStyleSheet("color: #ff6b35; font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        # Plot widget
        self.cost_plot = pg.PlotWidget()
        self.cost_plot.setBackground('#1a1a1a')
        self.cost_plot.setLabel('left', 'Cost ($)', color='#aaa')
        self.cost_plot.setLabel('bottom', 'Vehicle', color='#aaa')
        self.cost_plot.setTitle("Average Cost per Delivery by Vehicle", color='#aaa')
        self.cost_plot.getAxis('left').setPen(pg.mkPen('#555'))
        self.cost_plot.getAxis('bottom').setPen(pg.mkPen('#555'))
        layout.addWidget(self.cost_plot)
        
        # Stats
        self.cost_stats = QLabel("Loading...")
        self.cost_stats.setStyleSheet("color: #cccccc; font-size: 11px; padding: 10px;")
        layout.addWidget(self.cost_stats)
        
        return widget
    
    def create_distance_tab(self):
        """Create distance analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Average Distance per Delivery")
        title.setStyleSheet("color: #ff6b35; font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        # Plot widget
        self.distance_plot = pg.PlotWidget()
        self.distance_plot.setBackground('#1a1a1a')
        self.distance_plot.setLabel('left', 'Distance (km)', color='#aaa')
        self.distance_plot.setLabel('bottom', 'Vehicle', color='#aaa')
        self.distance_plot.setTitle("Average Distance per Delivery by Vehicle", color='#aaa')
        self.distance_plot.getAxis('left').setPen(pg.mkPen('#555'))
        self.distance_plot.getAxis('bottom').setPen(pg.mkPen('#555'))
        layout.addWidget(self.distance_plot)
        
        # Stats
        self.distance_stats = QLabel("Loading...")
        self.distance_stats.setStyleSheet("color: #cccccc; font-size: 11px; padding: 10px;")
        layout.addWidget(self.distance_stats)
        
        return widget
    
    def create_capacity_tab(self):
        """Create capacity utilization tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Truck Capacity Utilization")
        title.setStyleSheet("color: #ff6b35; font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title)
        
        # Plot widget
        self.capacity_plot = pg.PlotWidget()
        self.capacity_plot.setBackground('#1a1a1a')
        self.capacity_plot.setLabel('left', 'Utilization (%)', color='#aaa')
        self.capacity_plot.setLabel('bottom', 'Vehicle', color='#aaa')
        self.capacity_plot.setTitle("Weight & Volume Utilization", color='#aaa')
        self.capacity_plot.getAxis('left').setPen(pg.mkPen('#555'))
        self.capacity_plot.getAxis('bottom').setPen(pg.mkPen('#555'))
        layout.addWidget(self.capacity_plot)
        
        # Stats
        self.capacity_stats = QLabel("Loading...")
        self.capacity_stats.setStyleSheet("color: #cccccc; font-size: 11px; padding: 10px;")
        layout.addWidget(self.capacity_stats)
        
        return widget
    
    def create_summary_tab(self):
        """Create summary statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Scrollable summary
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 10px; background: #2a2a2a; }
            QScrollBar::handle:vertical { background: #555; border-radius: 5px; }
        """)
        
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # Overall metrics
        overall_group = QGroupBox("Overall Metrics")
        overall_group.setStyleSheet("""
            QGroupBox {
                color: #ff6b35;
                border: 1px solid #ff6b35;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        overall_layout = QGridLayout(overall_group)
        
        self.summary_total_points = QLabel("Total Deliveries: 0")
        self.summary_total_dist = QLabel("Total Distance: 0.0 km")
        self.summary_total_cost = QLabel("Total Cost: $0.00")
        self.summary_total_weight = QLabel("Total Weight: 0.0 kg")
        
        for label in [self.summary_total_points, self.summary_total_dist, 
                      self.summary_total_cost, self.summary_total_weight]:
            label.setStyleSheet("color: #cccccc; padding: 5px;")
        
        overall_layout.addWidget(self.summary_total_points, 0, 0)
        overall_layout.addWidget(self.summary_total_dist, 0, 1)
        overall_layout.addWidget(self.summary_total_cost, 1, 0)
        overall_layout.addWidget(self.summary_total_weight, 1, 1)
        
        summary_layout.addWidget(overall_group)
        
        # Vehicle breakdown
        vehicle_group = QGroupBox("Vehicle Type Breakdown")
        vehicle_group.setStyleSheet("""
            QGroupBox {
                color: #ff6b35;
                border: 1px solid #ff6b35;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        vehicle_layout = QVBoxLayout(vehicle_group)
        
        self.summary_vehicles = QLabel("Loading...")
        self.summary_vehicles.setStyleSheet("color: #cccccc; font-size: 11px; padding: 5px;")
        self.summary_vehicles.setWordWrap(True)
        vehicle_layout.addWidget(self.summary_vehicles)
        
        summary_layout.addWidget(vehicle_group)
        summary_layout.addStretch()
        
        scroll.setWidget(summary_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def load_solution_data(self):
        """Load solution data from file or parent"""
        try:
            solution = None
            
            # Try parent first
            if self.parent_window and hasattr(self.parent_window, 'solution'):
                solution = self.parent_window.solution
            
            # Try file
            if not solution:
                backend_folder = self.get_backend_folder()
                if backend_folder:
                    solution_file = os.path.join(backend_folder, 'solution.json')
                    if os.path.exists(solution_file):
                        with open(solution_file, 'r') as f:
                            solution = json.load(f)
            
            if solution:
                self.current_solution = solution
                waves = solution.get('waves', [])
                if not waves and any(k.startswith('wave_') for k in solution.keys()):
                    waves = [solution[k] for k in sorted([k for k in solution.keys() if k.startswith('wave_')])]
                
                if waves:
                    self.current_wave = waves[0]
                    self.update_all_charts()
        except Exception as e:
            print(f"Error loading solution data: {e}")
    
    def auto_refresh_data(self):
        """Periodically refresh data"""
        if not self._widget_destroyed:
            self.load_solution_data()
    
    def refresh_data(self):
        """Manual refresh"""
        self.load_solution_data()
    
    def update_all_charts(self):
        """Update all charts with current data"""
        if not self.current_wave:
            return
        
        try:
            self.update_cost_chart()
            self.update_distance_chart()
            self.update_capacity_chart()
            self.update_summary()
        except Exception as e:
            print(f"Error updating charts: {e}")
    
    def update_cost_chart(self):
        """Update cost per delivery chart"""
        try:
            drones = self.current_wave.get('drones', [])
            trucks = self.current_wave.get('trucks', [])
            
            names = []
            costs = []
            colors = []
            
            for i, drone in enumerate(drones):
                avg_cost = drone['cost'] / len(drone['node_ids'])
                names.append(f"D{i+1}")
                costs.append(avg_cost)
                colors.append('#3b82f6')
            
            for truck in trucks:
                avg_cost = truck['cost'] / len(truck['node_ids'])
                vehicle_id = truck.get('vehicle_id', 'Truck')
                if 'E_' in vehicle_id:
                    names.append("ET")
                    colors.append('#10b981')
                else:
                    names.append("FT")
                    colors.append('#f97316')
                costs.append(avg_cost)
            
            # Clear and replot
            self.cost_plot.clear()
            x = list(range(len(names)))
            self.cost_plot.plot(x, costs, pen=None, symbol='o', symbolSize=10, 
                              symbolBrush=pg.mkBrush('#ff6b35'))
            self.cost_plot.setXRange(-0.5, len(names) - 0.5)
            
            # Update stats label
            avg_all = sum(costs) / len(costs) if costs else 0
            stats_text = f"Average: ${avg_all:.2f}/delivery | Min: ${min(costs):.2f} | Max: ${max(costs):.2f}"
            self.cost_stats.setText(stats_text)
        except Exception as e:
            print(f"Error updating cost chart: {e}")
    
    def update_distance_chart(self):
        """Update distance per delivery chart"""
        try:
            drones = self.current_wave.get('drones', [])
            trucks = self.current_wave.get('trucks', [])
            
            names = []
            distances = []
            
            for i, drone in enumerate(drones):
                avg_dist = drone['distance'] / len(drone['node_ids'])
                names.append(f"D{i+1}")
                distances.append(avg_dist)
            
            for truck in trucks:
                avg_dist = truck['distance'] / len(truck['node_ids'])
                vehicle_id = truck.get('vehicle_id', 'Truck')
                if 'E_' in vehicle_id:
                    names.append("ET")
                else:
                    names.append("FT")
                distances.append(avg_dist)
            
            # Clear and replot
            self.distance_plot.clear()
            x = list(range(len(names)))
            self.distance_plot.plot(x, distances, pen=None, symbol='s', symbolSize=10,
                                   symbolBrush=pg.mkBrush('#10b981'))
            self.distance_plot.setXRange(-0.5, len(names) - 0.5)
            
            # Update stats
            avg_all = sum(distances) / len(distances) if distances else 0
            stats_text = f"Average: {avg_all:.2f}km/delivery | Min: {min(distances):.2f}km | Max: {max(distances):.2f}km"
            self.distance_stats.setText(stats_text)
        except Exception as e:
            print(f"Error updating distance chart: {e}")
    
    def update_capacity_chart(self):
        """Update capacity utilization chart"""
        try:
            trucks = self.current_wave.get('trucks', [])
            
            names = []
            weights = []
            volumes = []
            
            for truck in trucks:
                vehicle_id = truck.get('vehicle_id', 'Truck')
                if 'E_' in vehicle_id:
                    names.append("E-Truck")
                else:
                    names.append("F-Truck")
                
                capacity = truck.get('capacity_utilization', {})
                weights.append(capacity.get('weight_percent', 0))
                volumes.append(capacity.get('volume_percent', 0))
            
            # Clear and replot
            self.capacity_plot.clear()
            x = list(range(len(names)))
            self.capacity_plot.plot(x, weights, pen=pg.mkPen('#3b82f6', width=2), 
                                   symbol='o', symbolSize=8, name='Weight %')
            self.capacity_plot.plot(x, volumes, pen=pg.mkPen('#f97316', width=2),
                                   symbol='s', symbolSize=8, name='Volume %')
            self.capacity_plot.setXRange(-0.5, len(names) - 0.5)
            self.capacity_plot.addLegend()
            
            # Update stats
            avg_weight = sum(weights) / len(weights) if weights else 0
            avg_volume = sum(volumes) / len(volumes) if volumes else 0
            stats_text = f"Avg Weight: {avg_weight:.1f}% | Avg Volume: {avg_volume:.1f}%"
            self.capacity_stats.setText(stats_text)
        except Exception as e:
            print(f"Error updating capacity chart: {e}")
    
    def update_summary(self):
        """Update summary statistics"""
        try:
            drones = self.current_wave.get('drones', [])
            trucks = self.current_wave.get('trucks', [])
            
            total_deliveries = sum(len(d['node_ids']) for d in drones) + sum(len(t['node_ids']) for t in trucks)
            total_distance = sum(d['distance'] for d in drones) + sum(t['distance'] for t in trucks)
            total_cost = sum(d['cost'] for d in drones) + sum(t['cost'] for t in trucks)
            total_weight = sum(d['total_weight'] for d in drones) + sum(t['total_weight'] for t in trucks)
            
            self.summary_total_points.setText(f"Total Deliveries: {total_deliveries}")
            self.summary_total_dist.setText(f"Total Distance: {total_distance:.2f} km")
            self.summary_total_cost.setText(f"Total Cost: ${total_cost:.2f}")
            self.summary_total_weight.setText(f"Total Weight: {total_weight:.2f} kg")
            
            # Vehicle breakdown
            vehicle_text = ""
            for i, drone in enumerate(drones):
                vehicle_text += f"Drone {i+1}: {len(drone['node_ids'])} deliveries, {drone['distance']:.2f}km, ${drone['cost']:.2f}\n"
            for truck in trucks:
                vehicle_id = truck.get('vehicle_id', 'Truck')
                vehicle_text += f"{vehicle_id}: {len(truck['node_ids'])} deliveries, {truck['distance']:.2f}km, ${truck['cost']:.2f}\n"
            
            self.summary_vehicles.setText(vehicle_text.strip())
        except Exception as e:
            print(f"Error updating summary: {e}")
    
    def get_backend_folder(self):
        """Get backend folder path"""
        try:
            current_file = os.path.abspath(__file__)
            frontend_widgets = os.path.dirname(current_file)
            frontend = os.path.dirname(frontend_widgets)
            project_root = os.path.dirname(frontend)
            return os.path.join(project_root, 'backend')
        except:
            return None
    
    def closeEvent(self, event):
        """Clean up on close"""
        self._widget_destroyed = True
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)