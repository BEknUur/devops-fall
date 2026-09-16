class Endpoint:
    def __init__(self,host:str, port:int):
        if not isinstance(port,int) or isinstance(port,bool):
            raise ValueError(f"port must me the integer")

        if not 1<=port<=65535:
            raise ValueError(f"port out of range: {port}")


        self.host = host 
        self.port = port 

    @property
    def url(self):
        return f"http://{self.host}:{self.port}"


    #for debugging i use the repr 

    def __repr__(self):
         return f"Endpoint({self.host!r}, {self.port})"

        
