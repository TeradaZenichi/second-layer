from opt import software
from opt import dojot

class SYSTEM:
    def __init__(self, setup):
        self.Pmax = setup['Pmax']
        self.Vnom = setup['Vnom']
        self.controllable = setup['controllable']
        self.available = []
        self.charging  = []
        self.evcs = []
        self.bess = []
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
            total_power += bess['Pmax']
        for pv in self.pv:
            # check pv power generation
            total_power += pv['Pmax']
        
        for v2g in self.v2g:
            # check v2g state of charge
            total_power += v2g['Pmax']
    

    def evcs_status(self):
        par = software.get_timeconfig(1)
        for evcs in self.evcs:
            heartbeat = dojot.check_data(par["URL"], evcs['id'], "heartbeatReq", 240)
            statusNotification = dojot.check_data(par["URL"], evcs['id'], "statusNotificationReq", 240)
            if heartbeat:
                if statusNotification:
                    if statusNotification['value']['status'] in ['Preparing', 'Charging', "Reserved"]:
                        self.charging.append(evcs)
                else:
                    self.available.append(evcs)

            a = 1
            
        

def optimize(setup):
    system = SYSTEM(setup)
    system.add_devices(setup)
    system.total_power()
    print("Checking EVCS status")
    system.evcs_status()
    print("Setting EVCS to 0")
    Ptotal = system.Ptotal
    for evcs in system.available:
        if evcs is not None:
            print(f'Setting EVCS {evcs["device_id"]} to 0')
            dojot.set_charging_profile(evcs['device_id'], evcs['connector_id'], evcs['control'], 1.5)
    
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
                control.update({(evcs, connector_id): pdisp})
                

    # Activate BESS before EVCS   
    for bess in system.bess:
        # check bess state of charge
        print('BESS dispatch')


    for evcs, connector_id in control:
        if evcs['control'] == 'current':
            limit = int(control[(evcs, connector_id)] * 1000 / evcs[f'conn{connector_id}_Vnom'])
            data = dojot.set_charging_profile(evcs['id'], connector_id, 'A', limit)
            print(data)

        elif evcs['control'] == 'power':
            limit = control[(evcs, connector_id)]
            data = dojot.set_charging_profile(evcs['id'], connector_id, 'W', limit * 1000)
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
