import requests

BASE_URL = "http://127.0.0.1:8000/api"

def seed():
    # 1. Racks
    r1 = requests.post(f"{BASE_URL}/racks", json={"name": "Rack Principal", "location_description": "CPD - Sala de TI", "description": "Rack principal dos servidores e switches core."})
    r1_json = r1.json() if r1.status_code == 201 else requests.get(f"{BASE_URL}/racks").json()[0]

    r2 = requests.post(f"{BASE_URL}/racks", json={"name": "Rack 3º Andar", "location_description": "Sala Técnica 3º Andar", "description": "Rack de distribuição do andar superior."})
    r2_json = r2.json() if r2.status_code == 201 else requests.get(f"{BASE_URL}/racks").json()[-1]

    # 2. VLANs
    requests.post(f"{BASE_URL}/vlans", json={"vlan_number": 10, "name": "Administrativo", "subnet": "10.10.10.0/24", "gateway": "10.10.10.1"})
    requests.post(f"{BASE_URL}/vlans", json={"vlan_number": 20, "name": "Consultórios", "subnet": "10.10.20.0/24", "gateway": "10.10.20.1"})
    requests.post(f"{BASE_URL}/vlans", json={"vlan_number": 30, "name": "Wi-Fi Corporativo", "subnet": "10.10.30.0/24", "gateway": "10.10.30.1"})

    vlans = requests.get(f"{BASE_URL}/vlans").json()
    v20 = [v for v in vlans if v["vlan_number"] == 20][0]
    v30 = [v for v in vlans if v["vlan_number"] == 30][0]

    # 3. Locations
    requests.post(f"{BASE_URL}/locations", json={"name": "Recepção", "sector": "Atendimento", "floor": "Térreo"})
    requests.post(f"{BASE_URL}/locations", json={"name": "Consultório 05", "sector": "Ambulatório", "floor": "1º Andar"})

    locs = requests.get(f"{BASE_URL}/locations").json()
    l_rec = [l for l in locs if l["name"] == "Recepção"][0]
    l_c05 = [l for l in locs if l["name"] == "Consultório 05"][0]

    # 4. Switches
    sw1_res = requests.post(f"{BASE_URL}/switches", json={
        "name": "SW-CORE-01", "hostname": "HOD-SW-CORE01", "ip_address": "10.10.10.2",
        "port_count": 24, "rack_id": r1_json["id"], "manufacturer": "Cisco", "model": "Catalyst 9300"
    })

    sw2_res = requests.post(f"{BASE_URL}/switches", json={
        "name": "Switch 01", "hostname": "HOD-SW01", "ip_address": "10.10.10.10",
        "port_count": 24, "rack_id": r2_json["id"], "manufacturer": "HP Aruba", "model": "2930F"
    })

    switches = requests.get(f"{BASE_URL}/switches").json()
    sw1 = [s for s in switches if s["hostname"] == "HOD-SW-CORE01"][0]
    sw2 = [s for s in switches if s["hostname"] == "HOD-SW01"][0]

    # 5. Devices
    pc1_res = requests.post(f"{BASE_URL}/devices", json={
        "name": "CONS05-PC01", "hostname": "CONS05-PC01", "ip_address": "10.10.20.35",
        "mac_address": "00:11:22:33:44:55", "device_type": "computador", "location_id": l_c05["id"], "vlan_id": v20["id"]
    })

    ap1_res = requests.post(f"{BASE_URL}/devices", json={
        "name": "AP-03", "hostname": "AP-03-REC", "ip_address": "10.10.30.5",
        "mac_address": "00:AA:BB:CC:DD:EE", "device_type": "access_point", "location_id": l_rec["id"], "vlan_id": v30["id"]
    })

    devices = requests.get(f"{BASE_URL}/devices").json()
    pc1 = [d for d in devices if d["name"] == "CONS05-PC01"][0]
    ap1 = [d for d in devices if d["name"] == "AP-03"][0]

    # Connect PC1 to Switch 01 Port 7
    requests.put(f"{BASE_URL}/switches/{sw2['id']}/ports/7", json={
        "vlan_id": v20["id"],
        "destination_location_id": l_c05["id"],
        "connected_device_id": pc1["id"],
        "description": "Ponto de rede do consultório 05"
    })

    # Connect AP1 to Switch 01 Port 18
    requests.put(f"{BASE_URL}/switches/{sw2['id']}/ports/18", json={
        "vlan_id": v30["id"],
        "destination_location_id": l_rec["id"],
        "connected_device_id": ap1["id"],
        "description": "Access Point Wi-Fi Corporativo"
    })

    # Create Uplink between SW-CORE-01 Port 24 and Switch 01 Port 1
    sp_core_24 = [p for p in sw1["ports"] if p["port_number"] == 24][0]
    sp_sw01_1 = [p for p in sw2["ports"] if p["port_number"] == 1][0]

    requests.post(f"{BASE_URL}/connections", json={
        "source_port_id": sp_core_24["id"],
        "target_port_id": sp_sw01_1["id"],
        "description": "Uplink Fibra Óptica 10Gbps"
    })

    print("Data seeded successfully!")

if __name__ == "__main__":
    seed()
