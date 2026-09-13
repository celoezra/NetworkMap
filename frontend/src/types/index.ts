export interface Rack {
  id: number;
  name: string;
  location_description: string;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface VLAN {
  id: number;
  vlan_number: number;
  name: string;
  description?: string;
  subnet?: string;
  gateway?: string;
  created_at: string;
  updated_at: string;
}

export interface Location {
  id: number;
  name: string;
  sector?: string;
  floor?: string;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: number;
  name: string;
  hostname?: string;
  ip_address?: string;
  mac_address?: string;
  device_type: string;
  location_id?: number;
  vlan_id?: number;
  manufacturer?: string;
  model?: string;
  asset_tag?: string;
  serial_number?: string;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  location_name?: string;
  vlan_name?: string;
  connected_switch_id?: number;
  connected_switch_name?: string;
  connected_port_number?: number;
}

export interface SwitchPort {
  id: number;
  switch_id: number;
  port_number: number;
  name?: string;
  description?: string;
  vlan_id?: number;
  destination_location_id?: number;
  connected_device_id?: number;
  connection_type: string; // Access, Trunk, Uplink
  status: 'connected' | 'free' | 'uplink' | 'network_device' | 'issue';
  notes?: string;
  vlan_number?: number;
  vlan_name?: string;
  destination_location_name?: string;
  connected_device_name?: string;
  connected_device_ip?: string;
  connected_device_mac?: string;
  created_at: string;
  updated_at: string;
}

export interface Switch {
  id: number;
  name: string;
  hostname: string;
  manufacturer?: string;
  model?: string;
  ip_address?: string;
  mac_address?: string;
  port_count: number;
  rack_id?: number;
  rack_position?: string;
  notes?: string;
  rack_name?: string;
  ports: SwitchPort[];
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_racks: number;
  total_switches: number;
  total_ports: number;
  used_ports: number;
  free_ports: number;
  total_devices: number;
  total_vlans: number;
  total_locations: number;
}

export interface SearchResult {
  query: string;
  devices: Array<any>;
  switches: Array<any>;
  racks: Array<any>;
  locations: Array<any>;
  vlans: Array<any>;
  total_matches: number;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  user: string;
  action: string;
  entity_type: string;
  entity_id?: number;
  entity_name?: string;
  previous_values?: string;
  new_values?: string;
}
