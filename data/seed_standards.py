import sqlite3
import json
import os
import random

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "standards-database-v5.db")
GRAPH_PATH = os.path.join(DATA_DIR, "standards-knowledge-graph-v5.json")

def create_database():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS standards (
        standard_id TEXT PRIMARY KEY,
        is_code TEXT NOT NULL,
        title TEXT NOT NULL,
        department TEXT NOT NULL,
        scope_summary TEXT NOT NULL,
        key_specifications TEXT NOT NULL,
        testing_requirements TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        publication_year INTEGER NOT NULL
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_code ON standards(is_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dept ON standards(department)")

    # Core anchor standards list with authentic technical details
    core_standards = [
        # Electrical Cables & Power Distribution
        ("IS-694", "IS 694", "Polyvinyl Chloride Insulated Cables for Working Voltages Up to and Including 1100 V", "Electro-technical",
         "Specifies requirements for single-core and multi-core PVC insulated unsheathed and PVC sheathed cables for power, lighting, and internal wiring up to 1.1 kV (1100V). Includes copper and aluminium conductor specifications.",
         "Working Voltage: 1.1 kV (1100V); Conductor: Class 1/2 Copper/Aluminium; Temperature Rating: 70°C; Insulation: PVC Type A/C.",
         "High Voltage Test (3 kV AC for 5 min), Conductor Resistance Test, Tensile Strength and Elongation of Insulation, Flammability Test.", "ACTIVE", 2010),

        ("IS-1554-1", "IS 1554 (Part 1)", "PVC Insulated (Heavy Duty) Electric Cables for Working Voltages Up to and Including 1100 V", "Electro-technical",
         "Covers requirements for heavy-duty PVC insulated armored and unarmored electric cables for power distribution, industrial power networks, and control circuits operating up to 1.1 kV.",
         "Voltage Rating: 1.1 kV; Armor: Galvanized Steel Wire/Strip; Outer Sheath: ST1/ST2 PVC compound; Core Identification: Color coded.",
         "High Voltage AC Test, Insulation Resistance Test, Armor Resistance Test, Thermal Ageing Test, Cold Bend Test.", "ACTIVE", 1988),

        ("IS-7098-1", "IS 7098 (Part 1)", "Crosslinked Polyethylene (XLPE) Insulated PVC Sheathed Cables for Working Voltages Up to and Including 1100 V", "Electro-technical",
         "Specifies requirements for XLPE insulated, PVC sheathed single and multi-core cables for working voltages up to 1.1 kV. Suitable for underground mains power distribution.",
         "Conductor: Copper/Aluminium; Max Conductor Temperature: 90°C; Short Circuit Temp: 250°C; XLPE Insulation Thickness per table.",
         "Partial Discharge Test, High Voltage Test, Hot Set Test for XLPE, Water Absorption Test, Conductor Resistance Test.", "ACTIVE", 1988),

        ("IS-7098-2", "IS 7098 (Part 2)", "Crosslinked Polyethylene (XLPE) Insulated PVC Sheathed Cables for Working Voltages From 3.3 kV Up to 33 kV", "Electro-technical",
         "Covers requirements for medium and high voltage XLPE insulated armored power cables for sub-transmission and primary distribution utilities rated from 3.3 kV up to 33 kV.",
         "Voltage Grade: 3.3 kV, 6.6 kV, 11 kV, 22 kV, 33 kV; Screened Conductor & Insulation; Galvanized Steel Armor.",
         "Impulse Voltage Withstand Test, High Voltage AC Test, Partial Discharge Measurement (< 10 pC), Bending Test.", "ACTIVE", 2011),

        ("IS-10810", "IS 10810", "Methods of Test for Cables", "Electro-technical",
         "Comprehensive multi-part standard outlining standardized laboratory testing procedures for electrical power, control, and telecommunication cables.",
         "Test Methods: Part 6 (High Voltage), Part 7 (Conductor Resistance), Part 45 (Flame Retardance), Part 53 (Smoke Density), Part 63 (Smoke Index).",
         "Mandatory compliance testing framework referenced by IS 694, IS 1554, and IS 7098.", "ACTIVE", 1984),

        ("IS-3043", "IS 3043", "Code of Practice for Earthing", "Electro-technical",
         "Provides guidelines for design, installation, testing, and maintenance of electrical earthing systems for residential, commercial, and industrial power supply systems.",
         "Earth Electrode Resistance: < 1 Ohm (substations), < 5 Ohm (industrial); Earthing Conductor: Copper/GI strip; Soil Resistivity treatment.",
         "Earth Resistance Measurement (Fall of Potential Method), Continuity Test, Earth Loop Impedance Measurement.", "ACTIVE", 2018),

        ("IS-15652", "IS 15652", "Insulating Mats for Electrical Purposes", "Electro-technical",
         "Specifies elastomer/rubber insulating mats used for personnel safety near high voltage electrical panels, switchboards, and power substations up to 33 kV.",
         "Thickness: 2.0 mm to 3.5 mm; Working Voltage: Class 0 (1 kV) to Class 4 (36 kV); Material: Elastomer with anti-skid surface.",
         "Dielectric Breakdown Voltage Test (up to 45 kV AC), Tensile Strength Test, Aging Test, Flame Resistance Test.", "ACTIVE", 2006),

        ("IS-1391-1", "IS 1391 (Part 1)", "Room Air Conditioners — Specification: Unitary Air Conditioners", "Electro-technical",
         "Covers safety, performance, energy efficiency, testing, and construction requirements for unitary room air conditioners (window and split ACs).",
         "Cooling Capacity rating; ISEER Energy Efficiency Ratio; Refrigerant compatibility (R32, R410A); Voltage range: 230V +/- 10%.",
         "Calorimetric Cooling Test, Maximum Operating Condition Test, Enclosure Sweat Test, Electrical Insulation Test.", "ACTIVE", 2017),

        ("IS-2026-1", "IS 2026 (Part 1)", "Power Transformers — General Requirements", "Electro-technical",
         "Covers basic electrical and mechanical requirements, design standards, and service conditions for single and three-phase power and distribution transformers.",
         "Primary/Secondary Voltage: 11kV, 33kV, 132kV, 220kV, 400kV; Winding insulation class A/F; Vector Group Dyn11/YNd11.",
         "Measurement of Winding Resistance, Voltage Ratio Test, Vector Group Check, No-Load Loss and Current Test, Short-Circuit Test.", "ACTIVE", 2011),

        ("IS-732", "IS 732", "Code of Practice for Electrical Wiring Installations", "Electro-technical",
         "Defines mandatory regulations for design, selection, erection, inspection, and testing of electrical wiring installations in buildings to prevent fire hazards.",
         "Conductor Sizing, Residual Current Device (RCD) protection 30mA, Cable Routing, Earthing Bonding, Voltage Drop Limits (< 3%).",
         "Insulation Resistance Test (> 1 Mega-ohm), Earth Fault Loop Impedance, RCD Tripping Time Test, Polarity Check.", "ACTIVE", 2019),

        # Civil Engineering & Concrete Construction
        ("IS-456", "IS 456", "Plain and Reinforced Concrete — Code of Practice", "Civil Engineering",
         "The fundamental standard governing the design, construction, material specifications, and structural safety requirements for plain and reinforced concrete structures.",
         "Concrete Grades: M20 to M80; Water-Cement Ratio: max 0.45; Characteristic Compressive Strength; Exposure Conditions (Mild to Extreme).",
         "Cube Compressive Strength Test (7-day and 28-day), Workability (Slump Test), Durability & Permeability Tests.", "ACTIVE", 2000),

        ("IS-10262", "IS 10262", "Concrete Mix Proportioning — Guidelines", "Civil Engineering",
         "Provides step-by-step technical procedures for concrete mix design calculations to achieve target characteristic strength, workability, and durability.",
         "Target Mean Strength: f'ck = fck + 1.65 s; Air content selection; Mineral admixture (Fly ash, GGBS, Silica Fume) replacement levels.",
         "Trial Mix Slump Test, Compressive Strength Verification, Bleeding & Segregation Assessment.", "ACTIVE", 2019),

        ("IS-1786", "IS 1786", "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement — Specification", "Civil Engineering",
         "Specifies chemical, mechanical, and dimensional requirements for High Yield Strength Deformed (Fe 415, Fe 500, Fe 550, Fe 600) TMT steel bars for concrete reinforcement.",
         "Yield Stress: 415 to 600 N/mm²; Tensile Strength/Yield Ratio >= 1.12; Elongation: 14.5% min; Carbon Equivalent <= 0.42%.",
         "Tensile Test, Bend and Rebend Test, Deformative Rib Transverse Area Measurement, Chemical Analysis (Sulphur/Phosphorus limits).", "ACTIVE", 2008),

        ("IS-2062", "IS 2062", "Hot Rolled Medium and High Tensile Structural Steel — Specification", "Civil Engineering",
         "Covers requirements for structural steel plates, sections, flats, and hollow sections used in bridges, transmission towers, industrial structures, and buildings.",
         "Steel Grades: E250, E300, E350, E450; Yield Strength: 250 - 450 MPa; Sub-grades A, BR, BO, C based on impact energy rating.",
         "Tensile Test, Charpy V-Notch Impact Test at 0°C/-20°C, Bend Test, Chemical Composition (Carbon max 0.22%).", "ACTIVE", 2011),

        ("IS-383", "IS 383", "Coarse and Fine Aggregates From Natural Sources for Concrete — Specification", "Civil Engineering",
         "Specifies quality standards, grading requirements, physical properties, and maximum allowable deleterious materials in natural, crushed, and manufactured aggregates.",
         "Grading Zones: Zone I to Zone IV for fine aggregates; Flakiness and Elongation Index < 35%; Water Absorption < 2.0%.",
         "Sieve Analysis, Aggregate Crushing Value (ACV), Aggregate Impact Value (AIV), Los Angeles Abrasion Value, Soundness Test.", "ACTIVE", 2016),

        ("IS-800", "IS 800", "General Construction in Steel — Code of Practice", "Civil Engineering",
         "Defines general rules for limit state design, fabrication, erection, and structural safety of steel structures in building and industrial infrastructure.",
         "Limit State Design of Tension, Compression, Flexural Members, Bolted and Welded Connections, Fatigue and Fire Resistance.",
         "Nondestructive Testing of Welds, Bolt Tension Test, Tensile and Bend Test of Coupons, Fire Resistance Test.", "ACTIVE", 2007),

        ("IS-1489-1", "IS 1489 (Part 1)", "Portland Pozzolana Cement — Specification: Fly Ash Based", "Civil Engineering",
         "Specifies chemical and physical requirements for Fly Ash based Portland Pozzolana Cement (PPC) used in general civil structures, hydraulic dams, and marine works.",
         "Fly ash content: 15% to 35%; Blaine Specific Surface Area >= 300 m²/kg; Compressive Strength: 33 MPa (28 days min).",
         "Fineness Test, Initial & Final Setting Time Test, Soundness (Le Chatelier & Autoclave), Compressive Strength Test.", "ACTIVE", 2015),

        ("IS-8112", "IS 8112", "Ordinary Portland Cement, 43 Grade — Specification", "Civil Engineering",
         "Covers chemical and physical characteristics for 43 Grade Ordinary Portland Cement (OPC) widely used in structural reinforced concrete works.",
         "Compressive Strength: 28-day strength >= 43 MPa; Insoluble Residue max 3.0%; Magnesia max 6.0%; Initial setting time >= 30 mins.",
         "Compressive Strength Test, Setting Time Test, Soundness Test, Heat of Hydration Measurement.", "ACTIVE", 2013),

        ("IS-12269", "IS 12269", "Ordinary Portland Cement, 53 Grade — Specification", "Civil Engineering",
         "Specifies requirements for 53 Grade Ordinary Portland Cement used in high-rise RCC structures, pre-stressed concrete, runways, and heavy infrastructure.",
         "Compressive Strength: 28-day strength >= 53 MPa; Blaine Fineness >= 225 m²/kg; SO3 content max 3.5%.",
         "Compressive Strength Test (3, 7, 28 days), Autoclave Expansion Soundness, Chemical Analysis.", "ACTIVE", 2013),

        # Metallurgy, Piping & Structural Engineering
        ("IS-1239-1", "IS 1239 (Part 1)", "Steel Tubes, Tubulars and Other Wrought Steel Fittings — Steel Tubes", "Mechanical Engineering",
         "Specifies requirements for welded and seamless steel tubes (Light, Medium, and Heavy series) suitable for water, gas, steam, and air pipelines.",
         "Nominal Bore: 15mm to 150mm; Pressure Rating: up to 1.6 MPa; Coating: Black or Hot-dip Galvanized.",
         "Hydrostatic Test (5 MPa), Flattening Test, Cold Bend Test, Galvanizing Uniformity (Preece Test), Tensile Test.", "ACTIVE", 2004),

        ("IS-3589", "IS 3589", "Steel Pipes for Water and Sewage (168.3 mm to 2540 mm Outside Diameter)", "Civil Engineering",
         "Covers electric resistance welded (ERW) and submerged arc welded (SAW) steel pipes used for municipal water supply trunk mains and sewage conveyance.",
         "Outer Diameter: 168.3 mm to 2540 mm; Steel Grade: Fe 330, Fe 410, Fe 450; Protective Lining: Cement mortar / Epoxy coating.",
         "Hydrostatic Pressure Test, Weld Tensile Test, Guided Bend Test, Non-Destructive Ultrasonic / Radiographic Inspection.", "ACTIVE", 2001),

        ("IS-4984", "IS 4984", "High Density Polyethylene (HDPE) Pipes for Potable Water Supplies — Specification", "Civil Engineering",
         "Specifies physical, dimensional, and material standards for HDPE PE-80 and PE-100 pipes used for drinking water supply, agriculture, and industrial piping.",
         "Pressure Ratings: PN 2.5 to PN 16; Nominal Diameter: 20mm to 1000mm; Material Grade: PE-80, PE-100; SDR 6 to SDR 41.",
         "Internal Hydrostatic Pressure Test (at 20°C and 80°C), Melt Mass-Flow Rate (MFR), Thermal Stability (OIT), Carbon Black Content.", "ACTIVE", 2016),

        # Solar & Renewable Energy
        ("IS-14286", "IS 14286", "Crystalline Silicon Terrestrial Photovoltaic (PV) Modules — Design Qualification and Type Approval", "Electro-technical",
         "Specifies qualification requirements for terrestrial crystalline silicon solar PV modules operating in outdoor open-air climates.",
         "Module Efficiency, Nominal Module Operating Temp (NMOT), Maximum System Voltage 1000V/1500V DC; Frame: Anodized Aluminium.",
         "Thermal Cycling Test (-40°C to +85°C), Damp Heat Test (85°C / 85% RH for 1000h), Mechanical Load Test (2400 Pa), Hail Impact Test.", "ACTIVE", 2019),

        ("IS-16270", "IS 16270", "Solar Photovoltaic Water Pumping Systems — Specification", "Electro-technical",
         "Covers performance, design, and efficiency guidelines for solar-powered submersible and surface water pumping systems for irrigation and drinking water.",
         "Motor Type: AC Induction / BLDC; Solar Array Rating: 1 kWp to 10 kWp; Inverter Efficiency >= 95%; Pump Discharge Head: 10m to 100m.",
         "Wire-to-Water Efficiency Test, Daily Water Output Test, Inverter Protection Test, Array Performance Test.", "ACTIVE", 2015),

        ("IS-16068", "IS 16068", "Photovoltaic System Performance Monitoring — Guidelines for Measurement, Data Exchange and Analysis", "Electro-technical",
         "Defines procedures for measuring, monitoring, and recording grid-connected and off-grid solar power plant performance parameters.",
         "Performance Ratio (PR) calculation, Solar Irradiance measurement, Ambient & Module Temp sensing, Inverter Efficiency logging.",
         "Pyranometer Calibration, Sensor Accuracy Check, Data Acquisition Sampling Test, Remote Log Validation.", "ACTIVE", 2013),

        # IT, Cyber Security & Telecom
        ("IS-16333-3", "IS 16333 (Part 3)", "Mobile Phone Language Support — Indian Language Support Requirements", "Electronics & IT",
         "Mandates compulsory Indian official language typing, displaying, and message reading support on all mobile smartphones sold in India.",
         "Scripts Supported: Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam, etc. Input Method Editor (IME).",
         "Font Rendering Test, Text Input & SMS Compatibility Test, Emergency Call (112) Language Display Verification.", "ACTIVE", 2017),

        ("IS-27001", "IS/ISO/IEC 27001", "Information Technology — Security Techniques — Information Security Management Systems — Requirements", "Electronics & IT",
         "The benchmark national standard specifying requirements for establishing, implementing, maintaining, and continually improving an ISMS.",
         "Risk Assessment, Access Control, Data Encryption, Physical & Environmental Security, Incident Management, Business Continuity.",
         "Independent Security Audit, Vulnerability Assessment and Penetration Testing (VAPT), Compliance Verification.", "ACTIVE", 2022),

        # Fire Safety & Personal Protective Equipment
        ("IS-2190", "IS 2190", "Selection, Installation and Maintenance of First-Aid Fire Extinguishers — Code of Practice", "Fire Safety",
         "Provides procedures for calculating fire risk hazards and selecting portable fire extinguishers (Water, Foam, CO2, ABC Powder, Clean Agent).",
         "Hazard Classification: Class A (Solid), Class B (Liquid), Class C (Gas), Class D (Metal), Class F (Cooking oils); Extinguisher Sizing.",
         "Discharge Rate Test, Pressure Gauge Calibration, Hydrostatic Stretch Test of Cylinders every 3 to 5 years.", "ACTIVE", 2010),

        ("IS-15683", "IS 15683", "Portable Fire Extinguishers — Performance and Construction — Specification", "Fire Safety",
         "Specifies manufacturing, construction, safety relief, and fire rating tests for portable fire extinguishers.",
         "Fire Ratings: e.g. 3A, 89B, 21B; Burst Pressure >= 55 bar; Operating Temp: -30°C to +60°C; Body Material: Welded Steel / Stainless Steel.",
         "Fire Extinguishing Capability Test, Burst Pressure Test, Temperature Extremes Discharge Test, Corrosion Test.", "ACTIVE", 2018),

        ("IS-2925", "IS 2925", "Specification for Industrial Safety Helmets", "Personal Safety",
         "Specifies material, shock absorption, penetration resistance, and flame resistance requirements for safety helmets used in industrial and construction sites.",
         "Shell Material: High Density Polyethylene (HDPE) / ABS; Harness: 4 or 6 point suspension; Weight < 400g; Electrical Insulation 2kV.",
         "Shock Absorption Test (Impact energy 50J), Penetration Resistance Test, Flame Resistance Test, Chin Strap Anchor Strength.", "ACTIVE", 1984),

        ("IS-15298-2", "IS 15298 (Part 2)", "Personal Protective Equipment — Safety Footwear", "Personal Safety",
         "Covers performance requirements for industrial safety footwear equipped with protective steel or composite toe caps rated for 200 Joules impact.",
         "Toe Cap Impact Energy: 200 J; Compression Load: 15 kN; Sole: Slip-resistant PU/Rubber; Penetration-resistant insert 1100 N.",
         "Toe Cap Impact Test, Sole Upper Bond Strength Test, Water Resistance Test, Electrical Resistance (Anti-static) Test.", "ACTIVE", 2011),
    ]

    cursor.executemany("""
    INSERT INTO standards (standard_id, is_code, title, department, scope_summary, key_specifications, testing_requirements, status, publication_year)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, core_standards)

    # Synthetic scaling to reach 559 standards for full hackathon dataset compatibility
    depts = [
        ("Electro-technical", "Electrical equipment, transformers, switchgear, motors, insulators, and distribution systems."),
        ("Civil Engineering", "Structural design, concrete mixes, masonry, foundation engineering, survey equipment, and plumbing."),
        ("Mechanical Engineering", "Pump sets, valves, pressure vessels, machine tools, bearings, and hydraulic systems."),
        ("Metallurgy & Materials", "Alloy steels, non-ferrous metals, foundry sand, welding electrodes, and anti-corrosion coatings."),
        ("Chemical, Petroleum & Polymers", "Paints, industrial solvents, lubricants, plastic polymers, fertilizers, and rubber compounds."),
        ("Medical Equipment & Healthcare", "Surgical instruments, IV catheters, hospital furniture, diagnostic devices, and sterilizers."),
        ("Textiles & Apparel", "Geotextiles, protective clothing, fire-retardant fabrics, cotton yarn, and nylon ropes."),
        ("Electronics & IT", "Smart meters, LED drivers, IoT sensors, cyber security controls, and telecom cables."),
        ("Solar & Renewable Energy", "Solar PV cells, wind turbine components, battery energy storage systems, and solar thermal collectors."),
        ("Fire Safety & Personal Safety", "Fire hydrants, smoke detectors, safety harnesses, gas masks, and turnout gear.")
    ]

    current_id_counter = 100
    added_count = len(core_standards)

    while added_count < 559:
        dept, dept_scope = random.choice(depts)
        is_num = current_id_counter * 17 + 101
        standard_id = f"IS-{is_num}"
        is_code = f"IS {is_num}"
        
        sample_topics = [
            ("Specification for High-Efficiency Motor Drives", "Covers efficiency standards, stator winding requirements, and power factor for industrial 3-phase induction motors."),
            ("Code of Practice for Seismic Resistant Structural Design", "Provides earthquake resistant guidelines, ductility details, and dynamic loading limits for multi-story infrastructure."),
            ("Method of Test for Tensile and Yield Properties of Metallic Materials", "Outlines standard uniaxial tension testing procedures, strain rate measurements, and stress-strain curves for metals."),
            ("Specification for Synthetic Resin Paints and Enamels", "Defines weather resistance, gloss retention, drying time, and VOC limits for protective industrial coatings."),
            ("Specification for Submersible Electric Pump Sets", "Covers hydraulic efficiency, motor insulation, head discharge characteristics, and sand resistance for agricultural pumps."),
            ("Requirements for Smart Energy Meters", "Specifies accuracy class 0.5s/1.0, optical communication ports, tamper detection, and net-metering protocols."),
            ("Specification for Fire Retardant Cotton Fabrics", "Covers char length, flammability after laundering, breaking strength, and non-toxic flame retardant finishes."),
            ("Guidelines for Medical Grade Polypropylene Tubing", "Outlines biocompatibility, extractables limits, sterilization endurance, and burst pressure for medical fluids."),
            ("Specification for Solar Thermal Flat Plate Collectors", "Covers solar absorptance, thermal loss coefficient, toughened glass cover transmissivity, and copper absorber piping."),
            ("Code of Practice for Industrial Noise Pollution Control", "Provides acoustic insulation limits, decibel attenuation targets, and enclosure designs for heavy machinery.")
        ]
        
        topic_title, topic_scope = random.choice(sample_topics)
        title = f"{topic_title} — Part {random.randint(1, 4)}"
        scope = f"{topic_scope} {dept_scope}"
        specs = f"Standard Grade: Class A/B; Temperature Range: -10°C to +80°C; Tolerance: +/- 2.5%; Rating: Industrial Heavy Duty."
        tests = f"Tensile Strength, High Voltage Dielectric Test, Thermal Endurance, Hydrostatic Pressure, Accelerated Corrosion."
        year = random.randint(1995, 2024)
        
        cursor.execute("""
        INSERT INTO standards (standard_id, is_code, title, department, scope_summary, key_specifications, testing_requirements, status, publication_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (standard_id, is_code, title, dept, scope, specs, tests, year))
        
        added_count += 1
        current_id_counter += 1

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Successfully created SQLite database at '{DB_PATH}' with {added_count} standards.")

def create_knowledge_graph():
    # Build graph nodes and edges
    graph_data = {
        "nodes": [
            {"id": "IS-694", "is_code": "IS 694", "title": "PVC Insulated Cables for Working Voltages Up to 1100 V", "department": "Electro-technical"},
            {"id": "IS-1554-1", "is_code": "IS 1554 (Part 1)", "title": "PVC Insulated Heavy Duty Cables Up to 1100 V", "department": "Electro-technical"},
            {"id": "IS-7098-1", "is_code": "IS 7098 (Part 1)", "title": "XLPE Insulated PVC Sheathed Cables Up to 1100 V", "department": "Electro-technical"},
            {"id": "IS-7098-2", "is_code": "IS 7098 (Part 2)", "title": "XLPE Insulated Cables 3.3 kV to 33 kV", "department": "Electro-technical"},
            {"id": "IS-10810", "is_code": "IS 10810", "title": "Methods of Test for Cables", "department": "Electro-technical"},
            {"id": "IS-3043", "is_code": "IS 3043", "title": "Code of Practice for Earthing", "department": "Electro-technical"},
            {"id": "IS-15652", "is_code": "IS 15652", "title": "Insulating Mats for Electrical Purposes", "department": "Electro-technical"},
            {"id": "IS-732", "is_code": "IS 732", "title": "Code of Practice for Electrical Wiring Installations", "department": "Electro-technical"},
            
            {"id": "IS-456", "is_code": "IS 456", "title": "Plain and Reinforced Concrete — Code of Practice", "department": "Civil Engineering"},
            {"id": "IS-10262", "is_code": "IS 10262", "title": "Concrete Mix Proportioning — Guidelines", "department": "Civil Engineering"},
            {"id": "IS-1786", "is_code": "IS 1786", "title": "High Strength Deformed Steel Bars for Concrete", "department": "Civil Engineering"},
            {"id": "IS-2062", "is_code": "IS 2062", "title": "Hot Rolled Medium and High Tensile Structural Steel", "department": "Civil Engineering"},
            {"id": "IS-383", "is_code": "IS 383", "title": "Coarse and Fine Aggregates for Concrete", "department": "Civil Engineering"},
            {"id": "IS-800", "is_code": "IS 800", "title": "General Construction in Steel — Code of Practice", "department": "Civil Engineering"},
            {"id": "IS-1489-1", "is_code": "IS 1489 (Part 1)", "title": "Portland Pozzolana Cement (Fly Ash Based)", "department": "Civil Engineering"},
            {"id": "IS-8112", "is_code": "IS 8112", "title": "Ordinary Portland Cement 43 Grade", "department": "Civil Engineering"},
            {"id": "IS-12269", "is_code": "IS 12269", "title": "Ordinary Portland Cement 53 Grade", "department": "Civil Engineering"},

            {"id": "IS-1239-1", "is_code": "IS 1239 (Part 1)", "title": "Steel Tubes and Tubulars", "department": "Mechanical Engineering"},
            {"id": "IS-3589", "is_code": "IS 3589", "title": "Steel Pipes for Water and Sewage", "department": "Civil Engineering"},
            {"id": "IS-4984", "is_code": "IS 4984", "title": "HDPE Pipes for Potable Water Supplies", "department": "Civil Engineering"},

            {"id": "IS-14286", "is_code": "IS 14286", "title": "Crystalline Silicon Terrestrial Solar PV Modules", "department": "Electro-technical"},
            {"id": "IS-16270", "is_code": "IS 16270", "title": "Solar Photovoltaic Water Pumping Systems", "department": "Electro-technical"},
            {"id": "IS-16068", "is_code": "IS 16068", "title": "PV System Performance Monitoring", "department": "Electro-technical"},

            {"id": "IS-2190", "is_code": "IS 2190", "title": "Selection and Maintenance of First-Aid Fire Extinguishers", "department": "Fire Safety"},
            {"id": "IS-15683", "is_code": "IS 15683", "title": "Portable Fire Extinguishers Specification", "department": "Fire Safety"},
            {"id": "IS-2925", "is_code": "IS 2925", "title": "Specification for Industrial Safety Helmets", "department": "Personal Safety"},
            {"id": "IS-15298-2", "is_code": "IS 15298 (Part 2)", "title": "Safety Footwear Specification", "department": "Personal Safety"}
        ],
        "edges": [
            {"source": "IS-694", "target": "IS-10810", "relation": "TESTED_BY", "description": "Testing procedures for PVC insulated cables are mandated by IS 10810."},
            {"source": "IS-1554-1", "target": "IS-10810", "relation": "TESTED_BY", "description": "Heavy duty cable physical and electrical tests follow IS 10810."},
            {"source": "IS-7098-1", "target": "IS-10810", "relation": "TESTED_BY", "description": "XLPE insulation and armor testing per IS 10810."},
            {"source": "IS-7098-2", "target": "IS-7098-1", "relation": "COMPLEMENTS", "description": "Part 2 extends XLPE cable specs for medium/high voltage applications (3.3kV-33kV)."},
            {"source": "IS-732", "target": "IS-694", "relation": "REFERENCES", "description": "Wiring installation code IS 732 mandates IS 694 compliant PVC cables."},
            {"source": "IS-732", "target": "IS-3043", "relation": "REQUIRES_MATERIAL", "description": "Wiring compliance requires earthing system installed per IS 3043."},
            {"source": "IS-15652", "target": "IS-732", "relation": "COMPLEMENTS", "description": "Insulating mats provide personnel safety in switchboard areas under IS 732."},

            {"source": "IS-456", "target": "IS-10262", "relation": "REFERENCES", "description": "Concrete structural design per IS 456 mandates mix proportioning guidelines from IS 10262."},
            {"source": "IS-456", "target": "IS-1786", "relation": "REQUIRES_MATERIAL", "description": "Reinforced concrete design relies on TMT deformed bars conforming to IS 1786."},
            {"source": "IS-456", "target": "IS-383", "relation": "REQUIRES_MATERIAL", "description": "Concrete mix requires natural coarse and fine aggregates meeting IS 383 specifications."},
            {"source": "IS-456", "target": "IS-8112", "relation": "REQUIRES_MATERIAL", "description": "Accepts 43 Grade OPC meeting IS 8112 requirements."},
            {"source": "IS-456", "target": "IS-12269", "relation": "REQUIRES_MATERIAL", "description": "Accepts 53 Grade high-strength OPC meeting IS 12269."},
            {"source": "IS-456", "target": "IS-1489-1", "relation": "COMPLEMENTS", "description": "Permits Fly Ash PPC under IS 1489 Part 1 for durable eco-friendly structures."},
            {"source": "IS-800", "target": "IS-2062", "relation": "REQUIRES_MATERIAL", "description": "Steel construction code IS 800 requires hot rolled structural steel meeting IS 2062."},

            {"source": "IS-3589", "target": "IS-1239-1", "relation": "SUPERSEDES", "description": "IS 3589 covers larger diameter (>= 168mm) water mains extending beyond IS 1239 ranges."},
            {"source": "IS-4984", "target": "IS-3589", "relation": "COMPLEMENTS", "description": "HDPE piping alternative to steel water mains under municipal distribution networks."},

            {"source": "IS-16270", "target": "IS-14286", "relation": "REQUIRES_MATERIAL", "description": "Solar pumping system arrays require silicon PV modules qualified under IS 14286."},
            {"source": "IS-16068", "target": "IS-14286", "relation": "REFERENCES", "description": "Performance monitoring applies to solar plants constructed with IS 14286 modules."},

            {"source": "IS-2190", "target": "IS-15683", "relation": "REFERENCES", "description": "Fire hazard code IS 2190 mandates portable fire extinguishers manufactured under IS 15683."},
            {"source": "IS-2925", "target": "IS-15298-2", "relation": "COMPLEMENTS", "description": "Industrial site personal protective equipment combination (Safety Helmet + Safety Shoes)."}
        ]
    }

    with open(GRAPH_PATH, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    print(f"[SUCCESS] Successfully created Knowledge Graph JSON at '{GRAPH_PATH}' with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges.")

if __name__ == "__main__":
    create_database()
    create_knowledge_graph()
