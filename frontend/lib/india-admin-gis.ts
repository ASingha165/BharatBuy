/**
 * Administrative Reference Boundaries and Operational Logistics GIS Dataset
 * 
 * Sourced from BharatBuy static GIS reference geometries (administrative context)
 * and Indian National Highway corridor reference paths.
 * Packaged locally for administrative and operational logistics context in Hybrid map mode.
 */

// 1. India National Boundary and State Administrative Boundaries (GeoJSON FeatureCollection)
export const INDIA_ADMIN_GEOJSON: any = {
  type: 'FeatureCollection',
  features: [
    // India National Perimeter Outline
    {
      type: 'Feature',
      properties: {
        name: 'Republic of India',
        category: 'NATIONAL_BOUNDARY',
        authority: 'Administrative context — BharatBuy static GIS dataset',
        type: 'National Boundary Outline'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [74.5, 37.1], [77.8, 35.5], [79.0, 34.3], [79.5, 32.5], [81.0, 30.3],
            [88.2, 27.8], [88.9, 27.3], [91.5, 27.9], [97.4, 28.3], [96.2, 26.5],
            [95.2, 24.2], [93.1, 23.7], [92.2, 22.0], [89.0, 21.6], [87.0, 21.5],
            [85.0, 19.5], [83.3, 17.7], [80.3, 13.1], [79.8, 10.3], [77.5, 8.1],
            [76.3, 9.5], [74.8, 12.8], [73.8, 15.5], [72.8, 19.0], [72.7, 21.0],
            [68.5, 23.5], [70.5, 24.5], [71.0, 27.5], [74.0, 30.5], [74.5, 32.5],
            [74.5, 37.1]
          ]
        ]
      }
    },
    // Northern Zone - Jammu & Kashmir, Ladakh, Punjab, Haryana, Delhi NCR, UP
    {
      type: 'Feature',
      properties: { name: 'Ladakh & Jammu & Kashmir', code: 'IN-JK', zone: 'Northern', capital: 'Srinagar / Leh' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[73.5, 33.0], [74.5, 37.1], [77.8, 35.5], [79.0, 34.3], [77.5, 32.5], [74.5, 32.5], [73.5, 33.0]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Punjab & Haryana', code: 'IN-PB-HR', zone: 'Northern', capital: 'Chandigarh', industrial_hub: 'Ludhiana Corridor' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[74.0, 30.0], [76.5, 31.0], [77.5, 30.5], [77.3, 28.5], [75.5, 28.0], [74.0, 30.0]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'National Capital Region (Delhi)', code: 'IN-DL', zone: 'Northern', capital: 'New Delhi', industrial_hub: 'Okhla Industrial Area' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[76.8, 28.4], [77.3, 28.9], [77.4, 28.4], [76.9, 28.3], [76.8, 28.4]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Uttar Pradesh', code: 'IN-UP', zone: 'Northern', capital: 'Lucknow', industrial_hub: 'Kanpur / Noida Corridor' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[77.3, 28.5], [77.8, 30.0], [80.5, 28.8], [84.0, 27.3], [83.0, 24.5], [78.5, 24.5], [77.3, 28.5]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Rajasthan', code: 'IN-RJ', zone: 'Western', capital: 'Jaipur', industrial_hub: 'Bhiwadi / Neemrana' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[71.0, 27.5], [74.0, 30.0], [77.0, 28.0], [77.0, 26.5], [74.5, 24.0], [71.5, 24.5], [71.0, 27.5]]]
      }
    },
    // Western Zone - Gujarat, Maharashtra, Goa
    {
      type: 'Feature',
      properties: { name: 'Gujarat', code: 'IN-GJ', zone: 'Western', capital: 'Gandhinagar', industrial_hub: 'Sanand & Vadodara Clusters' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[68.5, 23.5], [71.5, 24.5], [74.0, 22.0], [73.0, 20.5], [71.0, 21.0], [69.5, 22.5], [68.5, 23.5]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Maharashtra', code: 'IN-MH', zone: 'Western', capital: 'Mumbai', industrial_hub: 'Mumbai-Pune-Nagpur Industrial Belt' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[72.8, 19.0], [73.0, 21.5], [78.5, 21.5], [80.5, 19.0], [77.0, 16.0], [73.5, 16.0], [72.8, 19.0]]]
      }
    },
    // Central & Eastern Steel / Mineral Zone - MP, Chhattisgarh, Jharkhand, Odisha, West Bengal, Bihar
    {
      type: 'Feature',
      properties: { name: 'Madhya Pradesh', code: 'IN-MP', zone: 'Central', capital: 'Bhopal', industrial_hub: 'BHEL Bhopal & Pithampur' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[74.5, 24.0], [78.5, 24.5], [82.5, 24.0], [82.0, 21.5], [76.0, 21.5], [74.5, 24.0]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Chhattisgarh', code: 'IN-CT', zone: 'Central', capital: 'Raipur', industrial_hub: 'SAIL Bhilai Steel Complex' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[80.5, 23.5], [83.5, 23.5], [83.0, 18.0], [80.5, 18.5], [80.5, 23.5]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Jharkhand', code: 'IN-JH', zone: 'Eastern', capital: 'Ranchi', industrial_hub: 'SAIL Bokaro & Jamshedpur Industrial Belt' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[83.5, 24.5], [87.5, 24.5], [87.0, 22.0], [84.0, 22.0], [83.5, 24.5]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Odisha', code: 'IN-OD', zone: 'Eastern', capital: 'Bhubaneswar', industrial_hub: 'Kalinga Nagar Industrial Complex' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[83.0, 22.0], [87.0, 22.0], [87.0, 21.5], [85.0, 19.5], [82.5, 18.0], [83.0, 22.0]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'West Bengal & Bihar', code: 'IN-WB-BR', zone: 'Eastern', capital: 'Kolkata / Patna', industrial_hub: 'Durgapur-Asansol & Haldia' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[84.0, 27.5], [88.5, 27.0], [89.0, 21.5], [87.0, 22.0], [83.5, 24.5], [84.0, 27.5]]]
      }
    },
    // Southern Zone - Karnataka, Tamil Nadu, Andhra Pradesh, Telangana, Kerala
    {
      type: 'Feature',
      properties: { name: 'Karnataka', code: 'IN-KA', zone: 'Southern', capital: 'Bengaluru', industrial_hub: 'Peenya Industrial Area & ITI Bengaluru' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[74.0, 15.0], [77.5, 18.0], [78.5, 13.5], [77.0, 11.5], [75.0, 12.0], [74.0, 15.0]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Tamil Nadu', code: 'IN-TN', zone: 'Southern', capital: 'Chennai', industrial_hub: 'Sriperumbudur & Coimbatore Corridors' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[77.0, 13.5], [80.3, 13.1], [79.8, 10.3], [77.5, 8.1], [76.5, 10.0], [77.0, 13.5]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Andhra Pradesh & Telangana', code: 'IN-AP-TS', zone: 'Southern', capital: 'Hyderabad / Amaravati', industrial_hub: 'Visakhapatnam & Hyderabad Corridors' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[77.5, 18.0], [81.0, 19.0], [83.5, 17.5], [80.0, 14.0], [78.0, 14.0], [77.5, 18.0]]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Kerala', code: 'IN-KL', zone: 'Southern', capital: 'Thiruvananthapuram', industrial_hub: 'Kochi Industrial Corridor' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[75.0, 12.0], [76.5, 11.5], [77.5, 8.5], [76.3, 9.5], [75.0, 12.0]]]
      }
    },
    // North-Eastern Zone
    {
      type: 'Feature',
      properties: { name: 'North-Eastern States', code: 'IN-NE', zone: 'North-Eastern', capital: 'Guwahati', industrial_hub: 'Guwahati Logistics Hub' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[89.5, 26.5], [94.0, 28.0], [97.0, 28.0], [95.0, 24.0], [92.0, 23.0], [90.0, 25.0], [89.5, 26.5]]]
      }
    }
  ]
};

// 2. Official District Administrative Context (Key Sourcing Districts)
export interface IndiaDistrictContext {
  id: string;
  district: string;
  state: string;
  coordinates: [number, number]; // [lat, lng]
  sourcingCorridor: string;
  category: string;
}

export const INDIA_KEY_SOURCING_DISTRICTS: IndiaDistrictContext[] = [
  { id: 'DIST-01', district: 'Bengaluru Urban', state: 'Karnataka', coordinates: [13.0315, 77.5186], sourcingCorridor: 'Peenya Industrial Area', category: 'ELECTRICAL_ELECTRONICS' },
  { id: 'DIST-02', district: 'Vadodara', state: 'Gujarat', coordinates: [22.3072, 73.1812], sourcingCorridor: 'Makarpura Industrial Estate', category: 'POWER_EQUIPMENT' },
  { id: 'DIST-03', district: 'East Singhbhum', state: 'Jharkhand', coordinates: [22.8046, 86.2029], sourcingCorridor: 'Jamshedpur Industrial Belt', category: 'STEEL_METALLURGY' },
  { id: 'DIST-04', district: 'Bokaro', state: 'Jharkhand', coordinates: [23.6693, 86.1511], sourcingCorridor: 'SAIL Bokaro Steel City', category: 'HEAVY_STEEL' },
  { id: 'DIST-05', district: 'Jajpur', state: 'Odisha', coordinates: [20.8524, 85.9682], sourcingCorridor: 'Kalinga Nagar Industrial Complex', category: 'STEEL_MINERALS' },
  { id: 'DIST-06', district: 'Bhopal', state: 'Madhya Pradesh', coordinates: [23.2599, 77.4126], sourcingCorridor: 'BHEL Heavy Electricals Hub', category: 'POWER_ELECTRICAL' },
  { id: 'DIST-07', district: 'Durg', state: 'Chhattisgarh', coordinates: [21.1938, 81.2849], sourcingCorridor: 'SAIL Bhilai Steel Plant', category: 'RAIL_STRUCTURAL_STEEL' },
  { id: 'DIST-08', district: 'Ahmedabad', state: 'Gujarat', coordinates: [22.9868, 72.3789], sourcingCorridor: 'Sanand Industrial Cluster', category: 'AUTOMOTIVE_SOLAR' },
  { id: 'DIST-09', district: 'South East Delhi', state: 'Delhi', coordinates: [28.5355, 77.2732], sourcingCorridor: 'Okhla Industrial Area', category: 'IT_HARDWARE_ELECTRONICS' },
  { id: 'DIST-10', district: 'Coimbatore', state: 'Tamil Nadu', coordinates: [11.0168, 76.9558], sourcingCorridor: 'Coimbatore Pump & Valve Cluster', category: 'PRECISION_ENGINEERING' },
  { id: 'DIST-11', district: 'Kanchipuram', state: 'Tamil Nadu', coordinates: [12.9815, 79.9702], sourcingCorridor: 'Sriperumbudur Electronics Belt', category: 'TELECOM_ELECTRONICS' },
  { id: 'DIST-12', district: 'Ludhiana', state: 'Punjab', coordinates: [30.9010, 75.8573], sourcingCorridor: 'Ludhiana Industrial Cluster', category: 'FASTENERS_ENGINEERING' }
];

// 3. Operational Freight & Highway Logistics Corridors (Connecting Procurement Matrix Hubs)
export interface IndiaLogisticsCorridor {
  name: string;
  highwayCode: string;
  description: string;
  coordinates: [number, number][]; // Array of [lat, lng]
}

export const INDIA_LOGISTICS_CORRIDORS: IndiaLogisticsCorridor[] = [
  {
    name: 'Western Industrial Freight Spine (Golden Quadrilateral West)',
    highwayCode: 'NH-48',
    description: 'Connects Delhi NCR, Neemrana, Jaipur, Ahmedabad, Vadodara, Mumbai, Pune, Peenya (Bengaluru)',
    coordinates: [
      [28.5355, 77.2732], // Delhi Okhla
      [27.9150, 76.3860], // Neemrana
      [26.9124, 75.7873], // Jaipur
      [24.5854, 73.7125], // Udaipur
      [23.0225, 72.5714], // Ahmedabad
      [22.3072, 73.1812], // Vadodara
      [21.1702, 72.8311], // Surat
      [19.0760, 72.8777], // Mumbai
      [18.5204, 73.8567], // Pune
      [15.3647, 75.1240], // Hubballi
      [13.0315, 77.5186]  // Peenya Bengaluru
    ]
  },
  {
    name: 'Eastern Industrial & Mineral Corridor (Golden Quadrilateral East)',
    highwayCode: 'NH-19',
    description: 'Connects Delhi NCR, Agra, Kanpur, Bokaro, Jamshedpur, Durgapur, Kolkata',
    coordinates: [
      [28.5355, 77.2732], // Delhi
      [27.1767, 78.0081], // Agra
      [26.4499, 80.3319], // Kanpur
      [25.3176, 82.9739], // Varanasi
      [23.6693, 86.1511], // Bokaro Steel City
      [22.8046, 86.2029], // Jamshedpur
      [23.5204, 87.3119], // Durgapur
      [22.5726, 88.3639]  // Kolkata
    ]
  },
  {
    name: 'East Coast Heavy Steel & Marine Corridor',
    highwayCode: 'NH-16',
    description: 'Connects Kolkata, Kalinga Nagar, Bhubaneswar, Visakhapatnam, Chennai, Sriperumbudur',
    coordinates: [
      [22.5726, 88.3639], // Kolkata
      [20.8524, 85.9682], // Kalinga Nagar
      [20.2961, 85.8245], // Bhubaneswar
      [17.6868, 83.2185], // Visakhapatnam
      [13.0827, 80.2707], // Chennai
      [12.9815, 79.9702]  // Sriperumbudur
    ]
  },
  {
    name: 'Central Industrial Energy Corridor',
    highwayCode: 'NH-44 / NH-46',
    description: 'Connects Delhi NCR, Gwalior, BHEL Bhopal, Nagpur, Hyderabad, Bengaluru',
    coordinates: [
      [28.5355, 77.2732], // Delhi
      [26.2183, 78.1828], // Gwalior
      [23.2599, 77.4126], // Bhopal BHEL
      [21.1458, 79.0882], // Nagpur
      [17.3850, 78.4867], // Hyderabad
      [13.0315, 77.5186]  // Bengaluru Peenya
    ]
  },
  {
    name: 'Steel & Metallurgy Logistics Arc',
    highwayCode: 'NH-53',
    description: 'Connects SAIL Bhilai, Raipur, Sambalpur, Kalinga Nagar, Jamshedpur',
    coordinates: [
      [21.1938, 81.2849], // Bhilai Steel Plant
      [21.2514, 81.6296], // Raipur
      [21.4669, 83.9812], // Sambalpur
      [20.8524, 85.9682], // Kalinga Nagar
      [22.8046, 86.2029]  // Jamshedpur
    ]
  }
];
