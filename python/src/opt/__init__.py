from datetime import datetime, timedelta
from opt import software
from opt import dojot
import numpy as np
import opt.bess
import opt.pv
import time
import os

INTERVAL = os.environ.get('INTERVAL', 5) # minutes
SECURITY_MODE = os.environ.get('SECURITY_MODE', "TRUE")
NOTIFICATION = os.environ.get('NOTIFICATION', "TRUE")

#Define minimum power to charge a vehicle
Pmin = 1.5 #kW

class SYSTEM:
    def __init__(self, setup):
        self.Pmax = setup['Pmax']
        self.Pnom = setup['Pmax']
        self.Vnom = setup['Vnom']
        self.controllable = setup['controllable']
        self.unavailable = []
        self.available = []
        self.charging  = []
        self.evcs = []
        self.bess = []
        self.bess_to_charge = []
        self.bess_to_discharge = []
        self.bess_half_charged = []
        self.pv   = []
        self.v2g  = []
        self.PPV  = 0
        self.PEV  = 0

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
            if NOTIFICATION: print(f"Response from BESS {bess['id']}: {response}")
            reference = datetime.now() - timedelta(minutes=5)
            if NOTIFICATION: print(response)
            if NOTIFICATION: print(f'reference: {reference}')
            if response:
                date = datetime.strptime(response['date'], "%Y-%m-%dT%H:%M:%S")
                if date >= reference:
                    soc = float(response['battery_level'])/100
                    demand = (INTERVAL/60) * bess['Pmax']
                    if soc <= 0.5:
                        self.bess_half_charged.append(bess)
                    if soc * bess['Emax'] > demand:
                        self.Ptotal += bess['Pmax']
                        self.bess_to_discharge.append(bess)
                    else:
                        self.bess_to_charge.append(bess)
                                
            
        for pv in self.pv:
            # check pv power generation
            reference = datetime.now() - timedelta(minutes=10)
            response = opt.pv.get_pv_measurements(pv['id'])
            if response:
                date = datetime.strptime(response['date'], "%Y-%m-%dT%H:%M:%S")
                if datetime.strptime(response['date'], "%Y-%m-%dT%H:%M:%S") >= reference:
                    self.Ptotal += float(response['total_DC_power'])/1000
                    self.PPV += float(response['total_DC_power'])/1000
                    if NOTIFICATION: print(f"PV {pv['id']} power: {float(response['total_DC_power'])}W")
        
        for v2g in self.v2g:
            # check v2g state of charge
            for connector in range(1, v2g['nconn'] + 1):
                self.Ptotal += v2g[f'conn{connector}_Pmax']
    

    def evcs_status(self):
        if NOTIFICATION: print("Checking EVCS status")
        par = software.get_timeconfig(1)
        for evcs in self.evcs:
            protocol, statusNotification = dojot.check_data(par["URL"], evcs['id'], "statusNotificationReq", 240)
            evcs['protocol'] = protocol
            if statusNotification:
                if protocol == "OCPP 2.0.1":
                    if statusNotification['value']['connectorStatus'] in ['Preparing', 'Charging', "Reserved"]:
                        self.charging.append(evcs)
                    if statusNotification['value']['connectorStatus'] in ["Available", "Finishing", "Unavailable", "Faulted", "SuspendedEV", "SuspendedEVSE"]:
                        self.available.append(evcs)
                elif protocol == "OCPP 1.6":
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
                        if NOTIFICATION: print(f"EVCS {evcs['id']} is not sending data")
            time.sleep(1)

def optimize(setup):
    system = SYSTEM(setup)
    system.add_devices(setup)
    system.total_power()
    system.evcs_status()


    if NOTIFICATION: print("Setting EVCS to its minimum power")
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
    
                if NOTIFICATION: print(f'Setting EVCS {evcs["id"]} to {Pmin} kW')
                if evcs['control'] == 'current':
                    limit = int(Pmin * 1000 / evcs[f'conn{connector}_Vnom'])
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'A', limit, evcs['protocol'])
                    if NOTIFICATION: print(data)                    
                    # verify if the limit is set correctly data should be {'status': 'Accepted'} but could be a empty dict
                    if data != {'status': 'Accepted'}: 
                        if NOTIFICATION: print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                        system.Ptotal = system.Ptotal - evcs[f'conn{connector}_Pmax']
                    else:
                        if NOTIFICATION: print(f'Success setting EVCS {evcs["id"]} to {limit} A')
                        system.Ptotal = system.Ptotal - Pmin

                
                elif evcs['control'] == 'power':
                    limit = Pmin
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'W', limit * 1000, evcs['protocol'])
                    print(data)
                    if data != {'status': 'Accepted'}: 
                        print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                        system.Ptotal = system.Ptotal - evcs[f'conn{connector}_Pmax']
                    else:
                        print(f'Success setting EVCS {evcs["id"]} to {limit} A')
                        system.Ptotal = system.Ptotal - Pmin

    
    if NOTIFICATION: print(f"Total power for EV dispatch: {system.Ptotal} kW")
    if NOTIFICATION: print("Starting seending power to devices")
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

                pdisp = max(min((evcs[f'conn{connector}_Pmax'] * system.Ptotal)/Pmax_evcs, evcs[f'conn{connector}_Pmax']) ,0)
                system.PEV += pdisp
                if evcs['control'] == 'current':
                    limit = int(pdisp * 1000 / evcs[f'conn{connector}_Vnom'])
                    control.update({(evcs["id"], connector_id): [limit, "A"]})
                elif evcs['control'] == 'power':    
                    limit = pdisp
                    control.update({(evcs["id"], connector_id): [limit, "W"]})
                


    if NOTIFICATION: print('Start BESS dispatch')
    # check bess state of charge
    par = software.get_timeconfig(1)
    tmin_d = datetime.strptime(par["tmin_d"], "%H:%M")
    tmax_d = datetime.strptime(par["tmax_d"], "%H:%M")
    tmin_c = datetime.strptime(par["tmin_c"], "%H:%M")
    tmax_c = datetime.strptime(par["tmax_c"], "%H:%M")
    now = datetime.now()
    if tmin_d <= now <= tmax_d:
        for bess in system.bess_to_discharge:
            
            pdisp = min(system.PEV, bess['Pmax'])
            response = opt.bess.send_command(bess['id'], -pdisp)
            if response == {'status': 'Accepted'}:
                if NOTIFICATION: print(f"discharging BESS {bess['id']} with {pdisp}kW")
                system.PEV -= pdisp
                
    elif system.PEV > system.Pnom + system.PPV:
        Pbess = system.PEV - system.Pnom - system.PPV
        for bess in system.bess_to_discharge:
            pdisp = min(Pbess, bess['Pmax'])
            response = opt.bess.send_command(bess['id'], -pdisp)
            if response == {'status': 'Accepted'}:
                if NOTIFICATION: print(f"discharging BESS {bess['id']} with {pdisp}kW")
                Pbess -= pdisp
            if Pbess <= 0:
                break
    

    elif system.PPV > system.PEV:
        Pbess = system.PPV - system.PEV
        for bess in system.bess_to_charge + system.bess_to_discharge:
            pdisp = min(Pbess, bess['Pmax'])
            response = opt.bess.send_command(bess['id'], pdisp)
            if response == {'status': 'Accepted'}:
                if NOTIFICATION: print(f"charging BESS {bess['id']} with {pdisp}kW")
                Pbess -= pdisp
            if Pbess <= 0:
                break
                
    elif tmin_c <= now <= tmax_c:
        Pbess = system.Pnom + system.PPV - system.PEV
        for bess in system.bess_half_charged:
            if system.PEV <= system.Pnom + system.PPV - bess['Pmax']:
                pdisp = min(Pbess - system.PEV, bess['Pmax'])
                response = opt.bess.send_command(bess['id'], pdisp)
                if response == {'status': 'Accepted'}:
                    if NOTIFICATION: print(f"charging BESS {bess['id']} with {pdisp}kW")
                    Pbess -= pdisp
                    system.Ptotal -= bess['Pmax']
                    system.Ptotal -= pdisp

    else:
        for bess in system.bess:
            #set 0
            response = opt.bess.send_command(bess['id'], 0.001)
            if response == {'status': 'Accepted'}:
                if NOTIFICATION: print(f"Set BESS {bess['id']} with 0kW")
                system.Ptotal -= bess['Pmax']
                



    for evcs_name, connector_id in control:
        for evcs in system.charging:
            if evcs['id'] == evcs_name:
                limit = control[(evcs_name, connector_id)][0]
                unit = control[(evcs_name, connector_id)][1]
                if NOTIFICATION: print(f'Setting EVCS {evcs_name} to {limit} {unit}')
                data = dojot.set_charging_profile(evcs_name, connector_id, unit, limit, evcs['protocol'])
                if NOTIFICATION: print(data)


def set_zero(setup):
    #zero all bess and evcs
    for evcs in software.get_evcs_by_setup_id(setup['id']):
            for connector in range(1, evcs['nconn'] + 1):
                if evcs[f"conn{connector}_Pmax"] < 10:
                    Pmin = 1.5
                elif evcs[f"conn{connector}_Pmax"] < 30:
                    Pmin = 3
                elif evcs[f"conn{connector}_Pmax"] < 50:
                    Pmin = 5
                else:
                    Pmin = 10
    
                if NOTIFICATION: print(f'Setting EVCS {evcs["id"]} to {Pmin} kW')
                if evcs['control'] == 'current':
                    limit = int(Pmin * 1000 / evcs[f'conn{connector}_Vnom'])
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'A', limit, evcs['protocol'])
                    if NOTIFICATION: print(data)                    
                    if data != {'status': 'Accepted'}: 
                        if NOTIFICATION: print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                    else:
                        if NOTIFICATION: print(f'Success setting EVCS {evcs["id"]} to {limit} A')

                
                elif evcs['control'] == 'power':
                    limit = Pmin
                    if evcs['nconn'] == 1:
                        connector_id = 0
                    else:
                        connector_id = connector
                    data = dojot.set_charging_profile(evcs['id'], connector_id, 'W', limit * 1000, evcs['protocol'])
                    if NOTIFICATION: print(data)
                    if data != {'status': 'Accepted'}: 
                        if NOTIFICATION: print(f'Error setting EVCS {evcs["id"]} to {limit} A')
                    else:
                        if NOTIFICATION: print(f'Success setting EVCS {evcs["id"]} to {limit} A')


    for bess in software.get_bess_by_setup_id(setup['id']):
        response = opt.bess.send_command(bess['id'], 0.001)
        if NOTIFICATION: print(response)
    return



def cron_function():
    setups = software.get_setups()
    for setup in setups:
        if setup is not None:
            try:
                optimize(setup)
            except:
                if NOTIFICATION: print(f"Error in setup {setup['id']}")
                if SECURITY_MODE:
                    set_zero(setup)
    return


if __name__ == '__main__':
    cron_function()
