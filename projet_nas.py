import json

nombre_router_AS=0

def ipv4(adresse_ip,number):
    adresse_ip = adresse_ip.split('/')
    adresse_ip = adresse_ip[0]
    adresse_ip = adresse_ip +"."+ number +" "+"255.255.255.252"
    return adresse_ip


def read_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {file_path}.")
        return None

def create_cfg_config(base_server_config, router, intent, AS):
    global nombre_router_AS

    with open(f'i{router[-1]}_startup-config.cfg', 'w') as file:
        number=router[-1]
        for sentence in base_server_config:
            file.write(sentence + '\n!\n')
            protocol=intent[AS]['protocol']
            ebgp_neighbor=False
            if sentence == "service timestamps log datetime msec":
                file.write(f"hostname {router}\n")
            elif sentence == "ip tcp synwait-time 5":
                #mise en place de l'interface loopback
                if "address_loopback" in intent[AS]:
                    loopback_addr = intent[AS]['address_loopback']
                    loopback_addr = loopback_addr[0].split('/')
                    loopback = loopback_addr[0]+"."+str(number)

                    file.write(f"interface Loopback0\n ip address {loopback} 255.255.255.255\n")
                    file.write(" ip ospf 1 area 0\n")
                    file.write("!\n")
                #IPV4
                for router_other in intent[AS]['router'][router]:
                    if router_other == "ebgp_neighbors":
                        continue
                    if len(intent[AS]['router'][router][router_other]) > 2 and intent[AS]['router'][router][router_other] != "GigabitEthernet 1/0":
                        file.write(f"interface {intent[AS]['router'][router][router_other]}\n" 
                               f" ip address {ipv4(intent[AS]['address'][0],str(nombre_router_AS))}\n")
                    else:
                        file.write(f"interface {intent[AS]['router'][router][router_other]}\n" 
                               f" ip address {ipv4(intent[AS]['address'][0],str(nombre_router_AS))}\n")
                    nombre_router_AS+=1
                    print(nombre_router_AS)
                    
                    file.write(" ip ospf 1 area 0\n")
                    file.write(" negotiation auto\n mpls ip\n")
                    file.write("!\n")


                #CONFIGURATION OSPF
                file.write("router ospf 1\n")
                file.write(f" router-id {str(number)+'.'+str(number)+'.'+str(number)+'.'+str(number)}\n")
                file.write(" mpls ldp autoconfig\n")
                file.write("!\n")


def main(intent, base_server_config):
    global nombre_router_AS
    for AS in intent:
        nombre_router_AS = 1

        for router in intent[AS]["router"]:
            create_cfg_config(base_server_config, router, intent, AS)

if __name__ == "__main__":
    base_server_config = [
        "version 15.2",
        "service timestamps debug datetime msec",
        "service timestamps log datetime msec",
        "boot-start-marker",
        "boot-end-marker",
        "no aaa new-model",
        "no ip icmp rate-limit unreachable",
        "ip cef",
        "no ip domain lookup",
        "no ipv6 cef",
        "multilink bundle-name authenticated",
        "ip tcp synwait-time 5",
        "ip forward-protocol nd",
        "no ip http server",
        "no ip http secure-server",
        "control-plane",
        "line con 0",
        " exec-timeout 0 0",
        " privilege level 15",
        " logging synchronous",
        " stopbits 1",
        "line aux 0",
        " exec-timeout 0 0",
        " privilege level 15",
        " logging synchronous",
        " stopbits 1",
        "line vty 0 4",
        " login",
        "end"
    ]

    intent = read_json("router.json")
    if intent:
        main(intent, base_server_config)


                        # # Configuration iBGP avec tous les routeurs du même AS
                # for peer in intent[AS]['router']:
                #     if peer != router:
                #         peer_loopback = intent[AS]['router'][peer].get("Loopback0", "")
                #         if peer_loopback:
                #             peer_ip = peer_loopback.split('/')[0]
                #             file.write(f" neighbor {peer_ip} remote-as {as_number}\n")
                #             file.write(f" neighbor {peer_ip} update-source Loopback0\n")
                #             file.write(f" neighbor {peer_ip} next-hop-self\n")

                #             neighbors.append(peer_ip)
