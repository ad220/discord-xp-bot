from .server import Server

class Cache():
    def __init__(self):
        self.data: dict[int:Server] = {}
    
    def get_server(self, server_id: int) -> Server:
        return self.data.get(server_id, None)
    
    def add_server(self, server: Server):
        self.data[server.id] = server

    def rm_server(self, server_id: int):
        del self.data[server_id]
    
    def update_server_config(self, server: Server):
        self.data[server.id] = server
