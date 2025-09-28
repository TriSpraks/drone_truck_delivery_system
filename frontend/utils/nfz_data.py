"""
No-fly zone data for India airspace
"""

def get_india_no_fly_zones():
    """Comprehensive no-fly zones across India"""
    return [
        # EXISTING ZONES (from your current data)
        
        # Delhi NCR
        {
            'name': 'Indira Gandhi International Airport',
            'center': [28.5562, 77.1000],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major international airport'
        },
        {
            'name': 'Red Fort & India Gate Area',
            'center': [28.6562, 77.2410],
            'radius': 3000,
            'type': 'government',
            'description': 'High security government area'
        },
        {
            'name': 'Palam Air Force Station',
            'center': [28.5599, 77.1026],
            'radius': 6000,
            'type': 'military',
            'description': 'IAF base adjacent to IGIA'
        },
        
        # Mumbai
        {
            'name': 'Chhatrapati Shivaji International Airport',
            'center': [19.0896, 72.8656],
            'radius': 8000,
            'type': 'airport',
            'description': 'Busiest airport in India'
        },
        {
            'name': 'Bhabha Atomic Research Centre',
            'center': [19.0176, 72.9201],
            'radius': 5000,
            'type': 'nuclear',
            'description': 'Nuclear facility restricted zone'
        },
        {
            'name': 'Mumbai Port',
            'center': [18.9667, 72.8333],
            'radius': 3000,
            'type': 'port',
            'description': 'Major commercial port'
        },
        {
            'name': 'INS Shikra - Naval Air Station',
            'center': [19.0896, 72.8656],
            'radius': 4000,
            'type': 'military',
            'description': 'Naval aviation facility'
        },
        
        # Bangalore
        {
            'name': 'Kempegowda International Airport',
            'center': [13.1986, 77.7066],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major international airport'
        },
        {
            'name': 'HAL Airport & Aerospace Complex',
            'center': [12.9500, 77.6682],
            'radius': 4000,
            'type': 'military',
            'description': 'Military aerospace facility'
        },
        {
            'name': 'Yelahanka Air Force Station',
            'center': [13.1350, 77.6081],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF training base'
        },
        
        # Chennai
        {
            'name': 'Chennai International Airport',
            'center': [12.9941, 80.1709],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major South Indian airport'
        },
        {
            'name': 'INS Adyar - Naval Base',
            'center': [13.0067, 80.2206],
            'radius': 3000,
            'type': 'military',
            'description': 'Naval facility'
        },
        {
            'name': 'Chennai Port',
            'center': [13.0827, 80.3007],
            'radius': 2500,
            'type': 'port',
            'description': 'Major port facility'
        },
        
        # Hyderabad
        {
            'name': 'Rajiv Gandhi International Airport',
            'center': [17.2403, 78.4294],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major international airport'
        },
        {
            'name': 'Begumpet Airport',
            'center': [17.4532, 78.4676],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic and general aviation'
        },
        {
            'name': 'Dundigal Air Force Academy',
            'center': [17.6170, 78.4040],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF training academy'
        },
        
        # Kolkata
        {
            'name': 'Netaji Subhas Chandra Bose Airport',
            'center': [22.6540, 88.4477],
            'radius': 8000,
            'type': 'airport',
            'description': 'Eastern India major airport'
        },
        {
            'name': 'Kolkata Port',
            'center': [22.5726, 88.3639],
            'radius': 4000,
            'type': 'port',
            'description': 'Major river port'
        },
        {
            'name': 'Barrackpore Air Force Station',
            'center': [22.7606, 88.3784],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        
        # Mangaluru Region
        {
            'name': 'Mangaluru International Airport',
            'center': [12.9612, 74.8900],
            'radius': 6000,
            'type': 'airport',
            'description': 'International airport serving coastal Karnataka'
        },
        {
            'name': 'New Mangalore Port',
            'center': [12.9141, 74.7994],
            'radius': 3500,
            'type': 'port',
            'description': 'Major port on west coast'
        },
        {
            'name': 'NITK Surathkal Campus',
            'center': [13.0067, 74.7939],
            'radius': 1500,
            'type': 'government',
            'description': 'Educational institution restricted area'
        },
        
        # Gujarat
        {
            'name': 'Sardar Vallabhbhai Patel Airport',
            'center': [23.0726, 72.6177],
            'radius': 8000,
            'type': 'airport',
            'description': 'Gujarat major airport'
        },
        {
            'name': 'Kandla Port',
            'center': [23.0000, 70.2167],
            'radius': 4000,
            'type': 'port',
            'description': 'Major port in Gujarat'
        },
        {
            'name': 'Jamnagar Air Force Station',
            'center': [22.4707, 70.0527],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        {
            'name': 'Reliance Jamnagar Refinery',
            'center': [22.3000, 70.0500],
            'radius': 3000,
            'type': 'refinery',
            'description': 'World\'s largest oil refinery complex'
        },
        
        # Maharashtra (Additional)
        {
            'name': 'Pune Airport & Air Force Station',
            'center': [18.5822, 73.9197],
            'radius': 6000,
            'type': 'military',
            'description': 'Dual use military-civilian airport'
        },
        {
            'name': 'Nashik Air Force Station',
            'center': [19.9975, 73.7898],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        
        # Tamil Nadu (Additional)
        {
            'name': 'Coimbatore Airport',
            'center': [11.0297, 77.0434],
            'radius': 5000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Kudankulam Nuclear Power Plant',
            'center': [8.1644, 77.7069],
            'radius': 10000,
            'type': 'nuclear',
            'description': 'Major nuclear power facility'
        },
        {
            'name': 'Kalpakkam Nuclear Facility',
            'center': [12.5504, 80.1755],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear research facility'
        },
        {
            'name': 'Satish Dhawan Space Centre SHAR',
            'center': [13.7199, 80.2304],
            'radius': 10000,
            'type': 'space',
            'description': 'ISRO launch facility'
        },
        {
            'name': 'Tuticorin Port',
            'center': [8.7642, 78.1348],
            'radius': 3000,
            'type': 'port',
            'description': 'Major port in Tamil Nadu'
        },
        
        # Kerala
        {
            'name': 'Cochin International Airport',
            'center': [10.1520, 76.4019],
            'radius': 7000,
            'type': 'airport',
            'description': 'Major international airport in Kerala'
        },
        {
            'name': 'Kochi Port',
            'center': [9.9312, 76.2673],
            'radius': 3000,
            'type': 'port',
            'description': 'Major port in Kerala'
        },
        {
            'name': 'INS Dronacharya - Naval Academy',
            'center': [10.0889, 76.3394],
            'radius': 4000,
            'type': 'military',
            'description': 'Naval training facility'
        },
        {
            'name': 'Trivandrum International Airport',
            'center': [8.4821, 76.9200],
            'radius': 6000,
            'type': 'airport',
            'description': 'International airport'
        },
        
        # Goa
        {
            'name': 'Dabolim Airport & Naval Air Station',
            'center': [15.3808, 73.8314],
            'radius': 5000,
            'type': 'military',
            'description': 'Naval air station and civilian airport'
        },
        {
            'name': 'Mormugao Port',
            'center': [15.4000, 73.8000],
            'radius': 2500,
            'type': 'port',
            'description': 'Iron ore export port'
        },
        
        # Andhra Pradesh
        {
            'name': 'Visakhapatnam Airport',
            'center': [17.7211, 83.2245],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major airport in AP'
        },
        {
            'name': 'Visakhapatnam Port',
            'center': [17.6868, 83.2185],
            'radius': 4000,
            'type': 'port',
            'description': 'Major port on east coast'
        },
        {
            'name': 'INS Karna - Naval Base',
            'center': [17.6833, 83.2167],
            'radius': 3000,
            'type': 'military',
            'description': 'Naval facility'
        },
        
        # Punjab
        {
            'name': 'Sri Guru Ram Dass Jee International Airport',
            'center': [31.7098, 74.7979],
            'radius': 6000,
            'type': 'airport',
            'description': 'Amritsar international airport'
        },
        {
            'name': 'Pathankot Air Force Station',
            'center': [32.2338, 75.6346],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF base near Pakistan border'
        },
        {
            'name': 'Halwara Air Force Station',
            'center': [30.7467, 75.6133],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        
        # Strategic Military Zones
        {
            'name': 'Pokhran Test Range',
            'center': [27.0950, 71.7517],
            'radius': 15000,
            'type': 'military',
            'description': 'Nuclear test site - highly restricted'
        },
        {
            'name': 'Kargil Military Area',
            'center': [34.5539, 76.1313],
            'radius': 20000,
            'type': 'military',
            'description': 'High-altitude military zone'
        },
        {
            'name': 'Siachen Base Camp Area',
            'center': [35.4219, 77.0615],
            'radius': 25000,
            'type': 'military',
            'description': 'World\'s highest battlefield'
        },
        
        # NEW ADDITIONS - Missing Major Zones
        
        # Rajasthan
        {
            'name': 'Jaipur International Airport',
            'center': [26.8247, 75.8129],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major airport in Rajasthan'
        },
        {
            'name': 'Jodhpur Air Force Station',
            'center': [26.2389, 73.0485],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        {
            'name': 'Bikaner Air Force Station',
            'center': [28.0728, 73.2081],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        {
            'name': 'Udaipur Airport',
            'center': [24.6177, 73.8961],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Uttar Pradesh
        {
            'name': 'Chaudhary Charan Singh Airport Lucknow',
            'center': [26.7606, 80.8893],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major UP airport'
        },
        {
            'name': 'Lal Bahadur Shastri Airport Varanasi',
            'center': [25.4520, 82.8596],
            'radius': 4000,
            'type': 'airport',
            'description': 'International airport'
        },
        {
            'name': 'Kanpur Airport',
            'center': [26.4041, 80.4098],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Agra Airport & Air Force Station',
            'center': [27.1577, 77.9611],
            'radius': 4000,
            'type': 'military',
            'description': 'Dual use facility'
        },
        {
            'name': 'Allahabad Airport',
            'center': [25.4404, 81.7338],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Gorakhpur Airport',
            'center': [26.7396, 83.4496],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Madhya Pradesh
        {
            'name': 'Raja Bhoj Airport Bhopal',
            'center': [23.2875, 77.3374],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major MP airport'
        },
        {
            'name': 'Devi Ahilya Bai Holkar Airport Indore',
            'center': [22.7216, 75.8011],
            'radius': 5000,
            'type': 'airport',
            'description': 'International airport'
        },
        {
            'name': 'Gwalior Airport & Air Force Station',
            'center': [26.2933, 78.2275],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        {
            'name': 'Jabalpur Airport',
            'center': [23.1778, 80.0520],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Bihar & Jharkhand
        {
            'name': 'Jay Prakash Narayan Airport Patna',
            'center': [25.5913, 85.0880],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major Bihar airport'
        },
        {
            'name': 'Birsa Munda Airport Ranchi',
            'center': [23.3144, 85.3217],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major Jharkhand airport'
        },
        {
            'name': 'Gaya Airport',
            'center': [24.7443, 84.9512],
            'radius': 3000,
            'type': 'airport',
            'description': 'International airport for Buddhist circuit'
        },
        
        # Odisha
        {
            'name': 'Biju Patnaik Airport Bhubaneswar',
            'center': [20.2441, 85.8180],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major Odisha airport'
        },
        {
            'name': 'Paradip Port',
            'center': [20.2644, 86.6094],
            'radius': 4000,
            'type': 'port',
            'description': 'Major port on east coast'
        },
        {
            'name': 'Kalaikunda Air Force Station',
            'center': [22.3500, 87.2167],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        
        # West Bengal (Additional)
        {
            'name': 'Bagdogra Airport',
            'center': [26.6812, 88.3285],
            'radius': 4000,
            'type': 'airport',
            'description': 'North Bengal airport'
        },
        {
            'name': 'Haldia Port',
            'center': [22.0333, 88.1167],
            'radius': 3000,
            'type': 'port',
            'description': 'Major industrial port'
        },
        
        # Himachal Pradesh
        {
            'name': 'Gaggal Airport Dharamshala',
            'center': [32.1658, 76.2634],
            'radius': 3000,
            'type': 'airport',
            'description': 'Hill station airport'
        },
        {
            'name': 'Shimla Airport',
            'center': [31.0818, 77.0685],
            'radius': 2000,
            'type': 'airport',
            'description': 'Hill station airport'
        },
        {
            'name': 'Kullu Manali Airport',
            'center': [31.8763, 77.1544],
            'radius': 2000,
            'type': 'airport',
            'description': 'Tourism airport'
        },
        
        # Uttarakhand
        {
            'name': 'Jolly Grant Airport Dehradun',
            'center': [30.1897, 78.1804],
            'radius': 4000,
            'type': 'airport',
            'description': 'Uttarakhand main airport'
        },
        {
            'name': 'Pantnagar Airport',
            'center': [29.0336, 79.4737],
            'radius': 3000,
            'type': 'airport',
            'description': 'Agricultural university airport'
        },
        
        # Haryana
        {
            'name': 'Hisar Airport',
            'center': [29.1796, 75.7553],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Sirsa Air Force Station',
            'center': [29.5344, 75.0061],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF helicopter base'
        },
        
        # Jammu & Kashmir / Ladakh
        {
            'name': 'Sheikh ul-Alam Airport Srinagar',
            'center': [34.0839, 74.7742],
            'radius': 6000,
            'type': 'airport',
            'description': 'Kashmir main airport'
        },
        {
            'name': 'Jammu Airport',
            'center': [32.6890, 74.8378],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major J&K airport'
        },
        {
            'name': 'Leh Kushok Bakula Rimpochee Airport',
            'center': [34.1358, 77.5465],
            'radius': 4000,
            'type': 'airport',
            'description': 'High-altitude Ladakh airport'
        },
        {
            'name': 'Line of Control (LoC) Buffer Zone',
            'center': [34.0000, 74.5000],
            'radius': 30000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        
        # Assam & Northeast
        {
            'name': 'Lokpriya Gopinath Bordoloi Airport Guwahati',
            'center': [26.1061, 91.5856],
            'radius': 6000,
            'type': 'airport',
            'description': 'Northeast main airport'
        },
        {
            'name': 'Dibrugarh Airport',
            'center': [27.4839, 95.0169],
            'radius': 4000,
            'type': 'airport',
            'description': 'Upper Assam airport'
        },
        {
            'name': 'Jorhat Airport',
            'center': [26.7318, 94.1753],
            'radius': 3000,
            'type': 'airport',
            'description': 'Tea capital airport'
        },
        {
            'name': 'Silchar Airport',
            'center': [24.9129, 92.9787],
            'radius': 3000,
            'type': 'airport',
            'description': 'Barak Valley airport'
        },
        {
            'name': 'Tezpur Air Force Station',
            'center': [26.7094, 92.7847],
            'radius': 5000,
            'type': 'military',
            'description': 'Strategic northeastern IAF base'
        },
        {
            'name': 'Chabua Air Force Station',
            'center': [27.4500, 94.9500],
            'radius': 4000,
            'type': 'military',
            'description': 'Forward IAF base'
        },
        
        # Manipur, Mizoram, Tripura, Nagaland
        {
            'name': 'Imphal Airport',
            'center': [24.7597, 93.8967],
            'radius': 4000,
            'type': 'airport',
            'description': 'Manipur main airport'
        },
        {
            'name': 'Lengpui Airport Aizawl',
            'center': [23.8408, 92.6197],
            'radius': 3000,
            'type': 'airport',
            'description': 'Mizoram airport'
        },
        {
            'name': 'Agartala Airport',
            'center': [23.8870, 91.2403],
            'radius': 4000,
            'type': 'airport',
            'description': 'Tripura main airport'
        },
        {
            'name': 'Dimapur Airport',
            'center': [25.8839, 93.7711],
            'radius': 3000,
            'type': 'airport',
            'description': 'Nagaland airport'
        },
        
        # Meghalaya & Arunachal Pradesh
        {
            'name': 'Shillong Airport Umroi',
            'center': [25.7036, 91.9097],
            'radius': 3000,
            'type': 'airport',
            'description': 'Meghalaya airport'
        },
        {
            'name': 'Pasighat Airport',
            'center': [28.0661, 95.3356],
            'radius': 2000,
            'type': 'airport',
            'description': 'Arunachal Pradesh airport'
        },
        {
            'name': 'Along Airport',
            'center': [28.1750, 94.8000],
            'radius': 2000,
            'type': 'airport',
            'description': 'Advanced landing ground'
        },
        {
            'name': 'China Border Buffer Zone - Arunachal',
            'center': [28.2180, 94.7278],
            'radius': 25000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        
        # Sikkim
        {
            'name': 'Pakyong Airport Gangtok',
            'center': [27.2308, 88.5844],
            'radius': 3000,
            'type': 'airport',
            'description': 'Sikkim airport'
        },
        
        # Chhattisgarh
        {
            'name': 'Swami Vivekananda Airport Raipur',
            'center': [21.1802, 81.7388],
            'radius': 5000,
            'type': 'airport',
            'description': 'Chhattisgarh main airport'
        },
        {
            'name': 'Jagdalpur Airport',
            'center': [19.0717, 82.0300],
            'radius': 2000,
            'type': 'airport',
            'description': 'Tribal region airport'
        },
        
        # Telangana (Additional)
        {
            'name': 'Warangal Airport',
            'center': [17.9218, 79.5998],
            'radius': 2000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Nuclear & Space Facilities
        {
            'name': 'Narora Atomic Power Station',
            'center': [28.2006, 78.3897],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant UP'
        },
        {
            'name': 'Rawatbhata Nuclear Plant',
            'center': [24.9266, 75.5950],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant Rajasthan'
        },
        {
            'name': 'Tarapur Atomic Power Station',
            'center': [19.8500, 72.6500],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant Maharashtra'
        },
        {
            'name': 'Kaiga Nuclear Plant',
            'center': [14.8643, 74.4385],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant Karnataka'
        },
        {
            'name': 'VSSC Thumba',
            'center': [8.5241, 76.8593],
            'radius': 5000,
            'type': 'space',
            'description': 'ISRO rocket development center'
        },
        {
            'name': 'ISRO Satellite Centre Bangalore',
            'center': [13.0211, 77.5608],
            'radius': 3000,
            'type': 'space',
            'description': 'Satellite manufacturing facility'
        },
        
        # Additional Strategic Military Installations
        {
            'name': 'Ambala Air Force Station',
            'center': [30.3815, 76.8045],
            'radius': 5000,
            'type': 'military',
            'description': 'Major IAF fighter base'
        },
        {
            'name': 'Adampur Air Force Station',
            'center': [31.4338, 75.7581],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF fighter base Punjab'
        },
        {
            'name': 'Bareilly Air Force Station',
            'center': [28.4222, 79.4508],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base UP'
        },
        {
            'name': 'Hindon Air Force Station',
            'center': [28.7094, 77.3481],
            'radius': 4000,
            'type': 'military',
            'description': 'Transport aircraft base Delhi NCR'
        },
        {
            'name': 'Bhuj Air Force Station',
            'center': [23.2878, 69.6700],
            'radius': 5000,
            'type': 'military',
            'description': 'Strategic western border base'
        },
        {
            'name': 'Jaisalmer Air Force Station',
            'center': [26.8886, 70.8652],
            'radius': 4000,
            'type': 'military',
            'description': 'Desert strike base'
        },
        {
            'name': 'Suratgarh Air Force Station',
            'center': [29.3225, 73.8981],
            'radius': 4000,
            'type': 'military',
            'description': 'Transport base Rajasthan'
        },
        {
            'name': 'Uttarlai Air Force Station',
            'center': [25.2000, 71.8667],
            'radius': 4000,
            'type': 'military',
            'description': 'Strategic Rajasthan base'
        },
        
        # Naval Establishments
        {
            'name': 'INS Hansa - Goa Naval Aviation',
            'center': [15.3808, 73.8314],
            'radius': 5000,
            'type': 'military',
            'description': 'Naval aviation training base'
        },
        {
            'name': 'INS Garuda - Kochi Naval Base',
            'center': [9.9312, 76.2673],
            'radius': 4000,
            'type': 'military',
            'description': 'Southern Naval Command'
        },
        {
            'name': 'INS Rajali - Arakkonam Naval Air Station',
            'center': [13.0824, 79.6866],
            'radius': 4000,
            'type': 'military',
            'description': 'Naval aviation base Tamil Nadu'
        },
        {
            'name': 'INS Dega - Visakhapatnam Naval Air Station',
            'center': [17.7211, 83.2245],
            'radius': 4000,
            'type': 'military',
            'description': 'Eastern Fleet aviation base'
        },
        {
            'name': 'INS Hamla - Mumbai Naval Base',
            'center': [18.9220, 72.8347],
            'radius': 3000,
            'type': 'military',
            'description': 'Western Naval Command base'
        },
        {
            'name': 'Karwar Naval Base (Project Seabird)',
            'center': [14.8141, 74.1240],
            'radius': 5000,
            'type': 'military',
            'description': 'Major naval base Karnataka'
        },
        {
            'name': 'Chilka Naval Base',
            'center': [19.7179, 85.3240],
            'radius': 3000,
            'type': 'military',
            'description': 'Naval training establishment'
        },
        
        # Border Security & Coast Guard
        {
            'name': 'Pakistan Border Buffer Zone - Punjab',
            'center': [31.6040, 74.8723],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Pakistan Border Buffer Zone - Rajasthan',
            'center': [27.0238, 70.8022],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Pakistan Border Buffer Zone - Gujarat',
            'center': [23.7337, 68.8378],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Bangladesh Border Buffer Zone - West Bengal',
            'center': [22.6273, 88.7953],
            'radius': 10000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Myanmar Border Buffer Zone - Mizoram',
            'center': [23.7271, 93.2551],
            'radius': 10000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'China Border Buffer Zone - Sikkim',
            'center': [27.6009, 88.9140],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'China Border Buffer Zone - Ladakh',
            'center': [34.2996, 78.2932],
            'radius': 30000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        
        # Additional Ports
        {
            'name': 'Ennore Port',
            'center': [13.2167, 80.3167],
            'radius': 3000,
            'type': 'port',
            'description': 'Major port Tamil Nadu'
        },
        {
            'name': 'Jawaharlal Nehru Port Mumbai',
            'center': [18.9647, 72.9492],
            'radius': 4000,
            'type': 'port',
            'description': 'Container port Maharashtra'
        },
        {
            'name': 'Mundra Port',
            'center': [22.8395, 69.7937],
            'radius': 4000,
            'type': 'port',
            'description': 'Private port Gujarat'
        },
        {
            'name': 'Pipavav Port',
            'center': [20.9500, 71.0833],
            'radius': 3000,
            'type': 'port',
            'description': 'Container port Gujarat'
        },
        {
            'name': 'Kamarajar Port Ennore',
            'center': [13.2500, 80.3333],
            'radius': 3000,
            'type': 'port',
            'description': 'Coal import port'
        },
        
        # Oil Refineries & Petrochemical Complexes
        {
            'name': 'Mathura Refinery',
            'center': [27.4924, 77.6737],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery UP'
        },
        {
            'name': 'Panipat Refinery',
            'center': [29.3879, 76.9690],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Haryana'
        },
        {
            'name': 'Barauni Refinery',
            'center': [25.4816, 86.0336],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Bihar'
        },
        {
            'name': 'Digboi Refinery',
            'center': [27.3833, 95.6167],
            'radius': 2000,
            'type': 'refinery',
            'description': 'Asia\'s oldest refinery Assam'
        },
        {
            'name': 'Guwahati Refinery',
            'center': [26.1445, 91.7362],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Assam'
        },
        {
            'name': 'Bongaigaon Refinery',
            'center': [26.4609, 90.5501],
            'radius': 2000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Assam'
        },
        {
            'name': 'Haldia Refinery',
            'center': [22.0582, 88.0955],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery West Bengal'
        },
        {
            'name': 'Paradip Refinery',
            'center': [20.3180, 86.6503],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Odisha'
        },
        {
            'name': 'Chennai Refinery',
            'center': [13.1143, 80.3017],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Chennai Petroleum Corporation'
        },
        {
            'name': 'Mangalore Refinery',
            'center': [12.8697, 74.8860],
            'radius': 3000,
            'type': 'refinery',
            'description': 'MRPL refinery Karnataka'
        },
        {
            'name': 'Kochi Refinery',
            'center': [9.9816, 76.2999],
            'radius': 3000,
            'type': 'refinery',
            'description': 'BPCL refinery Kerala'
        },
        {
            'name': 'Mumbai Refinery',
            'center': [19.0330, 72.8570],
            'radius': 2000,
            'type': 'refinery',
            'description': 'BPCL refinery Maharashtra'
        },
        {
            'name': 'Vadodara Refinery',
            'center': [22.2587, 73.1394],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Gujarat'
        },
        
        # Research & Testing Facilities
        {
            'name': 'DRDO Chandipur',
            'center': [21.4500, 87.0167],
            'radius': 10000,
            'type': 'military',
            'description': 'Integrated test range Odisha'
        },
        {
            'name': 'DRDO Hyderabad Complex',
            'center': [17.4400, 78.4482],
            'radius': 5000,
            'type': 'military',
            'description': 'Defence research laboratories'
        },
        {
            'name': 'DRDO Pune Complex',
            'center': [18.5679, 73.9143],
            'radius': 3000,
            'type': 'military',
            'description': 'Armament research establishment'
        },
        {
            'name': 'Terminal Ballistics Research Laboratory',
            'center': [26.2124, 78.1772],
            'radius': 5000,
            'type': 'military',
            'description': 'Weapons testing facility Chandigarh'
        },
        {
            'name': 'High Energy Materials Research Laboratory',
            'center': [18.5204, 73.8567],
            'radius': 3000,
            'type': 'military',
            'description': 'Explosives research Pune'
        },
        
        # Central Government Security Zones
        {
            'name': 'Parliament House Complex',
            'center': [28.6172, 77.2082],
            'radius': 2000,
            'type': 'government',
            'description': 'Parliament and surrounding area'
        },
        {
            'name': 'Rashtrapati Bhavan Complex',
            'center': [28.6139, 77.1999],
            'radius': 1500,
            'type': 'government',
            'description': 'Presidential palace complex'
        },
        {
            'name': 'Supreme Court Complex',
            'center': [28.6229, 77.2397],
            'radius': 1000,
            'type': 'government',
            'description': 'Supreme Court of India'
        },
        {
            'name': 'PMO & South Block',
            'center': [28.6127, 77.2773],
            'radius': 1000,
            'type': 'government',
            'description': 'Prime Minister Office complex'
        },
        {
            'name': 'Reserve Bank of India Mumbai',
            'center': [18.9322, 72.8264],
            'radius': 500,
            'type': 'government',
            'description': 'Central bank headquarters'
        },
        
        # State Capital Security Zones
        {
            'name': 'Raj Bhavan Mumbai',
            'center': [18.9499, 72.8048],
            'radius': 1000,
            'type': 'government',
            'description': 'Maharashtra governor residence'
        },
        {
            'name': 'Vidhana Soudha Bangalore',
            'center': [12.9792, 77.5903],
            'radius': 1000,
            'type': 'government',
            'description': 'Karnataka state secretariat'
        },
        {
            'name': 'Fort St George Chennai',
            'center': [13.0840, 80.2892],
            'radius': 1000,
            'type': 'government',
            'description': 'Tamil Nadu secretariat'
        },
        {
            'name': 'Writers Building Kolkata',
            'center': [22.5726, 88.3639],
            'radius': 1000,
            'type': 'government',
            'description': 'West Bengal secretariat'
        },
        
        # Additional High-Security Installations
        {
            'name': 'CBI Headquarters',
            'center': [28.6139, 77.2090],
            'radius': 500,
            'type': 'government',
            'description': 'Central investigation agency'
        },
        {
            'name': 'Intelligence Bureau Delhi',
            'center': [28.6139, 77.2073],
            'radius': 500,
            'type': 'government',
            'description': 'Internal intelligence agency'
        },
        {
            'name': 'RAW Headquarters',
            'center': [28.6304, 77.2177],
            'radius': 1000,
            'type': 'government',
            'description': 'External intelligence agency'
        },
        
        # Emergency & Disaster Response Centers
        {
            'name': 'National Disaster Response Force HQ',
            'center': [28.5355, 77.3910],
            'radius': 1000,
            'type': 'government',
            'description': 'NDRF headquarters Ghaziabad'
        },
        
        # Communication & Satellite Facilities
        {
            'name': 'All India Radio Delhi',
            'center': [28.6139, 77.2090],
            'radius': 500,
            'type': 'government',
            'description': 'National broadcaster headquarters'
        },
        {
            'name': 'Doordarshan Kendra Delhi',
            'center': [28.6304, 77.2177],
            'radius': 500,
            'type': 'government',
            'description': 'National television broadcaster'
        },
        
        # VIP Helipads & Landing Sites
        {
            'name': 'Palam Technical Area',
            'center': [28.5665, 77.1031],
            'radius': 2000,
            'type': 'military',
            'description': 'VIP aircraft maintenance'
        },
        {
            'name': 'Safdarjung Airport',
            'center': [28.5843, 77.2058],
            'radius': 2000,
            'type': 'government',
            'description': 'Delhi flying club and emergency'
        }
    ]

def get_depot_selection_no_fly_zones():
    """Get major no-fly zones for depot selection"""
    return [
        # EXISTING ZONES (from your current data)
        
        # Delhi NCR
        {
            'name': 'Indira Gandhi International Airport',
            'center': [28.5562, 77.1000],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major international airport'
        },
        {
            'name': 'Red Fort & India Gate Area',
            'center': [28.6562, 77.2410],
            'radius': 3000,
            'type': 'government',
            'description': 'High security government area'
        },
        {
            'name': 'Palam Air Force Station',
            'center': [28.5599, 77.1026],
            'radius': 6000,
            'type': 'military',
            'description': 'IAF base adjacent to IGIA'
        },
        
        # Mumbai
        {
            'name': 'Chhatrapati Shivaji International Airport',
            'center': [19.0896, 72.8656],
            'radius': 8000,
            'type': 'airport',
            'description': 'Busiest airport in India'
        },
        {
            'name': 'Bhabha Atomic Research Centre',
            'center': [19.0176, 72.9201],
            'radius': 5000,
            'type': 'nuclear',
            'description': 'Nuclear facility restricted zone'
        },
        {
            'name': 'Mumbai Port',
            'center': [18.9667, 72.8333],
            'radius': 3000,
            'type': 'port',
            'description': 'Major commercial port'
        },
        {
            'name': 'INS Shikra - Naval Air Station',
            'center': [19.0896, 72.8656],
            'radius': 4000,
            'type': 'military',
            'description': 'Naval aviation facility'
        },
        
        # Bangalore
        {
            'name': 'Kempegowda International Airport',
            'center': [13.1986, 77.7066],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major international airport'
        },
        {
            'name': 'HAL Airport & Aerospace Complex',
            'center': [12.9500, 77.6682],
            'radius': 4000,
            'type': 'military',
            'description': 'Military aerospace facility'
        },
        {
            'name': 'Yelahanka Air Force Station',
            'center': [13.1350, 77.6081],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF training base'
        },
        
        # Chennai
        {
            'name': 'Chennai International Airport',
            'center': [12.9941, 80.1709],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major South Indian airport'
        },
        {
            'name': 'INS Adyar - Naval Base',
            'center': [13.0067, 80.2206],
            'radius': 3000,
            'type': 'military',
            'description': 'Naval facility'
        },
        {
            'name': 'Chennai Port',
            'center': [13.0827, 80.3007],
            'radius': 2500,
            'type': 'port',
            'description': 'Major port facility'
        },
        
        # Hyderabad
        {
            'name': 'Rajiv Gandhi International Airport',
            'center': [17.2403, 78.4294],
            'radius': 8000,
            'type': 'airport',
            'description': 'Major international airport'
        },
        {
            'name': 'Begumpet Airport',
            'center': [17.4532, 78.4676],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic and general aviation'
        },
        {
            'name': 'Dundigal Air Force Academy',
            'center': [17.6170, 78.4040],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF training academy'
        },
        
        # Kolkata
        {
            'name': 'Netaji Subhas Chandra Bose Airport',
            'center': [22.6540, 88.4477],
            'radius': 8000,
            'type': 'airport',
            'description': 'Eastern India major airport'
        },
        {
            'name': 'Kolkata Port',
            'center': [22.5726, 88.3639],
            'radius': 4000,
            'type': 'port',
            'description': 'Major river port'
        },
        {
            'name': 'Barrackpore Air Force Station',
            'center': [22.7606, 88.3784],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        
        # Mangaluru Region
        {
            'name': 'Mangaluru International Airport',
            'center': [12.9612, 74.8900],
            'radius': 6000,
            'type': 'airport',
            'description': 'International airport serving coastal Karnataka'
        },
        {
            'name': 'New Mangalore Port',
            'center': [12.9141, 74.7994],
            'radius': 3500,
            'type': 'port',
            'description': 'Major port on west coast'
        },
        {
            'name': 'NITK Surathkal Campus',
            'center': [13.0067, 74.7939],
            'radius': 1500,
            'type': 'government',
            'description': 'Educational institution restricted area'
        },
        
        # Gujarat
        {
            'name': 'Sardar Vallabhbhai Patel Airport',
            'center': [23.0726, 72.6177],
            'radius': 8000,
            'type': 'airport',
            'description': 'Gujarat major airport'
        },
        {
            'name': 'Kandla Port',
            'center': [23.0000, 70.2167],
            'radius': 4000,
            'type': 'port',
            'description': 'Major port in Gujarat'
        },
        {
            'name': 'Jamnagar Air Force Station',
            'center': [22.4707, 70.0527],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        {
            'name': 'Reliance Jamnagar Refinery',
            'center': [22.3000, 70.0500],
            'radius': 3000,
            'type': 'refinery',
            'description': 'World\'s largest oil refinery complex'
        },
        
        # Maharashtra (Additional)
        {
            'name': 'Pune Airport & Air Force Station',
            'center': [18.5822, 73.9197],
            'radius': 6000,
            'type': 'military',
            'description': 'Dual use military-civilian airport'
        },
        {
            'name': 'Nashik Air Force Station',
            'center': [19.9975, 73.7898],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        
        # Tamil Nadu (Additional)
        {
            'name': 'Coimbatore Airport',
            'center': [11.0297, 77.0434],
            'radius': 5000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Kudankulam Nuclear Power Plant',
            'center': [8.1644, 77.7069],
            'radius': 10000,
            'type': 'nuclear',
            'description': 'Major nuclear power facility'
        },
        {
            'name': 'Kalpakkam Nuclear Facility',
            'center': [12.5504, 80.1755],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear research facility'
        },
        {
            'name': 'Satish Dhawan Space Centre SHAR',
            'center': [13.7199, 80.2304],
            'radius': 10000,
            'type': 'space',
            'description': 'ISRO launch facility'
        },
        {
            'name': 'Tuticorin Port',
            'center': [8.7642, 78.1348],
            'radius': 3000,
            'type': 'port',
            'description': 'Major port in Tamil Nadu'
        },
        
        # Kerala
        {
            'name': 'Cochin International Airport',
            'center': [10.1520, 76.4019],
            'radius': 7000,
            'type': 'airport',
            'description': 'Major international airport in Kerala'
        },
        {
            'name': 'Kochi Port',
            'center': [9.9312, 76.2673],
            'radius': 3000,
            'type': 'port',
            'description': 'Major port in Kerala'
        },
        {
            'name': 'INS Dronacharya - Naval Academy',
            'center': [10.0889, 76.3394],
            'radius': 4000,
            'type': 'military',
            'description': 'Naval training facility'
        },
        {
            'name': 'Trivandrum International Airport',
            'center': [8.4821, 76.9200],
            'radius': 6000,
            'type': 'airport',
            'description': 'International airport'
        },
        
        # Goa
        {
            'name': 'Dabolim Airport & Naval Air Station',
            'center': [15.3808, 73.8314],
            'radius': 5000,
            'type': 'military',
            'description': 'Naval air station and civilian airport'
        },
        {
            'name': 'Mormugao Port',
            'center': [15.4000, 73.8000],
            'radius': 2500,
            'type': 'port',
            'description': 'Iron ore export port'
        },
        
        # Andhra Pradesh
        {
            'name': 'Visakhapatnam Airport',
            'center': [17.7211, 83.2245],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major airport in AP'
        },
        {
            'name': 'Visakhapatnam Port',
            'center': [17.6868, 83.2185],
            'radius': 4000,
            'type': 'port',
            'description': 'Major port on east coast'
        },
        {
            'name': 'INS Karna - Naval Base',
            'center': [17.6833, 83.2167],
            'radius': 3000,
            'type': 'military',
            'description': 'Naval facility'
        },
        
        # Punjab
        {
            'name': 'Sri Guru Ram Dass Jee International Airport',
            'center': [31.7098, 74.7979],
            'radius': 6000,
            'type': 'airport',
            'description': 'Amritsar international airport'
        },
        {
            'name': 'Pathankot Air Force Station',
            'center': [32.2338, 75.6346],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF base near Pakistan border'
        },
        {
            'name': 'Halwara Air Force Station',
            'center': [30.7467, 75.6133],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        
        # Strategic Military Zones
        {
            'name': 'Pokhran Test Range',
            'center': [27.0950, 71.7517],
            'radius': 15000,
            'type': 'military',
            'description': 'Nuclear test site - highly restricted'
        },
        {
            'name': 'Kargil Military Area',
            'center': [34.5539, 76.1313],
            'radius': 20000,
            'type': 'military',
            'description': 'High-altitude military zone'
        },
        {
            'name': 'Siachen Base Camp Area',
            'center': [35.4219, 77.0615],
            'radius': 25000,
            'type': 'military',
            'description': 'World\'s highest battlefield'
        },
        
        # NEW ADDITIONS - Missing Major Zones
        
        # Rajasthan
        {
            'name': 'Jaipur International Airport',
            'center': [26.8247, 75.8129],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major airport in Rajasthan'
        },
        {
            'name': 'Jodhpur Air Force Station',
            'center': [26.2389, 73.0485],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        {
            'name': 'Bikaner Air Force Station',
            'center': [28.0728, 73.2081],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF transport base'
        },
        {
            'name': 'Udaipur Airport',
            'center': [24.6177, 73.8961],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Uttar Pradesh
        {
            'name': 'Chaudhary Charan Singh Airport Lucknow',
            'center': [26.7606, 80.8893],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major UP airport'
        },
        {
            'name': 'Lal Bahadur Shastri Airport Varanasi',
            'center': [25.4520, 82.8596],
            'radius': 4000,
            'type': 'airport',
            'description': 'International airport'
        },
        {
            'name': 'Kanpur Airport',
            'center': [26.4041, 80.4098],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Agra Airport & Air Force Station',
            'center': [27.1577, 77.9611],
            'radius': 4000,
            'type': 'military',
            'description': 'Dual use facility'
        },
        {
            'name': 'Allahabad Airport',
            'center': [25.4404, 81.7338],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Gorakhpur Airport',
            'center': [26.7396, 83.4496],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Madhya Pradesh
        {
            'name': 'Raja Bhoj Airport Bhopal',
            'center': [23.2875, 77.3374],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major MP airport'
        },
        {
            'name': 'Devi Ahilya Bai Holkar Airport Indore',
            'center': [22.7216, 75.8011],
            'radius': 5000,
            'type': 'airport',
            'description': 'International airport'
        },
        {
            'name': 'Gwalior Airport & Air Force Station',
            'center': [26.2933, 78.2275],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        {
            'name': 'Jabalpur Airport',
            'center': [23.1778, 80.0520],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Bihar & Jharkhand
        {
            'name': 'Jay Prakash Narayan Airport Patna',
            'center': [25.5913, 85.0880],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major Bihar airport'
        },
        {
            'name': 'Birsa Munda Airport Ranchi',
            'center': [23.3144, 85.3217],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major Jharkhand airport'
        },
        {
            'name': 'Gaya Airport',
            'center': [24.7443, 84.9512],
            'radius': 3000,
            'type': 'airport',
            'description': 'International airport for Buddhist circuit'
        },
        
        # Odisha
        {
            'name': 'Biju Patnaik Airport Bhubaneswar',
            'center': [20.2441, 85.8180],
            'radius': 6000,
            'type': 'airport',
            'description': 'Major Odisha airport'
        },
        {
            'name': 'Paradip Port',
            'center': [20.2644, 86.6094],
            'radius': 4000,
            'type': 'port',
            'description': 'Major port on east coast'
        },
        {
            'name': 'Kalaikunda Air Force Station',
            'center': [22.3500, 87.2167],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base'
        },
        
        # West Bengal (Additional)
        {
            'name': 'Bagdogra Airport',
            'center': [26.6812, 88.3285],
            'radius': 4000,
            'type': 'airport',
            'description': 'North Bengal airport'
        },
        {
            'name': 'Haldia Port',
            'center': [22.0333, 88.1167],
            'radius': 3000,
            'type': 'port',
            'description': 'Major industrial port'
        },
        
        # Himachal Pradesh
        {
            'name': 'Gaggal Airport Dharamshala',
            'center': [32.1658, 76.2634],
            'radius': 3000,
            'type': 'airport',
            'description': 'Hill station airport'
        },
        {
            'name': 'Shimla Airport',
            'center': [31.0818, 77.0685],
            'radius': 2000,
            'type': 'airport',
            'description': 'Hill station airport'
        },
        {
            'name': 'Kullu Manali Airport',
            'center': [31.8763, 77.1544],
            'radius': 2000,
            'type': 'airport',
            'description': 'Tourism airport'
        },
        
        # Uttarakhand
        {
            'name': 'Jolly Grant Airport Dehradun',
            'center': [30.1897, 78.1804],
            'radius': 4000,
            'type': 'airport',
            'description': 'Uttarakhand main airport'
        },
        {
            'name': 'Pantnagar Airport',
            'center': [29.0336, 79.4737],
            'radius': 3000,
            'type': 'airport',
            'description': 'Agricultural university airport'
        },
        
        # Haryana
        {
            'name': 'Hisar Airport',
            'center': [29.1796, 75.7553],
            'radius': 3000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        {
            'name': 'Sirsa Air Force Station',
            'center': [29.5344, 75.0061],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF helicopter base'
        },
        
        # Jammu & Kashmir / Ladakh
        {
            'name': 'Sheikh ul-Alam Airport Srinagar',
            'center': [34.0839, 74.7742],
            'radius': 6000,
            'type': 'airport',
            'description': 'Kashmir main airport'
        },
        {
            'name': 'Jammu Airport',
            'center': [32.6890, 74.8378],
            'radius': 5000,
            'type': 'airport',
            'description': 'Major J&K airport'
        },
        {
            'name': 'Leh Kushok Bakula Rimpochee Airport',
            'center': [34.1358, 77.5465],
            'radius': 4000,
            'type': 'airport',
            'description': 'High-altitude Ladakh airport'
        },
        {
            'name': 'Line of Control (LoC) Buffer Zone',
            'center': [34.0000, 74.5000],
            'radius': 30000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        
        # Assam & Northeast
        {
            'name': 'Lokpriya Gopinath Bordoloi Airport Guwahati',
            'center': [26.1061, 91.5856],
            'radius': 6000,
            'type': 'airport',
            'description': 'Northeast main airport'
        },
        {
            'name': 'Dibrugarh Airport',
            'center': [27.4839, 95.0169],
            'radius': 4000,
            'type': 'airport',
            'description': 'Upper Assam airport'
        },
        {
            'name': 'Jorhat Airport',
            'center': [26.7318, 94.1753],
            'radius': 3000,
            'type': 'airport',
            'description': 'Tea capital airport'
        },
        {
            'name': 'Silchar Airport',
            'center': [24.9129, 92.9787],
            'radius': 3000,
            'type': 'airport',
            'description': 'Barak Valley airport'
        },
        {
            'name': 'Tezpur Air Force Station',
            'center': [26.7094, 92.7847],
            'radius': 5000,
            'type': 'military',
            'description': 'Strategic northeastern IAF base'
        },
        {
            'name': 'Chabua Air Force Station',
            'center': [27.4500, 94.9500],
            'radius': 4000,
            'type': 'military',
            'description': 'Forward IAF base'
        },
        
        # Manipur, Mizoram, Tripura, Nagaland
        {
            'name': 'Imphal Airport',
            'center': [24.7597, 93.8967],
            'radius': 4000,
            'type': 'airport',
            'description': 'Manipur main airport'
        },
        {
            'name': 'Lengpui Airport Aizawl',
            'center': [23.8408, 92.6197],
            'radius': 3000,
            'type': 'airport',
            'description': 'Mizoram airport'
        },
        {
            'name': 'Agartala Airport',
            'center': [23.8870, 91.2403],
            'radius': 4000,
            'type': 'airport',
            'description': 'Tripura main airport'
        },
        {
            'name': 'Dimapur Airport',
            'center': [25.8839, 93.7711],
            'radius': 3000,
            'type': 'airport',
            'description': 'Nagaland airport'
        },
        
        # Meghalaya & Arunachal Pradesh
        {
            'name': 'Shillong Airport Umroi',
            'center': [25.7036, 91.9097],
            'radius': 3000,
            'type': 'airport',
            'description': 'Meghalaya airport'
        },
        {
            'name': 'Pasighat Airport',
            'center': [28.0661, 95.3356],
            'radius': 2000,
            'type': 'airport',
            'description': 'Arunachal Pradesh airport'
        },
        {
            'name': 'Along Airport',
            'center': [28.1750, 94.8000],
            'radius': 2000,
            'type': 'airport',
            'description': 'Advanced landing ground'
        },
        {
            'name': 'China Border Buffer Zone - Arunachal',
            'center': [28.2180, 94.7278],
            'radius': 25000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        
        # Sikkim
        {
            'name': 'Pakyong Airport Gangtok',
            'center': [27.2308, 88.5844],
            'radius': 3000,
            'type': 'airport',
            'description': 'Sikkim airport'
        },
        
        # Chhattisgarh
        {
            'name': 'Swami Vivekananda Airport Raipur',
            'center': [21.1802, 81.7388],
            'radius': 5000,
            'type': 'airport',
            'description': 'Chhattisgarh main airport'
        },
        {
            'name': 'Jagdalpur Airport',
            'center': [19.0717, 82.0300],
            'radius': 2000,
            'type': 'airport',
            'description': 'Tribal region airport'
        },
        
        # Telangana (Additional)
        {
            'name': 'Warangal Airport',
            'center': [17.9218, 79.5998],
            'radius': 2000,
            'type': 'airport',
            'description': 'Domestic airport'
        },
        
        # Nuclear & Space Facilities
        {
            'name': 'Narora Atomic Power Station',
            'center': [28.2006, 78.3897],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant UP'
        },
        {
            'name': 'Rawatbhata Nuclear Plant',
            'center': [24.9266, 75.5950],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant Rajasthan'
        },
        {
            'name': 'Tarapur Atomic Power Station',
            'center': [19.8500, 72.6500],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant Maharashtra'
        },
        {
            'name': 'Kaiga Nuclear Plant',
            'center': [14.8643, 74.4385],
            'radius': 8000,
            'type': 'nuclear',
            'description': 'Nuclear power plant Karnataka'
        },
        {
            'name': 'VSSC Thumba',
            'center': [8.5241, 76.8593],
            'radius': 5000,
            'type': 'space',
            'description': 'ISRO rocket development center'
        },
        {
            'name': 'ISRO Satellite Centre Bangalore',
            'center': [13.0211, 77.5608],
            'radius': 3000,
            'type': 'space',
            'description': 'Satellite manufacturing facility'
        },
        
        # Additional Strategic Military Installations
        {
            'name': 'Ambala Air Force Station',
            'center': [30.3815, 76.8045],
            'radius': 5000,
            'type': 'military',
            'description': 'Major IAF fighter base'
        },
        {
            'name': 'Adampur Air Force Station',
            'center': [31.4338, 75.7581],
            'radius': 4000,
            'type': 'military',
            'description': 'IAF fighter base Punjab'
        },
        {
            'name': 'Bareilly Air Force Station',
            'center': [28.4222, 79.4508],
            'radius': 5000,
            'type': 'military',
            'description': 'IAF fighter base UP'
        },
        {
            'name': 'Hindon Air Force Station',
            'center': [28.7094, 77.3481],
            'radius': 4000,
            'type': 'military',
            'description': 'Transport aircraft base Delhi NCR'
        },
        {
            'name': 'Bhuj Air Force Station',
            'center': [23.2878, 69.6700],
            'radius': 5000,
            'type': 'military',
            'description': 'Strategic western border base'
        },
        {
            'name': 'Jaisalmer Air Force Station',
            'center': [26.8886, 70.8652],
            'radius': 4000,
            'type': 'military',
            'description': 'Desert strike base'
        },
        {
            'name': 'Suratgarh Air Force Station',
            'center': [29.3225, 73.8981],
            'radius': 4000,
            'type': 'military',
            'description': 'Transport base Rajasthan'
        },
        {
            'name': 'Uttarlai Air Force Station',
            'center': [25.2000, 71.8667],
            'radius': 4000,
            'type': 'military',
            'description': 'Strategic Rajasthan base'
        },
        
        # Naval Establishments
        {
            'name': 'INS Hansa - Goa Naval Aviation',
            'center': [15.3808, 73.8314],
            'radius': 5000,
            'type': 'military',
            'description': 'Naval aviation training base'
        },
        {
            'name': 'INS Garuda - Kochi Naval Base',
            'center': [9.9312, 76.2673],
            'radius': 4000,
            'type': 'military',
            'description': 'Southern Naval Command'
        },
        {
            'name': 'INS Rajali - Arakkonam Naval Air Station',
            'center': [13.0824, 79.6866],
            'radius': 4000,
            'type': 'military',
            'description': 'Naval aviation base Tamil Nadu'
        },
        {
            'name': 'INS Dega - Visakhapatnam Naval Air Station',
            'center': [17.7211, 83.2245],
            'radius': 4000,
            'type': 'military',
            'description': 'Eastern Fleet aviation base'
        },
        {
            'name': 'INS Hamla - Mumbai Naval Base',
            'center': [18.9220, 72.8347],
            'radius': 3000,
            'type': 'military',
            'description': 'Western Naval Command base'
        },
        {
            'name': 'Karwar Naval Base (Project Seabird)',
            'center': [14.8141, 74.1240],
            'radius': 5000,
            'type': 'military',
            'description': 'Major naval base Karnataka'
        },
        {
            'name': 'Chilka Naval Base',
            'center': [19.7179, 85.3240],
            'radius': 3000,
            'type': 'military',
            'description': 'Naval training establishment'
        },
        
        # Border Security & Coast Guard
        {
            'name': 'Pakistan Border Buffer Zone - Punjab',
            'center': [31.6040, 74.8723],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Pakistan Border Buffer Zone - Rajasthan',
            'center': [27.0238, 70.8022],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Pakistan Border Buffer Zone - Gujarat',
            'center': [23.7337, 68.8378],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Bangladesh Border Buffer Zone - West Bengal',
            'center': [22.6273, 88.7953],
            'radius': 10000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'Myanmar Border Buffer Zone - Mizoram',
            'center': [23.7271, 93.2551],
            'radius': 10000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'China Border Buffer Zone - Sikkim',
            'center': [27.6009, 88.9140],
            'radius': 15000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        {
            'name': 'China Border Buffer Zone - Ladakh',
            'center': [34.2996, 78.2932],
            'radius': 30000,
            'type': 'military',
            'description': 'International border restricted zone'
        },
        
        # Additional Ports
        {
            'name': 'Ennore Port',
            'center': [13.2167, 80.3167],
            'radius': 3000,
            'type': 'port',
            'description': 'Major port Tamil Nadu'
        },
        {
            'name': 'Jawaharlal Nehru Port Mumbai',
            'center': [18.9647, 72.9492],
            'radius': 4000,
            'type': 'port',
            'description': 'Container port Maharashtra'
        },
        {
            'name': 'Mundra Port',
            'center': [22.8395, 69.7937],
            'radius': 4000,
            'type': 'port',
            'description': 'Private port Gujarat'
        },
        {
            'name': 'Pipavav Port',
            'center': [20.9500, 71.0833],
            'radius': 3000,
            'type': 'port',
            'description': 'Container port Gujarat'
        },
        {
            'name': 'Kamarajar Port Ennore',
            'center': [13.2500, 80.3333],
            'radius': 3000,
            'type': 'port',
            'description': 'Coal import port'
        },
        
        # Oil Refineries & Petrochemical Complexes
        {
            'name': 'Mathura Refinery',
            'center': [27.4924, 77.6737],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery UP'
        },
        {
            'name': 'Panipat Refinery',
            'center': [29.3879, 76.9690],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Haryana'
        },
        {
            'name': 'Barauni Refinery',
            'center': [25.4816, 86.0336],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Bihar'
        },
        {
            'name': 'Digboi Refinery',
            'center': [27.3833, 95.6167],
            'radius': 2000,
            'type': 'refinery',
            'description': 'Asia\'s oldest refinery Assam'
        },
        {
            'name': 'Guwahati Refinery',
            'center': [26.1445, 91.7362],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Assam'
        },
        {
            'name': 'Bongaigaon Refinery',
            'center': [26.4609, 90.5501],
            'radius': 2000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Assam'
        },
        {
            'name': 'Haldia Refinery',
            'center': [22.0582, 88.0955],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery West Bengal'
        },
        {
            'name': 'Paradip Refinery',
            'center': [20.3180, 86.6503],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Odisha'
        },
        {
            'name': 'Chennai Refinery',
            'center': [13.1143, 80.3017],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Chennai Petroleum Corporation'
        },
        {
            'name': 'Mangalore Refinery',
            'center': [12.8697, 74.8860],
            'radius': 3000,
            'type': 'refinery',
            'description': 'MRPL refinery Karnataka'
        },
        {
            'name': 'Kochi Refinery',
            'center': [9.9816, 76.2999],
            'radius': 3000,
            'type': 'refinery',
            'description': 'BPCL refinery Kerala'
        },
        {
            'name': 'Mumbai Refinery',
            'center': [19.0330, 72.8570],
            'radius': 2000,
            'type': 'refinery',
            'description': 'BPCL refinery Maharashtra'
        },
        {
            'name': 'Vadodara Refinery',
            'center': [22.2587, 73.1394],
            'radius': 3000,
            'type': 'refinery',
            'description': 'Indian Oil refinery Gujarat'
        },
        
        # Research & Testing Facilities
        {
            'name': 'DRDO Chandipur',
            'center': [21.4500, 87.0167],
            'radius': 10000,
            'type': 'military',
            'description': 'Integrated test range Odisha'
        },
        {
            'name': 'DRDO Hyderabad Complex',
            'center': [17.4400, 78.4482],
            'radius': 5000,
            'type': 'military',
            'description': 'Defence research laboratories'
        },
        {
            'name': 'DRDO Pune Complex',
            'center': [18.5679, 73.9143],
            'radius': 3000,
            'type': 'military',
            'description': 'Armament research establishment'
        },
        {
            'name': 'Terminal Ballistics Research Laboratory',
            'center': [26.2124, 78.1772],
            'radius': 5000,
            'type': 'military',
            'description': 'Weapons testing facility Chandigarh'
        },
        {
            'name': 'High Energy Materials Research Laboratory',
            'center': [18.5204, 73.8567],
            'radius': 3000,
            'type': 'military',
            'description': 'Explosives research Pune'
        },
        
        # Central Government Security Zones
        {
            'name': 'Parliament House Complex',
            'center': [28.6172, 77.2082],
            'radius': 2000,
            'type': 'government',
            'description': 'Parliament and surrounding area'
        },
        {
            'name': 'Rashtrapati Bhavan Complex',
            'center': [28.6139, 77.1999],
            'radius': 1500,
            'type': 'government',
            'description': 'Presidential palace complex'
        },
        {
            'name': 'Supreme Court Complex',
            'center': [28.6229, 77.2397],
            'radius': 1000,
            'type': 'government',
            'description': 'Supreme Court of India'
        },
        {
            'name': 'PMO & South Block',
            'center': [28.6127, 77.2773],
            'radius': 1000,
            'type': 'government',
            'description': 'Prime Minister Office complex'
        },
        {
            'name': 'Reserve Bank of India Mumbai',
            'center': [18.9322, 72.8264],
            'radius': 500,
            'type': 'government',
            'description': 'Central bank headquarters'
        },
        
        # State Capital Security Zones
        {
            'name': 'Raj Bhavan Mumbai',
            'center': [18.9499, 72.8048],
            'radius': 1000,
            'type': 'government',
            'description': 'Maharashtra governor residence'
        },
        {
            'name': 'Vidhana Soudha Bangalore',
            'center': [12.9792, 77.5903],
            'radius': 1000,
            'type': 'government',
            'description': 'Karnataka state secretariat'
        },
        {
            'name': 'Fort St George Chennai',
            'center': [13.0840, 80.2892],
            'radius': 1000,
            'type': 'government',
            'description': 'Tamil Nadu secretariat'
        },
        {
            'name': 'Writers Building Kolkata',
            'center': [22.5726, 88.3639],
            'radius': 1000,
            'type': 'government',
            'description': 'West Bengal secretariat'
        },
        
        # Additional High-Security Installations
        {
            'name': 'CBI Headquarters',
            'center': [28.6139, 77.2090],
            'radius': 500,
            'type': 'government',
            'description': 'Central investigation agency'
        },
        {
            'name': 'Intelligence Bureau Delhi',
            'center': [28.6139, 77.2073],
            'radius': 500,
            'type': 'government',
            'description': 'Internal intelligence agency'
        },
        {
            'name': 'RAW Headquarters',
            'center': [28.6304, 77.2177],
            'radius': 1000,
            'type': 'government',
            'description': 'External intelligence agency'
        },
        
        # Emergency & Disaster Response Centers
        {
            'name': 'National Disaster Response Force HQ',
            'center': [28.5355, 77.3910],
            'radius': 1000,
            'type': 'government',
            'description': 'NDRF headquarters Ghaziabad'
        },
        
        # Communication & Satellite Facilities
        {
            'name': 'All India Radio Delhi',
            'center': [28.6139, 77.2090],
            'radius': 500,
            'type': 'government',
            'description': 'National broadcaster headquarters'
        },
        {
            'name': 'Doordarshan Kendra Delhi',
            'center': [28.6304, 77.2177],
            'radius': 500,
            'type': 'government',
            'description': 'National television broadcaster'
        },
        
        # VIP Helipads & Landing Sites
        {
            'name': 'Palam Technical Area',
            'center': [28.5665, 77.1031],
            'radius': 2000,
            'type': 'military',
            'description': 'VIP aircraft maintenance'
        },
        {
            'name': 'Safdarjung Airport',
            'center': [28.5843, 77.2058],
            'radius': 2000,
            'type': 'government',
            'description': 'Delhi flying club and emergency'
        }
    ]