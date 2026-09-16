def failed_deployments(path:str):
    """
    Yield only failed deployments as (service, reason) tuples
    """

    with open(path) as f:
        for line in f:
            parts = line.split()

            if len(parts)!=4:
                continue

            _date, service, status, reason = parts
            if status =="FAILED":
                yield service,reason



if __name__ =="__main__":
    for service,reason in failed_deployments("test.log"):
        print(service,reason)



#check the lazy 
gen = failed_deployments("test.log")
print(type(gen))
print(next(gen))