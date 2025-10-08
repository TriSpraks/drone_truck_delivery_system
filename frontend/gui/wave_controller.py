"""
Wave Controller Module
Handles wave completion and transitions
"""
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox


class WaveController:
    """Manages wave transitions and auto-start timers"""
    
    def __init__(self, parent):
        self.parent = parent
        self.current_wave = 0
        self.wave_completed = False
        self.waiting_for_next_wave = False
        self.auto_next_wave_timer = None
        self.auto_next_wave_countdown = 0
    
    def on_wave_completed(self):
        """Handle wave completion"""
        self.parent.vehicle_manager.wave_running = False
        self.parent.vehicle_manager.wave_completed = True
        self.wave_completed = True
        
        stats = self.parent.vehicle_manager.get_wave_statistics()
        print(f"Wave {self.current_wave + 1} completed!")
        print(f"  Distance: {stats['distance']:.2f} km")
        print(f"  Cost: ${stats['cost']:.2f}")
        print(f"  Weight: {stats['weight']:.2f} kg")
        
        # Check for more waves
        has_more_waves = (self.parent.waves_data and 
                         self.current_wave < len(self.parent.waves_data) - 1)
        
        if has_more_waves:
            # Show next wave button
            self.parent.next_wave_action.setVisible(True)
            self.start_auto_next_wave_timer()
            
            QMessageBox.information(
                self.parent,
                f"Wave {self.current_wave + 1} Completed",
                f"Deliveries: {stats['deliveries']}\n"
                f"Distance: {stats['distance']:.2f} km\n"
                f"Cost: ${stats['cost']:.2f}\n\n"
                f"Next wave starts automatically in 5 minutes."
            )
        else:
            # Final wave
            total_waves = len(self.parent.waves_data) if self.parent.waves_data else 1
            QMessageBox.information(
                self.parent,
                "All Waves Completed",
                f"All {total_waves} wave(s) completed!\n\n"
                f"Final statistics:\n"
                f"Deliveries: {stats['deliveries']}\n"
                f"Distance: {stats['distance']:.2f} km\n"
                f"Cost: ${stats['cost']:.2f}"
            )
    
    def start_auto_next_wave_timer(self):
        """Start 5-minute countdown for next wave"""
        self.waiting_for_next_wave = True
        self.auto_next_wave_timer = QTimer()
        self.auto_next_wave_countdown = 300  # 5 minutes
        
        def countdown_tick():
            if (self.parent._widgets_destroyed or 
                not self.waiting_for_next_wave):
                if self.auto_next_wave_timer:
                    self.auto_next_wave_timer.stop()
                return
            
            self.auto_next_wave_countdown -= 1
            minutes = self.auto_next_wave_countdown // 60
            seconds = self.auto_next_wave_countdown % 60
            
            self.parent.next_wave_action.setText(
                f"⏭ Next Wave (Auto in {minutes}:{seconds:02d})"
            )
            
            if self.auto_next_wave_countdown <= 0:
                self.auto_next_wave_timer.stop()
                self.start_next_wave()
        
        self.auto_next_wave_timer.timeout.connect(countdown_tick)
        self.auto_next_wave_timer.start(1000)
    
    def start_next_wave(self):
        """Start next wave of vehicles"""
        if self.parent._widgets_destroyed:
            return
        
        # Cancel auto-timer
        if self.auto_next_wave_timer:
            self.auto_next_wave_timer.stop()
            self.auto_next_wave_timer = None
        
        self.waiting_for_next_wave = False
        self.parent.vehicle_manager.wave_completed = False
        self.wave_completed = False
        self.parent.next_wave_action.setVisible(False)
        
        # Move to next wave
        self.current_wave += 1
        
        if (self.parent.waves_data and 
            self.current_wave < len(self.parent.waves_data)):
            print(f"Starting Wave {self.current_wave + 1}")
            
            # Clear vehicles
            self.parent.vehicle_manager.vehicles.clear()
            self.parent.map_handler.clear_all_vehicles()
            
            # Start new wave
            self.parent.start_vehicles_optimized()
        else:
            # All waves done
            print("All waves completed!")
            self.current_wave = 0
            self.parent.vehicle_manager.vehicles_started = False
            self.parent.start_stop_action.setChecked(False)
            self.parent.start_stop_action.setText("▶ Start Vehicles")
    
    def stop(self):
        """Stop wave controller timers"""
        if self.auto_next_wave_timer:
            self.auto_next_wave_timer.stop()
            self.auto_next_wave_timer = None