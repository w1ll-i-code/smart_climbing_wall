#!/usr/bin/env bash
from flask import Flask
from flask import request
import requests
import json

ROUTES_STORAGE_PATH = '/var/lib/cw/routes.json'

class HandleMapping():
    ips = []
    mappings = []

    def __init__(self, found_handles):
        for ip, mapping in found_handles:
            self.ips.append(ip)
            if mapping is not None:
                self.set_new_mapping(ip, mapping)

            print(self.ips, self.mappings)

    def get_handles_with_mappings(self):
        selected = [False] * len(self.ips)
        handles_with_mappings = []

        for mapping, ip_index in enumerate(self.mappings):
            if ip_index is not None:
                selected[ip_index] = True
                handles_with_mappings.append({
                    'ip': self.ips[ip_index],
                    'mapping': mapping
                })

        for ip_index, selected in enumerate(selected):
            if not selected:
                handles_with_mappings.append({
                    'ip': self.ips[ip_index],
                    'mapping': None
                })
        
        return handles_with_mappings

    def set_new_mapping(self, ip, mapping):
        try:
            ip_index = self.ips.index(ip)
        except ValueError:
            return False

        try:
            remove = self.mappings.index(ip_index)
            self.mappings[remove] = None
        except ValueError:
            pass

        if mapping >= len(self.mappings):
            self.mappings.extend([None] * (mapping - len(self.mappings)))
            self.mappings.append(ip_index)
        else:
            self.mappings[mapping] = ip_index

        return True

    def collapse_mappings(self):
        # Todo: inform handles
        compressed = []
        for mapping in self.mappings:
            if mapping is not None:
                compressed.append(mapping)

    def get_ip_from_mapping(self, mapping):
        if mapping >= len(self.mappings):
            return None
        
        index = self.mappings[mapping]
        if index is None:
            return None
        
        return self.ips[index]


app = Flask(__name__)

@app.get('/handles/scan_network')
def map_handles():
    global available_handles

    found_handles = []
    for i in range(0, 255):
        ip = f"192.168.1.{i}"
        try:
            result = requests.get(f"http://{ip}/handle_id")
        except Exception:
            continue

        try:
            found_handles.append((ip, int(result.text)))
        except Exception:
            found_handles.append((ip, None))
        

    available_handles = HandleMapping(found_handles)


# Helper
def save_routes():
    global routes
    with open(ROUTES_STORAGE_PATH, 'w') as file:
        json.dump(routes, file)


# Route management
@app.get("/routes")
def get_all_routes():
    global routes
    return json.dumps(routes)

# Route management
@app.get("/routes/<route>")
def get_route(route):
    global routes
    found_route = routes.get(route)

    if found_route is None:
        return json.dumps({ 'error': 'Route not found' }), 404
    else:
        return json.dumps(found_route)


@app.put("/routes/<route>")
def create_route(route):
    global routes
    if route in routes.keys():
        return json.dumps({ 'error': 'Route exists already' }), 403
    else:
        routes[route] = request.json
        save_routes()
        return ""


@app.post("/routes/<route>")
def update_route(route):
    global routes
    if route in routes.keys():
        routes[route] = request.json
        save_routes()
        return ""
    else:
        return json.dumps({ 'error': 'Route not found' }), 404


@app.delete("/routes/<route>")
def delete_route(route):
    global routes
    routes.pop(route, None)
    save_routes()
    return ""


# Handle management
@app.get("/handle/mappings")
def get_handle_mappings():
    global available_handles
    return json.dumps(available_handles.get_handles_with_mappings())


@app.get('/handle/test/ip/<ip>')
def test_handle_by_ip(ip):
    # Todo: make request
    return f"Lighting up handle with ip {ip}"


@app.get('/handle/test/mapping/<id>')
def test_handle_by_mapping(id):
    global available_handles

    ip = available_handles.get_ip_from_mapping(int(id))
    if ip is None:
        return "", 404

    return test_handle_by_ip(ip)

@app.post('/handle/mapping/<mapping>')
def handle_set_mapping(mapping):
    global available_handles
    available_handles.set_new_mapping(request.json, int(mapping))
    return ""


# Brew coffee
@app.get('/brew_coffee')
def brew_coffee():
    return "I'm a climbing wall", 418












if __name__ == '__main__':
    # Load data from file
    with open(ROUTES_STORAGE_PATH, 'r') as file:
        routes = json.load(file)

    available_handles = HandleMapping([
        ('192.168.1.10', 1),
        ('192.168.1.11', 2),
        ('192.168.1.12', None),
        ('192.168.1.13', None),
    ])
    # map_handles()
    app.run()