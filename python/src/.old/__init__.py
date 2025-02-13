from datetime import datetime, timedelta
from opt import software
from opt import dojot
import opt.bess
import opt.pv
import time
import os

INTERVAL = os.environ.get('INTERVAL', 5) # minutes

#Define minimum power to charge a vehicle
Pmin = 1.5 #kW

class SYSTEM:
    def __init__(self, setup):
        self.Pmax = setup['Pmax']
        self.Pnom = setup['Pmax']
        self.Vnom = setup['Vnom']
        self.PPV  = 0
        self.controllable = setup['controllable']
        self.unavailable = []
        self.available = []
        self.charging  = []
        self.evcs = []
        self.bess = []
        self.bess_to_charge = []
        self.bess_to_discharge = []
        self.pv   = []
        self.v2g  = []

    def add_devices(self, setup):
        for evcs in software.get_evcs_by_setup_id(setup['id']):
            self.evcs.append(evcs)

        for bess in software.get_bess_by_setup_id(setup['id']):
            self.bess.append(bess)

        for pv in software.get_pv_by_setup_id(setup['id']):
            self.pv.append(pv)

        for v2g in software.get_v2g_by_setup_id(setup['id']):
            self.v2g.append(v2g)
        return
    
        
    def total_power(self):
        self.Ptotal = float(self.Pmax)
        for bess in self.bess:
            # check bess state of charge
            response = opt.bess.get_bess_measurements(bess['id'])
            reference = datetime.now() - timedelta(minutes=5)
    
            if response:
                date = datetime.strptime(response['date'], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=3)
                if date >= reference:
                    soc = float(response['soc'])/100
                    demand = (INTERVAL/60) * bess['Pmax']
                    if soc * bess['Emax'] > demand:
                        self.Ptotal += bess['Pmax']
                        self.bess_to_discharge.append(bess)
                    else:
                        self.bess_to_charge.append(bess)
                                
            self.Ptotal += bess['Pmax']
        for pv in self.pv:
            # check pv power generation
            reference = datetime.now() - timedelta(minutes=5)
            response = opt.pv.get_pv_measurements(pv['id'])
            if response:
                date = datetime.strptime(response['date'], "%Y-%m-%dT%H:%M:%S") - timedelta(hours=3)
                if datetime.strptime(response['date'], "%Y-%m-%dT%H:%M:%S") >= reference:
                    self.Ptotal += float(response['total_PV_generation'])/1000
                    self.PPV += float(response['total_PV_generation'])/1000
        
        for v2g in self.v2g:
            # check v2g state of charge
            for connector in range(1, v2g['nconn'] + 1):
                self.Ptotal += v2g[f'conn{connector}_Pmax']
    

    def evcs_status(self):
        par = software.get_timeconfig(1)
        for evcs in self.evcs:
            statusNotification = dojot.check_data(par["URL"], evcs['id'], "statusNotificationReq", 240)
            if statusNotification:
                if statusNotification['value']['status'] in ['Preparing', 'Charging', "Reserved"]:
                    self.charging.append(evcs)
                if statusNotification['value']['status'] in ["Available", "Finishing", "Unavailable", "Faulted", "SuspendedEV", "SuspendedEVSE"]:
                    self.available.append(evcs)
            else:
                heartbeat = dojot.check_data(par["URL"], evcs['id'], "heartbeatReq", 30)
                if heartbeat:
                    self.available.append(evcs)
                else:
                    self.unavailable.append(evcs)
                    if os.environ.get('SECURITY_MODE', "TRUE") != 'FALSE':
                        for connector in range(1, evcs['nconn'] + 1):
                             self.Ptotal = max(self.Ptotal - evcs[f'conn{connector}_Pmax'], 0)
                        print(f"EVCS {evcs['id']} is not sending data")
            time.sleep(1)

def optimize(setup):
    system = SYSTEM(setup)
    system.add_devices(setup)
    system.total_power()
    print("Checking EVCS status")
    system.evcs_status()
    print("Setting EVCS to its minimum power")
    Ptotal = system.Ptotal
    for evcs in system.available:
        if evcs is not None:
            for connector in range(1, evcs['nconn'] + 1):
                if evcs[f"conn{connector}_Pmax"] < 10:
                    Pmin = 1.5
                elif evcs[f"conn{connector}_Pmax"] < 30:
                    Pmin = 3
                elif evcs[f"conn{connector}_Pmax"] < 50:
                    Pmin = 5
                else:
                    Pmin = 10
    
                print(f'Setting EVCS {evcs["id"]} to {Pmin} kW')
                if evcs['control'] == 'current':
                    limit = int(Pmin * 1000 / evcs[f'conn{connector}_Vnom'])
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'A', limit)
                    print(data)                    
                    # verify if the limit is set correctly data should be {'status': 'Accepted'} but could be a empty dict
                    if data != {'status': 'Accepted'}: 
                        print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                        Ptotal = Ptotal - evcs[f'conn{connector}_Pmax']
                    else:
                        print(f'Success setting EVCS {evcs["id"]} to {limit} A')
                        Ptotal = Ptotal - Pmin

                    


                elif evcs['control'] == 'power':
                    limit = Pmin
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'W', limit * 1000)
                    print(data)
                    if data != {'status': 'Accepted'}: 
                        print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                        Ptotal = Ptotal - evcs[f'conn{connector}_Pmax']
                    else:
                        print(f'Success setting EVCS {evcs["id"]} to {limit} A')
                        Ptotal = Ptotal - Pmin

    print("Safe BESS operation")
    # estimate total ev charging usage
    Pestimated = 0
    for ev in system.charging:
        for connector in range(1, ev['nconn'] + 1):
            Pestimated += max(min((evcs[f'conn{connector}_Pmax'] * Ptotal)/Pmax_evcs,evcs[f'conn{connector}_Pmax']) ,0)

    if Pestimated - system.PPV > system.Pnom:
        Pbess = Pestimated - system.PPV
        for bess in system.bess_to_discharge:
            pdisp = min(Pbess, bess['Pmax'])
            status = opt.bess.send_command(bess['id'], pdisp)
            if status == {'status': 'Accepted'}:
                Pbess = Pbess - pdisp
            if Pbess < system.Pnom - system.PPV:
                break
    
    if Pbess > system.Pnom - system.PPV:
        print("operation is not safe")
        # set all charging ev to minimun
        for evcs in system.charging:
            for connector in range(1, evcs['nconn'] + 1):
                if evcs[f"conn{connector}_Pmax"] < 10:
                    Pmin = 1.5
                elif evcs[f"conn{connector}_Pmax"] < 30:
                    Pmin = 3
                elif evcs[f"conn{connector}_Pmax"] < 50:
                    Pmin = 5
                else:
                    Pmin = 10
    
                print(f'Setting EVCS {evcs["id"]} to {Pmin} kW')
                if evcs['control'] == 'current':
                    limit = int(Pmin * 1000 / evcs[f'conn{connector}_Vnom'])
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'A', limit)
                    print(data)                    
                    # verify if the limit is set correctly data should be {'status': 'Accepted'} but could be a empty dict
                    if data != {'status': 'Accepted'}: 
                        print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                        Ptotal = Ptotal - evcs[f'conn{connector}_Pmax']
                    else:
                        print(f'Success setting EVCS {evcs["id"]} to {limit} A')
                        Ptotal = Ptotal - Pmin
        return


    print(f"Total power for EV dispatch: {Ptotal} kW")
    print("Starting seending power to devices")
    Pmax_evcs = 0
    for evcs in system.charging:
        if evcs is not None:
            for connector in range(1, evcs['nconn'] + 1):
                Pmax_evcs += evcs[f'conn{connector}_Pmax']

    control = {}
    for evcs in system.charging:
        if evcs is not None:
            for connector in range(1, evcs['nconn'] + 1):
                if evcs['nconn'] == 1:
                    connector_id = 0
                else:
                    connector_id = evcs['connector_id']

                pdisp = max(min((evcs[f'conn{connector}_Pmax'] * Ptotal)/Pmax_evcs,evcs[f'conn{connector}_Pmax']) ,0)
                if evcs['control'] == 'current':
                    limit = int(pdisp * 1000 / evcs[f'conn{connector}_Vnom'])
                    control.update({(evcs["id"], connector_id): [limit, "A"]})
                elif evcs['control'] == 'power':    
                    limit = pdisp
                    control.update({(evcs["id"], connector_id): [limit, "W"]})
                

    # Activate BESS before EVCS   
    for bess in system.bess:
        # check bess state of charge
        print('BESS dispatch')


    for evcs, connector_id in control:
        limit = control[(evcs, connector_id)][0]
        unit = control[(evcs, connector_id)][1]
        print(f'Setting EVCS {evcs} to {limit} {unit}')
        data = dojot.set_charging_profile(evcs, connector_id, unit, limit)
        print(data)

    
    for v2g in system.v2g:
        # check v2g state of charge
        print('V2G dispatch') 

    return


def cron_function():
    setups = software.get_setups()
    for setup in setups:
        if setup is not None:
            optimize(setup)
    return


if __name__ == '__main__':
    cron_function()
